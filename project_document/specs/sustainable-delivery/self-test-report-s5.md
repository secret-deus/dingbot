# Self-Test Report - S5 Release Pipeline

## Summary

- Slice: S5 Release Pipeline and Docker ToolSearch Runtime
- Date: 2026-05-06
- Tester: Codex
- Result: PASS

## Current Status Update - 2026-05-18

- ToolSearch production audit is currently clean after updating the locked transitive `hono` version to `4.12.19`.
- Tool execution recovery is currently complete for the generated catalog: `55` total, `55` executable, `0` catalog-only.
- Local full gate passed on 2026-05-18: backend 41 tests, frontend build, ToolSearch 7 tests, ToolSearch audit, Compose config, and diff check.
- Full Compose/browser smoke remains a release-candidate validation item.

## Environment

- Branch: `codex/refactor-baseline`
- Backend: `backend-v2` FastAPI
- Frontend: `frontend-v3` Vue/Vite
- ToolSearch: `mcp-servers/toolsearch`
- Docker runtime: available; backend image built as `ding-robot-backend`
- LLM mode: local tests use mocked or disabled LLM paths
- DingTalk notification: mock-backed tests

## Automated Checks

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Backend tests | `cd backend-v2 && poetry run pytest` | PASS | 17 passed |
| Frontend build | `cd frontend-v3 && npm run build` | PASS | Vite build completed without chunk warning |
| ToolSearch tests | `cd mcp-servers/toolsearch && npm test` | PASS | 6 passed |
| ToolSearch audit | `cd mcp-servers/toolsearch && npm audit --omit=dev` | PASS | 0 vulnerabilities |
| Compose config | `docker compose config` | PASS | Backend build context is repository root |
| Compose build | `VERIFY_DOCKER_BUILD=1 scripts/verify.sh` | PASS | Images `ding-robot-backend` and `ding-robot-frontend` built |
| Docker ToolSearch runtime | `docker run --rm --entrypoint sh ding-robot-backend -c 'node --version && test -f /app/mcp-servers/toolsearch/dist/src/index.js && cd /app/mcp-servers/toolsearch && node -e "import(\"@modelcontextprotocol/sdk/server/mcp.js\").then(() => console.log(\"toolsearch deps ok\"))"'` | PASS | Node v22.22.2 and MCP SDK import verified |
| Diff whitespace | `git diff --check` | PASS | No whitespace errors |

## Manual Smoke

| Scenario | Result | Evidence |
| --- | --- | --- |
| Login | PASS | Covered by S3 browser smoke |
| Chat ToolSearch candidates | PASS | Covered by S3 browser smoke and backend orchestration tests |
| MCP config health | PASS | Covered by S3 browser smoke and backend health tests |
| Scheduler manual run | PASS | Covered by S4 API/browser smoke |
| Scheduler execution history | PASS | Covered by S4 API/browser smoke |
| DingTalk notification | PASS | Mock-backed S4 tests |

## Issues

| Severity | Issue | Owner | Status |
| --- | --- | --- | --- |
| Medium | Full `docker compose up --build` browser smoke was not rerun in S5 because the changed scope is backend image packaging and release gates. | Project | Follow-up when validating an end-to-end release candidate |
| Medium | Historical frontend Docker build `npm ci` dependency advisory state. | Project | Superseded by the 2026-05-18 local gate; ToolSearch production audit is clean. |

## Decision

- Release decision: PASS for S5 release pipeline and backend ToolSearch Docker runtime.
- Follow-up tasks: run full Compose browser smoke and real ECS credential smoke before a release candidate.
