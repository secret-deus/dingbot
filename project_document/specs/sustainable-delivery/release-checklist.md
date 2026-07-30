# Release Checklist

Use this checklist before handing a delivery slice to test or committing a release branch.

## Scope

- [ ] `project_document/specs/**/tasks.md` reflects the completed slice.
- [ ] README and config docs match the implemented behavior.
- [x] Runtime secrets, kubeconfig, cloud credentials, logs, and SQLite databases are not staged.
- [ ] Production runtime sets `APP_ENV=production`, a non-placeholder `SECRET_KEY`,
      concrete `CORS_ALLOW_ORIGINS`, and a non-default bootstrap admin password
      or disables bootstrap admin creation.
- [ ] Browser screenshots or smoke notes are updated for UI changes.

## Verification

Run the CI-equivalent local gate:

```bash
scripts/verify.sh
```

Run Docker image build when the local Docker runtime is available:

```bash
VERIFY_DOCKER_BUILD=1 scripts/verify.sh
```

Expected checks:

- `cd backend-v2 && poetry run pytest`
- `cd frontend-v3 && npm run build`
- `cd mcp-servers/toolsearch && npm test`
- `cd mcp-servers/toolsearch && npm audit --omit=dev`
- `docker compose config`
- `docker compose build` when explicitly enabled
- `git diff --check`

## Runtime Smoke

- [ ] Start backend with a non-secret local `.env`.
- [ ] Start frontend or Docker Compose.
- [ ] Login with a local admin account.
- [ ] Open chat and verify ToolSearch candidate cards render when ToolSearch is enabled.
- [ ] Open MCP config and verify ToolSearch health/catalog stats.
- [ ] Create a scheduled task and run it manually.
- [ ] Confirm execution history records status, result, error, start time, and finish time.
- [ ] If `DINGTALK_WEBHOOK_URL` is set, verify a test notification reaches the target group.

## Handoff

- [ ] Fill `self-test-report-template.md` for the slice.
- [x] Record skipped checks with concrete reasons.
- [x] Review `git status --short` and classify files as commit now, fix then commit, or ignore.
- [ ] Commit only source, specs, generated frontend assets, and report screenshots that are intentionally part of the deliverable.
