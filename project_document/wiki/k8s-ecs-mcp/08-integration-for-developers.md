# 08 研发对接指南

[← Wiki 首页](./README.md)

## 1. 在其他模块中调用 builtin 工具

**推荐路径**（与主应用一致）：

1. 确保 `register_builtin_tools_once()` 已执行（主进程启动时会调）。
2. 使用 `EnhancedMCPClient.call_tool(tool_name, parameters: dict)`。
3. 解析返回：兼容 **JSON 字符串** 与 **dict**（见 `mcp_call_result_to_payload`）。

**不要**绕过 `call_tool` 直接 `execute_tool`，除非你在写单元测试或内部脚本，否则 Skill 与遥测可能不一致。

## 2. Skill（工具白名单）

- 配置：`config/skills/` 与 `SkillRegistry`（详见仓库 `backend/src/skills/`）。
- 会话携带 `skill_id` 时，`list_tools` 应只暴露允许的工具；**`call_tool` 必须二次校验**工具名，防止客户端伪造。

## 3. 与 `mcp_config.json` 的协同

- 服务器名 `k8s-mcp`、`ecs-sse-server` 等可配置为 **builtin** 或跳过远程，避免与进程内工具重复。
- 详见 `builtin_k8s_ecs.resolved_skip_remote_server_names()`。

## 4. 新增一个 K8s 工具（检查清单）

1. 在 `backend/src/k8s_mcp/tools/` 下实现 `MCPToolBase` 子类。
2. `get_schema()` 提供完整 JSON Schema（`required` 必填）。
3. 若只读，加入 `SAFE_QUERY_TOOLS`。
4. `register_all_tools()` 已遍历 `SAFE_QUERY_TOOLS`，一般无需改注册逻辑。
5. 补充本 Wiki [06](./06-tools-reference-kubernetes.md) 一行说明。
6. 若涉及新 K8s API，更新 [05](./05-kubernetes-rbac-and-kubeconfig.md) RBAC 说明。

## 5. 新增一个 ECS 工具

1. 实现工具类并 `tool_registry.register(..., "ecs")`。
2. 加入 `ecs_mcp/tools/__init__.py` 的 `SAFE_QUERY_TOOLS`。
3. 若调用新阿里云 API，在 [04](./04-aliyun-ram-network-security.md) 增加 **Action → RAM** 行。
4. 若使用 RPC，复用 `ecs_rpc`/`cms_rpc` 或扩展 `sign_parameters` 的 Version。

## 6. 测试建议

- 单元测试：对 `execute()` 传入最小参数，Mock `K8sClient` 或阿里云 HTTP（见仓库 `backend/tests` 模式）。
- 集成测试：需真实 kubeconfig 与测试账号 RAM；勿在 CI 中硬编码 AK。

## 7. 文档维护

- 工具行为以 **`get_schema()`** 为唯一真相来源。
- 更新本 Wiki 时同步修改 [README](./README.md) 索引（如有新章）。

下一章：[09 排错与 FAQ](./09-troubleshooting-and-faq.md)
