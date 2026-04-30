"""
运维巡检端点
POST /api/v2/inspection/run
"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from loguru import logger

from ....mcp.enhanced_client import EnhancedMCPClient
from ....llm.processor import EnhancedLLMProcessor
from ....mcp.types import ChatMessage
from ....security.auth import require_permission
from ..dependencies import (
    get_active_container,
    get_llm_processor as resolve_llm_processor,
    get_mcp_client as resolve_mcp_client,
)


router = APIRouter(
    prefix="/inspection",
    tags=["Inspection"],
    dependencies=[Depends(require_permission("inspection:run"))],
)


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


def _get_mcp_client(request: Request) -> Optional[EnhancedMCPClient]:
    return resolve_mcp_client(request)


def _get_llm_processor(request: Request) -> EnhancedLLMProcessor:
    return resolve_llm_processor(request)


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

        # 如果k8s-cluster-summary不可用，尝试使用其他工具组合
        logger.info("尝试使用备用工具组合进行巡检...")
        try:
            # 使用知识图谱资源指标查询工具
            metrics_result = await mcp_client.call_tool("k8s-resource-metrics-query", {
                "cpu_threshold": 70.0,
                "memory_threshold": 70.0,
                "include_optimization_only": False,
                "limit": 50
            })

            # 获取基础集群信息
            pods_result = await mcp_client.call_tool("k8s-get-pods", {
                "all_namespaces": True,
                "show_status": True
            })

            # 组合结果
            cluster_summary = {
                "cluster_overview": {
                    "status": "partial_data",
                    "message": "使用备用工具获取集群信息"
                },
                "resource_metrics": metrics_result,
                "pod_status": pods_result
            }

            logger.info("✅ 使用备用工具组合成功获取巡检数据")

        except Exception as backup_e:
            logger.error(f"备用工具调用也失败: {backup_e}")
            raise HTTPException(status_code=502, detail=f"集群巡检工具调用失败: 主工具({e}), 备用工具({backup_e})")

    # 2) 使用LLM生成Markdown分析
    system_prompt = (
        "你是资深SRE，请基于下列 Kubernetes 集群巡检原始数据，"
        "生成面向运维群的 Markdown 报告：\n"
        "- 主标题请以 '🔥 ' 开头，例如：'# 🔥 Kubernetes 集群巡检报告 - YYYY-MM-DD'\n"
        "- 必含结构：现状总览 -> 资源监控 -> 异常清单（含严重度）-> 根因猜测 -> 影响范围 -> 建议措施 -> 待跟进事项\n"
        "- 资源监控部分重点关注：CPU使用率、内存使用率、节点健康状态、资源压力等级\n"
        "- 如果数据中包含resource_monitoring或resource_summary，请详细分析资源使用情况\n"
        "- 控制长度并提供可执行建议；如信息不足，列出需要补充的数据。\n"
        "- Markdown 输出规范（重要）：仅在确为代码/命令/配置时使用三反引号代码块；正文、段落、列表、表格、标题、引用等一律不要放入代码块。\n"
        "- 代码块语言请使用标准、紧随三反引号的语言标记，例如 '```bash'、'```yaml'、'```json'；不要写成 '``` yaml'、'```yaml1'、'``bash' 等非标准形式，反引号数量必须为3。\n"
        "- 若需绘制流程/架构图，仅在确有图形内容时使用 '```mermaid'；不要将普通文本放入 mermaid 代码块。\n"
        "- 严禁将整篇报告包裹在单个代码块中，报告主体必须是正常的 Markdown 文本。"
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
            dingtalk_bot = get_active_container().dingtalk_bot
            if dingtalk_bot and getattr(dingtalk_bot, "webhook_url", None):
                # 优先使用Markdown分片发送，减少长度与关键字限制问题
                sent_ok = await dingtalk_bot.send_markdown_message(
                    dingtalk_bot.webhook_url,
                    title="🔥 K8s 巡检报告",
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
        return f"# 🔥 巡检结果(回退)\n\n```json\n{text}\n```\n"
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
    ding_enabled = get_active_container().dingtalk_bot is not None

    result = await perform_inspection(
        mcp_client=mcp_client,
        llm_processor=llm_processor,
        scope=request.scope,
        options=request.options,
        dingtalk_enabled=ding_enabled,
    )
    return result
