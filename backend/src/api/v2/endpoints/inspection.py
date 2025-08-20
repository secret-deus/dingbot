"""
运维巡检端点
POST /api/v2/inspection/run
"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from ....mcp.enhanced_client import EnhancedMCPClient
from ....llm.processor import EnhancedLLMProcessor
from ....mcp.types import ChatMessage


router = APIRouter(prefix="/inspection", tags=["Inspection"])


class InspectionScope(BaseModel):
    namespace: Optional[str] = Field(default=None, description="单一命名空间")
    includeNamespaces: Optional[List[str]] = Field(default=None, description="命名空间列表")
    maxDepth: int = Field(default=2, description="关联查询最大深度")


class InspectionOptions(BaseModel):
    sendToDingTalk: bool = Field(default=True, description="是否推送到钉钉")
    summaryType: str = Field(default="overview", description="摘要类型")
    includeAnomalies: bool = Field(default=True, description="是否包含异常检测")
    maxSizeKB: int = Field(default=16, description="最大输出KB")
    llmModel: Optional[str] = Field(default=None, description="可选覆盖模型名称")


class InspectionRequest(BaseModel):
    scope: InspectionScope = Field(default_factory=InspectionScope)
    options: InspectionOptions = Field(default_factory=InspectionOptions)


class InspectionResponse(BaseModel):
    analysisId: str
    analysisMarkdown: str
    toolPayload: Dict[str, Any]
    dingTalk: Dict[str, Any]


def _get_mcp_client() -> Optional[EnhancedMCPClient]:
    from main import mcp_client
    return mcp_client


def _get_llm_processor() -> EnhancedLLMProcessor:
    from main import llm_processor
    if not llm_processor:
        raise HTTPException(status_code=503, detail="LLM处理器未初始化")
    return llm_processor


async def perform_inspection(
    mcp_client: EnhancedMCPClient,
    llm_processor: EnhancedLLMProcessor,
    scope: InspectionScope,
    options: InspectionOptions,
    dingtalk_enabled: bool = False,
) -> Dict[str, Any]:
    """执行一次巡检，返回分析结果与钉钉发送状态。"""
    if not mcp_client or getattr(mcp_client, "status", None) is None:
        raise HTTPException(status_code=503, detail="MCP客户端不可用")

    # 1) 调用K8s-MCP聚合工具：集群概要 + 异常
    tool_params = {
        "summary_type": options.summaryType,
        "max_size_kb": options.maxSizeKB,
        "include_anomalies": options.includeAnomalies,
    }
    logger.info(f"开始调用 k8s-cluster-summary, 参数: {tool_params}")

    try:
        cluster_summary = await mcp_client.call_tool("k8s-cluster-summary", tool_params)
    except Exception as e:
        logger.error(f"k8s-cluster-summary 调用失败: {e}")
        raise HTTPException(status_code=502, detail=f"集群摘要工具调用失败: {e}")

    # 2) 使用LLM生成Markdown分析
    system_prompt = (
        "你是资深SRE，请基于下列 Kubernetes 集群巡检原始数据，"
        "生成面向运维群的 Markdown 报告：\n"
        "- 必含结构：现状总览 -> 异常清单（含严重度）-> 根因猜测 -> 影响范围 -> 建议措施 -> 待跟进事项\n"
        "- 控制长度并提供可执行建议；如信息不足，列出需要补充的数据。"
    )

    try:
        # 仅使用LLM，不再触发工具
        json_text = json.dumps(cluster_summary, ensure_ascii=False) if not isinstance(cluster_summary, str) else cluster_summary
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(
                role="user",
                content=(
                    "请根据以下JSON数据生成巡检报告（使用Markdown）：\n" + json_text[:20000]
                ),
            ),
        ]

        # 直接使用简化的无工具聊天
        result = await llm_processor._chat_without_tools(messages)  # 返回 ProcessResult
        analysis_text = result.content or "(LLM未返回内容)"
    except Exception as e:
        # 尝试展开tenacity RetryError
        try:
            from tenacity import RetryError
            if isinstance(e, RetryError) and e.last_attempt:
                inner = e.last_attempt.exception()
                logger.error(f"LLM生成分析失败(内部异常): {inner}")
            else:
                logger.error(f"LLM生成分析失败: {e}")
        except Exception:
            logger.error(f"LLM生成分析失败: {e}")

        # 回退：基于工具结果生成最小可读Markdown，避免接口失败
        analysis_text = _build_fallback_markdown(cluster_summary)

    # 3) 可选：推送钉钉
    ding_result = {"sent": False}
    if options.sendToDingTalk and dingtalk_enabled:
        try:
            from main import dingtalk_bot
            if dingtalk_bot and getattr(dingtalk_bot, "webhook_url", None):
                # 优先使用Markdown分片发送，减少长度与关键字限制问题
                sent_ok = await dingtalk_bot.send_markdown_message(
                    dingtalk_bot.webhook_url,
                    title="K8s 巡检报告",
                    markdown_text=analysis_text
                )
                ding_result = {"sent": bool(sent_ok)}
            else:
                logger.warning("钉钉Bot未配置，跳过发送")
                ding_result = {"sent": False, "reason": "not_configured"}
        except Exception as e:
            logger.error(f"钉钉发送失败: {e}")
            ding_result = {"sent": False, "error": str(e)}

    analysis_id = datetime.utcnow().isoformat() + "Z"
    return {
        "analysisId": analysis_id,
        "analysisMarkdown": analysis_text,
        "toolPayload": {"clusterSummary": cluster_summary},
        "dingTalk": ding_result,
    }


def _build_fallback_markdown(summary: Any) -> str:
    """当LLM失败时，生成最小可读的巡检报告。"""
    try:
        if isinstance(summary, dict):
            # 提取常见字段
            nodes = summary.get("nodes") or summary.get("node_count")
            pods = summary.get("pods") or summary.get("pod_count")
            anomalies = summary.get("anomalies") or summary.get("anomaly_list") or summary.get("issues")
            namespaces = summary.get("namespaces") or summary.get("namespace_count")

            lines = ["# 巡检结果(回退)", "", "## 集群概览"]
            if nodes is not None:
                lines.append(f"- 节点数量: {nodes}")
            if pods is not None:
                lines.append(f"- Pod数量: {pods}")
            if namespaces is not None:
                lines.append(f"- 命名空间数量: {namespaces}")

            lines.append("")
            lines.append("## 异常与事件")
            if anomalies:
                if isinstance(anomalies, list):
                    for i, item in enumerate(anomalies[:20], 1):
                        lines.append(f"- {i}. {item}")
                else:
                    lines.append(f"- {anomalies}")
            else:
                lines.append("- 未检测到异常，或工具未返回异常字段")

            lines += [
                "",
                "## 建议",
                "- 若需详细分析，请检查LLM配置并重试",
                "- 建议查看 kube-system 命名空间事件与异常Pod日志",
            ]
            return "\n".join(lines)
        # 非字典结果
        text = summary if isinstance(summary, str) else json.dumps(summary, ensure_ascii=False)[:5000]
        return f"# 巡检结果(回退)\n\n```json\n{text}\n```\n"
    except Exception as e:
        logger.error(f"构建回退Markdown失败: {e}")
        return "# 巡检结果(回退)\n\n- 无法解析工具结果。"


@router.post("/run", response_model=InspectionResponse)
async def run_inspection(
    request: InspectionRequest,
    mcp_client: Optional[EnhancedMCPClient] = Depends(_get_mcp_client),
    llm_processor: EnhancedLLMProcessor = Depends(_get_llm_processor),
):
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP客户端未初始化")

    # 检查是否可推送钉钉
    try:
        from main import dingtalk_bot
        ding_enabled = dingtalk_bot is not None
    except Exception:
        ding_enabled = False

    result = await perform_inspection(
        mcp_client=mcp_client,
        llm_processor=llm_processor,
        scope=request.scope,
        options=request.options,
        dingtalk_enabled=ding_enabled,
    )
    return result


