# ToolSearch MCP Spec - Tasks

## Current Status

- [x] Confirm existing spec should not be placed in `.kiro`.
- [x] Confirm current repository has no ToolSearch spec yet.
- [x] Confirm old `config/mcp_config.json` contains 21 tool definitions.
- [x] Confirm current `backend-v2` built-in K8s list contains 8 tools, with ECS conditional on credentials.

## Implementation Backlog

- [ ] 1. Stabilize local MCP configuration
  - [x] Fix `MCP_CONFIG_PATH` resolution for local dev so `backend-v2` can reliably find root `config/mcp_config.json`.
  - [x] Verify Docker runtime path behavior and document the difference from local `poetry run`.
  - [x] Add a backend smoke test that proves configured MCP servers are loaded.

- [x] 2. Restore and normalize tool inventory
  - Generate `config/tool_catalog.json` from `config/mcp_config.json` and built-in registry metadata.
  - Preserve all 21 known old catalog tools.
  - Mark missing implementations as `catalog_only`.
  - Add `dangerLevel`, `tags`, `title`, `examples`, `server`, and `executionPolicy` fields.

- [x] 3. Build local ToolSearch MCP server
  - Create `mcp-servers/toolsearch` TypeScript package.
  - Implement `toolsearch`, `tool_get`, `tool_categories`, and `tool_reload_catalog`.
  - Ensure stdio server writes logs only to stderr.
  - Add build and start scripts.

- [x] 4. Implement ranking logic
  - Normalize Chinese/English text and tokenize safely.
  - Add weighted scoring for name, title, category, tags, description, schema, and examples.
  - Add synonym expansion for Kubernetes, logs, metrics, IAM, audit, scheduler, and LLM categories.
  - Add unit tests for common query cases.

- [x] 5. Integrate ToolSearch with backend MCP manager
  - Add ToolSearch stdio server entry to MCP config.
  - Verify the Python MCP stdio client call signature against the installed SDK.
  - Merge ToolSearch tools into backend tool cache without collision.
  - Add health output for ToolSearch connection and catalog size.

- [x] 6. Redesign LLM tool orchestration
  - Make LLM call `toolsearch` before loading large real tool definitions.
  - Load full metadata with `tool_get` only when needed.
  - Keep final execution routed through existing backend tool execution APIs.
  - Add fallback behavior when ToolSearch is unavailable.

- [x] 7. Add IAM, confirmation, and audit gates
  - Map every tool to read/write/dangerous risk.
  - Add permission checks before real tool execution.
  - Require confirmation for write/dangerous actions.
  - Record search, selection, execution, result, and caller in audit logs.

- [x] 8. Update frontend UX
  - [x] Replace the confusing "connect button + switch" MCP behavior with automatic server lifecycle plus "include in context" toggle.
  - [x] Add ToolSearch status and catalog stats to MCP config management.
  - [x] Show compact tool candidate cards in chat.
  - [x] Keep colors aligned with the unified non-blue theme.

- [ ] 9. Recover missing executable tools
  - [ ] Implement or reconnect `k8s-get-deployment-history`.
  - [x] Implement or reconnect `k8s-get-endpoints`.
  - [ ] Implement or reconnect `k8s-relation-query`.
  - [ ] Implement or reconnect metrics and report tools.
  - [ ] Implement or reconnect `ecs-describe-instance-monitor-data`.
  - [x] Add self-test report for `k8s-get-endpoints` recovery.
  - [x] Add code review report for `k8s-get-endpoints` recovery.

- [ ] 10. Fix rewrite stabilization TODOs
  - [x] Add missing `frontend-v3/Dockerfile` or update `docker-compose.yml`.
  - [x] Finish LLM configuration UI flow so placeholder API keys do not look like runtime failures.
  - [x] Support hot-applied multi-provider LLM config and chat-side model selection.
  - [x] Add CI commands for `backend-v2`, `frontend-v3`, and `mcp-servers/toolsearch`.
  - [ ] Decide Vite/esbuild audit remediation path without forced breaking upgrades.

- [ ] 11. Verification
  - [x] Run ToolSearch unit tests.
  - [x] Run backend MCP integration tests.
  - [x] Run backend K8s endpoints tool tests.
  - [x] Run frontend build.
  - [x] Run `VERIFY_DOCKER_BUILD=1 scripts/verify.sh`.
  - [x] Smoke test backend chat orchestration with ToolSearch enabled.
  - [ ] Smoke test minikube read-only Kubernetes tools.

## Done Definition

1. `project_document/specs/toolsearch-mcp/*` documents are updated.
2. `config/tool_catalog.json` contains the full restored catalog.
3. ToolSearch MCP server starts locally through stdio.
4. Backend health shows ToolSearch connected.
5. Chat can discover tools through ToolSearch before selecting real execution.
6. Write/dangerous tools require permission and confirmation.
7. Audit logs show search and execution traceability.
