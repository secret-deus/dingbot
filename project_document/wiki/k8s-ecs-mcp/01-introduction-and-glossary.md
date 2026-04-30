# 01 引言与术语

[← Wiki 首页](./README.md)

## 1. 本文档解决什么问题

研发团队在以下场景需要一份**可检索、可交付**的说明：

- 在**另一个服务**里调用与本项目相同的「K8s/ECS 只读工具」行为，需要对齐**参数、返回、超时、权限**；
- 向**安全/运维**说明需要开通哪些 **RAM Action**、哪些 **K8s RBAC**、哪些**出站域名**；
- 新人接手 `backend/src/k8s_mcp`、`backend/src/ecs_mcp` 时快速建立心智模型。

本 Wiki 按「Wiki 多页 + 交叉链接」组织，避免单文件过长难以维护。

## 2. 文档范围（明确包含 / 不包含）

| 包含 | 不包含 |
|------|--------|
| 主进程内 **builtin** K8s/ECS MCP 工具 | 独立进程 `k8s-mcp` / `ecs-mcp` HTTP Server 的部署手册（若已归档见 `archived/`） |
| `EnhancedMCPClient` 对 builtin 工具的 `call_tool` 路径 | 具体业务 REST API 的完整 OpenAPI（见 `backend` 路由与 `/docs`） |
| RAM、K8s RBAC、Prometheus、环境变量 | 钉钉机器人密钥、LLM Key 等非 MCP 直依赖（仅在其他章节点到） |

## 3. 术语表

| 术语 | 含义 |
|------|------|
| **MCP** | Model Context Protocol；此处指「工具名 + JSON Schema 参数 + 文本/JSON 结果」的调用约定。 |
| **builtin 工具** | 编译进 `backend` 进程、由 `builtin_k8s_ecs` 注册的工具，不依赖远程 SSE MCP。 |
| **进程内注册表** | `k8s_mcp.core.tool_registry` 与 `ecs_mcp.core.tool_registry` 两套 `tool_registry`，最终由 `register_builtin_tools_once()` 拉通。 |
| **SAFE_QUERY_TOOLS** | K8s/ECS 侧「仅只读」工具列表；当前对外注册以此为准（见各 `tools/__init__.py`）。 |
| **Skill** | 本仓库可选的「工具白名单」机制：`skill_id` 关联允许的工具名/前缀（见 `config/skills/` 与 `08-integration-for-developers.md`）。 |
| **DescribeInstances** | 阿里云 ECS OpenAPI Action；RAM 一般为 `ecs:DescribeInstances`。 |
| **CMS / 云监控** | 指标查询走 `metrics.*.aliyuncs.com`，Action 如 `DescribeMetricList`、`QueryMetricList`；RAM 一般为 `cms:*`（以控制台为准）。 |

## 4. 与「远程 MCP Server」的关系

历史形态可能通过 `config/mcp_config.json` 配置 **k8s-mcp**、**ecs-sse-server** 等远程服务。当前推荐：

- 环境变量 **`BUILTIN_K8S_ECS_TOOLS=true`**（默认）时，在进程内注册工具；
- **`MCP_SKIP_REMOTE_SERVER_NAMES`** 或配置中 `implementation=builtin` 的服务器名，可避免重复连接远程同名 MCP。

细节见 [02-architecture-and-data-flow.md](./02-architecture-and-data-flow.md)。

## 5. 源码目录（研发速查）

```
backend/src/mcp/builtin_k8s_ecs.py       # 注册开关、merge_builtin_mcptools、execute_builtin_tool
backend/src/k8s_mcp/
├── config.py                            # K8sConfig、环境变量
├── k8s_client.py                        # Kubernetes API 封装
├── core/tool_registry.py                # MCPToolBase、注册表
└── tools/                               # 各工具实现
backend/src/ecs_mcp/
├── config.py                            # ECSConfig、AK/SK
├── clients/ecs_rpc.py, cms_rpc.py       # 阿里云 RPC 签名与 HTTP GET
└── tools/                               # ECS 工具实现
```

下一章：[02 架构与数据流](./02-architecture-and-data-flow.md)
