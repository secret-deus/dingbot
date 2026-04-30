"""内置工具注册 - K8s & ECS 进程内工具（无需单独 MCP 服务器）"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.core.config import get_settings
from app.mcp.tools.k8s import K8sClient
from app.mcp.tools.ecs import ECSClient


class BuiltinToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Any] = {}
        self._tool_defs: list[dict] = []
        self._k8s: K8sClient | None = None
        self._ecs: ECSClient | None = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        settings = get_settings()

        self._k8s = K8sClient(
            kubeconfig_path=settings.kubeconfig_path,
            in_cluster=settings.k8s_in_cluster,
            default_namespace=settings.k8s_namespace,
        )
        self._register_k8s_tools()

        if settings.alibaba_access_key_id:
            self._ecs = ECSClient(
                access_key_id=settings.alibaba_access_key_id,
                access_key_secret=settings.alibaba_access_key_secret or "",
                region_id=settings.alibaba_region_id,
            )
            self._register_ecs_tools()

    def _register_k8s_tools(self) -> None:
        k8s_tools = [
            ("k8s-get-pods", "获取 Pod 列表", {"namespace": {"type": "string", "description": "命名空间"}, "label_selector": {"type": "string", "description": "标签选择器"}}),
            ("k8s-get-services", "获取 Service 列表", {"namespace": {"type": "string", "description": "命名空间"}}),
            ("k8s-get-deployments", "获取 Deployment 列表", {"namespace": {"type": "string", "description": "命名空间"}}),
            ("k8s-get-nodes", "获取 Node 列表", {}),
            ("k8s-get-logs", "获取 Pod 日志", {"pod_name": {"type": "string", "description": "Pod名称"}, "namespace": {"type": "string", "description": "命名空间"}, "tail_lines": {"type": "integer", "description": "行数"}}),
            ("k8s-describe-pod", "描述 Pod 详情", {"pod_name": {"type": "string", "description": "Pod名称"}, "namespace": {"type": "string", "description": "命名空间"}}),
            ("k8s-get-events", "获取事件列表", {"namespace": {"type": "string", "description": "命名空间"}}),
            ("k8s-cluster-summary", "集群概览", {}),
        ]
        for name, desc, schema in k8s_tools:
            required = [k for k, v in schema.items() if "namespace" not in k or k == "pod_name"]
            self._tool_defs.append({
                "name": name, "description": desc,
                "inputSchema": {"type": "object", "properties": schema, "required": required},
                "server": "builtin",
            })
            self._handlers[name] = self._k8s

    def _register_ecs_tools(self) -> None:
        ecs_tools = [
            ("ecs-list-instances", "获取 ECS 实例列表", {"page_size": {"type": "integer", "description": "每页数量"}}),
            ("ecs-describe-instance", "查询实例详情", {"instance_id": {"type": "string", "description": "实例ID"}}),
            ("ecs-inspect", "ECS 巡检", {"instance_ids": {"type": "string", "description": "实例ID列表(逗号分隔)"}}),
        ]
        for name, desc, schema in ecs_tools:
            required = [k for k in schema if k == "instance_id"]
            self._tool_defs.append({
                "name": name, "description": desc,
                "inputSchema": {"type": "object", "properties": schema, "required": required},
                "server": "builtin",
            })
            self._handlers[name] = self._ecs

    def list_tools(self) -> list[dict]:
        self._ensure_initialized()
        return list(self._tool_defs)

    async def call(self, name: str, arguments: dict) -> dict:
        self._ensure_initialized()
        handler = self._handlers.get(name)
        if handler is None:
            return {"error": f"内置工具 {name} 不存在"}

        try:
            method_name = name.replace("-", "_")
            method = getattr(handler, method_name, None)
            if method is None:
                return {"error": f"工具方法 {method_name} 未实现"}
            result = await method(**arguments)
            return {"result": result}
        except Exception as e:
            logger.error("内置工具 {} 执行失败: {}", name, e)
            return {"error": str(e)}
