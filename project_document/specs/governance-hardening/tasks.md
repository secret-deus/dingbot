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

- [x] 4. Backend user management API
  - [x] Add failing tests for admin list/create/update and non-admin denial.
  - [x] Add `UserRepository.list_all()`.
  - [x] Add `GET /auth/users`.
  - [x] Add `PATCH /auth/users/{username}`.
  - [x] Reject self-demotion and self-deactivation.
  - [x] Enforce current user role and active state on authenticated routes.
  - [x] Verify focused backend tests.

- [x] 5. Frontend user management UI
  - [x] Add user account API/types.
  - [x] Load real users in `AccessControl.vue`.
  - [x] Enable new-user modal.
  - [x] Add per-row role/active updates.
  - [x] Keep policy descriptions read-only.
  - [x] Verify frontend build.

## Verification

- [x] `cd backend-v2 && poetry run pytest tests/test_audit_filters.py -q`
- [x] `cd frontend-v3 && PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH npm run build`
- [x] `git diff --check`
- [x] Targeted secret scan on changed files
- [x] `cd backend-v2 && poetry run pytest tests/test_user_management.py tests/test_audit_filters.py -q`
- [x] `cd frontend-v3 && PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH npm run build`
- [x] `cd backend-v2 && poetry run pytest -q`
- [x] Browser smoke on `/spa/access-control` with temp SQLite backend

## Done Definition

1. Admin can filter audit rows by actor/action/resource/resource_id/result.
2. Viewer receives `403` from `/api/v2/config/audit`.
3. Audit API returns `resource_id` and `details`.
4. AccessControl exposes apply/clear filters without pretending user writes exist.
5. No secrets or local state are staged.
6. Admin can list, create, and update users.
7. Non-admin user management access is denied.
8. Admin cannot demote or deactivate their own account.
9. Disabled users cannot keep using an existing token.
