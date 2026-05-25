# ToolSearch MCP Spec - Design

## Overview

ToolSearch is a local stdio MCP server dedicated to searching the operations tool catalog. It returns tool metadata only. Real execution remains in `backend-v2` through built-in handlers or connected MCP servers.

The target flow is:

```text
User question
  -> LLM receives compact system prompt and ToolSearch tools
  -> LLM calls toolsearch(query)
  -> ToolSearch returns ranked candidates
  -> LLM selects a real tool, if needed
  -> Backend checks IAM, risk, confirmation, audit
  -> Backend executes real tool through MCPManager
  -> LLM summarizes result for the user
```

## Proposed File Layout

```text
project_document/specs/toolsearch-mcp/
  requirements.md
  design.md
  tasks.md
  implementation-logic.md

mcp-servers/toolsearch/
  package.json
  tsconfig.json
  tools.json
  src/index.ts

config/
  mcp_config.json
  tool_catalog.json
```

`mcp-servers/toolsearch` is preferred over placing the server under `.kiro` or hidden workflow directories because this is product runtime code, not IDE-only planning state.

## Components

### 1. ToolSearch MCP Server

Runtime: TypeScript + `@modelcontextprotocol/sdk` + stdio transport.

Exposed tools:

| Tool | Purpose |
|------|---------|
| `toolsearch` | Search the catalog by natural language query, category, limit, and optional risk filter. |
| `tool_get` | Return full metadata for one exact tool name. |
| `tool_categories` | Return available categories and counts. |
| `tool_reload_catalog` | Reload the catalog from disk after editing tool definitions. |

### 2. Tool Catalog

The catalog should be generated from two sources:

1. `config/mcp_config.json` `tools[]`: old rich metadata and all 21 known tools.
2. `backend-v2/app/mcp/builtin.py`: current executable built-in tools.

Normalized catalog entry:

```json
{
  "name": "k8s-get-logs",
  "title": "获取 Pod 日志",
  "category": "kubernetes",
  "description": "获取 Kubernetes Pod 日志",
  "tags": ["k8s", "pod", "logs", "日志", "故障排查"],
  "dangerLevel": "read",
  "server": "builtin",
  "executionPolicy": "executable",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pod_name": { "type": "string", "description": "Pod 名称" },
      "namespace": { "type": "string", "description": "命名空间" }
    },
    "required": ["pod_name"]
  },
  "examples": ["查看 nginx pod 最近 100 行日志"]
}
```

`executionPolicy` values:

| Value | Meaning |
|-------|---------|
| `executable` | The backend can execute this tool now. |
| `catalog_only` | Searchable metadata exists, but implementation is missing or disabled. |
| `external_mcp` | Requires a remote/SSE MCP server connection. |

`dangerLevel` values:

| Value | Meaning |
|-------|---------|
| `read` | Read-only diagnostics. |
| `write` | Controlled mutation such as restart, scale, or config update. |
| `dangerous` | Destructive or broad-impact operation. |

### 3. Backend Integration

Backend changes should stay inside the MCP and LLM orchestration boundary:

| Area | Design |
|------|--------|
| MCP config loading | Resolve relative config paths from repo root or backend working directory predictably. |
| Stdio MCP | Use the Python MCP SDK's current stdio server parameter API and test it locally. |
| Tool cache | Merge built-in tools, external MCP tools, and ToolSearch tools without name collision. |
| LLM tool strategy | Inject only `toolsearch`, `tool_get`, and a small execution capability initially. |
| Execution gate | Before calling real tools, run IAM, risk classification, optional confirmation, and audit. |

### 4. Frontend Integration

Frontend should treat ToolSearch as a discovery step, not a second "connect" action.

| Page | Behavior |
|------|----------|
| Chat | Show selected candidate tools in compact cards with risk and source labels. |
| MCP Config | Show ToolSearch health, catalog totals, executable totals, and catalog-only totals. |
| Settings | Let users toggle "include MCP context in this conversation"; server lifecycle should be automatic. |

## Search Algorithm

Phase 1 should use deterministic weighted lexical scoring because it is easy to test and debug.

Field weights:

| Field | Weight |
|-------|--------|
| `name` | 10 |
| `title` | 8 |
| `category` | 5 |
| `tags` | 5 |
| `description` | 3 |
| `inputSchema` | 2 |
| `examples` | 2 |

Ranking signals:

1. Exact phrase match gets a multiplier.
2. Exact token match gets a stronger score than partial match.
3. Prefix match scores higher than contains match.
4. Chinese/English synonyms expand query tokens.
5. Read intent boosts read tools.
6. Mutation intent boosts write/dangerous tools but does not auto-execute them.

Initial synonym examples:

```json
{
  "日志": ["log", "logs", "loki"],
  "指标": ["metric", "metrics", "prometheus"],
  "重启": ["restart", "rollout"],
  "权限": ["permission", "iam", "rbac"],
  "审计": ["audit", "security"],
  "定时任务": ["cron", "scheduler"]
}
```

Phase 2 can replace or augment this with BM25 or MiniSearch after the phase 1 baseline is stable.

## Current Tool Inventory

Current generated catalog:

```text
total: 68
executable: 68
catalog_only: 0
categories: kubernetes=52, ecs=3, aliyun=13
```

The old 21-tool catalog from `config/mcp_config.json` is preserved inside the generated catalog. The current old-catalog set includes:

```text
k8s-get-pods
k8s-get-services
k8s-get-deployments
k8s-get-nodes
k8s-get-logs
k8s-describe-pod
k8s-get-events
k8s-get-deployment-history
k8s-get-endpoints
k8s-relation-query
k8s-cluster-summary
k8s-get-cluster-metrics
k8s-resource-metrics-query
k8s-prometheus-app-metrics
k8s-update-knowledge-graph-metrics
k8s-resource-monitor
k8s-metrics-coverage-report
k8s-resource-analysis-report
ecs-describe-instance-monitor-data
ecs-list-instances
ecs-inspect
```

Future missing executable handlers should be marked `catalog_only` until implemented, but the current generated catalog has no `catalog_only` entries.

## Security Design

ToolSearch is safe by construction because it returns metadata only. The backend still needs the following controls before execution:

1. Resolve selected real tool by exact name.
2. Check user role and tool permission.
3. Check danger level.
4. Require explicit confirmation for `write` and `dangerous`.
5. Call the real tool only after approval.
6. Store an audit record with input parameters, caller, tool, result status, and request id.

## Success Metrics

1. Tool catalog contains at least the 21 old tools.
2. ToolSearch can return top 3-5 relevant tools for common Chinese and English ops queries.
3. Chat prompt no longer needs to load all real tool schemas by default.
4. Write/dangerous tools cannot be executed through ToolSearch alone.
5. Frontend shows clear catalog and candidate state without old blue-heavy styling regressions.
