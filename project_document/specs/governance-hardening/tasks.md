# Governance Hardening Spec - Tasks

## Current Status

- [x] RC1 local hardening is complete.
- [x] Audit rows already exist through middleware and tool execution.
- [x] AccessControl page currently reads `/config/audit` but has only static role data
  and no useful audit filters.

## Implementation Backlog

- [x] 1. Backend audit query contract
  - [x] Add failing tests for audit filtering, response shape, and viewer denial.
  - [x] Extend `AuditRepository.query()` with `resource`, `resource_id`, and `result`.
  - [x] Change `/config/audit` to require admin.
  - [x] Return `resource_id` and `details`.
  - [x] Verify focused backend tests.

- [x] 2. Frontend audit filter UI
  - [x] Extend `AuditLog` and `systemApi.auditLogs` types.
  - [x] Add filter state and controls to `AccessControl.vue`.
  - [x] Ensure apply/clear reloads the table.
  - [x] Verify frontend build.

- [x] 3. Documentation and rollout
  - [x] Update `project_document/DELIVERY_PLAN.md` current priority/risk state.
  - [x] Run `git diff --check`.
  - [x] Run targeted secret scan on changed files.
  - [x] Commit locally without push.

## Verification

- [x] `cd backend-v2 && poetry run pytest tests/test_audit_filters.py -q`
- [x] `cd frontend-v3 && PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH npm run build`
- [x] `git diff --check`
- [x] Targeted secret scan on changed files

## Done Definition

1. Admin can filter audit rows by actor/action/resource/resource_id/result.
2. Viewer receives `403` from `/api/v2/config/audit`.
3. Audit API returns `resource_id` and `details`.
4. AccessControl exposes apply/clear filters without pretending user writes exist.
5. No secrets or local state are staged.
