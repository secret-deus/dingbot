# Self-Test Report - Aliyun Read-Only MCP Slice

## Summary

- Slice: Aliyun read-only MCP adapter, ToolSearch discovery, and delivery documentation
- Date: 2026-05-25
- Tester: Codex
- Result: PASS

## Environment

- Branch: `codex/refactor-baseline`
- Backend: `backend-v2` on `127.0.0.1:8001`
- Frontend: `frontend-v3` on `127.0.0.1:3000/spa/`
- ToolSearch: stdio MCP, catalog total `68`, executable `68`, catalog-only `0`
- Docker runtime: compose config verified; image build not rerun in this slice
- LLM mode: configured local provider; chat smoke used ToolSearch discovery-only prompt
- DingTalk notification: disabled in local runtime

## Automated Checks

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Backend tests | `cd backend-v2 && poetry run pytest` | PASS | 63 passed, 1 deprecation warning |
| Frontend build | `cd frontend-v3 && npm run build` | PASS | Vite build completed |
| ToolSearch tests | `cd mcp-servers/toolsearch && npm test` | PASS | 7 passed |
| ToolSearch audit | `cd mcp-servers/toolsearch && npm audit --omit=dev` | PASS | 0 vulnerabilities after `qs` lockfile update |
| Compose config | `docker compose config` | PASS | Compose config rendered successfully |
| Compose build | `docker compose build` | SKIP | Not rerun; this slice did not change Docker build files |
| Diff whitespace | `git diff --check` | PASS | No whitespace errors |
| Scoped Python lint | `cd backend-v2 && poetry run ruff check app/services/chat_service.py tests/test_chat_toolsearch_orchestration.py` | PASS | Chat orchestration change is clean |

## Manual Smoke

| Scenario | Result | Evidence |
| --- | --- | --- |
| Login | PASS | Local admin token worked for API/browser flows |
| Chat ToolSearch candidates | PASS | Discovery-only prompt for Aliyun lightweight application server tools rendered ToolSearch execution details and returned `aliyun-swas-list-instances` as the top candidate |
| MCP config health | PASS | API health showed ToolSearch connected, catalog total `68`, builtin tools `69`, builtin available `69`, unavailable `0` after credential-backed restart |
| Scheduler manual run | SKIP | Covered by existing S4 report; this slice did not change scheduler behavior |
| Scheduler execution history | SKIP | Covered by existing S4 report |
| DingTalk notification | SKIP | `DINGTALK_WEBHOOK_URL` is not set in local runtime |

## Issues

| Severity | Issue | Owner | Status |
| --- | --- | --- | --- |
| Low | `scripts/verify.sh` requires a working Node.js on `PATH`; Homebrew Node on this machine has a broken `llhttp` linkage, so the successful gate used the local nvm Node 24 path. | Project | Documented in command evidence |
| Low | Python test suite emits one `datetime.utcnow()` deprecation warning. | Project | Existing warning, not touched in this slice |

## Decision

- Release decision: PASS for local Aliyun read-only MCP and ToolSearch discovery slice.
- Follow-up tasks: rerun Docker image build before a release candidate; verify SLS/detail/health tools when concrete resource IDs or SLS mappings are available.
