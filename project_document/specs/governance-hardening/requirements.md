# Governance Hardening Spec - Requirements

## Goal

Turn the current read-mostly governance surfaces into operational controls that can be
used during local release validation without exposing secrets or mutating cloud resources.

## Slice 1: Audit Filtering

### Functional Requirements

1. `/api/v2/config/audit` must be admin-only.
2. The endpoint must support filtering by:
   - `actor`
   - `action`
   - `resource`
   - `resource_id`
   - `result`
3. Text filters for `actor`, `action`, `resource`, and `resource_id` must allow partial
   matching so operators can search by route fragments such as `/chat` or action fragments
   such as `tool`.
4. `result` must remain exact because it is a controlled status field.
5. Audit responses must include `resource_id` and `details` so the UI can show why an
   event matched without exposing secrets.
6. The permissions page must expose compact audit filters and keep the current role/policy
   presentation read-only.

### Non-Goals

- No user creation, role editing, password reset, or account deactivation in this slice.
- No DingTalk real-send validation in this slice.
- No new write or dangerous tool confirmation flow in this slice.
- No migration of old audit rows.

## Slice 2: User Management

### Functional Requirements

1. Admin can list users with username, display name, role, active state, and timestamps.
2. Admin can create a user with username, password, display name, and role.
3. Admin can update another user's display name, role, and active state.
4. Admin cannot deactivate or demote their own account through the API.
5. Role changes and inactive state must be enforced on existing tokens through authenticated route checks.
6. Viewer/operator cannot list, create, or update users.
7. AccessControl page must load real users from the backend instead of static examples.
8. AccessControl page must keep role policy descriptions read-only.

### Non-Goals

- No hard delete of users.
- No password reset flow.
- No multi-tenant groups or fine-grained per-tool grants.
- No self-service profile editing.

## Slice 3: Dangerous Tool Confirmation

### Functional Requirements

1. Write and dangerous tools must not be executable by passing a model-controlled boolean flag.
2. When an operator/admin triggers a write or dangerous tool without confirmation, the backend must return a confirmation payload instead of executing the tool.
3. The confirmation payload must be signed by the backend, scoped to the current user, tool name, danger level, and exact arguments.
4. Confirmation tokens must expire quickly.
5. Confirming a pending chat tool call must execute the original tool arguments only if the token is valid.
6. Confirmation attempts must write audit rows distinct from the original denied execution.
7. The chat UI must show pending write/dangerous tool calls and expose an explicit confirm action.

### Non-Goals

- No automatic confirmation from the LLM.
- No cloud or Kubernetes write smoke against real resources.
- No long-lived approval queue or multi-user approval workflow.

## Acceptance

1. Admin can filter audit rows by actor/action/resource/result.
2. Viewer cannot read audit logs.
3. The permissions page can apply and clear filters.
4. Existing audit middleware and tool-execution audit writes continue to work.
5. Backend focused tests and frontend build pass.
6. Admin can create and update users from the permissions page.
7. Self-demotion and self-deactivation are rejected.
8. Deactivated users cannot keep using an existing token.
9. Write/dangerous tools require a backend-signed confirmation token.
10. Confirmed tool calls are audited as `tool.confirm`.
