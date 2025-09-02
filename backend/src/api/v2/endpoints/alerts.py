"""
资源告警API端点

处理来自K8s MCP服务器的资源告警请求，
包括LLM分析和钉钉通知发送。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from loguru import logger

# 导入后端服务
try:
    from ...llm.processor import get_llm_processor
    from ...dingtalk.bot import DingTalkBot
    from ...mcp.types import ChatMessage
except ImportError as e:
    logger.warning(f"导入后端服务失败: {e}")
    # 使用占位符
    def get_llm_processor():
        return None
    
    class DingTalkBot:
        def __init__(self):
            pass
        
        async def send_markdown_message(self, *args, **kwargs):
            return {"success": True, "message": "模拟发送成功"}
    
    class ChatMessage:
        def __init__(self, role: str, content: str):
            self.role = role
            self.content = content


router = APIRouter(prefix="/alerts", tags=["alerts"])


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


@router.post("/resource", response_model=AlertProcessResult)
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
        messages = [
            ChatMessage(role="system", content="你是一个专业的K8s运维专家，擅长分析资源问题并提供解决方案。"),
            ChatMessage(role="user", content=analysis_prompt)
        ]
        
        # 调用LLM分析
        llm_response = await llm_processor.process_messages(
            messages=messages,
            max_tokens=1000,
            temperature=0.3
        )
        
        if llm_response.get("success"):
            alert_stats["llm_analysis_success"] += 1
            logger.info(f"LLM分析成功: {alert_id}")
            return {
                "status": "success",
                "analysis": llm_response.get("content", ""),
                "timestamp": datetime.now().isoformat(),
                "model_info": llm_response.get("model_info"),
                "token_usage": llm_response.get("token_usage")
            }
        else:
            alert_stats["llm_analysis_failed"] += 1
            logger.warning(f"LLM分析失败: {alert_id}, 错误: {llm_response.get('error')}")
            return {
                "status": "failed",
                "error": llm_response.get("error", "未知错误"),
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
    
    prompt += """

### 分析要求
请基于以上信息，提供专业的分析和建议：

1. **问题分析**: 分析资源利用率异常的可能原因
2. **影响评估**: 评估对应用和集群的潜在影响
3. **解决方案**: 提供具体的优化建议和操作步骤
4. **预防措施**: 建议如何避免类似问题再次发生

请使用Markdown格式输出，内容要专业、简洁、可操作。"""
    
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
        dingtalk_bot = DingTalkBot()
        
        # 构建告警消息
        message = _build_dingtalk_message(alert_data, llm_result)
        
        # 发送Markdown消息
        send_result = await dingtalk_bot.send_markdown_message(
            title=f"🔥 K8s资源告警 - {alert_data.resource_id}",
            text=message
        )
        
        if send_result.get("success"):
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
            logger.warning(f"钉钉通知发送失败: {alert_id}, 错误: {send_result.get('error')}")
            return {
                "status": "failed",
                "error": send_result.get("error", "发送失败"),
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
    
    message = f"""## 🔥 K8s资源告警 {urgency['emoji']}

### 📋 资源信息
- **资源ID**: `{alert_data.resource_id}`
- **告警时间**: {alert_data.timestamp}
- **紧急度**: {urgency['level']} ({urgency['description']})

### 📊 资源利用率
- **CPU**: {metrics.get('avg_cpu_utilization', 'N/A')}%
- **内存**: {metrics.get('avg_memory_utilization', 'N/A')}%
- **分析周期**: {metrics.get('days_analyzed', 'N/A')}天"""
    
    # 添加告警原因
    if alert_data.alert_reasons:
        message += "\n\n### ⚠️ 告警原因\n"
        for reason in alert_data.alert_reasons:
            message += f"- {reason}\n"
    
    # 添加LLM分析结果
    if llm_result and llm_result.get("status") == "success":
        analysis = llm_result.get("analysis", "")
        if len(analysis) > 1000:  # 限制长度
            analysis = analysis[:1000] + "..."
        message += f"\n\n### 🤖 智能分析\n{analysis}"
    elif llm_result:
        message += f"\n\n### 🤖 智能分析\n> LLM分析失败: {llm_result.get('error', '未知错误')}"
    
    # 添加快速处理指南
    message += f"""

### 🚀 快速处理
1. **立即检查**: 使用 `kubectl top pods -n {alert_data.resource_id.split('/')[1]}` 查看实时资源使用
2. **扩容应用**: 考虑增加Pod副本数或资源配额
3. **查看日志**: 检查应用日志是否有异常
4. **监控趋势**: 观察资源使用趋势，避免再次告警

---
> 告警来源: {alert_data.source} | 处理时间: {datetime.now().strftime('%H:%M:%S')}"""
    
    return message


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


@router.post("/test")
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
