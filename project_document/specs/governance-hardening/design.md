# Governance Hardening Spec - Design

## Architecture

The audit filter capability stays inside the existing governance ownership boundaries:

- `backend-v2/app/db/repositories/audit_repo.py` owns audit query construction.
- `backend-v2/app/api/config.py` owns the `/config/audit` HTTP contract.
- `frontend-v3/src/views/AccessControl.vue` owns the permissions/audit screen.
- `frontend-v3/src/api/client.ts` and `frontend-v3/src/types/index.ts` own frontend
  API typing.

No new service layer is required for this slice because the endpoint is a thin query over
the existing `AuditLog` table.

## API Contract

`GET /api/v2/config/audit`

Query parameters:

- `actor?: string`
- `action?: string`
- `resource?: string`
- `resource_id?: string`
- `result?: string`
- `limit?: number`
- `offset?: number`

Authorization:

- Requires `admin`.

Response row shape:

```json
{
  "id": 1,
  "actor": "admin",
  "action": "api.get",
  "resource": "/api/v2/config/dashboard",
  "resource_id": null,
  "result": "success",
  "ip": "127.0.0.1",
  "details": {"status_code": 200},
  "created_at": "2026-05-25 18:00:00"
}
```

## Query Semantics

- `actor`, `action`, `resource`, and `resource_id` use SQL `contains` matching.
- `result` uses exact matching.
- Empty strings are ignored.
- Ordering remains newest-first.
- Existing `limit` and `offset` behavior remains unchanged.

## Frontend

The permissions page adds a compact filter bar above the audit table:

- Actor input
- Action input
- Resource input
- Result segmented/select control
- Apply and clear buttons

The page still shows role users and policies as read-only static context. User management
is intentionally left for a later slice.

## User Management Slice

The next slice keeps account administration under the existing auth API owner:

- `GET /api/v2/auth/users` lists users and requires admin.
- `POST /api/v2/auth/register` remains the create endpoint and requires admin.
- `PATCH /api/v2/auth/users/{username}` updates display name, role, and active state.

Self-protection rules live in the API layer because they depend on the current authenticated
admin, not only the persisted user row:

- The current admin cannot change their own role.
- The current admin cannot deactivate their own account.
- Authenticated route checks reload the user row so role changes and inactive state apply
  to existing tokens immediately.

The frontend switches the static user examples to real backend users. It keeps policy
descriptions read-only and exposes only user create/update controls:

- New user modal for username/password/display name/role.
- Per-row role select.
- Per-row active switch.
- Save button per row.

Password reset, hard delete, groups, and fine-grained grants remain out of scope.

## Compatibility

- Existing callers using only `actor`, `action`, `limit`, and `offset` continue to work.
- Admin route access matches the frontend router's existing admin-only AccessControl route.
- Audit data stored before this slice remains readable; missing `resource_id` or `details`
  are returned as `null`.
- `/auth/register` keeps its request shape and gains no weakening of admin-only access.
- User updates do not rotate JWTs, but authenticated route checks use the current database
  role and active state instead of trusting the stale token role.

## Verification

- Add backend repository/API tests for filtering, response shape, and viewer denial.
- Run focused backend tests.
- Run frontend build.
- Run `git diff --check`.
