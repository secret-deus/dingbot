# ToolSearch MCP Server

Local stdio MCP server for searching the Ding Robot operations tool catalog.

ToolSearch is discovery-only. It returns metadata about tools and never calls Kubernetes, ECS, shell commands, or webhook APIs.
The current generated catalog contains 55 executable tool entries.

## Commands

```bash
npm install
npm run catalog:generate
npm run build
npm test
npm start
```

The catalog lives at `../../config/tool_catalog.json` relative to this package. Regenerate it after editing tool definitions.

## Tools

| Tool | Purpose |
| --- | --- |
| `toolsearch` | Search the catalog by query, category, limit, and risk filter. Returns flat `results`, `categoryGroups`, and `relevanceLayers`. |
| `tool_get` | Return one catalog entry by exact tool name. |
| `tool_categories` | Return category counts and execution policy counts. |
| `tool_reload_catalog` | Reload `config/tool_catalog.json` from disk. |
