"""聊天服务 - 编排 LLM、MCP、数据脱敏和消息持久化"""

from __future__ import annotations

import json
import re
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import MessageRole
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session_repo import MessageRepository, SessionRepository
from app.llm.chat import ChatService
from app.llm.config_store import LLMRuntimeConfig, load_llm_runtime
from app.llm.security import DataMasker
from app.mcp.manager import MCPManager

DISCOVERY_CONTEXT_TOOLS = {"toolsearch", "tool_get", "tool_categories"}
DISCOVERY_RESULT_TOOLS = {"toolsearch", "tool_get"}
MAX_TOOL_CALL_ROUNDS = 6
K8S_INSPECTION_KEYWORDS = (
    "巡检",
    "健康检查",
    "health check",
    "inspection",
)
K8S_INSPECTION_REQUIRED_TOOLS = {
    "k8s-cluster-summary",
    "k8s-get-nodes",
    "k8s-get-cluster-metrics",
}
TOOL_LOOP_STOP_MESSAGES = {
    "duplicate_tool_call": "模型重复请求相同工具，已停止继续调用工具。",
    "discovery_sufficient": "工具检索结果已返回，已停止继续调用工具。",
    "inspection_sufficient": "集群巡检所需的核心工具结果已齐备。",
    "tool_round_limit": "工具调用轮次已达到上限。",
    "llm_error_after_tools": "模型在工具执行后没有完成最终回答。",
}
K8S_CLUSTER_CONTEXT_KEYWORDS = (
    "集群",
    "k8s",
    "kubernetes",
    "cluster",
)
K8S_CLUSTER_ANCHOR_TOOLS = (
    "k8s-cluster-summary",
    "k8s-get-namespaces",
    "k8s-get-nodes",
    "k8s-get-pods",
    "k8s-get-deployments",
    "k8s-get-services",
    "k8s-get-events",
    "k8s-get-cluster-metrics",
)
K8S_POD_CONTEXT_KEYWORDS = (
    "pod",
    "pods",
    "容器组",
)
K8S_POD_ANCHOR_TOOLS = (
    "k8s-get-pods",
    "k8s-describe-pod",
    "k8s-get-logs",
    "k8s-get-events",
)
K8S_SERVICE_CONTEXT_KEYWORDS = (
    "service",
    "services",
    "svc",
    "服务",
    "endpoint",
    "endpoints",
)
K8S_SERVICE_ANCHOR_TOOLS = (
    "k8s-get-services",
    "k8s-describe-service",
    "k8s-get-endpoints",
)
K8S_WORKLOAD_CONTEXT_KEYWORDS = (
    "deployment",
    "deploy",
    "工作负载",
    "发布",
    "rollout",
)
K8S_WORKLOAD_ANCHOR_TOOLS = (
    "k8s-get-deployments",
    "k8s-get-deployment-history",
    "k8s-rollout-status",
)
K8S_MUTATION_ANCHOR_TOOLS = (
    "k8s-scale-deployment",
    "k8s-restart-deployment",
    "k8s-edit-resource",
    "k8s-patch-resource",
    "k8s-delete-resource",
    "k8s-exec-pod",
)
K8S_SCALE_CONTEXT_KEYWORDS = (
    "扩容",
    "缩容",
    "扩缩容",
    "副本",
    "replica",
    "replicas",
    "scale",
)
K8S_RESTART_CONTEXT_KEYWORDS = (
    "重启",
    "滚动重启",
    "restart",
)
ECS_CONTEXT_KEYWORDS = (
    "ecs",
    "云服务器",
    "实例",
    "主机",
    "巡检",
)
ECS_ANCHOR_TOOLS = (
    "ecs-list-instances",
    "ecs-inspect",
)
ALIYUN_CONTEXT_KEYWORDS = (
    "阿里云",
    "aliyun",
    "alibaba cloud",
    "cloudmonitor",
    "cms",
    "sls",
    "slb",
    "alb",
    "nlb",
    "负载均衡",
    "轻量应用服务器",
    "轻量服务器",
)
ALIYUN_SWAS_CONTEXT_KEYWORDS = (
    "轻量应用服务器",
    "轻量服务器",
    "swas",
    "simple application server",
)
ALIYUN_ECS_CONTEXT_KEYWORDS = (
    "ecs",
    "云服务器",
)
ALIYUN_OBSERVABILITY_CONTEXT_KEYWORDS = (
    "监控",
    "指标",
    "告警",
    "报警",
    "事件",
    "日志",
    "error",
    "exception",
)
ALIYUN_LB_CONTEXT_KEYWORDS = (
    "负载均衡",
    "slb",
    "alb",
    "nlb",
    "load balancer",
)
ALIYUN_DEFAULT_ANCHOR_TOOLS = (
    "aliyun-swas-list-instances",
    "aliyun-ecs-list-instances",
    "aliyun-cms-get-alerts",
)
ALIYUN_SWAS_ANCHOR_TOOLS = ("aliyun-swas-list-instances",)
ALIYUN_ECS_ANCHOR_TOOLS = (
    "aliyun-ecs-list-instances",
    "aliyun-ecs-describe-instance",
    "aliyun-cms-get-ecs-metrics",
)
ALIYUN_OBSERVABILITY_ANCHOR_TOOLS = (
    "aliyun-cms-get-alerts",
    "aliyun-cms-get-event-history",
    "aliyun-sls-query-logs",
    "aliyun-sls-query-error-summary",
)
ALIYUN_LB_ANCHOR_TOOLS = (
    "aliyun-lb-list-instances",
    "aliyun-lb-describe-health",
)
EXPLICIT_K8S_CONTEXT_KEYWORDS = (
    "k8s",
    "kubernetes",
    "集群",
    "cluster",
    "pod",
    "pods",
    "namespace",
    "deployment",
    "deploy",
    "workload",
    "工作负载",
    "service",
    "svc",
    "endpoint",
    "endpoints",
)
DISCOVERY_ONLY_KEYWORDS = (
    "只搜索",
    "搜索工具",
    "查找工具",
    "候选工具",
    "工具列表",
    "有哪些工具",
    "不要执行",
    "先不要执行",
    "不执行具体",
    "不要调用具体",
    "search tools",
    "tool candidates",
    "discovery only",
    "do not execute",
    "don't execute",
)


class ChatOrchestrator:
    def __init__(
        self,
        db: AsyncSession,
        chat_service: Optional[ChatService] = None,
        mcp_manager: Optional[MCPManager] = None,
        current_user: Optional[dict] = None,
    ):
        self.db = db
        self.chat = chat_service
        self.mcp = mcp_manager
        self.current_user = current_user or {"username": "system", "role": "admin"}
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)
        self.audit_repo = AuditRepository(db)

    async def handle_message(
        self,
        session_id: str,
        user_content: str,
        skill_id: Optional[str] = None,
        tool_context_enabled: bool = True,
        llm_provider_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        seq = await self.message_repo.next_seq(session_id)
        chat, runtime_config = self._resolve_chat(llm_provider_id)
        masker = self._build_masker(runtime_config)

        content_for_llm = masker.mask(user_content) if masker else user_content

        await self.message_repo.add_message(session_id, MessageRole.USER, user_content, seq)
        await self.db.commit()

        messages = await self._build_messages(session_id)
        if messages and messages[-1].get("role") == "user":
            messages[-1]["content"] = content_for_llm
        if tool_context_enabled:
            tools, tool_pool, unavailable_tools = await self._get_initial_tool_context(
                skill_id,
                user_content,
            )
        else:
            tools, tool_pool, unavailable_tools = [], {}, {}

        response_text = ""
        tool_calls_made = []
        tool_results_made = []
        tool_round_limit_reached = False
        tool_loop_stop_reason = None
        llm_error_after_tools = None
        discovery_only = self._discovery_only_intent(user_content)
        seen_tool_call_keys = set()
        direct_tool_call = (
            self._infer_direct_tool_call(user_content, tool_pool)
            if tool_context_enabled
            else None
        )

        if direct_tool_call:
            tool_calls_made.append(direct_tool_call)
            yield {"type": "tool_call", "tool_call": direct_tool_call}
            tool_result = await self._execute_tool(direct_tool_call)
            tool_results_made.append(
                {
                    "tool": direct_tool_call["function"]["name"],
                    "tool_call_id": direct_tool_call["id"],
                    "tool_name": direct_tool_call["function"]["name"],
                    "result": tool_result,
                }
            )
            yield {
                "type": "tool_result",
                "tool_call_id": direct_tool_call["id"],
                "result": tool_result,
            }
            generated_text = ""
            if chat is not None and self._direct_tool_result_can_be_summarized(
                direct_tool_call["function"]["name"],
                tool_result,
            ):
                generated_text = await self._generate_final_answer_from_tool_results(
                    chat=chat,
                    user_content=content_for_llm,
                    tool_results=tool_results_made,
                    stop_reason=None,
                )
            final_text = masker.unmask(generated_text) if masker else generated_text
            if not final_text.strip():
                final_text = self._direct_tool_result_message(direct_tool_call, tool_result)
            yield {"type": "token", "content": final_text}
            await self.message_repo.add_message(
                session_id,
                MessageRole.ASSISTANT,
                final_text,
                seq + 1,
                tool_calls=tool_calls_made,
                tool_results=tool_results_made,
            )
            await self.db.commit()
            yield {"type": "done", "session_id": session_id}
            return

        if chat is None:
            response_text = self._disabled_llm_message(runtime_config, llm_provider_id)
            yield {"type": "token", "content": response_text}
            await self.message_repo.add_message(
                session_id,
                MessageRole.ASSISTANT,
                response_text,
                seq + 1,
            )
            await self.db.commit()
            yield {"type": "done", "session_id": session_id}
            return

        for _round in range(MAX_TOOL_CALL_ROUNDS):
            made_tool_call = False
            round_text = ""
            async for event in chat.stream_chat(messages=messages, tools=tools):
                if event["type"] == "token":
                    round_text += event["content"]
                    yield {"type": "token", "content": event["content"]}

                elif event["type"] == "tool_call":
                    tool_call = self._normalize_discovery_tool_call(
                        event["tool_call"],
                        content_for_llm,
                    )
                    tool_call_key = self._tool_call_key(tool_call)
                    if tool_call_key in seen_tool_call_keys:
                        tool_loop_stop_reason = "duplicate_tool_call"
                        break

                    seen_tool_call_keys.add(tool_call_key)
                    made_tool_call = True
                    tool_calls_made.append(tool_call)
                    yield {"type": "tool_call", "tool_call": tool_call}

                    tool_result = await self._execute_tool(tool_call)
                    if tool_call["function"]["name"] in DISCOVERY_CONTEXT_TOOLS:
                        tool_result = self._annotate_discovery_result(
                            tool_result,
                            tool_pool,
                            unavailable_tools,
                        )
                    tool_results_made.append(
                        {
                            "tool": tool_call["function"]["name"],
                            "tool_call_id": tool_call["id"],
                            "tool_name": tool_call["function"]["name"],
                            "result": tool_result,
                        }
                    )
                    yield {
                        "type": "tool_result",
                        "tool_call_id": tool_call["id"],
                        "result": tool_result,
                    }

                    assistant_message = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call],
                    }
                    if event.get("reasoning_content"):
                        assistant_message["reasoning_content"] = event["reasoning_content"]
                    messages.append(assistant_message)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_result, ensure_ascii=False),
                        }
                    )
                    if discovery_only and tool_call["function"]["name"] in DISCOVERY_RESULT_TOOLS:
                        tool_loop_stop_reason = "discovery_sufficient"
                        break
                    if not discovery_only:
                        tools = self._expand_tools_after_result(tools, tool_pool, tool_result)
                    if self._should_finalize_after_tools(content_for_llm, tool_results_made):
                        tool_loop_stop_reason = "inspection_sufficient"
                        break

                elif event["type"] == "error":
                    if tool_results_made:
                        llm_error_after_tools = event["message"]
                        break
                    yield {"type": "error", "message": event["message"]}
                    return

            if llm_error_after_tools:
                tool_loop_stop_reason = "llm_error_after_tools"
                break
            if tool_loop_stop_reason:
                break
            if not made_tool_call:
                response_text += round_text
                break
        else:
            tool_round_limit_reached = True
            tool_loop_stop_reason = "tool_round_limit"

        final_text = masker.unmask(response_text) if masker else response_text
        if not final_text.strip() and tool_results_made:
            generated_text = await self._generate_final_answer_from_tool_results(
                chat=chat,
                user_content=content_for_llm,
                tool_results=tool_results_made,
                stop_reason=tool_loop_stop_reason,
            )
            final_text = masker.unmask(generated_text) if masker else generated_text
            if not final_text.strip():
                final_text = self._tool_result_fallback(
                    tool_results_made,
                    tool_round_limit_reached=tool_round_limit_reached,
                    stop_reason=tool_loop_stop_reason,
                )
            yield {"type": "token", "content": final_text}

        await self.message_repo.add_message(
            session_id,
            MessageRole.ASSISTANT,
            final_text,
            seq + 1,
            tool_calls=tool_calls_made if tool_calls_made else None,
            tool_results=tool_results_made if tool_results_made else None,
        )
        await self.db.commit()

        yield {"type": "done", "session_id": session_id}

    async def confirm_tool_call(self, message_id: str, tool_call_id: str) -> dict:
        message = await self.message_repo.get_by_id(message_id)
        if not message or message.role != MessageRole.ASSISTANT:
            return {"error": "message_not_found", "message": "未找到可确认的助手消息"}
        tool_call = self._find_tool_call(message.tool_calls or [], tool_call_id)
        if not tool_call:
            return {"error": "tool_call_not_found", "message": "未找到工具调用"}
        pending = self._find_pending_confirmation(message.tool_results or [], tool_call_id)
        if not pending:
            return {"error": "confirmation_not_found", "message": "未找到待确认操作"}
        confirmation = pending.get("confirmation") or {}
        token = confirmation.get("token")
        if not isinstance(token, str) or not token:
            return {"error": "confirmation_not_found", "message": "确认令牌不存在"}

        name = tool_call["function"]["name"]
        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return {"error": "invalid_tool_arguments", "message": "工具参数无效"}
        arguments_with_token = {**arguments, "__confirmation_token": token}

        if not self.mcp:
            return {"error": "mcp_unavailable", "message": "MCP 服务未连接"}

        decision = self.mcp.authorize_tool_call(name, self.current_user, dict(arguments_with_token))
        await self.audit_repo.log(
            actor=self.current_user.get("username", "unknown"),
            action="tool.confirm",
            resource=name,
            result="allowed" if decision.allowed else "denied",
            details=decision.to_audit_details(arguments_with_token),
        )
        await self.db.commit()
        if not decision.allowed:
            denied = {
                "error": "tool_execution_denied",
                "reason": decision.reason,
                "requires_confirmation": decision.requires_confirmation,
                "tool": name,
            }
            confirmation_payload = decision.to_confirmation_payload(arguments_with_token)
            if confirmation_payload:
                denied["confirmation"] = confirmation_payload
            return denied

        result = await self.mcp.call_tool(name, arguments_with_token, user=self.current_user)
        stored_results = list(message.tool_results or [])
        stored_results.append(
            {
                "tool_call_id": tool_call_id,
                "tool_name": name,
                "result": result,
                "confirmed": True,
            }
        )
        message.tool_results = stored_results
        await self.db.commit()
        return result

    def _resolve_chat(
        self, provider_id: Optional[str]
    ) -> tuple[Optional[ChatService], Optional[LLMRuntimeConfig]]:
        if self.chat is not None:
            return self.chat, None

        runtime_config = load_llm_runtime(provider_id)
        if not runtime_config.active or runtime_config.provider is None:
            return None, runtime_config
        return ChatService(runtime_config.provider), runtime_config

    async def _generate_final_answer_from_tool_results(
        self,
        chat: ChatService,
        user_content: str,
        tool_results: list[dict],
        stop_reason: Optional[str],
    ) -> str:
        if not hasattr(chat, "chat"):
            return ""

        result_summary = self._successful_tool_result_summary(
            tool_results,
            include_discovery=stop_reason == "discovery_sufficient",
        )
        if not result_summary:
            return ""

        messages = [
            {
                "role": "system",
                "content": (
                    "你是 Kubernetes / ECS / 阿里云运维助手。现在是最终总结阶段，不能再调用工具，"
                    "只能基于用户问题和已提供的工具结果摘要生成中文结论。"
                ),
            },
            {
                "role": "user",
                "content": self._final_answer_prompt(
                    user_content=user_content,
                    result_summary=result_summary,
                    stop_reason=stop_reason,
                ),
            },
        ]
        result = await chat.chat(messages, tools=None)
        if not isinstance(result, dict):
            return ""
        if result.get("error"):
            logger.warning("最终工具结果总结调用失败: {}", result["error"])
            return ""
        if result.get("tool_calls"):
            logger.warning("最终工具结果总结阶段仍返回工具调用，已忽略")
            return ""
        return result.get("content") or ""

    @staticmethod
    def _final_answer_prompt(
        user_content: str,
        result_summary: str,
        stop_reason: Optional[str],
    ) -> str:
        reason = TOOL_LOOP_STOP_MESSAGES.get(stop_reason or "", "工具已执行完成。")
        return (
            f"用户原始问题：{user_content}\n\n"
            f"收敛原因：{reason}\n\n"
            f"工具结果摘要：\n{result_summary}\n\n"
            "请直接生成最终回答。要求：\n"
            "1. 不要说还需要调用工具；\n"
            "2. 不要编造工具摘要中没有的数据；\n"
            "3. 如果是日志或事件查询，提炼关键现象、异常/错误线索和下一步建议；\n"
            "4. 如果是巡检，给出健康结论、关键指标、异常/风险点和下一步建议；\n"
            "5. 输出中文，结构清晰。"
        )

    @staticmethod
    def _tool_call_key(tool_call: dict) -> str:
        function = tool_call.get("function") or {}
        name = function.get("name") or ""
        raw_arguments = function.get("arguments") or ""
        try:
            arguments = (
                json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            )
        except json.JSONDecodeError:
            normalized_arguments = str(raw_arguments)
        else:
            normalized_arguments = json.dumps(arguments, ensure_ascii=False, sort_keys=True)
        return f"{name}:{normalized_arguments}"

    @classmethod
    def _normalize_discovery_tool_call(cls, tool_call: dict, user_content: str) -> dict:
        function = tool_call.get("function") or {}
        if function.get("name") != "toolsearch":
            return tool_call

        raw_arguments = function.get("arguments") or "{}"
        try:
            arguments = (
                json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            )
        except json.JSONDecodeError:
            return tool_call
        if not isinstance(arguments, dict):
            return tool_call

        normalized = cls._normalize_toolsearch_arguments(arguments, user_content)
        if normalized == arguments:
            return tool_call

        updated_call = dict(tool_call)
        updated_function = dict(function)
        updated_function["arguments"] = json.dumps(normalized, ensure_ascii=False)
        updated_call["function"] = updated_function
        return updated_call

    @staticmethod
    def _normalize_toolsearch_arguments(arguments: dict, user_content: str) -> dict:
        query = str(arguments.get("query") or "")
        combined = f"{user_content} {query}".lower()
        aliyun_intent = any(keyword in combined for keyword in ALIYUN_CONTEXT_KEYWORDS)
        explicit_k8s_intent = any(keyword in combined for keyword in EXPLICIT_K8S_CONTEXT_KEYWORDS)
        category = str(arguments.get("category") or "").lower()

        cloud_category_mismatch = category in {"", "ecs", "k8s", "kubernetes"}
        if aliyun_intent and not explicit_k8s_intent and cloud_category_mismatch:
            normalized = dict(arguments)
            normalized["category"] = "aliyun"
            return normalized

        return arguments

    @staticmethod
    def _should_finalize_after_tools(user_content: str, tool_results: list[dict]) -> bool:
        content = user_content.lower()
        if not any(keyword in content for keyword in K8S_INSPECTION_KEYWORDS):
            return False
        if not any(keyword in content for keyword in K8S_CLUSTER_CONTEXT_KEYWORDS):
            return False
        successful_tools = {
            item.get("tool")
            for item in tool_results
            if not ChatOrchestrator._tool_result_has_error(item)
        }
        return K8S_INSPECTION_REQUIRED_TOOLS.issubset(successful_tools)

    @staticmethod
    def _tool_result_has_error(tool_result_item: dict) -> bool:
        payload = ChatOrchestrator._unwrap_tool_result(tool_result_item.get("result"))
        return isinstance(payload, dict) and bool(payload.get("error"))

    @staticmethod
    def _direct_tool_result_can_be_summarized(tool_name: str, tool_result: dict) -> bool:
        if tool_name in K8S_MUTATION_ANCHOR_TOOLS:
            return False
        payload = ChatOrchestrator._unwrap_tool_result(tool_result)
        if not isinstance(payload, dict):
            return False
        if payload.get("error") or payload.get("requires_confirmation"):
            return False
        return True

    @staticmethod
    def _build_masker(runtime_config: Optional[LLMRuntimeConfig]) -> Optional[DataMasker]:
        if runtime_config is not None:
            return DataMasker() if runtime_config.masking_enabled else None
        return DataMasker() if get_settings().masking_enabled else None

    @staticmethod
    def _disabled_llm_message(
        runtime_config: Optional[LLMRuntimeConfig],
        provider_id: Optional[str],
    ) -> str:
        if provider_id and runtime_config and runtime_config.provider is None:
            return f"未找到模型配置 {provider_id}。请到 LLM 配置页确认配置仍然存在。"
        if runtime_config and not runtime_config.enabled:
            return "LLM 服务未启用。请到 LLM 配置页开启 LLM，保存后新消息会立即使用当前配置。"
        if runtime_config and runtime_config.provider and not runtime_config.provider.enabled:
            return (
                f"模型配置 {runtime_config.provider.name} 已停用。"
                "请在对话页切换模型，或到 LLM 配置页启用它。"
            )
        if (
            runtime_config
            and runtime_config.provider
            and not runtime_config.provider.api_key_configured
        ):
            return (
                f"模型配置 {runtime_config.provider.name} 未配置 API Key。"
                "请到 LLM 配置页填写密钥，保存后新消息会立即生效。"
            )
        return "LLM 服务未配置。请到 LLM 配置页添加模型配置，保存后新消息会立即生效。"

    async def _build_messages(self, session_id: str) -> list[dict]:
        db_msgs = await self.message_repo.list_by_session(session_id)
        result = []
        for m in db_msgs:
            if m.role == MessageRole.TOOL:
                continue
            result.append({"role": m.role.value, "content": m.content})
        return result

    async def _get_tools(self, skill_id: Optional[str] = None) -> list[dict]:
        if self.mcp is None:
            return []
        return await self.mcp.list_tools(skill_id)

    async def _get_initial_tool_context(
        self,
        skill_id: Optional[str] = None,
        user_content: str = "",
    ) -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
        if self.mcp is None:
            return [], {}, {}

        listed_tools = await self.mcp.list_tools()
        unavailable_tools = {
            tool["name"]: tool
            for tool in listed_tools
            if tool.get("name") and not self._tool_available_for_chat(tool)
        }
        all_tools = [tool for tool in listed_tools if self._tool_available_for_chat(tool)]
        scoped_tools = (
            [
                tool
                for tool in await self.mcp.list_tools(skill_id)
                if self._tool_available_for_chat(tool)
            ]
            if skill_id
            else all_tools
        )
        all_by_name = {tool["name"]: tool for tool in all_tools}
        scoped_by_name = {tool["name"]: tool for tool in scoped_tools}

        has_toolsearch = "toolsearch" in all_by_name
        if not has_toolsearch:
            return scoped_tools, scoped_by_name, unavailable_tools

        discovery_tools = [
            all_by_name[name] for name in sorted(DISCOVERY_CONTEXT_TOOLS) if name in all_by_name
        ]
        anchor_tools = self._intent_anchor_tools(user_content, scoped_by_name)
        tool_pool = dict(scoped_by_name)
        for tool in discovery_tools:
            tool_pool[tool["name"]] = tool
        initial_tools = self._dedupe_tools([*discovery_tools, *anchor_tools])
        return initial_tools, tool_pool, unavailable_tools

    @staticmethod
    def _dedupe_tools(tools: list[dict]) -> list[dict]:
        deduped: dict[str, dict] = {}
        for tool in tools:
            name = tool.get("name")
            if name:
                deduped[name] = tool
        return list(deduped.values())

    @classmethod
    def _infer_direct_tool_call(
        cls,
        user_content: str,
        tool_pool: dict[str, dict],
    ) -> Optional[dict]:
        if cls._discovery_only_intent(user_content):
            return None
        candidates = (
            ("k8s-scale-deployment", cls._parse_k8s_scale_arguments(user_content)),
            ("k8s-restart-deployment", cls._parse_k8s_restart_arguments(user_content)),
            ("k8s-get-logs", cls._parse_k8s_logs_arguments(user_content)),
        )
        for tool_name, arguments in candidates:
            if tool_name in tool_pool and arguments:
                return cls._direct_tool_call(tool_name, arguments)
        return None

    @staticmethod
    def _direct_tool_call(tool_name: str, arguments: dict[str, object]) -> dict:
        return {
            "id": f"direct-{tool_name}",
            "type": "function",
            "function": {
                "name": tool_name,
                "arguments": json.dumps(arguments, ensure_ascii=False),
            },
        }

    @classmethod
    def _parse_k8s_scale_arguments(cls, user_content: str) -> Optional[dict[str, object]]:
        deployment_name = cls._extract_deployment_name(user_content)
        replicas = cls._extract_replicas(user_content)
        if not deployment_name or replicas is None:
            return None
        return {
            "deployment_name": deployment_name,
            "namespace": cls._extract_namespace(user_content) or "default",
            "replicas": replicas,
        }

    @classmethod
    def _parse_k8s_restart_arguments(cls, user_content: str) -> Optional[dict[str, object]]:
        content = user_content.lower()
        if not any(keyword in content for keyword in K8S_RESTART_CONTEXT_KEYWORDS):
            return None
        deployment_name = cls._extract_deployment_name(user_content)
        if not deployment_name:
            return None
        return {
            "deployment_name": deployment_name,
            "namespace": cls._extract_namespace(user_content) or "default",
        }

    @classmethod
    def _parse_k8s_logs_arguments(cls, user_content: str) -> Optional[dict[str, object]]:
        content = user_content.lower()
        if not any(keyword in content for keyword in ("日志", "log", "logs")):
            return None
        pod_name = cls._extract_pod_name(user_content)
        if not pod_name:
            return None
        arguments: dict[str, object] = {
            "pod_name": pod_name,
            "namespace": cls._extract_namespace(user_content) or "default",
        }
        tail_lines = cls._extract_tail_lines(user_content)
        if tail_lines is not None:
            arguments["tail_lines"] = tail_lines
        return arguments

    @staticmethod
    def _extract_deployment_name(user_content: str) -> Optional[str]:
        patterns = (
            r"(?:deployment|deploy|工作负载)\s+([a-z0-9][a-z0-9.-]*)",
            (
                r"(?:重启|restart)\s*(?:一下|下)?\s*"
                r"(?:[a-z0-9][a-z0-9.-]*\s*(?:命名空间|namespace)(?:里|内|下|的)?\s*)?"
                r"(?:deployment|deploy|工作负载)?\s*([a-z0-9][a-z0-9.-]*)"
            ),
            (
                r"(?:把|将|请把|请将|帮我把|帮忙把)?\s*"
                r"(?:[a-z0-9][a-z0-9.-]*\s*(?:命名空间|namespace)(?:里|内|下|的)?\s*)?"
                r"(?:deployment|deploy|工作负载)?\s*([a-z0-9][a-z0-9.-]*)\s*"
                r"(?:扩到|缩到|扩容到|缩容到|调整到|调到|改成|设置为|设为|重启|restart)"
            ),
            r"([a-z0-9][a-z0-9.-]*)\s*(?:这个)?\s*(?:deployment|deploy|工作负载)\s*(?:重启|restart)",
            r"(?:把|将|请把|请将)\s+([a-z0-9][a-z0-9.-]*)\s*(?:扩|缩|副本|replica|调整|调|改|设|scale)",
        )
        for pattern in patterns:
            match = re.search(pattern, user_content, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" .,，。")
                if candidate.lower() not in {"default", "namespace", "deployment", "deploy"}:
                    return candidate
        return None

    @staticmethod
    def _extract_namespace(user_content: str) -> Optional[str]:
        patterns = (
            r"([a-z0-9][a-z0-9.-]*)\s*(?:命名空间|namespace)",
            r"(?:namespace|命名空间)\s*[:=]?\s*([a-z0-9][a-z0-9.-]*)",
        )
        for pattern in patterns:
            match = re.search(pattern, user_content, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip(" .,，。")
        return None

    @staticmethod
    def _extract_replicas(user_content: str) -> Optional[int]:
        patterns = (
            r"(?:扩到|缩到|扩容到|缩容到|调整到|调到|改成|设置为|设为)\s*(\d+)",
            r"(?:副本数?|replicas?)\D{0,12}(\d+)",
            r"(\d+)\s*个?\s*副本",
        )
        for pattern in patterns:
            match = re.search(pattern, user_content, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _extract_pod_name(user_content: str) -> Optional[str]:
        patterns = (
            r"(?:pod|pods|容器组)\s+([a-z0-9][a-z0-9.-]*)",
            (
                r"(?:看|查|查看|获取|帮我看|帮我查)\s*(?:一下)?\s*"
                r"(?:[a-z0-9][a-z0-9.-]*\s*(?:命名空间|namespace)(?:里|内|下|的)?\s*)?"
                r"([a-z0-9][a-z0-9.-]*)\s*(?:的)?"
                r"(?:最近|最后|tail)?\s*\d*\s*行?\s*(?:日志|log|logs)"
            ),
            r"(?:看|查|查看|获取)\s+([a-z0-9][a-z0-9.-]*)\s*(?:的)?(?:日志|log|logs)",
        )
        for pattern in patterns:
            match = re.search(pattern, user_content, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" .,，。")
                if candidate.lower() not in {"default", "namespace", "pod", "pods"}:
                    return candidate
        return None

    @staticmethod
    def _extract_tail_lines(user_content: str) -> Optional[int]:
        patterns = (
            r"(?:最近|最后|tail)\s*(\d+)\s*行?",
            r"(\d+)\s*行\s*(?:日志|log|logs)",
        )
        for pattern in patterns:
            match = re.search(pattern, user_content, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _direct_tool_result_message(tool_call: dict, result: dict) -> str:
        tool_name = (tool_call.get("function") or {}).get("name") or "工具"
        if result.get("requires_confirmation"):
            return f"已识别为需要确认的写入操作 `{tool_name}`，请在执行链路中确认后再执行。"
        if result.get("error"):
            return f"`{tool_name}` 执行未完成：{result.get('message') or result.get('reason') or result.get('error')}"
        return f"`{tool_name}` 已执行完成。"

    @staticmethod
    def _intent_anchor_tools(user_content: str, scoped_by_name: dict[str, dict]) -> list[dict]:
        content = user_content.lower()
        if ChatOrchestrator._discovery_only_intent(content):
            return []
        anchor_names: list[str] = []
        aliyun_intent = any(keyword in content for keyword in ALIYUN_CONTEXT_KEYWORDS)
        explicit_k8s_intent = any(keyword in content for keyword in EXPLICIT_K8S_CONTEXT_KEYWORDS)
        if aliyun_intent:
            anchor_names.extend(ALIYUN_DEFAULT_ANCHOR_TOOLS)
            if any(keyword in content for keyword in ALIYUN_SWAS_CONTEXT_KEYWORDS):
                anchor_names.extend(ALIYUN_SWAS_ANCHOR_TOOLS)
            if any(keyword in content for keyword in ALIYUN_ECS_CONTEXT_KEYWORDS):
                anchor_names.extend(ALIYUN_ECS_ANCHOR_TOOLS)
            if any(keyword in content for keyword in ALIYUN_OBSERVABILITY_CONTEXT_KEYWORDS):
                anchor_names.extend(ALIYUN_OBSERVABILITY_ANCHOR_TOOLS)
            if any(keyword in content for keyword in ALIYUN_LB_CONTEXT_KEYWORDS):
                anchor_names.extend(ALIYUN_LB_ANCHOR_TOOLS)

        if any(keyword in content for keyword in K8S_CLUSTER_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_CLUSTER_ANCHOR_TOOLS)
        if any(keyword in content for keyword in K8S_POD_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_POD_ANCHOR_TOOLS)
        if (not aliyun_intent or explicit_k8s_intent) and any(
            keyword in content for keyword in K8S_SERVICE_CONTEXT_KEYWORDS
        ):
            anchor_names.extend(K8S_SERVICE_ANCHOR_TOOLS)
        if any(keyword in content for keyword in K8S_WORKLOAD_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_WORKLOAD_ANCHOR_TOOLS)
        for tool_name in K8S_MUTATION_ANCHOR_TOOLS:
            if tool_name in content:
                anchor_names.append(tool_name)
        if any(keyword in content for keyword in K8S_SCALE_CONTEXT_KEYWORDS) and any(
            keyword in content for keyword in K8S_WORKLOAD_CONTEXT_KEYWORDS
        ):
            anchor_names.append("k8s-scale-deployment")
        if any(keyword in content for keyword in K8S_RESTART_CONTEXT_KEYWORDS) and any(
            keyword in content for keyword in K8S_WORKLOAD_CONTEXT_KEYWORDS
        ):
            anchor_names.append("k8s-restart-deployment")
        if not aliyun_intent and any(keyword in content for keyword in ECS_CONTEXT_KEYWORDS):
            anchor_names.extend(ECS_ANCHOR_TOOLS)
        return [scoped_by_name[name] for name in anchor_names if name in scoped_by_name]

    @staticmethod
    def _discovery_only_intent(user_content: str) -> bool:
        content = user_content.lower()
        return any(keyword in content for keyword in DISCOVERY_ONLY_KEYWORDS)

    def _expand_tools_after_result(
        self,
        active_tools: list[dict],
        tool_pool: dict[str, dict],
        tool_result: dict,
    ) -> list[dict]:
        active_by_name = {tool["name"]: tool for tool in active_tools}
        for name in self._candidate_tool_names(tool_result):
            tool = tool_pool.get(name)
            if tool:
                active_by_name[name] = tool
        return list(active_by_name.values())

    @staticmethod
    def _candidate_tool_names(tool_result: dict) -> list[str]:
        payload = tool_result.get("result")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return []
        if not isinstance(payload, dict):
            return []

        candidates = payload.get("results")
        if isinstance(candidates, list):
            return [
                item["name"]
                for item in candidates
                if isinstance(item, dict)
                and item.get("name")
                and item.get("executionPolicy") == "executable"
            ]

        if payload.get("name") and payload.get("executionPolicy") == "executable":
            return [payload["name"]]
        return []

    @classmethod
    def _annotate_discovery_result(
        cls,
        tool_result: dict,
        tool_pool: dict[str, dict],
        unavailable_tools: dict[str, dict],
    ) -> dict:
        parsed = cls._parse_tool_payload(tool_result)
        if parsed is None:
            return tool_result

        payload, was_json_string = parsed
        changed = False

        candidates = list(cls._iter_discovery_candidates(payload))
        if candidates:
            for item in candidates:
                if cls._mark_unavailable_candidate(item, tool_pool, unavailable_tools):
                    changed = True
        elif cls._mark_unavailable_candidate(payload, tool_pool, unavailable_tools):
            changed = True

        if not changed:
            return tool_result

        payload["availabilityNotice"] = "部分工具当前不可用，已从可执行工具上下文中过滤。"
        return cls._with_tool_payload(tool_result, payload, was_json_string)

    @staticmethod
    def _mark_unavailable_candidate(
        item: object,
        tool_pool: dict[str, dict],
        unavailable_tools: dict[str, dict],
    ) -> bool:
        if not isinstance(item, dict):
            return False
        name = item.get("name")
        if not name or name in tool_pool or name not in unavailable_tools:
            return False

        unavailable_tool = unavailable_tools[name]
        item["available"] = False
        item["executionPolicy"] = "unavailable"
        item["unavailableReason"] = unavailable_tool.get("unavailableReason") or "工具当前不可用"
        return True

    @staticmethod
    def _iter_discovery_candidates(payload: dict):
        candidates = payload.get("results")
        if isinstance(candidates, list):
            yield from (item for item in candidates if isinstance(item, dict))

        for group in payload.get("categoryGroups") or []:
            if isinstance(group, dict) and isinstance(group.get("results"), list):
                yield from (item for item in group["results"] if isinstance(item, dict))

        for layer in payload.get("relevanceLayers") or []:
            if not isinstance(layer, dict):
                continue
            if isinstance(layer.get("results"), list):
                yield from (item for item in layer["results"] if isinstance(item, dict))
            for group in layer.get("categoryGroups") or []:
                if isinstance(group, dict) and isinstance(group.get("results"), list):
                    yield from (item for item in group["results"] if isinstance(item, dict))

    @staticmethod
    def _parse_tool_payload(tool_result: dict) -> tuple[dict, bool] | None:
        payload = tool_result.get("result")
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                return None
            return (parsed, True) if isinstance(parsed, dict) else None
        return (payload, False) if isinstance(payload, dict) else None

    @staticmethod
    def _with_tool_payload(tool_result: dict, payload: dict, was_json_string: bool) -> dict:
        updated = dict(tool_result)
        updated["result"] = json.dumps(payload, ensure_ascii=False) if was_json_string else payload
        return updated

    async def _execute_tool(self, tool_call: dict) -> dict:
        name = tool_call["function"]["name"]
        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return {"error": f"无效的工具参数: {tool_call['function']['arguments']}"}

        try:
            if self.mcp:
                decision = self.mcp.authorize_tool_call(name, self.current_user, dict(arguments))
                await self.audit_repo.log(
                    actor=self.current_user.get("username", "unknown"),
                    action="tool.execute",
                    resource=name,
                    result="allowed" if decision.allowed else "denied",
                    details=decision.to_audit_details(arguments),
                )
                await self.db.commit()
                if not decision.allowed:
                    denied = {
                        "error": "tool_execution_denied",
                        "reason": decision.reason,
                        "requires_confirmation": decision.requires_confirmation,
                        "tool": name,
                    }
                    confirmation = decision.to_confirmation_payload(arguments)
                    if confirmation:
                        denied["confirmation"] = confirmation
                    return denied
                result = await self.mcp.call_tool(name, arguments, user=self.current_user)
            else:
                result = {"error": "MCP 服务未连接"}
        except Exception as e:
            logger.error(f"工具调用失败 {name}: {e}")
            result = {"error": str(e)}

        return result

    @staticmethod
    def _find_tool_call(tool_calls: list[dict], tool_call_id: str) -> Optional[dict]:
        for tool_call in tool_calls:
            if tool_call.get("id") == tool_call_id:
                return tool_call
        return None

    @staticmethod
    def _find_pending_confirmation(tool_results: list[dict], tool_call_id: str) -> Optional[dict]:
        for item in reversed(tool_results):
            if item.get("tool_call_id") != tool_call_id:
                continue
            result = item.get("result")
            if (
                isinstance(result, dict)
                and result.get("requires_confirmation") is True
                and isinstance(result.get("confirmation"), dict)
            ):
                return result
            if item.get("confirmed"):
                return None
        return None

    @staticmethod
    def _tool_available_for_chat(tool: dict) -> bool:
        return bool(tool.get("available", True))

    @staticmethod
    def _tool_result_fallback(
        tool_results: list[dict],
        tool_round_limit_reached: bool = False,
        stop_reason: Optional[str] = None,
    ) -> str:
        error_results = [
            item
            for item in tool_results
            if isinstance(item.get("result"), dict) and item["result"].get("error")
        ]
        if not error_results:
            successful_summary = ChatOrchestrator._successful_tool_result_summary(
                tool_results,
                include_discovery=stop_reason == "discovery_sufficient",
            )
            if successful_summary:
                prefix = "工具已执行完成，但模型没有返回文本结果。"
                if stop_reason == "duplicate_tool_call":
                    prefix = "模型重复请求相同工具，已停止继续调用。下面是已获得的工具结果摘要。"
                elif stop_reason == "discovery_sufficient":
                    prefix = "工具检索结果已返回，下面是候选工具摘要。"
                elif stop_reason == "inspection_sufficient":
                    prefix = "集群巡检所需的核心工具结果已齐备，下面是已获得的工具结果摘要。"
                elif tool_round_limit_reached:
                    prefix = "工具调用轮次已达到上限，下面是已获得的工具结果摘要。"
                return f"{prefix}\n\n{successful_summary}"

            unavailable_candidates = ChatOrchestrator._unavailable_candidates_from_results(
                tool_results
            )
            if unavailable_candidates:
                name, reason = unavailable_candidates[-1]
                if name.startswith("k8s-"):
                    return (
                        f"当前 Kubernetes 工具不可用：{reason} "
                        "配置 KUBECONFIG_PATH 并确保集群 API 可访问后再重试，"
                        "或关闭“工具上下文”进行普通对话。"
                    )
                return f"{name} 当前不可用：{reason}"
            if tool_round_limit_reached:
                return (
                    "工具检索没有收敛到可执行结果，已停止继续调用。"
                    "你可以换一种更具体的问题，或关闭“工具上下文”进行普通对话。"
                )
            return "工具已执行完成，但模型没有返回文本结果。"

        last_error = error_results[-1]
        result = last_error["result"]
        tool_name = last_error.get("tool", "工具")
        if result.get("reason") == "kubeconfig_not_configured":
            return (
                f"{tool_name} 当前不可用：{result.get('message') or '未找到 kubeconfig'} "
                "配置 KUBECONFIG_PATH 后再重试，或关闭“工具上下文”进行普通对话。"
            )
        return f"{tool_name} 执行失败：{result.get('message') or result.get('error')}"

    @staticmethod
    def _unavailable_candidates_from_results(tool_results: list[dict]) -> list[tuple[str, str]]:
        unavailable = []
        for item in tool_results:
            result = item.get("result")
            parsed = (
                ChatOrchestrator._parse_tool_payload(result) if isinstance(result, dict) else None
            )
            if parsed is None:
                continue
            payload, _ = parsed
            values = list(ChatOrchestrator._iter_discovery_candidates(payload)) or [payload]
            for candidate in values:
                if not isinstance(candidate, dict) or candidate.get("available") is not False:
                    continue
                name = candidate.get("name")
                if not name:
                    continue
                unavailable.append((name, candidate.get("unavailableReason") or "工具当前不可用"))
        return unavailable

    @staticmethod
    def _successful_tool_result_summary(
        tool_results: list[dict],
        include_discovery: bool = False,
    ) -> str:
        lines = []
        for item in tool_results:
            tool_name = item.get("tool", "")
            if tool_name in DISCOVERY_CONTEXT_TOOLS and not include_discovery:
                continue
            payload = ChatOrchestrator._unwrap_tool_result(item.get("result"))
            if not isinstance(payload, dict) or payload.get("error"):
                continue
            line = ChatOrchestrator._summarize_tool_payload(tool_name, payload)
            if line:
                lines.append(line)
        return "\n".join(lines[-8:])

    @staticmethod
    def _unwrap_tool_result(result: object) -> object:
        if not isinstance(result, dict):
            return result
        payload = result.get("result", result)
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return payload
        return payload

    @staticmethod
    def _summarize_tool_payload(tool_name: str, payload: dict) -> str:
        if tool_name == "toolsearch":
            results = payload.get("results") or []
            preview = ", ".join(
                f"{item.get('name')}({item.get('title') or item.get('category') or '候选'})"
                for item in results[:5]
                if isinstance(item, dict)
            )
            suffix = f"；候选：{preview}" if preview else ""
            total = payload.get("total", len(results))
            return f"- `toolsearch`: query={payload.get('query')}, total={total}{suffix}"
        if tool_name == "tool_get":
            return (
                f"- `tool_get`: name={payload.get('name')}, "
                f"title={payload.get('title') or payload.get('description') or '未提供'}"
            )
        if tool_name == "k8s-cluster-summary":
            phases = payload.get("pod_phases") or {}
            return (
                f"- `k8s-cluster-summary`: nodes={payload.get('nodes')}, "
                f"pods={payload.get('pods')}, deployments={payload.get('deployments')}, "
                f"pod_phases={phases}"
            )
        if tool_name == "k8s-get-pods":
            items = payload.get("items") or []
            preview = ", ".join(
                f"{item.get('namespace', '-')}/{item.get('name')}:{item.get('status')}"
                for item in items[:12]
            )
            suffix = f"；前 {min(len(items), 12)} 个：{preview}" if preview else ""
            return f"- `k8s-get-pods`: count={payload.get('count', len(items))}{suffix}"
        if tool_name == "k8s-get-logs":
            logs = str(payload.get("logs") or "").strip()
            if len(logs) > 4000:
                logs = f"{logs[:4000]}\n...<truncated>"
            return (
                f"- `k8s-get-logs`: namespace={payload.get('namespace')}, "
                f"pod={payload.get('pod')}\n日志内容：\n{logs or '<empty>'}"
            )
        if tool_name == "k8s-get-nodes":
            items = payload.get("items") or []
            preview = ", ".join(f"{item.get('name')}:{item.get('status')}" for item in items[:8])
            return f"- `k8s-get-nodes`: count={payload.get('count', len(items))}；{preview}"
        if tool_name == "k8s-get-deployments":
            items = payload.get("items") or []
            preview = ", ".join(
                f"{item.get('name')} {item.get('available')}/{item.get('replicas')}"
                for item in items[:8]
            )
            return f"- `k8s-get-deployments`: count={payload.get('count', len(items))}；{preview}"
        if tool_name == "k8s-get-services":
            items = payload.get("items") or []
            preview = ", ".join(
                f"{item.get('namespace', '-')}/{item.get('name')}:{item.get('type')}"
                for item in items[:8]
            )
            return f"- `k8s-get-services`: count={payload.get('count', len(items))}；{preview}"
        if tool_name == "k8s-get-events":
            items = payload.get("items") or []
            warnings = [item for item in items if item.get("type") == "Warning"]
            return (
                f"- `k8s-get-events`: count={payload.get('count', len(items))}, "
                f"warnings={len(warnings)}"
            )
        if tool_name == "k8s-get-cluster-metrics":
            return (
                f"- `k8s-get-cluster-metrics`: nodes={payload.get('node_count')}, "
                f"pods={payload.get('pod_count')}, cpu={payload.get('total_cpu_mcores')}m, "
                f"memory={payload.get('total_memory_mib')}Mi"
            )
        if "count" in payload:
            return f"- `{tool_name}`: count={payload.get('count')}"
        if payload.get("found") is not None:
            return f"- `{tool_name}`: found={payload.get('found')}"
        return f"- `{tool_name}`: 执行成功"
