# Sustainable Delivery Spec - Tasks

## Current Status

- [x] Assessed current repository state.
- [x] Confirmed `backend-v2` and `frontend-v3` are the active code paths.
- [x] Confirmed `archived/` contains old implementations.
- [x] Confirmed frontend build works but metadata was ignored by git.
- [x] Confirmed backend pytest previously collected zero tests.
- [x] Confirmed `docker-compose.yml` referenced a missing frontend Dockerfile.

## S0 Repository Baseline

- [x] Update `.gitignore` so `frontend-v3` dependency and TypeScript metadata can be versioned.
- [x] Add `frontend-v3/Dockerfile`.
- [x] Add Nginx config for `/spa/` serving and `/api/` proxying.
- [x] Add backend and frontend `.dockerignore` files.
- [x] Update backend Dockerfile to use the current Poetry install flag.
- [x] Add minimal backend public endpoint tests.
- [x] Update root `README.md` to current v3 structure and commands.
- [x] Add `project_document/DELIVERY_PLAN.md`.
- [x] Add this sustainable delivery spec.
- [x] Run backend pytest.
- [x] Run frontend build.
- [x] Run Docker Compose config validation.
- [x] Review git status for commit/ignore split.

## S1 ToolSearch MVP

- [x] Generate `config/tool_catalog.json` from old MCP config and current built-ins.
- [x] Preserve the 21 old catalog tools as searchable entries.
- [x] Mark unavailable executable handlers as `catalog_only`.
- [x] Create `mcp-servers/toolsearch` TypeScript package.
- [x] Implement `toolsearch`, `tool_get`, `tool_categories`, and `tool_reload_catalog`.
- [x] Add ToolSearch unit tests for ranking, synonyms, and category filters.
- [x] Add ToolSearch stdio MCP integration test.
- [x] Add backend MCP stdio integration smoke tests.

## S2 Execution Governance

- [x] Add tool `dangerLevel` and execution policy checks before execution.
- [x] Add role-based permission checks to tool execution.
- [x] Require explicit confirmation for write and dangerous tools.
- [x] Persist audit logs for search query, selected tool, executed tool, caller, risk, and result.
- [x] Add backend tests for denied and approved execution paths.

## S3 Frontend Workflow

- [x] Add backend ToolSearch-first chat orchestration test.
- [x] Show compact ToolSearch candidate cards in chat.
- [x] Show catalog totals and ToolSearch health in MCP config page.
- [x] Separate server lifecycle from "include tools in this conversation".
- [x] Add browser smoke test evidence for login, chat, MCP config, scheduler, and audit pages.
- [x] Address large frontend chunk warning with route-level or vendor chunk splitting.

## S4 Scheduler And DingTalk

- [x] Implement scheduler runner using persisted scheduled tasks.
- [x] Record task execution status, result, error, start time, and finish time.
- [x] Add DingTalk webhook notification service.
- [x] Add mock-backed tests for successful and failed notification.
- [x] Reflect execution state in frontend scheduler page.

## S5 Release Pipeline

- [x] Add CI-equivalent local verification script.
- [x] Add release checklist.
- [x] Add self-test report template.
- [x] Package ToolSearch runtime into the backend Docker image.
- [x] Add root `.dockerignore` for Docker build context hygiene.
- [x] Document local and Docker ToolSearch runtime paths.
- [x] Run `docker compose build backend`.
- [x] Verify ToolSearch Node runtime and production dependency import inside the backend image.
- [x] Add S5 self-test report.
- [x] Add S5 code review report.

## Verification

- [x] `cd backend-v2 && poetry run pytest`
- [x] `cd frontend-v3 && npm run build`
- [x] `cd mcp-servers/toolsearch && npm test`
- [x] `cd mcp-servers/toolsearch && npm audit --omit=dev`
- [x] `docker compose config`
- [x] `git diff --check`
- [x] `docker compose build backend`
- [x] `docker run --rm --entrypoint sh ding-robot-backend -c 'node --version && test -f /app/mcp-servers/toolsearch/dist/src/index.js && cd /app/mcp-servers/toolsearch && node -e "import(\"@modelcontextprotocol/sdk/server/mcp.js\").then(() => console.log(\"toolsearch deps ok\"))"'`

## Done Definition

1. A clean checkout contains all dependency and build metadata.
2. Runtime secrets and local state remain ignored.
3. Backend pytest collects and passes at least the baseline tests.
4. Frontend build passes.
5. Docker Compose references existing build files.
6. Future delivery slices are tracked in specs with verification gates.
