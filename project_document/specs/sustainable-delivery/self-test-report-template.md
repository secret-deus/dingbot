# Self-Test Report Template

## Summary

- Slice:
- Date:
- Tester:
- Result: PASS / FAIL / PARTIAL

## Environment

- Branch:
- Backend:
- Frontend:
- ToolSearch:
- Docker runtime:
- LLM mode:
- DingTalk notification:

## Automated Checks

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Backend tests | `cd backend-v2 && poetry run pytest` |  |  |
| Frontend build | `cd frontend-v3 && npm run build` |  |  |
| ToolSearch tests | `cd mcp-servers/toolsearch && npm test` |  |  |
| ToolSearch audit | `cd mcp-servers/toolsearch && npm audit --omit=dev` |  |  |
| Compose config | `docker compose config` |  |  |
| Compose build | `docker compose build` |  |  |
| Diff whitespace | `git diff --check` |  |  |

## Manual Smoke

| Scenario | Result | Evidence |
| --- | --- | --- |
| Login |  |  |
| Chat ToolSearch candidates |  |  |
| MCP config health |  |  |
| Scheduler manual run |  |  |
| Scheduler execution history |  |  |
| DingTalk notification |  |  |

## Issues

| Severity | Issue | Owner | Status |
| --- | --- | --- | --- |
|  |  |  |  |

## Decision

- Release decision:
- Follow-up tasks:
