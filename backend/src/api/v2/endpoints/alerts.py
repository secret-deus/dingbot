"""
资源告警API端点

处理来自K8s MCP服务器的资源告警请求，
包括LLM分析和钉钉通知发送。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from loguru import logger
from ..dependencies import get_active_container
from ....security.auth import require_permission

# 导入后端服务 - 通过运行时容器获取，避免 API 层导入 main
def get_llm_processor():
    """获取LLM处理器实例"""
    return get_active_container().llm_processor

def get_dingtalk_bot():
    """获取钉钉机器人实例"""
    return get_active_container().dingtalk_bot

def get_chat_message_class():
    """获取ChatMessage类"""
    try:
        import sys
        import os
        # 添加backend/src到路径
        backend_src = os.path.join(os.path.dirname(__file__), '..', '..')
        if backend_src not in sys.path:
            sys.path.insert(0, backend_src)
        from mcp.types import ChatMessage
        return ChatMessage
    except ImportError:
        # 返回一个简单的占位符类
        class ChatMessage:
            def __init__(self, role: str, content: str, tool_call_id: str = None, function_call = None):
                self.role = role
                self.content = content
                self.tool_call_id = tool_call_id
                self.function_call = function_call
        return ChatMessage


router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(require_permission("alerts:read"))],
)
WRITE_DEPENDENCIES = [Depends(require_permission("alerts:write"))]


class ResourceAlertData(BaseModel):
    """资源告警数据模型"""
    resource_id: str = Field(..., description="资源标识符")
    metrics: Dict[str, Any] = Field(..., description="资源指标数据")
    timestamp: str = Field(..., description="告警时间戳")
    source: str = Field(default="k8s-mcp-server", description="告警来源")
    alert_reasons: Optional[List[str]] = Field(None, description="告警原因列表")
    thresholds: Optional[Dict[str, float]] = Field(None, description="告警阈值")
    current_utilization: Optional[Dict[str, float]] = Field(None, description="当前利用率")


class AlertProcessResult(BaseModel):
    """告警处理结果"""
    success: bool = Field(..., description="处理是否成功")
    alert_id: str = Field(..., description="告警ID")
    llm_analysis: Optional[Dict[str, Any]] = Field(None, description="LLM分析结果")
    dingtalk_sent: Optional[Dict[str, Any]] = Field(None, description="钉钉发送结果")
    timestamp: str = Field(..., description="处理时间戳")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


# 全局统计信息
alert_stats = {
    "total_alerts_received": 0,
    "alerts_processed_success": 0,
    "alerts_processed_failed": 0,
    "llm_analysis_success": 0,
    "llm_analysis_failed": 0,
    "dingtalk_sent_success": 0,
    "dingtalk_sent_failed": 0,
    "last_alert_time": None,
    "last_processing_time_ms": 0
}


@router.post("/resource", response_model=AlertProcessResult, dependencies=WRITE_DEPENDENCIES)
async def handle_resource_alert(
    alert_data: ResourceAlertData,
    background_tasks: BackgroundTasks
) -> AlertProcessResult:
    """处理资源告警请求

    接收来自K8s MCP服务器的资源告警数据，
    进行LLM分析并发送钉钉通知。

    Args:
        alert_data: 资源告警数据
        background_tasks: 后台任务

    Returns:
        AlertProcessResult: 处理结果

    Raises:
        HTTPException: 处理失败时抛出
    """
    start_time = datetime.now()
    alert_id = f"alert-{start_time.strftime('%Y%m%d%H%M%S')}-{hash(alert_data.resource_id) % 10000:04d}"

    logger.info(f"接收到资源告警: {alert_data.resource_id} (ID: {alert_id})")

    try:
        # 更新统计信息
        alert_stats["total_alerts_received"] += 1
        alert_stats["last_alert_time"] = start_time.isoformat()

        # 构建处理结果
        result = AlertProcessResult(
            success=False,  # 默认为失败，处理成功后更新
            alert_id=alert_id,
            timestamp=start_time.isoformat(),
            processing_time_ms=0
        )

        # 异步处理LLM分析和钉钉发送
        background_tasks.add_task(
            _process_alert_async,
            alert_id,
            alert_data,
            start_time
        )

        # 立即返回接收确认
        result.success = True
        alert_stats["alerts_processed_success"] += 1

        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(processing_time)
        alert_stats["last_processing_time_ms"] = result.processing_time_ms

        logger.info(f"告警接收成功: {alert_id}, 处理时间: {result.processing_time_ms}ms")
        return result

    except Exception as e:
        alert_stats["alerts_processed_failed"] += 1

        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        alert_stats["last_processing_time_ms"] = int(processing_time)

        logger.error(f"处理资源告警失败 {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"处理告警失败: {str(e)}")


async def _process_alert_async(alert_id: str, alert_data: ResourceAlertData, start_time: datetime):
    """异步处理告警数据

    Args:
        alert_id: 告警ID
        alert_data: 告警数据
        start_time: 开始时间
    """
    logger.info(f"开始异步处理告警: {alert_id}")

    llm_result = None
    dingtalk_result = None

    try:
        # 1. LLM分析
        llm_result = await _perform_llm_analysis(alert_id, alert_data)

        # 2. 钉钉发送
        dingtalk_result = await _send_dingtalk_notification(alert_id, alert_data, llm_result)

        total_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"告警异步处理完成: {alert_id}, 总耗时: {total_time:.1f}ms")

    except Exception as e:
        logger.error(f"异步处理告警失败 {alert_id}: {e}")


async def _perform_llm_analysis(alert_id: str, alert_data: ResourceAlertData) -> Dict[str, Any]:
    """执行LLM分析

    Args:
        alert_id: 告警ID
        alert_data: 告警数据

    Returns:
        Dict[str, Any]: LLM分析结果
    """
    try:
        logger.info(f"开始LLM分析: {alert_id}")

        # 获取LLM处理器
        llm_processor = get_llm_processor()
        if not llm_processor:
            logger.warning(f"LLM处理器未初始化: {alert_id}")
            alert_stats["llm_analysis_failed"] += 1
            return {
                "status": "skipped",
                "reason": "LLM处理器未初始化",
                "timestamp": datetime.now().isoformat()
            }

        # 构建分析提示词
        analysis_prompt = _build_llm_analysis_prompt(alert_data)

        # 创建聊天消息
        ChatMessage = get_chat_message_class()
        messages = [
            ChatMessage(role="system", content="""你是一个资深的Kubernetes运维专家和系统架构师，拥有丰富的大规模集群运维经验。

你的专长包括：
- 深度分析K8s资源使用模式和性能瓶颈
- 识别潜在的系统风险和业务影响
- 提供专业的扩缩容和性能优化建议
- 制定完整的监控和运维策略

分析风格要求：
- 提供详细、全面的技术分析，不要过于简短
- 对每个问题都要深入分析根本原因
- 提供具体可操作的解决方案和命令示例
- 包含专业的运维见解和最佳实践
- 评估业务影响和系统风险
- 使用专业术语但保持清晰易懂"""),
            ChatMessage(role="user", content=analysis_prompt)
        ]

        # 调用LLM分析
        llm_response = await llm_processor._chat_without_tools(messages)

         # ProcessResult对象处理
        if llm_response and llm_response.content and not llm_response.content.startswith("调用LLM服务失败"):
            alert_stats["llm_analysis_success"] += 1
            logger.info(f"LLM分析成功: {alert_id}")
            return {
                "status": "success",
                "analysis": llm_response.content,
                "timestamp": datetime.now().isoformat(),
                "model_info": None,  # ProcessResult没有model_info字段
                "token_usage": llm_response.usage
            }
        else:
            alert_stats["llm_analysis_failed"] += 1
            # 检查是否是LLM服务调用失败
            if llm_response and llm_response.content and llm_response.content.startswith("调用LLM服务失败"):
                error_msg = llm_response.content
            else:
                error_msg = "LLM返回空内容" if llm_response else "LLM响应为空"
            logger.warning(f"LLM分析失败: {alert_id}, 错误: {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        alert_stats["llm_analysis_failed"] += 1
        logger.error(f"LLM分析异常: {alert_id}, 错误: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def _build_llm_analysis_prompt(alert_data: ResourceAlertData) -> str:
    """构建LLM分析提示词

    Args:
        alert_data: 告警数据

    Returns:
        str: 分析提示词
    """
    metrics = alert_data.metrics
    resource_parts = alert_data.resource_id.split("/")
    resource_type = resource_parts[0] if len(resource_parts) > 0 else "unknown"
    namespace = resource_parts[1] if len(resource_parts) > 1 else "default"
    app_name = resource_parts[2] if len(resource_parts) > 2 else "unknown"

    prompt = f"""## K8s资源告警分析请求

### 告警信息
- **资源类型**: {resource_type}
- **命名空间**: {namespace}
- **应用名称**: {app_name}
- **告警时间**: {alert_data.timestamp}

### 资源指标
- **CPU利用率**: {metrics.get('avg_cpu_utilization', 'N/A')}%
- **内存利用率**: {metrics.get('avg_memory_utilization', 'N/A')}%
- **分析周期**: {metrics.get('days_analyzed', 'N/A')}天
- **数据点数**: {metrics.get('total_data_points', 'N/A')}个

### 告警详情"""

    if alert_data.alert_reasons:
        prompt += "\n**告警原因**:\n"
        for reason in alert_data.alert_reasons:
            prompt += f"- {reason}\n"

    if alert_data.thresholds:
        prompt += "\n**告警阈值**:\n"
        for metric, threshold in alert_data.thresholds.items():
            prompt += f"- {metric}: {threshold:.0%}\n"

    if alert_data.current_utilization:
        prompt += "\n**当前利用率**:\n"
        for metric, utilization in alert_data.current_utilization.items():
            prompt += f"- {metric}: {utilization:.1%}\n"

    # 添加异常资源详情
    if metrics and metrics.get("abnormal_details"):
        abnormal_details = metrics.get("abnormal_details", [])
        total_resources = metrics.get("total_resources", 0)
        abnormal_resources = metrics.get("abnormal_resources", 0)

        prompt += f"\n**资源概况**:\n"
        prompt += f"- 总资源数: {total_resources}\n"
        prompt += f"- 异常资源数: {abnormal_resources}\n"
        prompt += f"- 异常比例: {(abnormal_resources/total_resources*100):.1f}%\n"

        prompt += "\n**异常资源详情**:\n"
        # 使用紧凑格式：名称|CPU%|内存%|问题类型
        prompt += "```\n"
        prompt += "资源名称                           |CPU% |内存%     |问题\n"
        prompt += "-----------------------------------|-----|----------|----\n"

        for detail in abnormal_details:
            if isinstance(detail, dict):
                name = detail.get("name", "未知资源")
                cpu_util = detail.get("cpu_utilization", 0)
                memory_util = detail.get("memory_utilization", 0)
                problem = detail.get("problem", "异常")

                # 截断长名称，保持格式对齐
                display_name = name[:35] if len(name) > 35 else name
                # 简化问题描述
                problem_short = "内存高" if "内存" in problem else "CPU高" if "CPU" in problem else "异常"

                # 安全的数值格式化，处理可能的字符串类型
                try:
                    cpu_val = float(cpu_util) if cpu_util is not None else 0.0
                    memory_val = float(memory_util) if memory_util is not None else 0.0
                    prompt += f"{display_name:<35}|{cpu_val:>4.1f}|{memory_val:>10.0f}|{problem_short}\n"
                except (ValueError, TypeError):
                    # 如果转换失败，使用字符串格式
                    cpu_str = str(cpu_util)[:4] if cpu_util is not None else "0"
                    memory_str = str(memory_util)[:10] if memory_util is not None else "0"
                    prompt += f"{display_name:<35}|{cpu_str:>4}|{memory_str:>10}|{problem_short}\n"
            elif isinstance(detail, str):
                # 字符串格式的详情，尝试解析或直接显示
                display_detail = detail[:50] if len(detail) > 50 else detail
                prompt += f"{display_detail:<35}|  - |    -     |异常\n"

        prompt += "```\n"

    # 添加建议信息
    if metrics and metrics.get("recommendations"):
        recommendations = metrics.get("recommendations", [])
        prompt += "\n**系统建议**: "
        # 使用分号分隔的紧凑格式
        rec_list = []
        for rec in recommendations:
            # 简化建议文本，去掉冗余词汇
            simplified_rec = rec.replace("建议", "").replace("或检查", "/检查").replace("增加", "↑").replace("减少", "↓")
            rec_list.append(simplified_rec.strip())
        prompt += "; ".join(rec_list) + "\n"


    # 添加集群上下文信息
    prompt += f"""

### 集群上下文
- **分析时间**: {alert_data.timestamp}
- **分析范围**: {namespace} 命名空间
- **资源类型**: {resource_type}
- **监控周期**: {metrics.get('days_analyzed', 'N/A')} 天
- **数据完整性**: {metrics.get('total_data_points', 'N/A')} 个数据点

### 分析要求
作为资深的Kubernetes运维专家，请基于以上信息提供**全面详细**的分析报告。

**输出格式要求**：

## 📊 概况分析
简要总结当前集群资源状况和主要发现

## 🔴 异常资源清单

| 资源名称 | CPU利用率 | 内存利用率 | 问题分析 |
|---------|----------|-----------|---------|
| [资源名1] | [X]% | [Y]% | [具体问题描述] |
| [资源名2] | [X]% | [Y]% | [具体问题描述] |

## 🔍 详细分析
对每个重要的异常资源进行深入分析：
- **资源使用模式**：分析CPU和内存的使用特点
- **潜在原因**：分析可能导致资源异常的原因
- **影响评估**：评估对业务和系统稳定性的影响

## ⚠️ 风险评估
- **紧急程度**：评估问题的紧急程度和处理优先级
- **影响范围**：分析可能影响的服务和用户
- **潜在风险**：识别可能的连锁反应和风险点

## 🚀 处理建议

### 立即处理措施
针对高优先级问题的具体操作建议

### 中长期优化
- **扩容建议**：具体的扩容方案和资源配置建议
- **缩容建议**：资源优化和成本控制建议
- **性能优化**：应用层面的优化建议
- **监控改进**：监控和告警策略优化

## 📈 后续监控
建议持续关注的指标和监控点

**分析要求**：
1. 提供详细的技术分析，不要过于简短
2. 对每个异常资源都要分析具体原因和影响
3. 提供可操作的具体建议和命令示例
4. 包含专业的运维见解和最佳实践
5. 使用专业术语但保持可读性"""

    return prompt


async def _send_dingtalk_notification(
    alert_id: str,
    alert_data: ResourceAlertData,
    llm_result: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """发送钉钉通知

    Args:
        alert_id: 告警ID
        alert_data: 告警数据
        llm_result: LLM分析结果

    Returns:
        Dict[str, Any]: 发送结果
    """
    try:
        logger.info(f"开始发送钉钉通知: {alert_id}")

        # 创建钉钉Bot实例
        dingtalk_bot = get_dingtalk_bot()

        # 构建告警消息
        message = _build_dingtalk_message(alert_data, llm_result)

        # 发送Markdown消息
        # 从环境变量获取webhook URL
        import os
        webhook_url = os.getenv("DINGTALK_WEBHOOK_URL")

        if not webhook_url:
            logger.warning(f"钉钉Webhook URL未配置: {alert_id}")
            return {
                "status": "skipped",
                "error": "钉钉Webhook URL未配置",
                "timestamp": datetime.now().isoformat()
            }
        if not dingtalk_bot:
            logger.warning(f"钉钉Bot未初始化: {alert_id}")
            return {
                "status": "skipped",
                "error": "钉钉Bot未初始化",
                "timestamp": datetime.now().isoformat()
            }

        send_result = await dingtalk_bot.send_markdown_message(
            webhook_url=webhook_url,
            title=f"🔥 K8s资源告警 - {alert_data.resource_id}",
            markdown_text=message
        )

        if send_result:
            alert_stats["dingtalk_sent_success"] += 1
            logger.info(f"钉钉通知发送成功: {alert_id}")
            return {
                "status": "success",
                "message_length": len(message),
                "timestamp": datetime.now().isoformat(),
                "response": send_result
            }
        else:
            alert_stats["dingtalk_sent_failed"] += 1
            logger.warning(f"钉钉通知发送失败: {alert_id}")
            return {
                "status": "failed",
                "error": "发送失败",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        alert_stats["dingtalk_sent_failed"] += 1
        logger.error(f"钉钉通知发送异常: {alert_id}, 错误: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def _build_dingtalk_message(alert_data: ResourceAlertData, llm_result: Optional[Dict[str, Any]]) -> str:
    """构建钉钉消息内容

    Args:
        alert_data: 告警数据
        llm_result: LLM分析结果

    Returns:
        str: 钉钉消息内容
    """
    metrics = alert_data.metrics

    # 计算紧急度
    urgency = _calculate_urgency(alert_data)

    # 获取异常资源数量用于标题
    abnormal_count = metrics.get('abnormal_resources', 0)

    message = f"""## 🔥 K8s资源告警 - 发现 {abnormal_count} 个异常资源"""

    # 添加LLM分析结果或退化摘要
    if llm_result and llm_result.get("status") == "success":
        analysis = llm_result.get("analysis", "")
        if len(analysis) > 2000:  # LLM分析有长度限制
            analysis = analysis[:2000] + "..."
        message += f"\n\n{analysis}"
    else:
        # LLM分析失败时的退化逻辑：使用原始数据摘要
        fallback_analysis = _generate_fallback_analysis(alert_data)
        # 退化分析不截断，确保显示完整的异常资源清单
        message += f"\n\n{fallback_analysis}"

    return message


def _generate_fallback_analysis(alert_data: ResourceAlertData) -> str:
    """生成极简的退化分析摘要 - 只包含异常资源清单和扩容/缩容建议

    Args:
        alert_data: 告警数据

    Returns:
        str: 极简的退化分析摘要
    """
    try:
        analysis_parts = []

        # 提取基础统计信息
        metrics = alert_data.metrics
        if metrics:
            abnormal_details = metrics.get("abnormal_details", [])

            if abnormal_details:
                analysis_parts.append("### 🔴 异常资源清单")
                analysis_parts.append("")

                # 使用表格格式显示所有异常资源
                analysis_parts.append("| 资源名称 | CPU利用率 | 内存利用率 |")
                analysis_parts.append("|---------|----------|-----------|")

                for detail in abnormal_details:
                    if isinstance(detail, dict):
                        name = detail.get("name", "未知资源")
                        memory_util = detail.get("memory_utilization", "N/A")
                        cpu_util = detail.get("cpu_utilization", "N/A")

                        # 表格格式：每个资源占一行
                        analysis_parts.append(f"| {name} | {cpu_util} | {memory_util} |")

                # 添加资源总数提示
                total_count = len(abnormal_details)
                analysis_parts.append("")
                analysis_parts.append(f"*共 {total_count} 个异常资源*")

                analysis_parts.append("")
                analysis_parts.append("### 🚀 处理建议")
                analysis_parts.append("")
                analysis_parts.append("**扩容**: 增加Pod副本数或资源配额")
                analysis_parts.append("")
                analysis_parts.append("**缩容**: 减少资源请求或优化应用性能")

        if not analysis_parts:
            # 如果没有提取到具体信息，提供通用分析
            analysis_parts = [
                "### 📊 基础分析",
                "",
                "检测到K8s集群资源异常",
                "",
                "### 🚀 处理建议",
                "",
                "**扩容**: 增加Pod副本数或资源配额",
                "",
                "**缩容**: 减少资源请求或优化应用性能"
            ]

        return "\n".join(analysis_parts)

    except Exception as e:
        logger.warning(f"生成退化分析失败: {e}")
        return "### 📊 基础分析\n检测到资源异常\n\n### 🚀 处理建议\n**扩容**: 增加资源配额\n**缩容**: 优化配置"


def _calculate_urgency(alert_data: ResourceAlertData) -> Dict[str, str]:
    """计算告警紧急度

    Args:
        alert_data: 告警数据

    Returns:
        Dict[str, str]: 紧急度信息
    """
    if not alert_data.current_utilization:
        return {"emoji": "⚠️", "level": "P2", "description": "中等"}

    max_util = max(
        alert_data.current_utilization.get("memory", 0),
        alert_data.current_utilization.get("cpu", 0)
    )

    if max_util >= 0.9:  # 90%以上
        return {"emoji": "🚨", "level": "P0", "description": "紧急 - 立即处理"}
    elif max_util >= 0.8:  # 80-90%
        return {"emoji": "🔥", "level": "P1", "description": "高 - 优先处理"}
    elif max_util >= 0.7:  # 70-80%
        return {"emoji": "⚠️", "level": "P2", "description": "中等 - 及时处理"}
    else:
        return {"emoji": "ℹ️", "level": "P3", "description": "低 - 正常处理"}


@router.get("/stats")
async def get_alert_statistics() -> Dict[str, Any]:
    """获取告警处理统计信息

    Returns:
        Dict[str, Any]: 统计信息
    """
    return {
        "statistics": alert_stats.copy(),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/test", dependencies=WRITE_DEPENDENCIES)
async def test_alert_processing(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """测试告警处理功能

    Args:
        background_tasks: 后台任务

    Returns:
        Dict[str, Any]: 测试结果
    """
    # 创建测试告警数据
    test_alert = ResourceAlertData(
        resource_id="deployment/test/demo-app",
        metrics={
            "avg_cpu_utilization": 85.0,
            "avg_memory_utilization": 78.0,
            "days_analyzed": 7,
            "total_data_points": 168,
            "analysis_period": "test period"
        },
        timestamp=datetime.now().isoformat(),
        source="test-client",
        alert_reasons=["CPU利用率过高: 85.0% > 80.0%"],
        thresholds={"cpu": 0.8, "memory": 0.7},
        current_utilization={"cpu": 0.85, "memory": 0.78}
    )

    # 处理测试告警
    result = await handle_resource_alert(test_alert, background_tasks)

    return {
        "test_status": "completed",
        "alert_result": result,
        "message": "测试告警已提交处理"
    }
