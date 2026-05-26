# Governance Hardening Spec - Requirements

## Goal

Turn the current read-mostly governance surfaces into operational controls that can be
used during local release validation without exposing secrets or mutating cloud resources.

## Slice 1: Audit Filtering

The first implementation slice covers audit filtering only.

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

## Acceptance

1. Admin can filter audit rows by actor/action/resource/result.
2. Viewer cannot read audit logs.
3. The permissions page can apply and clear filters.
4. Existing audit middleware and tool-execution audit writes continue to work.
5. Backend focused tests and frontend build pass.
