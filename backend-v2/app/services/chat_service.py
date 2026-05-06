"""聊天服务 - 编排 LLM、MCP、数据脱敏和消息持久化"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import MessageRole
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session_repo import SessionRepository, MessageRepository
from app.llm.chat import ChatService
from app.llm.config_store import LLMRuntimeConfig, load_llm_runtime
from app.llm.security import DataMasker
from app.mcp.manager import MCPManager


DISCOVERY_CONTEXT_TOOLS = {"toolsearch", "tool_get", "tool_categories"}
MAX_TOOL_CALL_ROUNDS = 6
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
                content_for_llm,
            )
        else:
            tools, tool_pool, unavailable_tools = [], {}, {}

        response_text = ""
        tool_calls_made = []
        tool_results_made = []
        tool_round_limit_reached = False
        discovery_only = self._discovery_only_intent(content_for_llm)

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
            async for event in chat.stream_chat(messages=messages, tools=tools):
                if event["type"] == "token":
                    response_text += event["content"]
                    yield {"type": "token", "content": event["content"]}

                elif event["type"] == "tool_call":
                    made_tool_call = True
                    tool_calls_made.append(event["tool_call"])
                    yield {"type": "tool_call", "tool_call": event["tool_call"]}

                    tool_result = await self._execute_tool(event["tool_call"])
                    if event["tool_call"]["function"]["name"] in DISCOVERY_CONTEXT_TOOLS:
                        tool_result = self._annotate_discovery_result(
                            tool_result,
                            tool_pool,
                            unavailable_tools,
                        )
                    tool_results_made.append({
                        "tool": event["tool_call"]["function"]["name"],
                        "result": tool_result,
                    })
                    yield {"type": "tool_result", "tool_call_id": event["tool_call"]["id"], "result": tool_result}

                    messages.append({"role": "assistant", "content": None, "tool_calls": [event["tool_call"]]})
                    messages.append({"role": "tool", "tool_call_id": event["tool_call"]["id"], "content": json.dumps(tool_result, ensure_ascii=False)})
                    if not discovery_only:
                        tools = self._expand_tools_after_result(tools, tool_pool, tool_result)

                elif event["type"] == "error":
                    yield {"type": "error", "message": event["message"]}

            if not made_tool_call:
                break
        else:
            tool_round_limit_reached = True

        final_text = masker.unmask(response_text) if masker else response_text
        if not final_text.strip() and tool_results_made:
            final_text = self._tool_result_fallback(
                tool_results_made,
                tool_round_limit_reached=tool_round_limit_reached,
            )
            if final_text:
                yield {"type": "token", "content": final_text}

        await self.message_repo.add_message(
            session_id, MessageRole.ASSISTANT, final_text, seq + 1,
            tool_calls=tool_calls_made if tool_calls_made else None,
        )
        await self.db.commit()

        yield {"type": "done", "session_id": session_id}

    def _resolve_chat(self, provider_id: Optional[str]) -> tuple[Optional[ChatService], Optional[LLMRuntimeConfig]]:
        if self.chat is not None:
            return self.chat, None

        runtime_config = load_llm_runtime(provider_id)
        if not runtime_config.active or runtime_config.provider is None:
            return None, runtime_config
        return ChatService(runtime_config.provider), runtime_config

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
            return f"模型配置 {runtime_config.provider.name} 已停用。请在对话页切换模型，或到 LLM 配置页启用它。"
        if runtime_config and runtime_config.provider and not runtime_config.provider.api_key_configured:
            return f"模型配置 {runtime_config.provider.name} 未配置 API Key。请到 LLM 配置页填写密钥，保存后新消息会立即生效。"
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
            [tool for tool in await self.mcp.list_tools(skill_id) if self._tool_available_for_chat(tool)]
            if skill_id
            else all_tools
        )
        all_by_name = {tool["name"]: tool for tool in all_tools}
        scoped_by_name = {tool["name"]: tool for tool in scoped_tools}

        has_toolsearch = "toolsearch" in all_by_name
        if not has_toolsearch:
            return scoped_tools, scoped_by_name, unavailable_tools

        discovery_tools = [
            all_by_name[name]
            for name in sorted(DISCOVERY_CONTEXT_TOOLS)
            if name in all_by_name
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

    @staticmethod
    def _intent_anchor_tools(user_content: str, scoped_by_name: dict[str, dict]) -> list[dict]:
        content = user_content.lower()
        if ChatOrchestrator._discovery_only_intent(content):
            return []
        anchor_names: list[str] = []
        if any(keyword in content for keyword in K8S_CLUSTER_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_CLUSTER_ANCHOR_TOOLS)
        if any(keyword in content for keyword in K8S_POD_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_POD_ANCHOR_TOOLS)
        if any(keyword in content for keyword in K8S_SERVICE_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_SERVICE_ANCHOR_TOOLS)
        if any(keyword in content for keyword in K8S_WORKLOAD_CONTEXT_KEYWORDS):
            anchor_names.extend(K8S_WORKLOAD_ANCHOR_TOOLS)
        if any(keyword in content for keyword in ECS_CONTEXT_KEYWORDS):
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
                    return {
                        "error": "tool_execution_denied",
                        "reason": decision.reason,
                        "requires_confirmation": decision.requires_confirmation,
                        "tool": name,
                    }
                result = await self.mcp.call_tool(name, arguments, user=self.current_user)
            else:
                result = {"error": "MCP 服务未连接"}
        except Exception as e:
            logger.error(f"工具调用失败 {name}: {e}")
            result = {"error": str(e)}

        return result

    @staticmethod
    def _tool_available_for_chat(tool: dict) -> bool:
        return bool(tool.get("available", True))

    @staticmethod
    def _tool_result_fallback(
        tool_results: list[dict],
        tool_round_limit_reached: bool = False,
    ) -> str:
        error_results = [
            item for item in tool_results
            if isinstance(item.get("result"), dict) and item["result"].get("error")
        ]
        if not error_results:
            successful_summary = ChatOrchestrator._successful_tool_result_summary(tool_results)
            if successful_summary:
                prefix = "工具已执行完成，但模型没有返回文本结果。"
                if tool_round_limit_reached:
                    prefix = "工具调用轮次已达到上限，下面是已获得的工具结果摘要。"
                return f"{prefix}\n\n{successful_summary}"

            unavailable_candidates = ChatOrchestrator._unavailable_candidates_from_results(tool_results)
            if unavailable_candidates:
                name, reason = unavailable_candidates[-1]
                if name.startswith("k8s-"):
                    return (
                        f"当前 Kubernetes 工具不可用：{reason} "
                        "配置 KUBECONFIG_PATH 并确保集群 API 可访问后再重试，或关闭“工具上下文”进行普通对话。"
                    )
                return f"{name} 当前不可用：{reason}"
            if tool_round_limit_reached:
                return "工具检索没有收敛到可执行结果，已停止继续调用。你可以换一种更具体的问题，或关闭“工具上下文”进行普通对话。"
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
            parsed = ChatOrchestrator._parse_tool_payload(result) if isinstance(result, dict) else None
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
    def _successful_tool_result_summary(tool_results: list[dict]) -> str:
        lines = []
        for item in tool_results:
            tool_name = item.get("tool", "")
            if tool_name in DISCOVERY_CONTEXT_TOOLS:
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
            preview = ", ".join(f"{item.get('namespace', '-')}/{item.get('name')}:{item.get('type')}" for item in items[:8])
            return f"- `k8s-get-services`: count={payload.get('count', len(items))}；{preview}"
        if tool_name == "k8s-get-events":
            items = payload.get("items") or []
            warnings = [item for item in items if item.get("type") == "Warning"]
            return f"- `k8s-get-events`: count={payload.get('count', len(items))}, warnings={len(warnings)}"
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
