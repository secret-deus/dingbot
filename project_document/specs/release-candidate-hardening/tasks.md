# Release Candidate Hardening Spec - Tasks

## Current Status

- [x] Baseline local MVP is complete on `codex/refactor-baseline`.
- [x] ToolSearch catalog currently has `68` tools, `68` executable, `0` catalog-only.
- [x] Aliyun read-only adapter currently exposes `13/13` tools when credentials are present.
- [x] Latest local release gate passed with backend tests, frontend build, ToolSearch tests,
  ToolSearch production audit, Compose config, and diff check.
- [x] Current branch is local-only and ahead of origin; no push is part of this slice unless
  explicitly requested.

## Implementation Backlog

- [x] 1. Stabilize local release command entrypoint
  - [x] Verify `PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH scripts/verify.sh`
    from a clean shell.
  - [x] Decide whether to document the nvm Node path or make `scripts/verify.sh` select it
    automatically when present.
  - [x] Keep failures visible; do not silently skip ToolSearch tests or audit.
  - [x] Update README/config docs only if the command path changes.

- [x] 2. Run Docker Compose release smoke
  - [x] Run `docker compose config`.
  - [x] Run `docker compose build`.
  - [x] Run `docker compose up --build`.
  - [x] Verify backend health in the Compose runtime.
  - [x] Verify frontend is reachable at `http://127.0.0.1:3010/spa/` with
    `FRONTEND_PORT=3010` because local dev frontend owns `3000`.
  - [x] Verify backend container logs show ToolSearch startup and catalog counts.
  - [x] Stop Compose cleanly and record the command used.

- [x] 3. Browser smoke core pages
  - [x] Login as `admin/admin`.
  - [x] Open `/spa/mcp-config` and verify ToolSearch connected, catalog total, executable
    count, catalog-only count, and Aliyun tool count.
  - [x] Open `/spa/chat` and submit:
    `只搜索工具：有哪些工具可以查询阿里云轻量应用服务器？先不要执行具体资源查询。`
  - [x] Verify ToolSearch execution details render and the top candidate includes
    `aliyun-swas-list-instances`.
  - [x] Open `/spa/scheduler`, create a harmless RC smoke task, run it manually, and verify
    execution history fields.
  - [x] Capture screenshots or write exact smoke notes under this spec directory.

- [x] 4. Credential and state hygiene check
  - [x] Confirm runtime credentials are held only in ignored local config or process
    environment.
  - [x] Run `git status --short` and classify every changed file.
  - [x] Run a targeted secret scan on staged/report files.
  - [x] Confirm no SQLite DB, logs, kubeconfig, AccessKey, JWT, or webhook token is staged.
  - [x] Record credential rotation expectation for any key pasted during manual testing.

- [x] 5. Real-resource gap verification
  - [x] If an ECS instance ID is available, verify `aliyun-ecs-describe-instance`.
  - [x] If an ECS instance ID is available, verify `aliyun-cms-get-ecs-metrics`.
  - [x] If an LB instance ID is available, verify `aliyun-lb-describe-health`.
  - [x] If SLS mappings are available, verify `aliyun-sls-list-logstores`,
    `aliyun-sls-query-logs`, and `aliyun-sls-query-error-summary`.
  - [x] If inputs are not available, mark each check skipped with the missing input.

- [x] 6. Write RC self-test report
  - [x] Create `project_document/specs/release-candidate-hardening/self-test-report-rc1.md`
    from the sustainable-delivery report shape.
  - [x] Include branch, commit, runtime ports, automated checks, browser smoke, Compose
    result, DingTalk state, skipped checks, and residual risks.
  - [x] Link or embed screenshots/smoke notes.
  - [x] Update `project_document/DELIVERY_PLAN.md` current priority status.

- [x] 7. Local commit only
  - [x] Run final `git diff --check`.
  - [x] Run final secret scan against changed files.
  - [x] Commit source/docs/report changes locally.
  - [x] Do not push unless explicitly requested.

## Verification

- [x] `PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH scripts/verify.sh`
- [x] `docker compose config`
- [x] `docker compose build`
- [x] `docker compose up --build`
- [x] Browser smoke for login, MCP config, chat ToolSearch candidates, and scheduler
- [x] `git diff --check`
- [x] Targeted secret scan on changed files

## Done Definition

1. The RC self-test report exists and distinguishes PASS, FAIL, and SKIP checks.
2. Docker Compose runtime is verified or skipped with a concrete local blocker.
3. Browser smoke evidence covers login, MCP config, chat candidate cards, and scheduler.
4. ToolSearch and Aliyun readiness counts are recorded from the runtime under test.
5. Real-resource gaps are explicit and actionable.
6. No runtime secret or local state is staged.
7. The branch remains local unless the user asks to push.
