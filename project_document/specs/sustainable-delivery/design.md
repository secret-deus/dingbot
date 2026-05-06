# Sustainable Delivery Spec - Design

## Overview

The delivery system has three layers:

1. Repository baseline: dependency metadata, Docker build files, ignore rules, and README.
2. Verification baseline: backend pytest and frontend Vite build.
3. Planning baseline: spec documents and a delivery roadmap that define the next slices.

This keeps feature development independent from delivery hygiene while still requiring every feature to pass the same local gates.

## Repository Rules

Versioned:

- `backend-v2/pyproject.toml`
- `backend-v2/poetry.lock`
- `frontend-v3/package.json`
- `frontend-v3/package-lock.json`
- `frontend-v3/tsconfig.json`
- `frontend-v3/tsconfig.node.json`
- `config/*.example.json`
- `config/README.md`
- `project_document/specs/**`

Ignored:

- Runtime `.env` files
- Runtime `config/*.json`
- SQLite databases
- Logs and caches
- Kubeconfig and cloud credentials
- `node_modules/`

## Container Design

Backend:

- Built from `backend-v2/Dockerfile` with the repository root as Docker build context.
- Exposes FastAPI on port `8000`.
- Mounts `backend-v2/data`, `backend-v2/logs`, and root `config`.
- Builds ToolSearch in a Node 22 stage and copies the runtime `dist` plus production `node_modules` into `/app/mcp-servers/toolsearch`.
- Runs FastAPI from `/app`, so the relative ToolSearch command path `mcp-servers/toolsearch/dist/src/index.js` works in both local repo root and Docker runtime.

Frontend:

- Built from `frontend-v3/Dockerfile`.
- Uses Node 22 for build and Nginx for runtime.
- Serves the built SPA under `/spa/` to match the Vite `base`.
- Proxies `/api/` to `http://backend:8000`.

## Verification Design

Baseline commands:

```bash
cd backend-v2 && poetry run pytest
cd frontend-v3 && npm run build
```

The initial backend test focuses on public endpoints and app startup. Later slices should add targeted tests:

- Auth/session API tests for user workflows.
- MCP manager tests for ToolSearch and execution boundaries.
- Scheduler runner tests for task execution.
- Frontend build plus browser smoke tests for UI changes.

## Spec Workflow

Every major slice follows:

```text
requirements.md -> design.md -> tasks.md -> implementation -> verification -> docs update
```

The `tasks.md` file is the operational checklist. It must include:

- Current status
- Implementation tasks
- Verification tasks
- Done definition

## Rollout Slices

S0 Repository Baseline:

- Fix ignored frontend metadata.
- Add missing frontend Dockerfile.
- Add minimal backend tests.
- Update README and delivery plan.

S1 ToolSearch MVP:

- Generate `config/tool_catalog.json`.
- Add `mcp-servers/toolsearch`.
- Add backend stdio MCP integration smoke coverage.

S2 Execution Governance:

- Add risk classification.
- Add IAM checks before tool execution.
- Add confirmation for write/dangerous tools.
- Persist audit details for search and execution.

S3 User Workflow:

- Show ToolSearch candidates in chat.
- Improve MCP config status and catalog stats.
- Run browser smoke tests.

S4 Automation:

- Implement scheduler runner.
- Implement DingTalk webhook notification.
- Test execution history and notification failures.

S5 Release Hardening:

- Add CI-equivalent local command set.
- Add self-test report template.
- Add release checklist.
- Verify Docker runtime packaging for ToolSearch.
- Split frontend chunks if bundle remains large.
