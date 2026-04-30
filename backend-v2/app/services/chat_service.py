"""聊天服务 - 编排 LLM、MCP、数据脱敏和消息持久化"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import MessageRole
from app.db.repositories.session_repo import SessionRepository, MessageRepository
from app.llm.chat import ChatService
from app.llm.security import DataMasker
from app.mcp.manager import MCPManager


class ChatOrchestrator:
    def __init__(
        self,
        db: AsyncSession,
        chat_service: ChatService,
        mcp_manager: Optional[MCPManager] = None,
    ):
        self.db = db
        self.chat = chat_service
        self.mcp = mcp_manager
        self.masker = DataMasker() if get_settings().masking_enabled else None
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)

    async def handle_message(
        self,
        session_id: str,
        user_content: str,
        skill_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        seq = await self.message_repo.next_seq(session_id)

        content_for_llm = self.masker.mask(user_content) if self.masker else user_content

        await self.message_repo.add_message(session_id, MessageRole.USER, user_content, seq)

        messages = await self._build_messages(session_id)
        tools = await self._get_tools(skill_id)

        response_text = ""
        tool_calls_made = []

        async for event in self.chat.stream_chat(messages=messages, tools=tools):
            if event["type"] == "token":
                response_text += event["content"]
                yield {"type": "token", "content": event["content"]}

            elif event["type"] == "tool_call":
                tool_calls_made.append(event["tool_call"])
                yield {"type": "tool_call", "tool_call": event["tool_call"]}

                tool_result = await self._execute_tool(event["tool_call"])
                yield {"type": "tool_result", "tool_call_id": event["tool_call"]["id"], "result": tool_result}

                messages.append({"role": "assistant", "content": None, "tool_calls": [event["tool_call"]]})
                messages.append({"role": "tool", "tool_call_id": event["tool_call"]["id"], "content": json.dumps(tool_result, ensure_ascii=False)})

                async for followup in self.chat.stream_chat(messages=messages, tools=tools):
                    if followup["type"] == "token":
                        response_text += followup["content"]
                        yield {"type": "token", "content": followup["content"]}

            elif event["type"] == "error":
                yield {"type": "error", "message": event["message"]}

        final_text = self.masker.unmask(response_text) if self.masker else response_text

        await self.message_repo.add_message(
            session_id, MessageRole.ASSISTANT, final_text, seq + 1,
            tool_calls=tool_calls_made if tool_calls_made else None,
        )
        await self.db.commit()

        yield {"type": "done", "session_id": session_id}

    async def _build_messages(self, session_id: str) -> list[dict]:
        db_msgs = await self.message_repo.list_by_session(session_id)
        result = []
        for m in db_msgs:
            msg: dict = {"role": m.role.value, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            result.append(msg)
        return result

    async def _get_tools(self, skill_id: Optional[str] = None) -> list[dict]:
        if self.mcp is None:
            return []
        return await self.mcp.list_tools(skill_id)

    async def _execute_tool(self, tool_call: dict) -> dict:
        name = tool_call["function"]["name"]
        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return {"error": f"无效的工具参数: {tool_call['function']['arguments']}"}

        try:
            if self.mcp:
                result = await self.mcp.call_tool(name, arguments)
            else:
                result = {"error": "MCP 服务未连接"}
        except Exception as e:
            logger.error(f"工具调用失败 {name}: {e}")
            result = {"error": str(e)}

        return result
