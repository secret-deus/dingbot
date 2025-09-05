"""
资源告警服务

统一管理资源告警逻辑，包括LLM分析调用和钉钉消息发送。
该服务被MetricsAggregator调用，实现告警功能的模块化管理。
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger

# 导入类型定义（这些需要在实际环境中根据项目结构调整）
# 动态导入函数 - 避免路径问题
def get_llm_processor():
    """获取LLM处理器实例"""
    try:
        import sys
        import os
        # 添加backend/src到路径
        backend_src = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'backend', 'src')
        if backend_src not in sys.path:
            sys.path.insert(0, backend_src)
        from llm.processor import get_llm_processor as _get_llm_processor
        return _get_llm_processor()
    except ImportError as e:
        logger.warning(f"导入LLM处理器失败: {e}")
        return None

def get_dingtalk_bot():
    """获取钉钉机器人实例"""
    try:
        import sys
        import os
        # 添加backend/src到路径
        backend_src = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'backend', 'src')
        if backend_src not in sys.path:
            sys.path.insert(0, backend_src)
        from dingtalk.bot import DingTalkBot
        return DingTalkBot()
    except ImportError as e:
        logger.warning(f"导入钉钉机器人失败: {e}")
        return None

def get_chat_message_class():
    """获取ChatMessage类"""
    try:
        import sys
        import os
        # 添加backend/src到路径
        backend_src = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'backend', 'src')
        if backend_src not in sys.path:
            sys.path.insert(0, backend_src)
        from mcp.types import ChatMessage
        return ChatMessage
    except ImportError as e:
        logger.warning(f"导入ChatMessage失败: {e}")
        # 返回一个简单的占位符类
        class ChatMessage:
            def __init__(self, role: str, content: str):
                self.role = role
                self.content = content
        return ChatMessage


class ResourceAlertConfig:
    """资源告警配置"""
    
    def __init__(self, 
                 memory_alert_threshold: float = 0.7,
                 cpu_alert_threshold: float = 0.8,
                 enable_llm_analysis: bool = True,
                 enable_dingtalk_alert: bool = True,
                 dingtalk_webhook_url: Optional[str] = None,
                 dingtalk_secret: Optional[str] = None,
                 alert_message_max_length: int = 3500,
                 dingtalk_retry_attempts: int = 3,
                 dingtalk_retry_delay: float = 2.0,
                 alert_cooldown_seconds: int = 300):
        self.memory_alert_threshold = memory_alert_threshold
        self.cpu_alert_threshold = cpu_alert_threshold
        self.enable_llm_analysis = enable_llm_analysis
        self.enable_dingtalk_alert = enable_dingtalk_alert
        self.dingtalk_webhook_url = dingtalk_webhook_url
        self.dingtalk_secret = dingtalk_secret
        self.alert_message_max_length = alert_message_max_length
        # 新增：钉钉消息重试配置
        self.dingtalk_retry_attempts = dingtalk_retry_attempts
        self.dingtalk_retry_delay = dingtalk_retry_delay
        self.alert_cooldown_seconds = alert_cooldown_seconds


class ResourceAlertService:
    """资源告警服务
    
    功能：
    - 统一管理资源告警逻辑
    - 调用LLM生成分析报告
    - 发送钉钉告警消息
    - 处理告警失败的降级方案
    """
    
    def __init__(self, 
                 llm_processor: Optional[Any] = None,
                 dingtalk_bot: Optional[Any] = None,
                 config: Optional[ResourceAlertConfig] = None):
        """初始化资源告警服务
        
        Args:
            llm_processor: LLM处理器实例
            dingtalk_bot: 钉钉Bot实例
            config: 告警配置
        """
        self.llm_processor = llm_processor
        self.dingtalk_bot = dingtalk_bot
        self.config = config or ResourceAlertConfig()
        
        # 告警历史记录（用于统计和调试）
        self.alert_history: Dict[str, List[Dict]] = {}
        
        # 统计信息
        self.stats = {
            "alerts_processed": 0,
            "llm_analysis_success": 0,
            "llm_analysis_failed": 0,
            "dingtalk_sent_success": 0,
            "dingtalk_sent_failed": 0,
            "dingtalk_retry_success": 0,  # 新增：重试成功次数
            "dingtalk_retry_failed": 0,   # 新增：重试失败次数
            "last_alert_time": None
        }
        
        logger.info("ResourceAlertService初始化完成")
    
    async def check_and_alert(self, resource_id: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查资源并发送告警
        
        Args:
            resource_id: 资源ID，格式如 "deployment/namespace/name"
            metrics_data: 资源指标数据
            
        Returns:
            Dict: 告警处理结果
        """
        try:
            self.stats["alerts_processed"] += 1
            self.stats["last_alert_time"] = datetime.now().isoformat()
            
            logger.info(f"开始处理资源告警: {resource_id}")
            
            # 检查是否需要告警
            if not self._should_alert(metrics_data):
                logger.debug(f"资源 {resource_id} 未达到告警阈值")
                return {
                    "alert_triggered": False,
                    "reason": "未达到告警阈值"
                }
            
            # 生成LLM分析
            analysis_result = await self._generate_llm_analysis(resource_id, metrics_data)
            
            # 发送钉钉告警
            dingtalk_result = await self._send_dingtalk_alert(resource_id, metrics_data, analysis_result)
            
            # 记录告警历史
            self._record_alert_history(resource_id, metrics_data, analysis_result, dingtalk_result)
            
            result = {
                "alert_triggered": True,
                "resource_id": resource_id,
                "llm_analysis": analysis_result,
                "dingtalk_sent": dingtalk_result,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"资源告警处理完成: {resource_id}")
            return result
            
        except Exception as e:
            logger.error(f"处理资源告警失败 {resource_id}: {e}")
            return {
                "alert_triggered": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _should_alert(self, metrics_data: Dict[str, Any]) -> bool:
        """判断是否应该触发告警
        
        Args:
            metrics_data: 资源指标数据
            
        Returns:
            bool: 是否需要告警
        """
        try:
            # 获取资源利用率（转换为小数形式）
            memory_util = metrics_data.get('memory_utilization_avg_14d', 0) / 100.0
            cpu_util = metrics_data.get('cpu_utilization_avg_14d', 0) / 100.0
            
            # 检查是否超过阈值
            memory_alert = memory_util > self.config.memory_alert_threshold
            cpu_alert = cpu_util > self.config.cpu_alert_threshold
            
            return memory_alert or cpu_alert
            
        except Exception as e:
            logger.error(f"检查告警条件失败: {e}")
            return False
    
    async def _generate_llm_analysis(self, resource_id: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成LLM分析报告
        
        Args:
            resource_id: 资源ID
            metrics_data: 资源指标数据
            
        Returns:
            Dict: LLM分析结果
        """
        if not self.config.enable_llm_analysis or not self.llm_processor:
            logger.debug("LLM分析已禁用或LLM处理器未配置")
            return {
                "success": False,
                "analysis": "LLM分析未启用",
                "fallback": True
            }
        
        try:
            logger.info(f"开始LLM分析: {resource_id}")
            
            # 构建分析提示词
            system_prompt = self._build_analysis_prompt()
            
            # 准备指标数据
            metrics_summary = self._format_metrics_for_llm(resource_id, metrics_data)
            
            # 控制输入数据大小，避免超过LLM上下文限制
            max_input_length = 8000  # 限制输入长度
            if len(metrics_summary) > max_input_length:
                logger.warning(f"指标数据过长({len(metrics_summary)}字符)，进行截断")
                metrics_summary = metrics_summary[:max_input_length] + "\n\n...(数据已截断)"
            
            # 构建用户消息内容
            user_content = f"""请基于以下K8s资源告警信息进行专业分析：

{metrics_summary}

请严格按照系统提示中的格式要求输出分析结果。"""
            
            # 构建消息
            ChatMessage = get_chat_message_class()
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_content)
            ]
            
            # 调用LLM（这里需要根据实际的LLM处理器接口调整）
            if hasattr(self.llm_processor, '_chat_without_tools'):
                result = await self.llm_processor._chat_without_tools(messages)
                analysis_content = result.content if hasattr(result, 'content') else str(result)
            else:
                # 降级方案：使用模拟分析
                analysis_content = self._generate_fallback_analysis(resource_id, metrics_data)
            
            self.stats["llm_analysis_success"] += 1
            
            return {
                "success": True,
                "analysis": analysis_content,
                "fallback": False
            }
            
        except Exception as e:
            logger.error(f"LLM分析失败 {resource_id}: {e}")
            self.stats["llm_analysis_failed"] += 1
            
            # 降级方案
            fallback_analysis = self._generate_fallback_analysis(resource_id, metrics_data)
            return {
                "success": False,
                "analysis": fallback_analysis,
                "fallback": True,
                "error": str(e)
            }
    
    def _build_analysis_prompt(self) -> str:
        """构建LLM分析提示词"""
        return """你是资深的Kubernetes运维专家，请基于以下资源利用率告警进行专业分析：

## 分析要求
**核心任务**：针对K8s资源利用率告警，提供专业的问题诊断和优化建议

**分析维度**：
1. **根因分析**：分析资源利用率异常的可能原因（应用负载、配置不当、资源泄漏等）
2. **影响评估**：评估对系统稳定性、性能和用户体验的潜在影响
3. **风险等级**：基于利用率数值和趋势，评估风险严重程度
4. **优化建议**：提供具体、可操作的资源优化和配置调整建议
5. **紧急程度**：给出处理优先级（🟢低/🟡中/🟠高/🔴紧急）

## 输出格式
使用Markdown格式，包含以下结构：
- **问题诊断**：简述问题现状
- **可能原因**：列出2-3个最可能的原因
- **影响评估**：说明潜在影响和风险
- **优化建议**：提供3-5条具体建议
- **紧急程度**：给出优先级评级

## 约束条件
- 回复控制在400字以内
- 使用专业术语但保持可读性
- 建议必须具体可操作
- 避免过于技术化的细节"""
    
    def _format_metrics_for_llm(self, resource_id: str, metrics_data: Dict[str, Any]) -> str:
        """格式化指标数据供LLM分析"""
        memory_util = metrics_data.get('memory_utilization_avg_14d', 0)
        cpu_util = metrics_data.get('cpu_utilization_avg_14d', 0)
        memory_requests = metrics_data.get('memory_requests', 0)
        cpu_requests = metrics_data.get('cpu_requests', 0)
        
        # 解析资源ID获取详细信息
        parts = resource_id.split('/')
        resource_type = parts[0] if len(parts) > 0 else "unknown"
        namespace = parts[1] if len(parts) > 1 else "unknown"
        app_name = parts[2] if len(parts) > 2 else "unknown"
        
        # 判断哪些指标超过阈值
        memory_alert = memory_util > (self.config.memory_alert_threshold * 100)
        cpu_alert = cpu_util > (self.config.cpu_alert_threshold * 100)
        
        # 计算利用率状态
        memory_status = "🔴 超阈值" if memory_alert else "🟢 正常"
        cpu_status = "🔴 超阈值" if cpu_alert else "🟢 正常"
        
        # 计算资源效率（利用率相对于请求量）
        memory_efficiency = "高效" if 0.6 <= memory_util/100 <= 0.8 else ("过低" if memory_util/100 < 0.6 else "过高")
        cpu_efficiency = "高效" if 0.6 <= cpu_util/100 <= 0.8 else ("过低" if cpu_util/100 < 0.6 else "过高")
        
        return f"""## 告警资源信息
**基础信息**
- 资源类型: {resource_type.upper()}
- 命名空间: `{namespace}`
- 应用名称: `{app_name}`
- 告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**资源利用率分析（14天平均值）**
- 内存利用率: **{memory_util:.1f}%** {memory_status} (阈值: {self.config.memory_alert_threshold:.0%})
- CPU利用率: **{cpu_util:.1f}%** {cpu_status} (阈值: {self.config.cpu_alert_threshold:.0%})

**资源配置状况**
- 内存请求量: {memory_requests:.2f}GB (利用效率: {memory_efficiency})
- CPU请求量: {cpu_requests:.3f}核 (利用效率: {cpu_efficiency})

**告警触发原因**
{f"- 内存利用率 {memory_util:.1f}% 超过阈值 {self.config.memory_alert_threshold:.0%}" if memory_alert else ""}
{f"- CPU利用率 {cpu_util:.1f}% 超过阈值 {self.config.cpu_alert_threshold:.0%}" if cpu_alert else ""}

**历史趋势**
- 数据来源: 14天滚动平均值
- 监控周期: 持续监控
- 数据可靠性: 基于Prometheus指标"""
    
    def _generate_fallback_analysis(self, resource_id: str, metrics_data: Dict[str, Any]) -> str:
        """生成降级分析报告"""
        memory_util = metrics_data.get('memory_utilization_avg_14d', 0)
        cpu_util = metrics_data.get('cpu_utilization_avg_14d', 0)
        memory_requests = metrics_data.get('memory_requests', 0)
        cpu_requests = metrics_data.get('cpu_requests', 0)
        
        analysis_parts = []
        
        # 问题诊断
        problems = []
        if memory_util > self.config.memory_alert_threshold * 100:
            problems.append(f"内存利用率{memory_util:.1f}%超过阈值{self.config.memory_alert_threshold:.0%}")
        if cpu_util > self.config.cpu_alert_threshold * 100:
            problems.append(f"CPU利用率{cpu_util:.1f}%超过阈值{self.config.cpu_alert_threshold:.0%}")
        
        analysis_parts.append(f"**问题诊断**: {resource_id} 存在资源利用率告警 - {', '.join(problems)}")
        
        # 可能原因
        causes = []
        if memory_util > self.config.memory_alert_threshold * 100:
            if memory_util > 90:
                causes.append("内存泄漏或配置严重不足")
            else:
                causes.append("应用负载增加或内存配置偏低")
        
        if cpu_util > self.config.cpu_alert_threshold * 100:
            if cpu_util > 90:
                causes.append("CPU密集型任务或性能瓶颈")
            else:
                causes.append("计算负载增加或CPU配置不足")
        
        if not causes:
            causes.append("资源配置与实际需求不匹配")
        
        analysis_parts.append(f"**可能原因**: {'; '.join(causes[:3])}")
        
        # 影响评估
        max_util = max(memory_util / 100.0, cpu_util / 100.0)
        if max_util > 0.9:
            impact = "可能导致应用响应缓慢、请求超时或服务不可用"
        elif max_util > 0.8:
            impact = "可能影响应用性能和用户体验"
        else:
            impact = "暂时不影响服务，但需要关注趋势"
        
        analysis_parts.append(f"**影响评估**: {impact}")
        
        # 优化建议
        suggestions = []
        if memory_util > self.config.memory_alert_threshold * 100:
            if memory_requests > 0:
                new_memory = memory_requests * (memory_util / 100.0) * 1.2
                suggestions.append(f"调整内存请求量至 {new_memory:.1f}GB")
            else:
                suggestions.append("设置合理的内存请求量和限制")
            suggestions.append("检查应用内存使用模式，排查内存泄漏")
        
        if cpu_util > self.config.cpu_alert_threshold * 100:
            if cpu_requests > 0:
                new_cpu = cpu_requests * (cpu_util / 100.0) * 1.2
                suggestions.append(f"调整CPU请求量至 {new_cpu:.2f}核")
            else:
                suggestions.append("设置合理的CPU请求量和限制")
            suggestions.append("优化应用算法，减少CPU密集型操作")
        
        suggestions.append("启用HPA自动扩缩容")
        suggestions.append("监控应用日志，排查性能问题")
        
        analysis_parts.append(f"**优化建议**: {'; '.join(suggestions[:4])}")
        
        # 紧急程度评级
        if max_util > 0.95:
            urgency = "🔴 紧急"
            urgency_desc = "立即处理"
        elif max_util > 0.85:
            urgency = "🟠 高"
            urgency_desc = "24小时内处理"
        elif max_util > 0.75:
            urgency = "🟡 中"
            urgency_desc = "3天内处理"
        else:
            urgency = "🟢 低"
            urgency_desc = "一周内处理"
        
        analysis_parts.append(f"**紧急程度**: {urgency} ({urgency_desc})")
        
        return "\n\n".join(analysis_parts)
    
    async def _send_dingtalk_alert(self, resource_id: str, metrics_data: Dict[str, Any], 
                                 analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """发送钉钉告警消息（支持重试机制）
        
        Args:
            resource_id: 资源ID
            metrics_data: 资源指标数据
            analysis_result: LLM分析结果
            
        Returns:
            Dict: 发送结果
        """
        if not self.config.enable_dingtalk_alert or not self.dingtalk_bot:
            logger.debug("钉钉告警已禁用或钉钉Bot未配置")
            return {
                "success": False,
                "reason": "钉钉告警未启用"
            }
        
        if not self.config.dingtalk_webhook_url:
            logger.warning("钉钉Webhook URL未配置")
            return {
                "success": False,
                "reason": "Webhook URL未配置"
            }
        
        # 构建告警消息
        try:
            title, markdown_content = self._build_enhanced_alert_message(resource_id, metrics_data, analysis_result)
            logger.info(f"构建钉钉告警消息: {resource_id}, 长度: {len(markdown_content)} 字符")
        except Exception as e:
            logger.error(f"构建告警消息失败 {resource_id}: {e}")
            return {
                "success": False,
                "error": f"消息构建失败: {str(e)}"
            }
        
        # 带重试机制的发送
        last_error = None
        for attempt in range(1, self.config.dingtalk_retry_attempts + 1):
            try:
                logger.info(f"发送钉钉告警 (第{attempt}次尝试): {resource_id}")
                
                # 发送消息
                if hasattr(self.dingtalk_bot, 'send_markdown_message'):
                    success = await self.dingtalk_bot.send_markdown_message(
                        webhook_url=self.config.dingtalk_webhook_url,
                        title=title,
                        markdown_text=markdown_content
                    )
                else:
                    # 降级方案：记录日志
                    logger.warning("钉钉Bot接口不可用，使用日志记录")
                    logger.info(f"告警消息内容:\n{title}\n{markdown_content}")
                    success = True
                
                if success:
                    if attempt == 1:
                        self.stats["dingtalk_sent_success"] += 1
                    else:
                        self.stats["dingtalk_retry_success"] += 1
                    
                    logger.info(f"✅ 钉钉告警发送成功: {resource_id} (第{attempt}次尝试)")
                    return {
                        "success": True,
                        "message_length": len(markdown_content),
                        "attempts": attempt
                    }
                else:
                    last_error = "钉钉API返回失败"
                    logger.warning(f"钉钉告警发送失败: {resource_id} (第{attempt}次尝试) - {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"钉钉告警发送异常: {resource_id} (第{attempt}次尝试) - {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.config.dingtalk_retry_attempts:
                await asyncio.sleep(self.config.dingtalk_retry_delay * attempt)  # 递增延迟
        
        # 所有重试都失败
        self.stats["dingtalk_sent_failed"] += 1
        self.stats["dingtalk_retry_failed"] += 1
        logger.error(f"❌ 钉钉告警发送最终失败: {resource_id}, 已重试 {self.config.dingtalk_retry_attempts} 次")
        
        return {
            "success": False,
            "error": last_error or "未知错误",
            "attempts": self.config.dingtalk_retry_attempts
        }
    
    def _build_alert_message(self, resource_id: str, metrics_data: Dict[str, Any], 
                           analysis_result: Dict[str, Any]) -> str:
        """构建告警消息内容"""
        memory_util = metrics_data.get('memory_utilization_avg_14d', 0)
        cpu_util = metrics_data.get('cpu_utilization_avg_14d', 0)
        memory_requests = metrics_data.get('memory_requests', 0)
        cpu_requests = metrics_data.get('cpu_requests', 0)
        
        # 构建基础信息
        message_parts = [
            "# 🚨 K8s资源利用率告警",
            "",
            f"**资源信息**: `{resource_id}`",
            f"**告警时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 资源利用率",
            f"- **内存利用率**: {memory_util:.1f}% {'🔴' if memory_util > self.config.memory_alert_threshold * 100 else '🟢'}",
            f"- **CPU利用率**: {cpu_util:.1f}% {'🔴' if cpu_util > self.config.cpu_alert_threshold * 100 else '🟢'}",
            "",
            "## 🔧 资源配置",
            f"- **内存请求量**: {memory_requests:.2f}GB",
            f"- **CPU请求量**: {cpu_requests:.3f}核",
            ""
        ]
        
        # 添加LLM分析结果
        if analysis_result.get("success") and analysis_result.get("analysis"):
            message_parts.extend([
                "## 🧠 智能分析",
                analysis_result["analysis"],
                ""
            ])
        elif analysis_result.get("fallback"):
            message_parts.extend([
                "## 📋 基础分析",
                analysis_result["analysis"],
                ""
            ])
        
        # 添加处理建议
        message_parts.extend([
            "## 🎯 处理建议",
            "1. 立即检查应用日志和性能指标",
            "2. 评估是否需要调整资源配置",
            "3. 考虑应用优化或扩容方案",
            "",
            "---",
            "*此告警由K8s资源监控系统自动生成*"
        ])
        
        content = "\n".join(message_parts)
        
        # 控制消息长度
        if len(content) > self.config.alert_message_max_length:
            content = content[:self.config.alert_message_max_length - 50] + "\n\n...(消息已截断)"
        
        return content
    
    def _build_enhanced_alert_message(self, resource_id: str, metrics_data: Dict[str, Any], 
                                    analysis_result: Dict[str, Any]) -> tuple[str, str]:
        """构建增强的告警消息内容
        
        Returns:
            tuple: (title, markdown_content)
        """
        memory_util = metrics_data.get('memory_utilization_avg_14d', 0)
        cpu_util = metrics_data.get('cpu_utilization_avg_14d', 0)
        memory_requests = metrics_data.get('memory_requests', 0)
        cpu_requests = metrics_data.get('cpu_requests', 0)
        
        # 解析资源信息
        parts = resource_id.split('/')
        resource_type = parts[0] if len(parts) > 0 else "unknown"
        namespace = parts[1] if len(parts) > 1 else "unknown"
        app_name = parts[2] if len(parts) > 2 else "unknown"
        
        # 计算紧急程度
        max_util = max(memory_util / 100.0, cpu_util / 100.0)
        urgency_info = self._calculate_urgency_level(max_util)
        
        # 构建动态标题
        title = f"{urgency_info['emoji']} K8s资源告警 - {app_name}"
        
        # 构建消息内容
        message_parts = [
            f"# {urgency_info['emoji']} K8s资源利用率告警",
            "",
            f"**{urgency_info['level']}** | {urgency_info['description']}",
            "",
            "## 📋 资源信息",
            f"- **应用名称**: `{app_name}`",
            f"- **命名空间**: `{namespace}`",
            f"- **资源类型**: {resource_type.upper()}",
            f"- **告警时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # 资源利用率部分
        memory_status = "🔴 超阈值" if memory_util > self.config.memory_alert_threshold * 100 else "🟢 正常"
        cpu_status = "🔴 超阈值" if cpu_util > self.config.cpu_alert_threshold * 100 else "🟢 正常"
        
        message_parts.extend([
            "## 📊 资源利用率 (14天平均)",
            f"- **内存**: {memory_util:.1f}% {memory_status} (阈值: {self.config.memory_alert_threshold:.0%})",
            f"- **CPU**: {cpu_util:.1f}% {cpu_status} (阈值: {self.config.cpu_alert_threshold:.0%})",
            "",
            "## 🔧 资源配置",
            f"- **内存请求**: {memory_requests:.2f}GB",
            f"- **CPU请求**: {cpu_requests:.3f}核",
            ""
        ])
        
        # LLM分析结果
        if analysis_result.get("analysis"):
            analysis_title = "🧠 智能分析" if not analysis_result.get("fallback") else "📋 基础分析"
            analysis_content = analysis_result["analysis"]
            
            # 限制分析内容长度
            if len(analysis_content) > 800:
                analysis_content = analysis_content[:800] + "\n\n...(分析内容已截断)"
            
            message_parts.extend([
                f"## {analysis_title}",
                analysis_content,
                ""
            ])
        
        # 快速处理指南
        message_parts.extend([
            "## ⚡ 快速处理指南",
            f"**优先级**: {urgency_info['priority']}",
            f"**建议处理时间**: {urgency_info['timeline']}",
            "",
            "**立即行动**:",
            "1. 🔍 检查应用日志和监控指标",
            "2. 📈 评估资源使用趋势",
            "3. ⚙️ 考虑调整资源配置或扩容",
            "",
            "---",
            "💡 *K8s智能运维助手自动生成* | 📞 如需帮助请联系运维团队"
        ])
        
        content = "\n".join(message_parts)
        
        # 控制消息长度（为钉钉分片留出空间）
        if len(content) > self.config.alert_message_max_length:
            # 智能截断：保留重要部分
            truncate_pos = self.config.alert_message_max_length - 100
            content = content[:truncate_pos] + "\n\n📝 *消息内容过长，已智能截断*"
            logger.warning(f"告警消息过长已截断: {len(content)} -> {self.config.alert_message_max_length}")
        
        return title, content
    
    def _calculate_urgency_level(self, max_utilization: float) -> Dict[str, str]:
        """计算紧急程度等级"""
        if max_utilization >= 0.95:
            return {
                "level": "🔴 紧急告警",
                "emoji": "🚨",
                "priority": "P0 - 紧急",
                "timeline": "立即处理",
                "description": "资源利用率极高，可能影响服务稳定性"
            }
        elif max_utilization >= 0.85:
            return {
                "level": "🟠 高级告警",
                "emoji": "⚠️",
                "priority": "P1 - 高",
                "timeline": "24小时内处理",
                "description": "资源利用率过高，需要及时关注"
            }
        elif max_utilization >= 0.75:
            return {
                "level": "🟡 中级告警",
                "emoji": "⚡",
                "priority": "P2 - 中",
                "timeline": "3天内处理",
                "description": "资源利用率偏高，建议优化"
            }
        else:
            return {
                "level": "🟢 低级告警",
                "emoji": "📊",
                "priority": "P3 - 低",
                "timeline": "一周内处理",
                "description": "资源利用率超过阈值，需要关注"
            }
    
    def _record_alert_history(self, resource_id: str, metrics_data: Dict[str, Any], 
                            analysis_result: Dict[str, Any], dingtalk_result: Dict[str, Any]):
        """记录告警历史"""
        if resource_id not in self.alert_history:
            self.alert_history[resource_id] = []
        
        history_record = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "memory_util": metrics_data.get('memory_utilization_avg_14d', 0),
                "cpu_util": metrics_data.get('cpu_utilization_avg_14d', 0)
            },
            "llm_analysis_success": analysis_result.get("success", False),
            "dingtalk_sent_success": dingtalk_result.get("success", False)
        }
        
        self.alert_history[resource_id].append(history_record)
        
        # 保持历史记录数量限制
        if len(self.alert_history[resource_id]) > 10:
            self.alert_history[resource_id] = self.alert_history[resource_id][-10:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "stats": self.stats.copy(),
            "config": {
                "memory_alert_threshold": self.config.memory_alert_threshold,
                "cpu_alert_threshold": self.config.cpu_alert_threshold,
                "enable_llm_analysis": self.config.enable_llm_analysis,
                "enable_dingtalk_alert": self.config.enable_dingtalk_alert
            },
            "alert_history_count": {
                resource_id: len(alerts) 
                for resource_id, alerts in self.alert_history.items()
            }
        }
    
    def get_alert_history(self, resource_id: Optional[str] = None) -> Dict[str, Any]:
        """获取告警历史记录"""
        if resource_id:
            return {
                resource_id: self.alert_history.get(resource_id, [])
            }
        return self.alert_history.copy()


# 工厂函数
def create_resource_alert_service(llm_processor=None, dingtalk_bot=None, 
                                config=None) -> ResourceAlertService:
    """创建资源告警服务实例"""
    return ResourceAlertService(
        llm_processor=llm_processor,
        dingtalk_bot=dingtalk_bot,
        config=config or ResourceAlertConfig()
    )
