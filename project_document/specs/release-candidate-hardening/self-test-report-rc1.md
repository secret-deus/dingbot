# Self-Test Report - RC1 Release Candidate Hardening

## Summary

- Slice: RC1 Release Candidate Hardening
- Date: 2026-05-25 18:50 CST
- Tester: Codex
- Branch: `codex/refactor-baseline`
- Base commit before this slice: `d487180`
- Result: PASS with skipped real-resource checks

## Environment

- Backend: `backend-v2` FastAPI
- Frontend: `frontend-v3` Vue/Vite
- ToolSearch catalog: `68` tools, `68` executable, `0` catalog-only
- Compose ports: backend `8010 -> 8000`, frontend `3010 -> 80`
- Local dev ports: backend `8001`, frontend `3000`
- LLM mode: configured local runtime
- DingTalk notification: scheduler notification disabled for RC smoke

## Automated Checks

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Local release gate | `PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH scripts/verify.sh` | PASS | Backend `63 passed`, frontend build PASS, ToolSearch `7 passed`, audit `0 vulnerabilities`, Compose config PASS, diff check PASS |
| ToolSearch stdio regression | `cd backend-v2 && poetry run pytest tests/test_mcp_stdio_toolsearch.py -q` | PASS | `4 passed`; covers host absolute Node/cwd/env paths and container root layout |
| Targeted lint | `cd backend-v2 && poetry run ruff check app/mcp/manager.py tests/test_mcp_stdio_toolsearch.py` | PASS | No lint errors |
| Compose config | `BACKEND_PORT=8010 FRONTEND_PORT=3010 docker compose config` | PASS | Host ports are configurable to avoid local port conflicts |
| Compose build | `BACKEND_PORT=8010 FRONTEND_PORT=3010 docker compose build` | PASS | Docker Hub TLS mismatch was bypassed by pre-pulling/tagging base images from mirror, then building from local cache |
| Compose up | `BACKEND_PORT=8010 FRONTEND_PORT=3010 docker compose up --build -d` | PASS | Backend healthy, frontend reachable |
| Compose backend health | `curl http://127.0.0.1:8010/health` | PASS | `{"status":"healthy","version":"3.0.0"}` |
| Compose MCP health | `curl http://127.0.0.1:8010/api/v2/config/health` | PASS | ToolSearch connected, `4` stdio tools, catalog total `68` |
| Compose shutdown | `BACKEND_PORT=8010 FRONTEND_PORT=3010 docker compose down` | PASS | Frontend/backend containers and network removed |

## Manual Smoke

| Scenario | Result | Evidence |
| --- | --- | --- |
| Login | PASS | Browser login as `admin/admin` reached `/spa/dashboard` |
| Dashboard status | PASS | Dashboard showed MCP tools `4/69` in Compose runtime |
| MCP config health | PASS | `/spa/mcp-config` showed ToolSearch `已连接`, catalog `68`, executable `68`, catalog-only `0`, Aliyun `0/13` in Compose |
| Chat ToolSearch candidates | PASS | API/browser smoke session `rc1 toolsearch smoke`; `toolsearch` returned `aliyun-swas-list-instances` as top direct hit |
| Scheduler manual run | PASS | Task `rc1 scheduler smoke` ran manually with `status=success`; notification skipped because disabled |
| Scheduler execution history | PASS | `/spa/scheduler` showed paused smoke task, last run time, result text, and notification skipped reason |
| Screenshot evidence | SKIP | Browser DOM snapshots were captured; screenshot capture timed out in the browser plugin and was not used as evidence |

## Real Resource Checks

| Check | Result | Notes |
| --- | --- | --- |
| SWAS list | PASS | Local backend `8001` with runtime credentials exposed `aliyun-swas-list-instances`; readonly query in `cn-beijing` returned `1` item. Resource IDs and IPs intentionally omitted. |
| ECS describe | SKIP | No ECS instance ID provided; user stated the account currently only has lightweight application server resources. |
| ECS metrics | SKIP | No ECS instance ID provided. |
| LB health | SKIP | No load balancer instance ID provided. |
| SLS list/query/error summary | SKIP | No SLS mapping provided. |

## Hygiene

| Item | Result | Notes |
| --- | --- | --- |
| Credentials in tracked files | PASS | No AccessKey, JWT, webhook token, kubeconfig, DB, or log file is part of the source changes. |
| Runtime credentials | PASS | Cloud credentials remain in ignored local config or process environment only. |
| Local state | PASS | Browser/API smoke created local DB rows only under ignored runtime state. |
| Rotation expectation | ACTION | The AccessKey used during manual testing was pasted into chat and should be rotated before any shared or long-lived environment use. |

## Issues

| Severity | Issue | Owner | Status |
| --- | --- | --- | --- |
| Medium | Compose uses mounted local `config/mcp_config.json`; host absolute Node/cwd/env paths broke inside the container. | Backend MCP manager | Fixed by normalizing stdio command, cwd, args, and path-like env values against the runtime repo root. |
| Low | Compose runtime had no kubeconfig or cloud credentials, so built-in tools were registered but unavailable. | Local environment | Expected for this smoke; local backend `8001` verified cloud availability separately. |
| Low | Browser screenshot capture timed out. | Browser tooling | DOM/API evidence used instead; no product bug observed. |

## Decision

- Release decision: PASS for local RC1 hardening.
- Follow-up tasks: rotate the pasted AccessKey, then collect ECS/LB/SLS checks once concrete resource IDs or mappings are available.
