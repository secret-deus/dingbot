# ToolSearch MCP Implementation Logic

## 1. Purpose

ToolSearch is a local MCP server that exposes a searchable operations tool directory. It does not execute operational tools. It lets the LLM retrieve the most relevant 3-5 candidate tools instead of loading every tool schema into the prompt.

## 2. Runtime Shape

Recommended location:

```text
mcp-servers/toolsearch/
```

Implemented package:

```json
{
  "type": "module",
  "bin": {
    "toolsearch-mcp": "dist/src/index.js"
  },
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "start": "node dist/src/index.js",
    "test": "npm run build && node --test dist/src/*.test.js",
    "catalog:generate": "node scripts/generate-catalog.mjs"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.29.0",
    "zod": "^3.25.76"
  },
  "devDependencies": {
    "@types/node": "^22.15.3",
    "typescript": "^5.8.3"
  }
}
```

The server should use `StdioServerTransport`. It must not write logs to stdout because stdout is reserved for MCP JSON-RPC messages.

## 3. Catalog Loading

The server reads `TOOL_CATALOG_PATH` from environment first:

```text
TOOL_CATALOG_PATH=/Users/xhang/Documents/ding-robot/config/tool_catalog.json
```

If absent, it walks upward from the current working directory and falls back to `config/tool_catalog.json` at the repository root.

The catalog should be generated from:

1. `config/mcp_config.json` for complete old catalog metadata.
2. `backend-v2/app/mcp/builtin.py` or a backend export endpoint for currently executable built-in tools.

Recommended generation logic:

```text
load old catalog tools
load current executable tool names
for each old catalog tool:
  normalize name/category/schema fields
  infer dangerLevel
  infer tags and title if missing
  if tool exists in executable set:
    executionPolicy = executable
  else:
    executionPolicy = catalog_only
write config/tool_catalog.json
```

## 4. Catalog Schema

Required TypeScript shape:

```ts
type DangerLevel = "read" | "write" | "dangerous";
type ExecutionPolicy = "executable" | "catalog_only" | "external_mcp";

interface ToolDoc {
  name: string;
  title: string;
  category: string;
  description: string;
  tags: string[];
  dangerLevel: DangerLevel;
  server: string;
  executionPolicy: ExecutionPolicy;
  inputSchema: {
    type: "object";
    properties: Record<string, { type?: string; description?: string; examples?: string[] }>;
    required: string[];
  };
  examples: string[];
}
```

Validation rules:

1. `name` and `description` are required.
2. `name` must be unique.
3. `dangerLevel` defaults to `read`.
4. `executionPolicy` defaults to `catalog_only` unless known executable.
5. `inputSchema.properties` defaults to an empty object.
6. Tool names keep hyphen format, such as `k8s-get-logs`.

Current generated catalog:

```text
total: 21
executable: 11
catalog_only: 10
```

## 5. Search API

### `toolsearch`

Input:

```ts
{
  query: string;
  limit?: number;
  category?: string;
  dangerLevel?: "read" | "write" | "dangerous";
}
```

Output:

```json
{
  "query": "查看 pod 日志",
  "category": null,
  "total": 2,
  "results": [
    {
      "name": "k8s-get-logs",
      "title": "获取 Pod 日志",
      "category": "kubernetes",
      "description": "获取 Kubernetes Pod 日志",
      "tags": ["k8s", "pod", "logs", "日志"],
      "dangerLevel": "read",
      "server": "builtin",
      "executionPolicy": "executable",
      "score": 84,
      "matchedFields": ["name", "title", "description", "tags"],
      "inputSchema": {},
      "examples": []
    }
  ]
}
```

### `tool_get`

Returns one full catalog entry by exact tool name.

### `tool_categories`

Returns category names and counts:

```json
{
  "categories": [
    { "name": "kubernetes", "total": 18, "executable": 8 },
    { "name": "ecs", "total": 3, "executable": 2 }
  ]
}
```

### `tool_reload_catalog`

Reloads the catalog file and returns total count.

## 6. Ranking Logic

### Normalization

```text
lowercase
replace punctuation with spaces
keep letters, numbers, underscore, hyphen, slash, dot
split by whitespace
expand synonyms
```

### Field Text

Build searchable field text for each tool:

```text
name
title
category
description
tags joined by space
input schema property names/types/descriptions
examples joined by space
```

### Weights

```ts
const weights = {
  name: 10,
  title: 8,
  category: 5,
  tags: 5,
  description: 3,
  inputSchema: 2,
  examples: 2
};
```

### Score Rules

```text
if field contains full normalized query:
  score += weight * 5
for each query token:
  if field equals token:
    score += weight * 4
  else if field starts with token:
    score += weight * 2
  else if field contains token:
    score += weight
if query expresses read intent and tool is read:
  score += 3
if query expresses mutation intent and tool is write/dangerous:
  score += 4
```

Mutation boost is only a ranking signal. It must never imply permission to execute.

## 7. Backend Integration Logic

### MCP Config

Add a ToolSearch stdio server entry:

```json
{
  "name": "toolsearch",
  "type": "stdio",
  "enabled": true,
  "command": "node",
  "args": ["/Users/xhang/Documents/ding-robot/mcp-servers/toolsearch/build/index.js"],
  "env": {
    "TOOLSEARCH_CATALOG": "/Users/xhang/Documents/ding-robot/config/tool_catalog.json"
  }
}
```

Before implementation, verify the installed Python MCP SDK expects either:

```python
stdio_client(command, args)
```

or:

```python
StdioServerParameters(command=command, args=args, env=env)
stdio_client(params)
```

The current `backend-v2/app/mcp/manager.py` should be updated based on the installed SDK, not guessed.

### LLM Orchestration

Target behavior:

```text
initial tool list = [toolsearch, tool_get]
if query likely needs real tools:
  LLM calls toolsearch
  LLM inspects candidates
  LLM chooses real tool name
  backend checks IAM/risk/confirmation
  backend executes real tool
  LLM summarizes real result
```

Fallback behavior:

1. If ToolSearch is unavailable, use current built-in tool list.
2. If a candidate is `catalog_only`, explain that the tool exists in catalog but is not executable yet.
3. If LLM selects an unknown tool, reject and audit the failed selection.

Implemented chat orchestration:

1. Initial LLM tool context includes only `toolsearch`, `tool_get`, and `tool_categories` when ToolSearch is connected.
2. ToolSearch or `tool_get` results are parsed for `executionPolicy = executable` candidate names.
3. Only candidate tools already present in the MCP tool cache are added to the next LLM tool context.
4. Real execution still goes through `MCPManager.call_tool`, catalog policy, confirmation checks, and audit.
5. The loop stops after a bounded number of tool-call rounds.

## 8. Security and Audit Logic

Execution gate:

```text
selected tool
  -> exact-name lookup
  -> executable policy check
  -> IAM permission check
  -> dangerLevel check
  -> optional user confirmation
  -> real execution
  -> audit record
```

Audit event fields:

```json
{
  "actor": "admin",
  "action": "tool.execute",
  "resource": "k8s-get-logs",
  "result": "allowed",
  "details": {
    "allowed": true,
    "reason": "read_allowed",
    "tool": "k8s-get-logs",
    "category": "kubernetes",
    "dangerLevel": "read",
    "executionPolicy": "executable",
    "server": "builtin",
    "requiresConfirmation": false,
    "argumentKeys": ["namespace"],
    "argumentPreview": { "namespace": "default" }
  }
}
```

`argumentPreview` only records allowlisted operational fields such as `query`,
`category`, `name`, `namespace`, `pod_name`, and `deployment_name`. Sensitive
keys containing `secret`, `token`, `password`, `api_key`, or `access_key` are
redacted.

## 9. Test Plan

Unit tests:

1. Catalog validates required fields.
2. Duplicate tool names fail fast.
3. Chinese query `查看 pod 日志` ranks `k8s-get-logs` first.
4. English query `deployment history` ranks `k8s-get-deployment-history`.
5. Category filter returns only matching category.
6. Mutation query does not execute tools.

Backend integration tests:

1. Stdio ToolSearch connects successfully.
2. `MCPManager.list_tools()` includes ToolSearch tools.
3. `MCPManager.call_tool("toolsearch", ...)` returns candidate JSON.
4. `catalog_only` real execution is rejected.
5. Write/dangerous execution requires confirmation.

Frontend smoke tests:

1. MCP config page shows ToolSearch connected.
2. Chat shows candidate tools after a search.
3. Disabling "include MCP context" keeps server running but removes MCP from the chat context.

## 10. Rollout Plan

1. Write and review this spec.
2. Generate `config/tool_catalog.json`.
3. Build ToolSearch MCP server.
4. Integrate backend stdio connection.
5. Add LLM orchestration changes.
6. Add frontend candidate and catalog status UI.
7. Verify with local minikube read-only tools.
8. Add missing executable tools incrementally.
