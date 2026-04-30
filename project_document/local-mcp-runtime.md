# Local MCP Runtime

更新时间：2026-04-29

## 结论

K8s/ECS MCP 能力默认在 FastAPI 主进程内运行，不再要求单独启动 `k8s-mcp`、`ecs-mcp` 或远程 SSE 服务。远程 MCP 仍作为扩展适配能力保留，但不是主链路。

## 配置标准

`config/mcp_config.json` 中本地工具服务使用 `type=local` 和 `provider` 描述：

```json
{
  "name": "k8s-mcp",
  "type": "local",
  "provider": "k8s",
  "implementation": "builtin",
  "enabled": true,
  "enabled_tools": ["k8s-get-pods"]
}
```

字段约定：

- `type=local`：工具由主进程内 `LocalMCPRuntime` 注册和执行，不建立远程连接。
- `provider=k8s|ecs`：映射到本地 K8s/ECS provider。
- `enabled_tools` / `disabled_tools`：仍然生效，用于控制本地工具暴露范围。
- `implementation=builtin`：兼容旧配置和跳过远程连接的语义。

## 运行时边界

```text
EnhancedMCPClient
  ├─ LocalMCPRuntime
  │   ├─ K8sBuiltinProvider
  │   └─ EcsBuiltinProvider
  └─ Remote MCP adapters
      ├─ SSE
      └─ stdio
```

`EnhancedMCPClient.connect()` 会先跳过 `type=local` 和 `implementation=builtin` 的远程连接，再合并本地工具。手动 `connect_server("k8s-mcp")` 也会刷新本地 runtime，而不会尝试连接历史 SSE 端口。

## API 暴露

`GET /api/v2/ops/overview` 在标准 envelope 的 `data.mcp_runtime` / `data.mcpRuntime` 中返回运行时摘要：

```json
{
  "transport": "local",
  "status": "connected",
  "tool_count": 21,
  "remote_connections": 0,
  "providers": [
    {"id": "builtin-k8s", "transport": "local", "tool_count": 18},
    {"id": "builtin-ecs", "transport": "local", "tool_count": 3}
  ]
}
```

## 验收命令

```bash
PYTHONPATH=backend poetry run pytest -q backend/tests/test_mcp_builtin_skip.py backend/tests/test_api_standard_runtime_ops.py
PYTHONPATH=backend poetry run python -m py_compile backend/src/mcp/config.py backend/src/mcp/config_manager.py backend/src/mcp/enhanced_client.py backend/src/api/v2/endpoints/ops.py
```
