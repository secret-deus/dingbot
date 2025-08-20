"""
钉钉机器人集成模块 - Python版本
处理钉钉消息，集成 LLM 和 MCP 工具链
"""

import json
import time
import hashlib
import hmac
import base64
import urllib.parse
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import httpx
from pydantic import BaseModel

from ..llm.processor import EnhancedLLMProcessor
from ..mcp.types import ChatMessage, MCPException


class DingTalkMessage(BaseModel):
    """钉钉消息结构"""
    msgtype: str
    text: Optional[Dict[str, str]] = None
    markdown: Optional[Dict[str, str]] = None
    at: Optional[Dict[str, List[str]]] = None


class DingTalkWebhookRequest(BaseModel):
    """钉钉Webhook请求结构"""
    msgId: str
    msgtype: str
    text: Dict[str, str]
    chatbotUserId: str
    conversationId: str
    atUsers: Optional[List[Dict[str, str]]] = None
    conversationType: str
    conversationTitle: Optional[str] = None
    senderId: str
    senderNick: str
    senderCorpId: Optional[str] = None
    sessionWebhook: str
    createAt: int
    senderStaffId: Optional[str] = None
    isAdmin: Optional[bool] = None
    robotCode: Optional[str] = None


class DingTalkBot:
    """钉钉机器人处理器"""
    
    def __init__(
        self, 
        webhook_url: str,
        secret: Optional[str] = None,
        llm_processor: Optional[EnhancedLLMProcessor] = None
    ):
        self.webhook_url = webhook_url
        self.secret = secret
        self.llm_processor = llm_processor
        
    async def process_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理钉钉Webhook请求"""
        try:
            # 记录原始请求数据
            logger.info("=" * 60)
            logger.info("📨 收到钉钉机器人消息")
            logger.info(f"📋 原始请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            # 解析请求
            webhook_request = DingTalkWebhookRequest(**request_data)
            
            # 记录解析后的消息详情
            message_content = webhook_request.text.get('content', '')
            logger.info(f"💬 消息内容: '{message_content}'")
            logger.info(f"👤 发送者: {webhook_request.senderNick} (ID: {webhook_request.senderId})")
            logger.info(f"🏠 会话: {webhook_request.conversationId} ({webhook_request.conversationType})")
            logger.info(f"📅 时间戳: {datetime.fromtimestamp(webhook_request.createAt/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 记录@用户信息
            if webhook_request.atUsers:
                at_info = [f"{user.get('dingtalkId', 'Unknown')}({user.get('staffId', 'N/A')})" 
                          for user in webhook_request.atUsers]
                logger.info(f"🏷️  @用户: {', '.join(at_info)}")
            else:
                logger.info("🏷️  @用户: 无")
            
            # 处理消息
            logger.info("🔄 开始处理消息...")
            response_content = await self._process_message(webhook_request)
            logger.info(f"✅ 消息处理完成，响应长度: {len(response_content)} 字符")
            logger.info(f"📤 响应内容预览: {response_content[:200]}{'...' if len(response_content) > 200 else ''}")
            
            # 构建响应
            response = await self._build_response(webhook_request, response_content)
            logger.info(f"📦 构建响应类型: {response.msgtype}")
            
            # 发送响应
            logger.info(f"🚀 发送响应到: {webhook_request.sessionWebhook}")
            await self._send_response(webhook_request.sessionWebhook, response)
            logger.info("✅ 响应发送成功")
            logger.info("=" * 60)
            
            return {"success": True, "message": "消息处理成功"}
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ 处理钉钉消息失败: {e}")
            logger.error(f"📋 错误详情: {str(e)}")
            logger.error("=" * 60)
            return {"success": False, "error": str(e)}
    
    async def _process_message(self, request: DingTalkWebhookRequest) -> str:
        """处理消息内容"""
        content = request.text.get("content", "").strip()
        
        if not content:
            logger.warning("⚠️  收到空消息内容")
            return "请发送有效的消息内容"
        
        logger.info(f"🧠 消息路由分析:")
        logger.info(f"   消息类型: {'快捷指令' if content.startswith('/') else '普通消息'}")
        
        # 检查是否为快捷指令
        if content.startswith("/"):
            logger.info(f"⚡ 路由到快捷指令处理器")
            return await self._process_shortcut_command(content, request)
        
        # 所有普通消息都使用AI处理
        logger.info(f"🤖 AI处理需求评估: 需要（所有消息）")
        logger.info(f"🧠 路由到LLM处理器")
        return await self._process_with_llm(content, request)
    
    async def _process_shortcut_command(
        self, 
        content: str, 
        request: DingTalkWebhookRequest
    ) -> str:
        """处理快捷指令"""
        parts = content.split(" ", 1)
        shortcut = parts[0]
        additional_content = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"⚡ 快捷指令处理:")
        logger.info(f"   指令: {shortcut}")
        logger.info(f"   参数: '{additional_content}' ({len(additional_content)} 字符)")
        
        if not self.llm_processor:
            logger.error("❌ LLM处理器未配置")
            return "❌ LLM处理器未配置，无法执行快捷指令"
        
        try:
            context = {
                "user_id": request.senderId,
                "user_name": request.senderNick,
                "conversation_id": request.conversationId
            }
            
            logger.info(f"🔄 执行快捷指令: {shortcut}")
            result = await self.llm_processor.chat_with_shortcuts(
                shortcut, additional_content, context
            )
            
            logger.info(f"✅ 快捷指令执行成功，结果长度: {len(result.content)} 字符")
            return result.content
            
        except MCPException as e:
            logger.error(f"❌ 快捷指令MCP异常: {e}")
            return f"❌ 指令执行失败: {e.message}"
        except Exception as e:
            logger.error(f"❌ 快捷指令处理异常: {e}")
            return f"❌ 指令执行异常: {str(e)}"
    
    async def _process_with_llm(
        self, 
        content: str, 
        request: DingTalkWebhookRequest
    ) -> str:
        """使用LLM处理消息"""
        logger.info(f"🧠 LLM处理:")
        logger.info(f"   消息长度: {len(content)} 字符")
        logger.info(f"   发送者: {request.senderNick}")
        
        if not self.llm_processor:
            logger.error("❌ LLM处理器未配置")
            return "❌ LLM处理器未配置"
        
        try:
            messages = [
                ChatMessage(
                    role="system",
                    content="你是一个专业的Kubernetes运维助手，可以帮助用户管理和监控K8s集群。"
                ),
                ChatMessage(
                    role="user", 
                    content=content
                )
            ]
            
            logger.info(f"🔄 调用LLM处理器 (启用工具)")
            result = await self.llm_processor.chat(messages, enable_tools=True)
            logger.info(f"✅ LLM处理成功，结果长度: {len(result.content)} 字符")
            
            # 记录工具调用情况
            if hasattr(result, 'function_calls') and result.function_calls:
                logger.info(f"🛠️  工具调用数量: {len(result.function_calls)}")
                for i, call in enumerate(result.function_calls, 1):
                    logger.info(f"   工具{i}: {call.function_call.name}")
            
            return result.content
            
        except MCPException as e:
            logger.error(f"❌ LLM处理MCP异常: {e}")
            return f"❌ AI处理失败: {e.message}"
        except Exception as e:
            logger.error(f"❌ LLM处理异常: {e}")
            return f"❌ AI处理异常: {str(e)}"
    

    
    async def _build_response(
        self, 
        request: DingTalkWebhookRequest, 
        content: str
    ) -> DingTalkMessage:
        """构建响应消息"""
        # 限制消息长度
        if len(content) > 4000:
            content = content[:3900] + "\n\n... (内容过长，已截断)"
        
        # Markdown格式支持
        if self._is_markdown_content(content):
            return DingTalkMessage(
                msgtype="markdown",
                markdown={
                    "title": "K8s运维助手",
                    "text": content
                }
            )
        else:
            return DingTalkMessage(
                msgtype="text",
                text={"content": content}
            )
    
    def _is_markdown_content(self, content: str) -> bool:
        """检查内容是否包含Markdown格式"""
        markdown_indicators = ["**", "```", "###", "•", "📦", "✅", "❌"]
        return any(indicator in content for indicator in markdown_indicators)
    
    async def _send_response(self, session_webhook: str, message: DingTalkMessage) -> None:
        """发送响应消息"""
        try:
            # 记录发送详情
            message_dict = message.model_dump(exclude_none=True)
            logger.info(f"📤 准备发送响应:")
            logger.info(f"   消息类型: {message.msgtype}")
            logger.info(f"   目标URL: {session_webhook}")
            logger.info(f"   消息体大小: {len(json.dumps(message_dict, ensure_ascii=False))} 字符")
            
            if message.msgtype == "text" and message.text:
                content_preview = message.text.get("content", "")[:100]
                logger.info(f"   文本内容预览: {content_preview}{'...' if len(content_preview) >= 100 else ''}")
            elif message.msgtype == "markdown" and message.markdown:
                title = message.markdown.get("title", "")
                text_preview = message.markdown.get("text", "")[:100]
                logger.info(f"   Markdown标题: {title}")
                logger.info(f"   Markdown内容预览: {text_preview}{'...' if len(text_preview) >= 100 else ''}")
            
            # 如果有secret，添加签名验证
            final_webhook_url = session_webhook
            if self.secret:
                timestamp, sign = self._generate_sign()
                separator = '&' if '?' in session_webhook else '?'
                final_webhook_url = f"{session_webhook}{separator}timestamp={timestamp}&sign={sign}"
                logger.info(f"🔐 已添加签名验证:")
                logger.info(f"   时间戳: {timestamp}")
                logger.info(f"   签名: {sign[:20]}...")
            
            async with httpx.AsyncClient() as client:
                logger.info(f"🌐 发送HTTP请求...")
                response = await client.post(
                    final_webhook_url,
                    json=message_dict,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                logger.info(f"📈 HTTP响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    response_text = response.text
                    response_data = json.loads(response_text) if response_text else {}
                    
                    if response_data.get('errcode') == 0:
                        logger.info(f"✅ 消息发送成功")
                    else:
                        logger.error(f"❌ 钉钉API返回错误: {response_data}")
                        # 提供错误解决建议
                        errcode = response_data.get('errcode')
                        if errcode == 310000:
                            logger.error("🔧 签名验证失败，请检查SECRET配置")
                        elif errcode == 300001:
                            logger.error("🔧 Token无效，请检查WEBHOOK_URL配置")
                    
                    logger.info(f"📋 钉钉响应: {response_text}")
                else:
                    logger.error(f"❌ 消息发送失败: HTTP {response.status_code}")
                    logger.error(f"📋 错误响应: {response.text}")
                    
        except httpx.TimeoutException:
            logger.error(f"⏰ 发送响应超时 (30秒)")
        except httpx.RequestError as e:
            logger.error(f"🌐 网络请求错误: {e}")
        except Exception as e:
            logger.error(f"❌ 发送响应时发生未知错误: {e}")
    
    def _generate_sign(self) -> tuple[str, str]:
        """生成钉钉机器人签名（参考官方示例）"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            self.secret.encode('utf-8'), 
            string_to_sign.encode('utf-8'), 
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign
    
    def verify_signature(self, timestamp: str, signature: str) -> bool:
        """验证钉钉签名"""
        if not self.secret:
            return True  # 如果没有配置secret，跳过验证
        
        try:
            string_to_sign = f"{timestamp}\n{self.secret}"
            hmac_code = hmac.new(
                self.secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            return sign == signature
        except Exception as e:
            logger.error(f"签名验证失败: {e}")
            return False
    
    async def send_proactive_message(
        self, 
        webhook_url: str, 
        content: str, 
        at_users: Optional[List[str]] = None,
        at_user_ids: Optional[List[str]] = None,
        is_at_all: bool = False
    ) -> bool:
        """主动发送消息（支持签名验证）"""
        try:
            # 构建消息体，按照参考代码的格式
            message_data = {
                "msgtype": "text",
                "text": {"content": content},
                "at": {
                    "isAtAll": str(is_at_all).lower(),
                    "atUserIds": at_user_ids or [],
                    "atMobiles": at_users or []
                }
            }
            
            # 如果有secret，添加签名验证
            final_webhook_url = webhook_url
            if self.secret:
                timestamp, sign = self._generate_sign()
                separator = '&' if '?' in webhook_url else '?'
                final_webhook_url = f"{webhook_url}{separator}timestamp={timestamp}&sign={sign}"
                logger.info(f"🔐 主动消息已添加签名验证:")
                logger.info(f"   时间戳: {timestamp}")
                logger.info(f"   签名: {sign[:20]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    final_webhook_url,
                    json=message_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('errcode') == 0:
                        logger.info("✅ 主动消息发送成功")
                        return True
                    else:
                        logger.error(f"❌ 钉钉API返回错误: {response_data}")
                        # 提供错误解决建议
                        errcode = response_data.get('errcode')
                        if errcode == 310000:
                            logger.error("🔧 签名验证失败，请检查SECRET配置")
                        elif errcode == 300001:
                            logger.error("🔧 Token无效，请检查WEBHOOK_URL配置")
                        return False
                else:
                    logger.error(f"❌ 主动消息发送失败: HTTP {response.status_code}")
                    logger.error(f"📋 错误响应: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 发送主动消息异常: {e}")
            return False

    async def send_markdown_message(
        self,
        webhook_url: str,
        title: str,
        markdown_text: str,
        chunk_size: int = 3500
    ) -> bool:
        """发送Markdown消息，自动分片，支持签名。
        :param chunk_size: 每片内容最大字符数（留出JSON和标题空间，避免超限）
        """
        try:
            import os
            keyword = os.getenv("DINGTALK_KEYWORD", "").strip()
            safe_title = (keyword + " " if keyword else "") + (title or "通知")

            # 分片
            chunks: List[str] = []
            text = markdown_text or ""
            for i in range(0, len(text), chunk_size):
                chunks.append(text[i:i + chunk_size])

            if not chunks:
                chunks = ["(空内容)"]

            # 逐片发送
            for idx, part in enumerate(chunks, start=1):
                part_title = safe_title if len(chunks) == 1 else f"{safe_title} ({idx}/{len(chunks)})"
                message_data = {
                    "msgtype": "markdown",
                    "markdown": {"title": part_title, "text": part},
                }

                # 签名
                final_webhook_url = webhook_url
                if self.secret:
                    timestamp, sign = self._generate_sign()
                    separator = '&' if '?' in webhook_url else '?'
                    final_webhook_url = f"{webhook_url}{separator}timestamp={timestamp}&sign={sign}"

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        final_webhook_url,
                        json=message_data,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )

                    if response.status_code != 200:
                        logger.error(f"❌ Markdown消息发送失败: HTTP {response.status_code} - {response.text}")
                        return False
                    data = response.json() if response.text else {}
                    if data.get('errcode') != 0:
                        logger.error(f"❌ 钉钉API返回错误: {data}")
                        return False

            logger.info("✅ Markdown消息发送成功")
            return True
        except Exception as e:
            logger.error(f"❌ 发送Markdown消息异常: {e}")
            return False
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """获取机器人信息"""
        if self.llm_processor and self.llm_processor.mcp_client:
            tools = await self.llm_processor.mcp_client.list_tools()
            stats = self.llm_processor.mcp_client.get_stats()
            shortcuts = await self.llm_processor.get_available_shortcuts()
            
            return {
                "status": "active",
                "mcp_status": self.llm_processor.mcp_client.status.value,
                "available_tools": len(tools),
                "available_shortcuts": list(shortcuts.keys()),
                "stats": stats.model_dump()
            }
        else:
            return {
                "status": "basic",
                "mcp_status": "not_configured",
                "available_tools": 0,
                "available_shortcuts": ["/help"],
                "stats": {}
            } 