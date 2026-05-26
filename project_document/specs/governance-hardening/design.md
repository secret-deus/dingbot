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

## Dangerous Tool Confirmation Slice

The existing policy owner remains `backend-v2/app/mcp/policy.py`, but confirmation
switches from model-controlled `__confirmed` booleans to backend-signed confirmation
tokens.

Confirmation token contract:

- Signed with `SECRET_KEY`.
- Contains token type, user, tool name, danger level, argument hash, and expiry.
- The argument hash is calculated after removing internal confirmation fields.
- Default TTL is 10 minutes.

Execution flow:

1. Chat orchestration receives an LLM tool call.
2. `ToolCatalogPolicy.authorize()` denies write/dangerous calls without a valid token and
   returns a confirmation payload.
3. The denied tool result is persisted with the assistant message.
4. The frontend renders a pending-confirmation row and calls
   `POST /api/v2/chat/messages/{message_id}/tool-calls/{tool_call_id}/confirm`.
5. The backend reloads the stored tool call and confirmation payload, validates the token
   against the current user and original arguments, then executes the tool through the MCP
   manager.
6. The confirmed result is appended to the same message's `tool_results`.

Audit behavior:

- The original attempt remains `tool.execute` / `denied`.
- The explicit confirmation writes `tool.confirm` / `allowed` or `denied`.
- Audit details include safe argument previews only, not confirmation tokens.

## Compatibility

- Existing callers using only `actor`, `action`, `limit`, and `offset` continue to work.
- Admin route access matches the frontend router's existing admin-only AccessControl route.
- Audit data stored before this slice remains readable; missing `resource_id` or `details`
  are returned as `null`.
- `/auth/register` keeps its request shape and gains no weakening of admin-only access.
- User updates do not rotate JWTs, but authenticated route checks use the current database
  role and active state instead of trusting the stale token role.
- The legacy `__confirmed` boolean is intentionally retired for write/dangerous tools.
- Read-only tools and discovery tools keep their existing execution path.

## Verification

- Add backend repository/API tests for filtering, response shape, and viewer denial.
- Run focused backend tests.
- Run frontend build.
- Run `git diff --check`.
- Add policy and chat confirmation-flow tests.
