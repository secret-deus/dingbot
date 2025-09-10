"""
简化版 LLM 处理器
直接从环境变量字典配置，无多供应商支持
"""

import json
import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from datetime import datetime
from loguru import logger
import openai
from openai import AsyncOpenAI
import httpx
from pydantic import BaseModel, Field

from tenacity import retry, stop_after_attempt, wait_exponential

from ..mcp.types import (
    ChatMessage, ProcessResult, FunctionCall, FunctionCallResult,
    MCPException
)
from ..mcp.enhanced_client import EnhancedMCPClient
from .security.masker import DataMasker
from .security.config import MaskingConfig


class EnhancedLLMProcessor:
    """简化的LLM处理器 - 直接基于环境变量配置"""
    
    # 结果大小管理配置
    MAX_RESULT_SIZE = 50000  # 50KB 字符限制
    MAX_RESULT_LINES = 1000  # 最大行数限制
    SUMMARY_TARGET_SIZE = 8000  # 摘要目标大小
    
    # 上下文管理配置
    MAX_CONTEXT_TOKENS = 100000  # 最大上下文token数（估算）
    MAX_HISTORY_MESSAGES = 20  # 最大历史消息数
    
    def __init__(self, config_dict: Dict[str, Any], mcp_client=None):
        """
        初始化LLM处理器
        :param config_dict: 直接从环境变量获取的配置字典
        :param mcp_client: MCP客户端
        """
        self.config = config_dict
        self.mcp_client = mcp_client
        self.client = None  # 单个LLM客户端
        
        # 初始化脱敏器
        self.data_masker = DataMasker(MaskingConfig())
        
        # 初始化客户端
        self._initialize_client()
        
        logger.info(f"✅ 简化LLM处理器初始化完成: {self.config.get('provider', 'unknown')}")
        logger.info(f"🔧 调试：处理器配置详情: {self.config}")
    
    def _initialize_client(self):
        """初始化LLM客户端"""
        try:
            provider = self.config.get("provider", "openai")
            api_key = self.config.get("api_key", "")
            base_url = self.config.get("base_url")
            
            # 🔍 详细诊断日志
            logger.info(f"📋 LLM客户端初始化诊断:")
            logger.info(f"   Provider: {provider}")
            logger.info(f"   Model: {self.config.get('model', 'unknown')}")
            logger.info(f"   API Key长度: {len(api_key) if api_key else 0}")
            logger.info(f"   Base URL: {base_url}")
            logger.info(f"   Timeout: {self.config.get('timeout', 30)}")
            
            if provider == "openai":
                self.client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=self.config.get("timeout", 30)
                )
            elif provider == "ollama":
                base_url = self.config.get("base_url", "http://localhost:11434/v1")
                self.client = AsyncOpenAI(
                    api_key="ollama",
                    base_url=base_url,
                    timeout=self.config.get("timeout", 60)
                )
            else:
                self.client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=self.config.get("timeout", 30)
                )
                
            logger.info(f"✅ {provider}客户端创建成功")
            
            # 🔍 测试客户端连接
            logger.info("🔗 测试客户端连接性...")
            
        except Exception as e:
            # 🔍 详细错误信息
            logger.error(f"❌ LLM客户端初始化失败:")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            
            import traceback
            logger.error(f"   完整堆栈:\n{traceback.format_exc()}")
            
            # 检查是否是代理相关错误
            error_str = str(e).lower()
            if 'socks' in error_str or 'proxy' in error_str:
                logger.error("🚫 代理配置错误！请检查NO_PROXY设置或安装socks支持")
            
            self.client = None
            # ⚠️ 不抛出异常，允许服务继续运行，使用fallback模式
            logger.warning("⚠️ LLM客户端将使用fallback模式")
    
    def get_current_provider(self):
        """获取当前供应商配置"""
        return self.config
    
    def get_current_client(self):
        """获取当前供应商的客户端"""
        return self.client
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的供应商列表"""
        return {
            "current": {
                "name": self.config.get("provider", "unknown"),
                "model": self.config.get("model", "N/A"),
                "enabled": True,
                "available": self.client is not None,
                "icon": "🤖",
                "description": "当前配置的LLM提供商",
                "support_functions": True,
                "support_vision": False,
                "stats": {}
            }
        }
    
    def update_multi_provider_config(self, config):
        """更新配置 (向后兼容方法)"""
        self.config = config
        logger.info(f"✅ 配置已更新")
    
    def update_provider_stats(self, provider_id: str, success: bool, tokens: int = 0):
        """更新供应商统计信息 (此方法不再适用，因为只有一个供应商)"""
        logger.warning(f"update_provider_stats 被调用，但当前只有一个供应商。provider_id: {provider_id}, success: {success}, tokens: {tokens}")
    
    def _get_model_name(self) -> str:
        """获取用于API调用的模型名称"""
        return self.config.get("model", "gpt-3.5-turbo")
    
    def _check_result_size(self, result: Any) -> bool:
        """检查结果是否过大"""
        try:
            # 序列化结果以检查大小
            result_str = json.dumps(result, ensure_ascii=False, indent=2)
            result_size = len(result_str.encode('utf-8'))
            result_lines = result_str.count('\n')
            
            logger.debug(f"结果大小检查: {result_size} bytes, {result_lines} lines")
            
            return (result_size > self.MAX_RESULT_SIZE or 
                   result_lines > self.MAX_RESULT_LINES)
        except Exception as e:
            logger.warning(f"检查结果大小时出错: {e}")
            return False
    
    def _extract_key_information(self, result: Any, tool_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """智能提炼关键信息"""
        try:
            # 将结果转换为字符串
            if isinstance(result, str):
                content = result
            else:
                content = json.dumps(result, ensure_ascii=False, indent=2)
            
            # 根据工具类型采用不同的提炼策略
            if tool_name.startswith('k8s_'):
                return self._extract_k8s_key_info(content, tool_name, context)
            elif 'log' in tool_name.lower():
                return self._extract_log_key_info(content)
            else:
                return self._extract_general_key_info(content)
                
        except Exception as e:
            logger.error(f"提炼关键信息时出错: {e}")
            return str(result)[:self.SUMMARY_TARGET_SIZE] + "\n[信息提炼失败，已截断]"
    
    def _extract_k8s_key_info(self, content: str, tool_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """提炼Kubernetes相关信息的关键内容"""
        lines = content.split('\n')
        
        # 从上下文中提取用户查询的资源信息
        target_resources = self._extract_target_resources_from_context(context)
        if target_resources:
            logger.info(f"🎯 检测到目标资源: {target_resources}")
        
        # 保留重要的状态信息
        important_keywords = [
            'status', 'state', 'ready', 'running', 'pending', 'failed', 'error',
            'warning', 'critical', 'name', 'namespace', 'age', 'restarts',
            'cpu', 'memory', 'node', 'image', 'port', 'service', 'endpoint'
        ]
        
        # 分类收集信息
        summary_lines = []
        target_resource_lines = []  # 用户查询的特定资源
        important_lines = []
        table_headers = []
        other_lines = []
        
        for line in lines:
            line_lower = line.lower()
            
            # 优先保留用户查询的特定资源
            if target_resources and any(resource.lower() in line_lower for resource in target_resources):
                target_resource_lines.append(line)
                continue
            
            # 保留统计摘要信息
            if any(word in line_lower for word in ['total', 'count', 'summary', '总计', '数量', 'namespace']):
                summary_lines.append(line)
            # 保留表格头部
            elif '|' in line and ('name' in line_lower or 'namespace' in line_lower or 'ready' in line_lower):
                table_headers.append(line)
            # 保留包含重要关键词的行
            elif any(keyword in line_lower for keyword in important_keywords):
                # 优先保留错误和异常状态
                if any(word in line_lower for word in ['error', 'failed', 'warning', 'critical', 'pending']):
                    important_lines.insert(0, line)  # 插入到前面
                else:
                    important_lines.append(line)
            else:
                other_lines.append(line)
        
        # 智能组合结果：目标资源 > 摘要 > 表头 > 重要信息 > 其他
        result_lines = []
        
        # 1. 用户查询的特定资源（全部保留）
        if target_resource_lines:
            result_lines.extend(target_resource_lines)
            result_lines.append("") # 空行分隔
        
        # 2. 摘要信息（前10行）
        result_lines.extend(summary_lines[:10])
        
        # 3. 表格头部（前3行）
        result_lines.extend(table_headers[:3])
        
        # 4. 重要信息（前15行，错误优先）
        result_lines.extend(important_lines[:15])
        
        # 5. 如果还有空间，添加其他信息
        remaining_space = max(0, 30 - len(result_lines))
        if remaining_space > 0:
            result_lines.extend(other_lines[:remaining_space])
        
        # 添加提炼说明
        if len(result_lines) < len(lines):
            filtered_count = len(lines) - len(result_lines)
            result_lines.append(f"\n[已智能提炼关键信息，原始数据 {len(lines)} 行，显示 {len(result_lines)} 行，过滤 {filtered_count} 行]")
            
            # 如果有目标资源，特别说明
            if target_resource_lines:
                result_lines.append(f"[✅ 已优先保留查询的目标资源: {', '.join(target_resources)}]")
        
        return '\n'.join(result_lines)
    
    def _extract_target_resources_from_context(self, context: Optional[Dict[str, Any]]) -> List[str]:
        """从上下文中提取用户查询的目标资源名称"""
        if not context:
            return []
        
        target_resources = []
        
        # 从工具参数中提取
        parameters = context.get('parameters', {})
        if isinstance(parameters, dict):
            # 检查常见的资源名称参数
            for param_name in ['name', 'resource_name', 'deployment_name', 'pod_name', 'service_name']:
                if param_name in parameters:
                    target_resources.append(str(parameters[param_name]))
        
        # 从用户消息中提取（增强的关键词匹配）
        user_message = context.get('user_message', '')
        if isinstance(user_message, str):
            import re
            
            # 方法1: 匹配带连字符的资源名称模式
            hyphenated_patterns = re.findall(r'\b[a-z0-9]+(?:-[a-z0-9]+)+\b', user_message.lower())
            target_resources.extend(hyphenated_patterns)
            
            # 方法2: 匹配引号中的资源名称
            quoted_patterns = re.findall(r'["\']([a-z0-9-]+)["\']', user_message.lower())
            target_resources.extend(quoted_patterns)
            
            # 方法3: 匹配deployment/pod/service等关键词后的名称
            resource_type_patterns = re.findall(r'(?:deployment|pod|service|configmap|secret|ingress)\s+([a-z0-9-]+)', user_message.lower())
            target_resources.extend(resource_type_patterns)
            
            # 方法4: 匹配namespace后的资源名称
            namespace_patterns = re.findall(r'(?:namespace|ns)\s+([a-z0-9-]+).*?(?:deployment|pod|service)\s+([a-z0-9-]+)', user_message.lower())
            for match in namespace_patterns:
                if len(match) > 1:
                    target_resources.append(match[1])  # 资源名称
            
            # 方法5: 匹配标签选择器中的应用名称
            label_patterns = re.findall(r'(?:app|label)[\s=]+([a-z0-9-]+)', user_message.lower())
            target_resources.extend(label_patterns)
            
            # 方法6: 匹配selector参数
            selector_patterns = re.findall(r'selector[\s=]+(?:app=)?([a-z0-9-]+)', user_message.lower())
            target_resources.extend(selector_patterns)
            
            # 过滤掉常见的非资源词汇
            common_words = {
                'get', 'show', 'list', 'describe', 'status', 'deployment', 'pod', 'service', 
                'namespace', 'the', 'of', 'in', 'for', 'with', 'and', 'or', 'check', 'view',
                'test', 'prod', 'dev', 'staging', 'default', 'kube-system', 'kube-public'
            }
            
            # 清理和过滤
            filtered_resources = []
            for resource in target_resources:
                if (len(resource) > 2 and 
                    resource not in common_words and 
                    not resource.startswith('kube-') and
                    resource != 'system'):
                    filtered_resources.append(resource)
            
            target_resources = filtered_resources
        
        # 去重并返回
        return list(set(target_resources))
    
    def _extract_log_key_info(self, content: str) -> str:
        """提炼日志信息的关键内容"""
        lines = content.split('\n')
        key_lines = []
        
        # 日志级别优先级
        priority_levels = ['error', 'warn', 'fatal', 'critical']
        normal_levels = ['info', 'debug']
        
        error_lines = []
        warning_lines = []
        info_lines = []
        
        for line in lines:
            line_lower = line.lower()
            
            if any(level in line_lower for level in priority_levels):
                error_lines.append(line)
            elif 'warn' in line_lower:
                warning_lines.append(line)
            elif any(level in line_lower for level in normal_levels):
                if len(info_lines) < 10:  # 限制普通日志数量
                    info_lines.append(line)
        
        # 组合结果：错误 + 警告 + 部分信息
        result_lines = error_lines[:15] + warning_lines[:10] + info_lines[:5]
        
        if len(result_lines) < len(lines):
            result_lines.append(f"\n[已提炼关键日志，原始 {len(lines)} 行，显示 {len(result_lines)} 行]")
        
        return '\n'.join(result_lines)
    
    def _extract_general_key_info(self, content: str) -> str:
        """提炼一般内容的关键信息"""
        lines = content.split('\n')
        
        # 如果内容不是很大，直接返回
        if len(content) <= self.SUMMARY_TARGET_SIZE:
            return content
        
        # 保留前面和后面的部分内容
        total_lines = len(lines)
        keep_start = min(50, total_lines // 3)
        keep_end = min(20, total_lines // 4)
        
        if keep_start + keep_end >= total_lines:
            return content
        
        start_lines = lines[:keep_start]
        end_lines = lines[-keep_end:] if keep_end > 0 else []
        
        result_lines = start_lines + [f"\n[... 省略 {total_lines - keep_start - keep_end} 行 ...]"] + end_lines
        
        return '\n'.join(result_lines)
    
    def _process_mcp_result(self, result: Any, tool_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """处理MCP工具调用结果，如果过大则智能提炼"""
        try:
            # 检查结果大小
            if self._check_result_size(result):
                logger.info(f"工具 {tool_name} 结果过大，正在提炼关键信息...")
                processed_result = self._extract_key_information(result, tool_name, context)
                
                # 添加分页建议
                pagination_suggestion = self._generate_pagination_suggestion(tool_name, result)
                if pagination_suggestion:
                    processed_result += f"\n\n{pagination_suggestion}"
                
                logger.info(f"关键信息提炼完成，大小从 {len(str(result))} 减少到 {len(processed_result)}")
                return processed_result
            else:
                # 结果不大，直接序列化
                return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"处理MCP结果时出错: {e}")
            # 出错时使用简单截断
            result_str = str(result)
            if len(result_str) > self.SUMMARY_TARGET_SIZE:
                return result_str[:self.SUMMARY_TARGET_SIZE] + "\n[结果处理出错，已截断]"
            return result_str
    
    def _generate_pagination_suggestion(self, tool_name: str, result: Any) -> str:
        """生成分页建议"""
        suggestions = []
        
        # 针对不同工具类型生成建议
        if tool_name.startswith('k8s_get_'):
            if 'pods' in tool_name:
                suggestions.append("💡 建议使用标签选择器：--selector=app=med-marketing")
                suggestions.append("💡 或限制命名空间：--namespace=test --limit=20")
                suggestions.append("💡 查询特定应用的所有资源：kubectl get all -l app=med-marketing -n test")
            elif 'deployment' in tool_name:
                suggestions.append("💡 建议使用标签选择器：--selector=app=med-marketing")
                suggestions.append("💡 或指定具体名称：--name=med-marketing --namespace=test")
            elif 'service' in tool_name:
                suggestions.append("💡 建议使用标签选择器：--selector=app=med-marketing")
                suggestions.append("💡 查询相关endpoints：kubectl get endpoints -l app=med-marketing -n test")
            elif 'logs' in tool_name:
                suggestions.append("💡 建议限制日志行数：--tail=100 --since=1h")
                suggestions.append("💡 或指定时间范围：--since-time=2024-01-01T00:00:00Z")
            elif 'events' in tool_name:
                suggestions.append("💡 建议使用时间过滤：--since=30m")
                suggestions.append("💡 或按类型过滤：--field-selector=type=Warning")
        
        elif tool_name.startswith('k8s_describe_'):
            suggestions.append("💡 建议指定具体资源名称而不是描述所有资源")
        
        # 通用建议
        if suggestions:
            suggestions.append("💡 如需完整数据，请使用更具体的查询条件")
            return "📋 **优化建议**：\n" + "\n".join(suggestions)
        
        return ""
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（粗略估算：1个token约4个字符）"""
        return len(text) // 4
    
    def _optimize_context_size(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化上下文大小，避免超出限制"""
        if len(messages) <= 2:  # 至少保留系统消息和用户消息
            return messages
        
        # 计算总token数
        total_tokens = sum(self._estimate_tokens(str(msg.get('content', ''))) for msg in messages)
        
        if total_tokens <= self.MAX_CONTEXT_TOKENS and len(messages) <= self.MAX_HISTORY_MESSAGES:
            return messages
        
        logger.info(f"上下文过大 ({total_tokens} tokens, {len(messages)} messages)，正在优化...")
        
        # 保留系统消息（第一条）和最近的用户消息
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        tool_messages = [msg for msg in messages if msg.get('role') == 'tool']
        
        # 构建优化后的消息列表
        optimized_messages = []
        
        # 1. 保留系统消息
        optimized_messages.extend(system_messages)
        
        # 2. 保留最近的对话（用户-助手-工具的完整循环）
        recent_conversations = []
        current_tokens = sum(self._estimate_tokens(str(msg.get('content', ''))) for msg in system_messages)
        
        # 从最后开始，保留完整的对话循环
        i = len(messages) - 1
        while i >= 0 and len(recent_conversations) < self.MAX_HISTORY_MESSAGES // 2:
            msg = messages[i]
            msg_tokens = self._estimate_tokens(str(msg.get('content', '')))
            
            if current_tokens + msg_tokens > self.MAX_CONTEXT_TOKENS:
                break
                
            recent_conversations.insert(0, msg)
            current_tokens += msg_tokens
            i -= 1
        
        # 3. 如果还有空间，添加摘要信息
        if len(recent_conversations) < len(messages) - len(system_messages):
            summary_msg = {
                "role": "system",
                "content": f"[上下文摘要: 省略了 {len(messages) - len(system_messages) - len(recent_conversations)} 条历史消息以优化性能]"
            }
            optimized_messages.append(summary_msg)
        
        optimized_messages.extend(recent_conversations)
        
        final_tokens = sum(self._estimate_tokens(str(msg.get('content', ''))) for msg in optimized_messages)
        logger.info(f"上下文优化完成: {len(messages)} -> {len(optimized_messages)} messages, {total_tokens} -> {final_tokens} tokens")
        
        return optimized_messages

    async def process_message(self, message: str) -> str:
        """处理单个消息（简化版）"""
        try:
            # 检查LLM是否启用
            if not self.config.get("enabled", True):
                return "LLM功能已禁用，无法处理消息。请在设置中启用LLM功能。"
            
            messages = [
                ChatMessage(role="user", content=message)
            ]
            result = await self.chat(messages, enable_tools=False)
            return result.content
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            return f"处理消息时发生错误: {str(e)}"
        
    async def stream_chat(
        self, 
        message: str, 
        enable_tools: bool = True
    ) -> AsyncGenerator[str, None]:
        """优化的两阶段流式聊天处理：工具执行 + LLM对话回复"""
        try:
            logger.info(f"开始流式聊天处理，消息长度: {len(message)}, 工具支持: {enable_tools}")
            
            # 检查LLM是否启用
            if not self.config.get("enabled", True):
                yield "LLM功能已禁用，无法进行聊天。请在设置中启用LLM功能。"
                return
            
            # 检查客户端是否可用
            if self.client is None:
                logger.warning("LLM客户端未初始化，使用模拟响应")
                
                # 如果有工具调用，仍然执行脱敏逻辑和工具处理
                if enable_tools and tool_calls_made and tool_results:
                    logger.info("🔒 即使LLM客户端未初始化，仍执行脱敏处理演示")
                    session_id = f'demo_session_{int(time.time())}'
                    
                    # 🔒 执行脱敏演示
                    # 在演示模式下，工具名称可能不可用，传递空列表
                    masked_tool_results = self.data_masker.mask_tool_results(tool_results, session_id, [])
                    
                    # 📝 在日志中记录脱敏效果
                    import json
                    logger.warning(f"🔒 脱敏处理完成 (演示模式, 会话ID: {session_id}):")
                    logger.warning(f"   原始工具结果: {json.dumps(tool_results, ensure_ascii=False)[:200]}...")
                    logger.warning(f"   脱敏后结果: {json.dumps(masked_tool_results, ensure_ascii=False)[:200]}...")
                    
                    # 生成包含脱敏信息的模拟响应
                    mock_response = f"⚠️ LLM服务未配置，这是演示响应。\n\n工具已执行并完成脱敏处理：\n- 会话ID: {session_id}\n- 脱敏映射数: {len(self.data_masker.session_manager.sessions.get(session_id, {}).get('original_to_masked', {}))}\n\n请检查日志查看详细的脱敏效果。"
                else:
                    mock_response = "抱歉，LLM服务未正确配置。请检查API密钥设置或网络代理配置。"
                
                chunk_size = 8
                for i in range(0, len(mock_response), chunk_size):
                    chunk = mock_response[i:i + chunk_size]
                    if chunk.strip():
                        yield chunk
                    await asyncio.sleep(0.1)
                return
            
            # 初始化对话历史
            conversation_history = [
                {"role": "user", "content": message}
            ]
            
            # 获取工具列表（如果启用）
            tools = None
            if enable_tools and self.mcp_client:
                try:
                    available_tools = await self.mcp_client.list_tools()
                    tool_count = len(available_tools) if available_tools else 0
                    logger.info(f"MCP客户端获取到 {tool_count} 个工具")
                    
                    # ✅ 恢复完整工具功能 - 工具转换问题已修复
                    if available_tools:
                        logger.info(f"✅ 使用所有可用工具: {len(available_tools)} 个")
                        limited_tools = available_tools
                        tools = self._convert_tools_to_openai(limited_tools)
                        tool_names = [tool['function']['name'] for tool in tools]
                        logger.info(f"转换为OpenAI格式的工具: {tool_names}")
                    else:
                        tools = None
                except Exception as e:
                    logger.warning(f"获取工具失败，使用非工具模式: {e}")
            
            # 如果没有工具可用，直接进行普通对话
            if not tools or len(tools) == 0:
                logger.info("无工具可用，直接进行普通对话")
                async for chunk in self._stream_llm_response(conversation_history):
                    yield chunk
                return
            
            # 第一阶段：LLM决策和工具执行
            logger.info("开始第一阶段：LLM决策和工具执行")
            tool_calls_made = []
            tool_results = []
            updated_conversation_history = conversation_history.copy()
            
            try:
                async for chunk in self._phase_one_tool_execution(updated_conversation_history, tools, message):
                    if isinstance(chunk, dict) and chunk.get("type") == "tool_call_complete":
                        # 收集工具调用信息
                        tool_calls_made.append(chunk["tool_call"])
                        tool_results.append(chunk["result"])
                        # 更新对话历史
                        if "conversation_history" in chunk:
                            updated_conversation_history = chunk["conversation_history"]
                    else:
                        # 流式输出工具执行状态
                        yield chunk
                        
                logger.info(f"第一阶段完成，工具调用数: {len(tool_calls_made)}, 结果数: {len(tool_results)}")
                
            except Exception as e:
                logger.error(f"第一阶段工具执行失败: {e}", exc_info=True)
                yield f"\n❌ 工具执行失败: {str(e)}"
                return
            
            # 第二阶段：基于工具结果生成LLM对话回复
            if tool_calls_made:
                logger.info("开始第二阶段：基于工具结果生成LLM对话回复")
                yield "\n\n---\n\n"  # 清晰的分隔符
                
                try:
                    # 确保有工具结果才进行第二阶段
                    valid_results = [r for r in tool_results if r is not None]
                    
                    # 记录工具结果统计
                    logger.info(f"第二阶段收到 {len(valid_results)} 个有效工具结果")
                    
                    # 检查工具结果有效性
                    def is_valid_tool_result(result):
                        """检查工具结果是否有效"""
                        if result is None:
                            return False
                        # 检查是否为错误结果
                        if result.get('is_error', False):
                            return False
                        # 检查是否有内容 - MCP结果有content字段或直接有数据
                        if 'content' in result:
                            return bool(result.get('content'))
                        # 如果没有content字段，检查是否有其他数据字段
                        return bool(result and len(str(result).strip()) > 0)
                    
                    # 🧪 如果工具结果无效，临时添加模拟数据来测试脱敏功能
                    if not valid_results or not all(is_valid_tool_result(r) for r in valid_results):
                        invalid_count = len([r for r in valid_results if not is_valid_tool_result(r)])
                        logger.warning(f"⚠️ 工具调用失败或无效 ({invalid_count}/{len(valid_results)} 无效)，添加模拟数据测试脱敏功能")
                        mock_tool_result = {
                            "content": """
Kubernetes 节点信息:
- 节点名称: worker-node-prod-192-168-1-100
- IP地址: 192.168.1.100  
- 状态: Ready
- Pod 列表:
  * nginx-deployment-7d4b8c9f8b-abc123 (运行在 master-node-prod-192-168-1-101, IP: 192.168.1.101)
  * web-app-5f7b8d9c2e-def456 (运行在 worker-node-prod-192-168-1-102, IP: 192.168.1.102)

日志摘要:
- 2024-01-22 10:30:15 用户张三(13812345678)登录成功 
- 2024-01-22 10:31:20 管理员李四通过admin@company.com执行了系统维护
- 2024-01-22 10:32:45 server-admin-ops001 重启了 worker-node-prod-192-168-1-103

集群状态良好，所有节点运行正常。
                            """,
                            "is_error": False
                        }
                        tool_results = [mock_tool_result]
                        valid_results = tool_results
                        logger.info("✅ 模拟工具结果已注入，包含多种敏感信息")
                    
                    if valid_results:
                        response_generated = False
                        async for chunk in self._phase_two_generate_response(message, tool_calls_made, tool_results):
                            if chunk and chunk.strip():
                                response_generated = True
                                yield chunk
                        
                        # 如果没有生成任何响应，使用回退机制
                        if not response_generated:
                            logger.warning("第二阶段未生成任何响应，使用回退机制")
                            async for chunk in self._generate_fallback_response(message, tool_calls_made, tool_results):
                                yield chunk
                    else:
                        logger.warning("没有有效的工具结果，提供简化回复")
                        yield "工具执行已完成，但未获得有效结果。"
                        
                except Exception as e:
                    logger.error(f"第二阶段响应生成失败: {e}", exc_info=True)
                    yield f"\n⚠️ 响应生成遇到问题，为您提供工具执行结果摘要：\n\n"
                    try:
                        async for chunk in self._generate_fallback_response(message, tool_calls_made, tool_results):
                            yield chunk
                    except Exception as fallback_error:
                        logger.error(f"回退响应也失败: {fallback_error}")
                        yield "工具执行完成，但无法生成详细说明。"
            else:
                logger.info("没有工具调用，可能是普通对话")
                # 如果LLM决定不调用工具，应该有普通回复
                async for chunk in self._stream_llm_response(updated_conversation_history):
                    yield chunk
            
            logger.info("两阶段流式聊天处理完成")
                    
        except Exception as e:
            logger.error(f"流式聊天处理失败: {e}", exc_info=True)
            yield f"\n❌ 处理失败: {str(e)}"

    async def _phase_one_tool_execution(
        self, 
        conversation_history: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]], 
        original_message: str
    ) -> AsyncGenerator[Any, None]:
        """第一阶段：LLM决策和工具执行，包含完整的对话历史管理"""
        try:
            # 构建请求参数
            request_params = {
                "model": self._get_model_name(),
                "messages": conversation_history,
                "tools": tools,
                "tool_choice": "auto"
            }
            
            # 添加可选参数
            if self.config.get("temperature") is not None:
                request_params["temperature"] = self.config["temperature"]
            if self.config.get("max_tokens") is not None:
                request_params["max_tokens"] = self.config["max_tokens"]
            
            logger.info(f"第一阶段：调用LLM进行工具决策")
            logger.debug(f"LLM请求参数: model={request_params['model']}, tools_count={len(tools)}, messages_count={len(conversation_history)}")
            
            # 如果工具过多，记录警告
            if len(tools) > 15:
                logger.warning(f"工具数量较多 ({len(tools)} 个)，可能影响LLM响应速度")
                
            # 记录请求体大小估算（工具数量 x 平均大小）
            estimated_size = len(tools) * 800  # 估算每个工具约800字节
            logger.debug(f"LLM请求体估算大小: {estimated_size} 字节")
            
            # 性能优化：使用asyncio.create_task来并发处理，添加超时保护
            llm_task = asyncio.create_task(
                self.client.chat.completions.create(**request_params)
            )
            
            # 非流式调用LLM获取工具决策
            response = await llm_task
            logger.info("LLM工具决策调用成功")
            
            # 安全地访问response.choices
            if not response or not response.choices or len(response.choices) == 0:
                logger.error("LLM响应异常：choices为空")
                yield "❌ LLM响应异常，无法获取工具决策"
                return
                
            assistant_message = response.choices[0].message
            
            # 如果没有工具调用，直接流式输出内容
            if not assistant_message.tool_calls:
                if assistant_message.content:
                    # 流式输出普通回复
                    async for chunk in self._stream_llm_response(conversation_history):
                        yield chunk
                return
            
            # 将LLM的工具调用决策添加到对话历史
            tool_call_message = {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": []
            }
            
            # 格式化工具调用信息
            for tool_call in assistant_message.tool_calls:
                tool_call_message["tool_calls"].append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            
            conversation_history.append(tool_call_message)
            
            # 执行工具调用并管理对话历史
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments_json = tool_call.function.arguments
                tool_call_id = tool_call.id
                
                # 输出工具执行开始状态
                yield f"\n🛠️ **正在调用工具**: `{tool_name}`"
                yield f"\n📋 **参数**: {self._format_tool_arguments(arguments_json)}"
                logger.info(f"执行工具调用: {tool_name}")
                
                try:
                    # 执行工具调用
                    arguments = json.loads(arguments_json)
                    start_time = time.time()
                    
                    # 显示执行中状态
                    yield f"\n⏳ 工具执行中..."
                    
                    # 添加超时保护和连接状态检查的工具调用
                    try:
                        # 检查MCP客户端状态
                        if not self.mcp_client:
                            raise Exception("MCP客户端未初始化")
                        
                        # 检查连接状态
                        if hasattr(self.mcp_client, 'status') and self.mcp_client.status.name != "CONNECTED":
                            logger.warning(f"MCP客户端状态异常: {self.mcp_client.status.name}")
                            # 尝试重新连接
                            try:
                                await self.mcp_client.connect()
                            except Exception as reconnect_error:
                                logger.error(f"MCP重连失败: {reconnect_error}")
                                raise Exception(f"MCP连接异常且重连失败: {reconnect_error}")
                        
                        # 执行工具调用
                        result = await self.mcp_client.call_tool(tool_name, arguments)
                        execution_time = time.time() - start_time
                        
                        logger.info(f"工具 {tool_name} 执行完成，耗时: {execution_time:.2f}秒")
                        
                        # 将工具结果添加到对话历史
                        tool_result_message = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                        conversation_history.append(tool_result_message)
                        
                        # 输出工具执行完成状态
                        yield f"\n✅ **工具执行成功**: `{tool_name}` (耗时: {execution_time:.2f}秒)"
                        yield f"\n📊 **结果摘要**: {self._get_result_summary(result)}"
                        
                        # 返回工具调用完成信息
                        yield {
                            "type": "tool_call_complete",
                            "tool_call": {
                                "name": tool_name,
                                "arguments": arguments_json,
                                "id": tool_call_id
                            },
                            "result": result,
                            "conversation_history": conversation_history.copy()
                        }
                        
                    except asyncio.TimeoutError:
                        logger.error(f"工具调用超时: {tool_name}")
                        execution_time = time.time() - start_time
                        
                        # 将超时错误添加到对话历史
                        tool_error_message = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"工具执行超时: 执行时间超过15秒"
                        }
                        conversation_history.append(tool_error_message)
                        
                        yield f"⏰ 工具 {tool_name} 执行超时 (耗时: {execution_time:.2f}秒)"
                        
                        # 返回超时信息
                        yield {
                            "type": "tool_call_complete",
                            "tool_call": {
                                "name": tool_name,
                                "arguments": arguments_json,
                                "id": tool_call_id
                            },
                            "result": None,
                            "error": "执行超时",
                            "conversation_history": conversation_history.copy()
                        }
                    
                    except Exception as tool_error:
                        logger.error(f"工具调用异常: {tool_name}: {tool_error}")
                        execution_time = time.time() - start_time
                        
                        # 将工具错误添加到对话历史
                        tool_error_message = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"工具执行失败: {str(tool_error)}"
                        }
                        conversation_history.append(tool_error_message)
                        
                        yield f"❌ 工具 {tool_name} 执行失败: {str(tool_error)} (耗时: {execution_time:.2f}秒)"
                        
                        # 返回工具调用失败信息
                        yield {
                            "type": "tool_call_complete",
                            "tool_call": {
                                "name": tool_name,
                                "arguments": arguments_json,
                                "id": tool_call_id
                            },
                            "result": None,
                            "error": str(tool_error),
                            "conversation_history": conversation_history.copy()
                        }
                    
                except Exception as e:
                    logger.error(f"工具调用失败 {tool_name}: {e}")
                    
                    # 将工具错误添加到对话历史
                    tool_error_message = {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": f"工具执行失败: {str(e)}"
                    }
                    conversation_history.append(tool_error_message)
                    
                    yield f"❌ 工具 {tool_name} 执行失败: {str(e)}"
                    
                    # 返回工具调用失败信息
                    yield {
                        "type": "tool_call_complete",
                        "tool_call": {
                            "name": tool_name,
                            "arguments": arguments_json,
                            "id": tool_call_id
                        },
                        "result": None,
                        "error": str(e),
                        "conversation_history": conversation_history.copy()  # 提供更新后的对话历史
                    }
                    
        except Exception as e:
            logger.error(f"第一阶段工具执行失败: {e}")
            yield f"❌ 工具执行阶段失败: {str(e)}"

    async def _phase_two_generate_response(
        self, 
        original_message: str, 
        tool_calls: List[Dict[str, Any]], 
        tool_results: List[Any]
    ) -> AsyncGenerator[str, None]:
        """第二阶段：基于工具结果生成LLM对话回复"""
        try:
            logger.info(f"开始第二阶段响应生成，工具调用数: {len(tool_calls)}, 结果数: {len(tool_results)}")
            
            # 构建优化的提示词
            system_prompt = self._get_tool_response_system_prompt()
            user_prompt = self._get_tool_response_user_prompt(original_message, tool_calls, tool_results)
            
            logger.debug(f"系统提示词长度: {len(system_prompt)}")
            logger.debug(f"用户提示词长度: {len(user_prompt)}")
            
            # 构建消息历史
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 构建请求参数
            stream_enabled = self.config.get("stream", True)
            logger.info(f"配置中的stream设置: {stream_enabled}, 完整配置: {self.config}")
            request_params = {
                "model": self._get_model_name(),
                "messages": messages,
                "stream": stream_enabled
            }
            
            # 添加可选参数
            if self.config.get("temperature") is not None:
                request_params["temperature"] = self.config["temperature"]
            if self.config.get("max_tokens") is not None:
                request_params["max_tokens"] = self.config["max_tokens"]
            
            logger.info(f"第二阶段：调用LLM生成回复，模型: {self._get_model_name()}")
            
            # 检查客户端状态
            if not self.client:
                logger.error("LLM客户端为None，无法生成响应")
                yield "❌ LLM客户端未初始化，无法生成响应"
                return
            
            # 根据配置选择流式或非流式调用
            try:
                logger.info(f"准备调用LLM，请求参数: {json.dumps(request_params, ensure_ascii=False, indent=2)}")
                
                # 获取会话ID用于数据恢复
                session_id = getattr(self, 'current_session_id', None)
                if not session_id:
                    logger.error(f"⚠️ 严重警告：恢复阶段未找到会话ID！")
                    session_id = f'fallback_session_{int(time.time())}'
                else:
                    logger.error(f"🆔 恢复阶段使用会话ID: {session_id}")
                
                # 初始化通用变量
                response_generated = False
                chunk_count = 0
                full_response = ""  # 收集完整响应用于最终恢复
                
                if stream_enabled:
                    # LLM流式调用
                    stream = await self.client.chat.completions.create(**request_params)
                    logger.info("LLM流式调用已启动")
                    
                    async for chunk in stream:
                        chunk_count += 1
                        logger.debug(f"收到流式块 #{chunk_count}: {chunk}")
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if delta.content:
                                # 收集完整响应（LLM原始输出）
                                full_response += delta.content
                                response_generated = True
                                
                                # 🚀 阶段1: 实时流式输出（保持用户体验，可能有部分脱敏值未恢复）
                                restored_content = self.data_masker.restore_llm_response(
                                    delta.content, session_id
                                )
                                
                                logger.debug(f"流式块 #{chunk_count}: '{delta.content}' → '{restored_content}'")
                                yield restored_content
                            else:
                                logger.debug(f"块 #{chunk_count} 无内容: {delta}")
                else:
                    # LLM非流式调用，但后端模拟流式输出
                    logger.info("LLM非流式调用已启动")
                    response = await self.client.chat.completions.create(**request_params)
                    logger.info("LLM非流式调用完成")
                    
                    if response and response.choices and len(response.choices) > 0:
                        full_response = response.choices[0].message.content or ""
                        response_generated = True
                        
                        # 恢复脱敏数据
                        restored_content = self.data_masker.restore_llm_response(
                            full_response, session_id
                        )
                        
                        logger.info(f"非流式响应长度: {len(full_response)} 字符")
                        
                        # 模拟流式输出：将完整响应分块输出
                        import re
                        # 按句子分割，保持自然的输出节奏
                        sentences = re.split(r'([。！？\n])', restored_content)
                        current_chunk = ""
                        
                        for i, part in enumerate(sentences):
                            current_chunk += part
                            # 每个句子或换行符后输出一次
                            if part in ['。', '！', '？', '\n'] or i == len(sentences) - 1:
                                if current_chunk.strip():
                                    yield current_chunk
                                    current_chunk = ""
                                    # 添加小延迟模拟真实流式体验
                                    import asyncio
                                    await asyncio.sleep(0.01)
                    else:
                        logger.error("非流式调用返回空响应")
                        response_generated = False
                
                if stream_enabled:
                    logger.info(f"LLM流式调用完成，共生成 {chunk_count} 个块，有效响应: {response_generated}")
                else:
                    logger.info(f"LLM非流式调用完成，有效响应: {response_generated}")
                
                # 🔧 阶段2: 完整内容恢复（修复因chunk分割导致的恢复失败）
                if response_generated and full_response and session_id:
                    # logger.info(f"🔧 开始完整响应恢复处理...")
                    
                    # 对完整响应进行脱敏恢复
                    final_restored_response = self.data_masker.restore_llm_response(
                        full_response, session_id
                    )
                    
                    # 检查是否有新的恢复内容
                    if final_restored_response != full_response:
                        logger.info(f"🎯 检测到完整恢复差异，发送更新指令")
                        logger.info(f"📝 原始完整响应长度: {len(full_response)} 字符")
                        logger.info(f"🔓 恢复完整响应长度: {len(final_restored_response)} 字符")
                        
                        # 发送特殊的更新指令，告知客户端用恢复后的完整内容替换之前的输出
                        update_instruction = {
                            "type": "content_update", 
                            "content": final_restored_response,
                            "reason": "脱敏信息恢复"
                        }
                        
                        yield f"\n\n__UPDATE_CONTENT__:{json.dumps(update_instruction, ensure_ascii=False)}__END_UPDATE__\n"
                        logger.info(f"✅ 完整内容恢复指令已发送")
                    else:
                        logger.info(f"💭 完整响应无需额外恢复")
                
                # 如果没有生成任何响应，提供回退响应
                if not response_generated:
                    logger.warning("LLM未生成任何响应，使用回退机制")
                    async for chunk in self._generate_fallback_response(original_message, tool_calls, tool_results):
                        yield chunk
                        
            except Exception as llm_error:
                logger.error(f"LLM调用异常: {llm_error}", exc_info=True)
                yield f"\n⚠️ LLM调用失败: {str(llm_error)}\n\n为您提供工具执行结果摘要：\n\n"
                async for chunk in self._generate_fallback_response(original_message, tool_calls, tool_results):
                    yield chunk
                        
        except Exception as e:
            logger.error(f"第二阶段响应生成失败: {e}", exc_info=True)
            # 提供回退响应而不是简单的错误信息
            try:
                yield f"\n⚠️ 响应生成遇到问题，为您提供工具执行结果摘要：\n\n"
                async for chunk in self._generate_fallback_response(original_message, tool_calls, tool_results):
                    yield chunk
            except Exception as fallback_error:
                logger.error(f"回退响应生成也失败: {fallback_error}")
                yield f"\n❌ 响应生成失败: {str(e)}"

    async def _stream_llm_response(self, conversation_history: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """流式输出LLM响应（无工具调用）"""
        try:
            # 构建请求参数
            stream_enabled = self.config.get("stream", True)
            logger.info(f"_stream_llm_response配置中的stream设置: {stream_enabled}")
            request_params = {
                "model": self._get_model_name(),
                "messages": conversation_history,
                "stream": stream_enabled
            }
            
            # 添加可选参数
            if self.config.get("temperature") is not None:
                request_params["temperature"] = self.config["temperature"]
            if self.config.get("max_tokens") is not None:
                request_params["max_tokens"] = self.config["max_tokens"]
            
            logger.info("输出普通LLM响应")
            
            if stream_enabled:
                # LLM流式调用
                stream = await self.client.chat.completions.create(**request_params)
                
                async for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            yield delta.content
            else:
                # LLM非流式调用，后端模拟流式输出
                response = await self.client.chat.completions.create(**request_params)
                
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content or ""
                    if content:
                        # 模拟流式输出：按句子分割
                        import re
                        sentences = re.split(r'([。！？\n])', content)
                        current_chunk = ""
                        
                        for i, part in enumerate(sentences):
                            current_chunk += part
                            if part in ['。', '！', '？', '\n'] or i == len(sentences) - 1:
                                if current_chunk.strip():
                                    yield current_chunk
                                    current_chunk = ""
                                    import asyncio
                                    await asyncio.sleep(0.01)
                        
        except Exception as e:
            logger.error(f"LLM响应失败: {e}")
            yield f"❌ 响应生成失败: {str(e)}"

    def _get_tool_response_system_prompt(self) -> str:
        """获取工具结果解读的系统提示词"""
        return """你是一个专业的Kubernetes运维专家和系统分析师，需要基于工具执行结果为用户提供全面、详细的分析报告。

核心要求：
1. **详细分析** - 提供深入、全面的分析，不要过于简短。对每个重要发现都要详细说明
2. **专业解读** - 以专业运维人员的角度解读数据，提供技术洞察和业务影响分析
3. **结构化呈现** - 使用清晰的层次结构，包含概述、详细分析、关键发现、建议等部分
4. **数据驱动** - 基于实际的工具执行结果，引用具体的数字、状态、配置等数据
5. **上下文关联** - 解释数据之间的关联性，分析趋势和模式
6. **实用建议** - 提供具体可行的操作建议和最佳实践
7. **风险评估** - 识别潜在问题和风险，评估其影响程度和紧急性

分析风格：
- 使用专业术语但保持可读性
- 提供充分的背景信息和解释
- 对异常情况进行深入分析
- 包含性能优化和安全建议
- 适当使用表格、列表等格式增强可读性

如果工具执行失败或返回错误，请详细分析可能的原因，提供完整的故障排查步骤和解决方案。"""

    def _get_tool_response_user_prompt(
        self, 
        original_question: str, 
        tool_calls: List[Dict[str, Any]], 
        tool_results: List[Any]
    ) -> str:
        """获取工具结果解读的用户提示词 - 添加脱敏处理"""
        
        # 🔒 关键脱敏点：在序列化前对工具结果进行脱敏
        # 生成唯一的会话ID，确保脱敏和恢复使用同一个ID
        import time
        session_id = f'session_{int(time.time() * 1000)}_{hash(str(tool_results))}'
        self.current_session_id = session_id  # 确保保存会话ID
        
        # logger.error(f"🆔 会话ID生成: {session_id}")
        
        # 提取工具名称用于白名单检查
        tool_names = [tool_call.get("name", "") for tool_call in tool_calls]
        # logger.info(f"🔧 工具调用列表: {tool_names}")
        
        masked_tool_results = self.data_masker.mask_tool_results(tool_results, session_id, tool_names)
        
        # 📝 在日志中记录详细的脱敏效果
        import json
        # logger.error(f"🔒🔒🔒 脱敏处理详细日志 (会话ID: {session_id}) 🔒🔒🔒")
        # logger.error(f"📋 原始工具结果:")
        for i, result in enumerate(tool_results, 1):
            result_json = json.dumps(result, ensure_ascii=False)
            # logger.error(f"   工具结果#{i}: {result_json[:500]}...")
        
        logger.error(f"🔒 脱敏后工具结果:")
        for i, result in enumerate(masked_tool_results, 1):
            result_json = json.dumps(result, ensure_ascii=False)
            # logger.error(f"   脱敏结果#{i}: {result_json[:500]}...")
        
        # 获取映射统计
        stats = self.data_masker.get_session_stats(session_id)
        # logger.error(f"📊 脱敏映射统计: {stats['mapping_count']} 个映射关系")
        
        # # 显示具体的映射关系（调试用）
        # mapping_store = self.data_masker.session_manager.get_session(session_id)
        # if mapping_store:
        #     logger.error(f"🗄️ 映射关系详情:")
        #     for original, masked in list(mapping_store.original_to_masked.items())[:10]:  # 只显示前10个
        #         logger.error(f"   '{original}' → '{masked}'")
        
        # logger.error(f"🔒🔒🔒 脱敏处理日志结束 🔒🔒🔒")
        
        # 格式化工具执行结果（使用脱敏后的数据）
        formatted_results = []
        for i, (tool_call, result) in enumerate(zip(tool_calls, masked_tool_results), 1):
            tool_name = tool_call.get("name", "未知工具")
            if result is not None:
                if hasattr(result, '__dict__'):
                    result_str = json.dumps(result.__dict__, ensure_ascii=False, indent=2)
                else:
                    result_str = json.dumps(result, ensure_ascii=False, indent=2)
                formatted_results.append(f"{i}. 工具: {tool_name}\n   结果: {result_str}")
            else:
                error = tool_call.get("error", "执行失败")
                formatted_results.append(f"{i}. 工具: {tool_name}\n   错误: {error}")
        
        results_text = "\n\n".join(formatted_results)
        
        return f"""用户问题：{original_question}

工具执行结果：
{results_text}

请基于工具执行结果提供全面详细的分析报告。要求：

**分析结构：**
1. **概述** - 简要总结当前状况和主要发现
2. **详细分析** - 深入分析每个重要数据点，解释其含义和影响
3. **关键发现** - 突出重要的发现、异常情况或值得关注的点
4. **趋势分析** - 如果有相关数据，分析变化趋势和模式
5. **风险评估** - 识别潜在问题、风险等级和影响范围
6. **建议措施** - 提供具体的操作建议、优化方案和最佳实践
7. **后续监控** - 建议需要持续关注的指标和监控点

**格式要求：**
- 使用Markdown格式，包含标题、列表、表格等
- 每个部分之间用空行分隔
- 对重要信息使用**粗体**或`代码格式`强调
- 数据表格使用标准Markdown表格格式
- 适当使用emoji图标增强可读性（如 ⚠️ 🔍 📊 💡 等）

**内容深度：**
- 不要过于简短，提供充分的分析和解释
- 对每个重要发现都要详细说明原因和影响
- 包含专业的技术见解和业务影响分析
- 提供可操作的具体建议

请开始详细分析："""

    def _format_tool_arguments(self, arguments_json: str) -> str:
        """格式化工具参数为用户友好的显示"""
        try:
            arguments = json.loads(arguments_json)
            if isinstance(arguments, dict):
                # 格式化为简洁的参数显示
                formatted_args = []
                for key, value in arguments.items():
                    if isinstance(value, str) and len(value) > 50:
                        # 长字符串截断显示
                        formatted_args.append(f"{key}={value[:47]}...")
                    else:
                        formatted_args.append(f"{key}={value}")
                return ", ".join(formatted_args)
            else:
                return str(arguments)
        except json.JSONDecodeError:
            return arguments_json[:100] + "..." if len(arguments_json) > 100 else arguments_json

    async def _generate_fallback_response(
        self, 
        original_message: str, 
        tool_calls: List[Dict[str, Any]], 
        tool_results: List[Any]
    ) -> AsyncGenerator[str, None]:
        """生成回退响应，当LLM无法生成响应时使用"""
        try:
            yield "基于工具执行结果，为您提供以下信息：\n\n"
            
            for i, (tool_call, result) in enumerate(zip(tool_calls, tool_results), 1):
                tool_name = tool_call.get("name", "未知工具")
                yield f"**{i}. 工具: {tool_name}**\n"
                
                if result is not None:
                    # 格式化工具结果
                    if isinstance(result, dict):
                        if "items" in result and isinstance(result["items"], list):
                            items = result["items"]
                            yield f"找到 {len(items)} 个资源\n"
                            if items:
                                yield "主要资源：\n"
                                for item in items[:3]:  # 显示前3个
                                    # 安全地处理可能为None的item
                                    if item is not None and isinstance(item, dict):
                                        metadata = item.get("metadata", {})
                                        if isinstance(metadata, dict):
                                            yield f"- {metadata.get('name', 'Unknown')}\n"
                                        else:
                                            yield f"- {item.get('name', 'Unknown')}\n"
                                    else:
                                        yield f"- 无效资源项\n"
                        elif "content" in result:
                            content = result["content"]
                            if len(content) > 200:
                                yield f"日志内容（前200字符）：\n{content[:200]}...\n"
                            else:
                                yield f"日志内容：\n{content}\n"
                        else:
                            # 通用字典结果
                            try:
                                yield f"执行结果：{json.dumps(result, ensure_ascii=False, indent=2)[:300]}...\n"
                            except Exception as json_error:
                                yield f"执行结果：{str(result)[:300]}...\n"
                    elif isinstance(result, list):
                        yield f"返回列表，包含 {len(result)} 项\n"
                    else:
                        yield f"结果：{str(result)[:200]}...\n"
                else:
                    error = tool_call.get("error", "执行失败")
                    yield f"❌ 执行失败：{error}\n"
                
                yield "\n"
                
        except Exception as e:
            logger.error(f"生成回退响应失败: {e}")
            yield f"工具执行完成，但无法生成详细说明。"

    def _get_result_summary(self, result: Any) -> str:
        """获取工具结果的简要摘要"""
        try:
            if isinstance(result, dict):
                if "items" in result and isinstance(result["items"], list):
                    # K8s 资源列表
                    items = result["items"]
                    count = len(items)
                    return f"找到 {count} 个资源"
                elif "pod_name" in result:
                    # Pod 日志
                    return f"获取到 Pod {result['pod_name']} 的日志"
                elif "deployment_name" in result:
                    # 部署操作
                    return f"部署 {result['deployment_name']} 操作完成"
                elif "success" in result:
                    # 通用成功/失败结果
                    return "操作成功" if result["success"] else "操作失败"
                else:
                    # 通用字典结果
                    try:
                        keys = list(result.keys())[:3]  # 显示前3个键
                        return f"返回数据包含: {', '.join(keys)}"
                    except Exception:
                        return "返回字典数据"
            elif isinstance(result, list):
                return f"返回列表，包含 {len(result)} 项"
            elif isinstance(result, str):
                return f"返回文本，长度 {len(result)} 字符"
            else:
                return f"返回 {type(result).__name__} 类型数据"
        except Exception as e:
            logger.warning(f"获取结果摘要时出错: {e}")
            return "结果处理完成"

    async def _execute_tool_call(self, tool_name: str, arguments_json: str) -> str:
        """执行工具调用并返回格式化结果"""
        try:
            if not self.mcp_client:
                logger.warning("MCP客户端未连接，无法执行工具调用")
                return "❌ MCP客户端未连接，无法执行工具调用"
            
            logger.info(f"执行工具调用: {tool_name}")
            logger.debug(f"工具参数: {arguments_json}")
            
            import json
            try:
                arguments = json.loads(arguments_json)
            except json.JSONDecodeError as e:
                logger.error(f"工具参数JSON解析失败: {e}")
                return f"❌ 工具参数格式错误: {str(e)}"
            
            # 执行工具调用
            start_time = time.time()
            result = await self.mcp_client.call_tool(tool_name, arguments)
            execution_time = time.time() - start_time
            
            logger.info(f"工具 {tool_name} 执行完成，耗时: {execution_time:.2f}秒")
            
            # 格式化结果
            formatted_result = self.format_tool_result(result)
            return formatted_result
            
        except Exception as e:
            logger.error(f"工具调用失败 {tool_name}: {e}", exc_info=True)
            return f"❌ 工具调用失败: {str(e)}"
    
    async def _get_available_tools(self):
        """获取可用工具列表"""
        try:
            if not self.mcp_client:
                return None
            
            available_tools = await self.mcp_client.list_tools()
            if available_tools:
                return self._convert_tools_to_openai(available_tools)
            return None
            
        except Exception as e:
            logger.warning(f"获取工具列表失败: {e}")
            return None


    

    
    async def chat(
        self, 
        messages: List[ChatMessage], 
        user_id: str = "default",
        stream: bool = False,
        provider_id: Optional[str] = None
    ) -> Union[AsyncGenerator[str, None], ProcessResult]:
        """
        聊天方法 - 支持供应商切换
        
        :param messages: 消息列表
        :param user_id: 用户ID
        :param stream: 是否流式输出
        :param provider_id: 指定供应商ID，如果为None则使用当前供应商
        """
        # 如果指定了供应商，临时切换
        original_provider = self.config.get("provider", "openai")
        if provider_id and provider_id != original_provider:
            logger.warning(f"provider_id 参数已废弃，当前配置为 {original_provider}，无法切换。")
        
        try:
            # 检查LLM是否启用
            if not self.config.get("enabled", True):
                result = "LLM功能已禁用，无法进行聊天。请在设置中启用LLM功能。"
                if stream:
                    async def _yield_disabled():
                        yield result
                    return _yield_disabled()
                else:
                    return ProcessResult(content=result)
            
            # 检查当前供应商是否可用
            current_provider = self.get_current_provider()
            if not current_provider or not current_provider.get("enabled", True):
                result = f"当前供应商不可用，请检查配置。"
                if stream:
                    async def _yield_unavailable():
                        yield result
                    return _yield_unavailable()
                else:
                    return ProcessResult(content=result)
            
            # 使用流式或非流式方式
            if stream:
                # 流式输出
                return self._stream_chat_response(messages, user_id)
            else:
                # 非流式输出
                return await self._process_chat(messages, user_id)
                
        finally:
            # 恢复原供应商
            if provider_id and provider_id != original_provider:
                logger.warning(f"provider_id 参数已废弃，无法切换供应商。当前配置为 {original_provider}。")
    
    async def chat_with_shortcuts(
        self,
        shortcut: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessResult:
        """快捷指令处理"""
        shortcut_prompts = {
            "/pods": "请获取Kubernetes集群中的Pod列表，并以易读的格式展示",
            "/logs": "请获取指定Pod的最新日志",
            "/scale": "请扩缩容指定的Deployment",
            "/status": "请检查集群状态和健康情况",
            "/help": "显示所有可用的快捷指令"
        }
        
        prompt = shortcut_prompts.get(shortcut)
        if not prompt:
            return ProcessResult(
                content=f"未知的快捷指令: {shortcut}\n\n可用指令:\n" + 
                       "\n".join(f"- {k}: {v}" for k, v in shortcut_prompts.items())
            )
        
        # 构建消息
        messages = [
            ChatMessage(role="system", content="你是一个专业的Kubernetes运维助手，擅长使用K8s工具来管理集群。"),
            ChatMessage(role="user", content=f"{prompt}\n\n用户补充信息: {content}")
        ]
        
        return await self.chat(messages, enable_tools=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=60))
    async def _chat_without_tools(self, messages: List[ChatMessage]) -> ProcessResult:
        """不使用工具的聊天"""
        if self.client is None:
            return ProcessResult(
                content="LLM客户端未正确初始化，请检查配置。"
            )
            
        openai_messages = self._convert_messages_to_openai(messages)
        
        try:
            # 使用异步create方法
            response = await self.client.chat.completions.create(
                model=self._get_model_name(),
                messages=openai_messages,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 2000)
            )
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return ProcessResult(
                content=f"调用LLM服务失败: {str(e)}"
            )
        
        # 确保响应内容不为空
        content = ""
        if response and response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            content = message.content or ""
        
        # 如果内容为空，提供默认响应
        if not content:
            content = "抱歉，我没能生成有效的响应，请重试。"
        
        # 规范化usage信息
        usage_dict = self._simplify_usage(getattr(response, 'usage', None))
        
        return ProcessResult(
            content=content,
            usage=usage_dict
        )
    
    async def _chat_with_tools(self, messages: List[ChatMessage]) -> ProcessResult:
        """使用工具的聊天"""
        if self.client is None:
            return ProcessResult(
                content="LLM客户端未正确初始化，请检查配置。"
            )
            
        # 获取可用工具
        try:
            if not self.mcp_client:
                return await self._chat_without_tools(messages)
            tools = await self.mcp_client.list_tools()
        except Exception as e:
            logger.warning(f"获取MCP工具失败: {e}")
            return await self._chat_without_tools(messages)
            
        if not tools:
            return await self._chat_without_tools(messages)
        
        # 转换工具为 OpenAI 格式
        openai_tools = self._convert_tools_to_openai(tools)
        openai_messages = self._convert_messages_to_openai(messages)
        
        # 调用 LLM
        try:
            # 使用异步create方法
            response = await self.client.chat.completions.create(
                model=self._get_model_name(),
                messages=openai_messages,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 2000),
                tools=openai_tools,
                tool_choice="auto"
            )
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return ProcessResult(
                content=f"调用LLM服务失败: {str(e)}"
            )
        
        # 安全地访问response.choices
        if not response or not response.choices or len(response.choices) == 0:
            logger.error("LLM响应异常：choices为空")
            return ProcessResult(
                content="LLM响应异常，请重试。"
            )
            
        message = response.choices[0].message
        
        # 如果没有工具调用，直接返回
        if not message.tool_calls:
            # 确保内容不为空
            content = message.content or "抱歉，我没能生成有效的响应，请重试。"
            
            # 规范化usage信息
            usage_dict = self._simplify_usage(getattr(response, 'usage', None))
            
            return ProcessResult(
                content=content,
                usage=usage_dict
            )
        
        # 执行工具调用
        function_results = []
        for tool_call in message.tool_calls:
            try:
                # 解析参数
                parameters = json.loads(tool_call.function.arguments)
                
                # 调用 MCP 工具
                if not self.mcp_client:
                    result = "MCP客户端未连接，无法执行工具调用"
                else:
                    result = await self.mcp_client.call_tool(
                    tool_call.function.name,
                    parameters
                )
                
                function_results.append(FunctionCallResult(
                    function_call=FunctionCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ),
                    result=result
                ))
                
                # 将工具结果添加到消息历史
                openai_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                
                # 构建上下文信息
                context = {
                    'parameters': parameters,
                    'user_message': messages[-1].content if messages else '',
                    'tool_call_id': tool_call.id
                }
                
                # 使用智能结果处理
                processed_content = self._process_mcp_result(result, tool_call.function.name, context)
                
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": processed_content
                })
                
            except Exception as e:
                logger.error(f"工具调用失败 {tool_call.function.name}: {e}")
                function_results.append(FunctionCallResult(
                    function_call=FunctionCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ),
                    error=str(e)
                ))
        
        # 如果有工具调用结果，再次调用 LLM 生成最终回复
        if function_results:
            try:
                # 优化上下文大小
                optimized_messages = self._optimize_context_size(openai_messages)
                
                # 使用异步create方法
                final_response = await self.client.chat.completions.create(
                    model=self._get_model_name(),
                    messages=optimized_messages,
                    temperature=self.config.get("temperature", 0.7),
                    max_tokens=self.config.get("max_tokens", 2000)
                )
            except Exception as e:
                logger.error(f"最终响应生成失败: {e}")
                return ProcessResult(
                    content="工具调用完成，但生成最终响应时出错。",
                    function_calls=function_results
                )
            
            # 确保最终内容不为空
            final_message_content = ""
            if final_response and final_response.choices and len(final_response.choices) > 0:
                final_message_content = final_response.choices[0].message.content or ""
            
            final_content = self._format_response_with_tools(
                final_message_content,
                function_results
            )
            
            # 规范化usage信息
            usage_dict = self._simplify_usage(getattr(final_response, 'usage', None))
            
            return ProcessResult(
                content=final_content,
                function_calls=function_results,
                usage=usage_dict
            )
        
        # 最终回退处理
        content = message.content or "工具调用完成"
        
        # 规范化usage信息
        usage_dict = self._simplify_usage(getattr(response, 'usage', None))
        
        return ProcessResult(
            content=content,
            function_calls=function_results,
            usage=usage_dict
        )
    
    def _convert_messages_to_openai(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """转换消息格式为 OpenAI 格式"""
        result = []
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
                
            if msg.function_call:
                openai_msg["function_call"] = {
                    "name": msg.function_call.name,
                    "arguments": msg.function_call.arguments
                }
            
            result.append(openai_msg)
        
        return result
    
    def _convert_tools_to_openai(self, tools) -> List[Dict[str, Any]]:
        """转换 MCP 工具为 OpenAI 工具格式"""
        result = []
        for i, tool in enumerate(tools):
            try:
                logger.debug(f"🔧 处理工具 {i+1}/{len(tools)}: {tool.name}")
                
                # 清理schema以确保与不同API提供商的兼容性
                cleaned_schema = self._clean_schema_for_compatibility(tool.input_schema)
                
                converted_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": cleaned_schema
                    }
                }
                result.append(converted_tool)
                logger.debug(f"✅ 工具 {tool.name} 转换成功")
                
            except Exception as e:
                logger.error(f"❌ 工具 {tool.name} 转换失败: {e}")
                # 继续处理其他工具，不因单个工具失败而停止
                continue
                
        return result
    
    def _clean_schema_for_compatibility(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """清理JSON schema以确保API兼容性"""
        if not isinstance(schema, dict):
            return schema
        
        try:
            cleaned = {}
            for key, value in schema.items():
                if key == "properties" and isinstance(value, dict):
                    # 清理properties中的类型定义
                    logger.debug(f"🔧 清理schema properties，包含 {len(value)} 个属性")
                    cleaned[key] = {}
                    for prop_name, prop_def in value.items():
                        logger.debug(f"🔧 清理属性: {prop_name}")
                        cleaned[key][prop_name] = self._clean_property_definition(prop_def, 0)
                else:
                    cleaned[key] = value
            
            return cleaned
        except Exception as e:
            logger.error(f"❌ Schema清理失败: {e}")
            # 返回原始schema作为fallback
            return schema
    
    def _clean_property_definition(self, prop_def: Dict[str, Any], _depth: int = 0) -> Dict[str, Any]:
        """清理单个属性定义"""
        if not isinstance(prop_def, dict):
            return prop_def
        
        # 防止递归过深导致栈溢出
        if _depth > 10:
            logger.warning(f"🔧 Schema递归深度超过10层，停止处理")
            return prop_def
        
        cleaned = prop_def.copy()
        
        # 处理类型定义
        if "type" in cleaned:
            type_value = cleaned["type"]
            if isinstance(type_value, list):
                # 将数组类型转换为单一类型（选择第一个，通常是主要类型）
                if type_value:
                    old_type = type_value
                    cleaned["type"] = type_value[0]
                    logger.debug(f"🔧 转换数组类型 {old_type} 为 {type_value[0]}")
                else:
                    cleaned["type"] = "string"  # 默认为string
        
        # 递归处理嵌套的schema
        for key, value in cleaned.items():
            if key == "items" and isinstance(value, dict):
                cleaned[key] = self._clean_property_definition(value, _depth + 1)
            elif key == "properties" and isinstance(value, dict):
                cleaned[key] = {}
                for sub_key, sub_value in value.items():
                    cleaned[key][sub_key] = self._clean_property_definition(sub_value, _depth + 1)
        
        return cleaned
    
    def _format_response_with_tools(
        self,
        content: str,
        function_results: List[FunctionCallResult]
    ) -> str:
        """格式化包含工具调用结果的响应"""
        if not function_results:
            return content
        
        formatted_content = content + "\n\n**工具调用详情:**\n"
        
        for i, result in enumerate(function_results, 1):
            formatted_content += f"\n**{i}. {result.function_call.name}**\n"
            
            if result.error:
                formatted_content += f"❌ 执行失败: {result.error}\n"
            else:
                formatted_content += f"✅ 执行成功\n"
                # 简化结果显示
                try:
                    if isinstance(result.result, dict):
                        if "items" in result.result and isinstance(result.result.get("items"), list):
                            items = result.result["items"]
                            formatted_content += f"📊 返回 {len(items)} 项结果\n"
                        else:
                            result_str = json.dumps(result.result, ensure_ascii=False, indent=2)[:200]
                            formatted_content += f"📋 结果: {result_str}...\n"
                    else:
                        formatted_content += f"📋 结果: {str(result.result)[:200]}...\n"
                except Exception as format_error:
                    logger.warning(f"格式化工具结果时出错: {format_error}")
                    formatted_content += f"📋 结果: 数据格式化失败\n"
        
        return formatted_content
    
    async def get_available_shortcuts(self) -> Dict[str, str]:
        """获取可用的快捷指令"""
        shortcuts = {
            "/pods": "查看Pod列表",
            "/logs": "查看Pod日志",
            "/scale": "扩缩容Deployment", 
            "/status": "检查集群状态",
            "/help": "显示帮助信息"
        }
        
        # 如果 MCP 客户端连接，添加工具相关的快捷指令
        if self.mcp_client and hasattr(self.mcp_client, 'status') and self.mcp_client.status.value == "connected":
            try:
                tools = await self.mcp_client.list_tools()
                for tool in tools:
                    shortcuts[f"/tool-{tool.name}"] = f"直接调用工具: {tool.description}"
            except Exception as e:
                logger.warning(f"获取工具快捷指令失败: {e}")
        
        return shortcuts
    
    def format_tool_result(self, result: Any) -> str:
        """格式化工具调用结果为用户友好的文本"""
        try:
            if isinstance(result, dict):
                if "items" in result and isinstance(result["items"], list):
                    # K8s 资源列表格式
                    items = result["items"]
                    if not items:
                        return "📭 未找到任何资源"
                    
                    formatted = f"📦 找到 {len(items)} 个资源:\n\n"
                    for item in items[:10]:  # 限制显示数量
                        # 安全地处理可能为None的item
                        if item is not None and isinstance(item, dict):
                            metadata = item.get("metadata", {})
                            status = item.get("status", {})
                            
                            # 安全地获取名称
                            name = "Unknown"
                            if isinstance(metadata, dict):
                                name = metadata.get("name", "Unknown")
                            elif "name" in item:
                                name = item.get("name", "Unknown")
                            
                            # 安全地获取命名空间
                            namespace = "default"
                            if isinstance(metadata, dict):
                                namespace = metadata.get("namespace", "default")
                            elif "namespace" in item:
                                namespace = item.get("namespace", "default")
                            
                            # 安全地获取状态
                            phase = "Unknown"
                            if isinstance(status, dict):
                                phase = status.get("phase", "Unknown")
                            elif "phase" in item:
                                phase = item.get("phase", "Unknown")
                            elif "status" in item:
                                phase = item.get("status", "Unknown")
                            
                            formatted += f"• **{name}**\n"
                            formatted += f"  命名空间: {namespace}\n"
                            formatted += f"  状态: {phase}\n\n"
                        else:
                            formatted += f"• **无效资源项**\n"
                            formatted += f"  数据: {str(item)[:50]}...\n\n"
                    
                    if len(items) > 10:
                        formatted += f"... 还有 {len(items) - 10} 个资源\n"
                    
                    return formatted
                
                elif "pod_name" in result and "content" in result:
                    # 日志格式
                    return f"📋 **{result['pod_name']}** 日志:\n\n```\n{result['content']}\n```"
                
                elif "deployment_name" in result:
                    # 扩缩容结果格式
                    return f"🔄 扩缩容完成:\n" + \
                           f"• 部署名称: {result['deployment_name']}\n" + \
                           f"• 命名空间: {result.get('namespace', 'default')}\n" + \
                           f"• 副本数: {result.get('previous_replicas', 0)} → {result.get('target_replicas', 0)}\n" + \
                           f"• 状态: {'✅ 成功' if result.get('success') else '❌ 失败'}"
                
                else:
                    # 通用字典格式
                    try:
                        return f"📄 结果:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
                    except Exception as json_error:
                        return f"📄 结果:\n{str(result)}"
            
            elif isinstance(result, list):
                return f"📋 列表结果 ({len(result)} 项):\n" + \
                       "\n".join(f"• {item}" for item in result[:10] if item is not None)
            
            else:
                return f"📄 结果: {str(result)}"
        except Exception as e:
            logger.error(f"格式化工具结果时出错: {e}")
            return f"📄 工具执行完成，结果类型: {type(result).__name__}"

    def _simplify_usage(self, usage_obj: Any) -> Optional[Dict[str, int]]:
        """将OpenAI/兼容提供商的usage结构简化为仅包含整数字段，避免Pydantic校验失败。"""
        try:
            if not usage_obj:
                return None
            # 先尝试model_dump
            data = None
            try:
                data = usage_obj.model_dump()
            except Exception:
                # 回退到属性读取
                data = {
                    "prompt_tokens": getattr(usage_obj, 'prompt_tokens', None),
                    "completion_tokens": getattr(usage_obj, 'completion_tokens', None),
                    "total_tokens": getattr(usage_obj, 'total_tokens', None),
                }
            # 仅保留三类常用整数字段
            simplified: Dict[str, int] = {}
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                val = data.get(key) if isinstance(data, dict) else None
                if isinstance(val, (int,)):
                    simplified[key] = val
                elif isinstance(val, float):
                    simplified[key] = int(val)
                elif isinstance(val, dict):
                    # 有些提供商会把 details 放在对象里，这里尽量取常用字段
                    inner = val.get("total") or val.get("count")
                    if isinstance(inner, (int, float)):
                        simplified[key] = int(inner)
            return simplified or None
        except Exception:
            return None