# Release Candidate Hardening Spec - Design

## Overview

This slice converts the current local MVP into a release-candidate checkpoint. It does
not add another product capability. It verifies that the existing product capability can
be started, tested, documented, and handed off repeatably.

The target flow is:

```text
Clean worktree
  -> documented local runtime available
  -> scripts/verify.sh passes
  -> Docker Compose build/config/start smoke passes
  -> browser smoke covers login, MCP config, chat, scheduler
  -> secret scan and git status are clean
  -> RC self-test report records evidence and skipped checks
```

## Proposed File Layout

```text
project_document/specs/release-candidate-hardening/
  requirements.md
  design.md
  tasks.md
  self-test-report-rc1.md
  screenshots/
    login-rc1.png
    mcp-config-rc1.png
    chat-toolsearch-rc1.png
    scheduler-rc1.png
```

The `screenshots/` directory is optional. If browser automation cannot capture reliable
screenshots, written smoke notes in `self-test-report-rc1.md` are acceptable as long as
they include exact URLs, expected text, and API evidence.

## Components

### 1. Local Verification Gate

Owner files:

- `scripts/verify.sh`
- `README.md`
- `config/README.md`
- `mcp-servers/toolsearch/package-lock.json`

Design:

- Keep `scripts/verify.sh` as the release gate.
- Prefer fixing local toolchain lookup in docs or script only if the failure is
  reproducible from a clean shell.
- Preserve existing checks: backend pytest, frontend build, ToolSearch tests, ToolSearch
  production audit, Compose config, optional Compose build, and `git diff --check`.

### 2. Docker Compose Runtime Gate

Owner files:

- `docker-compose.yml`
- `backend-v2/Dockerfile`
- `frontend-v3/Dockerfile`
- `frontend-v3/nginx.conf`
- `project_document/specs/release-candidate-hardening/self-test-report-rc1.md`

Design:

- First run `docker compose config`.
- Then run `docker compose build`.
- Then run `docker compose up --build`.
- Verify `http://127.0.0.1:3000/spa/` loads and backend health responds.
- Verify backend container logs show ToolSearch startup and catalog stats.
- Do not mount or copy real secrets into committed files.

### 3. Browser Smoke Gate

Owner files:

- `frontend-v3/src/views/Login.vue`
- `frontend-v3/src/views/MCPConfig.vue`
- `frontend-v3/src/views/Chat.vue`
- `frontend-v3/src/views/Scheduler.vue`
- `project_document/specs/release-candidate-hardening/self-test-report-rc1.md`

Design:

- Use the in-app browser or Playwright to verify visible page behavior.
- The smoke does not need deep E2E automation in this slice; it needs deterministic
  evidence that the core views render and critical actions work.
- Chat smoke should use a discovery-only prompt to avoid executing live cloud reads when
  the goal is candidate rendering.
- Scheduler smoke should run a harmless task. If the LLM provider is disabled or busy,
  a failed execution with a clear error is acceptable as long as execution history records
  status, error, start time, and finish time.

### 4. Secret And State Hygiene Gate

Owner files:

- `.gitignore`
- `config/README.md`
- `project_document/specs/release-candidate-hardening/self-test-report-rc1.md`

Design:

- Use `git status --short` to classify all changed files before handoff.
- Use targeted `rg` scans against staged/report files for AccessKey, JWT, webhook URL,
  kubeconfig, and local DB paths.
- Treat live credentials as runtime-only evidence. The report may state that credentials
  were used, but must not include credential values.

### 5. RC Report

Owner files:

- `project_document/specs/sustainable-delivery/self-test-report-template.md`
- `project_document/specs/release-candidate-hardening/self-test-report-rc1.md`

Design:

- Reuse the existing report shape.
- Record skipped checks explicitly. Skipped real-resource checks are acceptable when the
  current account lacks ECS/LB/SLS resources.
- Include branch, commit, runtime ports, command outputs, screenshots or smoke notes, and
  residual risk.

## Compatibility Boundary

1. No product behavior should change unless a smoke test exposes a release blocker.
2. Existing ToolSearch catalog counts and Aliyun tool availability semantics must remain
   stable.
3. Runtime secret handling must remain server-side and masked.
4. Docker Compose must continue serving the SPA under `/spa/`.
5. Existing `scripts/verify.sh` behavior should be extended only when it reduces local
   release friction without hiding failures.

## Error Handling

| Failure | Handling |
| --- | --- |
| Docker unavailable | Mark Compose build/up as skipped with the exact reason; keep local gate evidence. |
| Port conflict | Record occupied port and rerun on documented alternate ports only for dev-server smoke; Compose smoke should keep mapped ports unless user approves changes. |
| LLM provider busy | Keep ToolSearch candidate smoke as the primary chat UI check and record model-service status separately. |
| Empty Aliyun account | Treat empty list results as PASS for list tools, but keep detail/metrics/health tools as skipped without concrete IDs. |
| DingTalk webhook missing | Mark DingTalk notification smoke skipped and record that `DINGTALK_WEBHOOK_URL` was not set. |

## Verification Strategy

Automated:

```bash
PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH scripts/verify.sh
docker compose config
docker compose build
```

Runtime/API:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/api/v2/config/health
```

Browser:

- Login page renders and accepts `admin/admin`.
- MCP config shows ToolSearch connected and catalog stats.
- Chat page renders ToolSearch execution details for an Aliyun discovery prompt.
- Scheduler page creates a smoke task, runs it manually, and shows execution history.

Hygiene:

```bash
git status --short
git diff --check
rg -n "LTAI|AccessKey Secret|eyJ[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+\\.[a-zA-Z0-9_-]+|DINGTALK_WEBHOOK_URL=https?://" <changed-files>
```

## Rollback Surface

This slice should mostly add docs and reports. If a real release blocker requires code,
that fix should be committed separately from the RC report so rollback remains clear.
