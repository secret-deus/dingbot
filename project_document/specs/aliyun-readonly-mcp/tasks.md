# Aliyun Read-Only MCP Adapter Spec - Tasks

## Current Status

- [x] Product boundary confirmed: phase 1 is read-only diagnostics only.
- [x] Integration boundary confirmed: local adapter, no direct full official MCP exposure to the LLM.
- [x] Product scope confirmed: ECS, CloudMonitor/CMS, SLS, SLB/ALB/NLB, and lightweight application servers.
- [x] Credential model confirmed: dedicated read-only RAM AccessKey held by backend.
- [x] Tool count confirmed: 13 phase-1 `aliyun-*` tools.
- [x] Scope controls confirmed: allowed regions plus tag filters.
- [x] Result persistence confirmed: chat display plus session summary, no automatic graph writes.
- [x] Role policy confirmed: `operator/admin` can call, `viewer` cannot.

## Implementation Backlog

- [x] 1. Add Aliyun config schema and masking
  - [x] Extend `backend-v2/app/core/config.py` with Aliyun config fields.
  - [x] Extend `backend-v2/app/mcp/config_store.py` normalization with `builtin.aliyun`.
  - [x] Extend `public_mcp_config()` with masked Aliyun state.
  - [x] Extend `apply_mcp_updates()` to update Aliyun fields without clearing secrets accidentally.
  - [x] Add `backend-v2/tests/test_aliyun_config.py`.
  - [x] Verify with `cd backend-v2 && poetry run pytest tests/test_aliyun_config.py -q`.

- [x] 2. Add Aliyun client wrappers
  - [x] Create `backend-v2/app/mcp/tools/aliyun_clients.py`.
  - [x] Implement thin wrappers for ECS, CMS, SLS, and load balancing clients.
  - [x] Keep SDK imports lazy so app startup does not fail when Aliyun is disabled.
  - [x] Add fake client fixtures for unit tests.
  - [x] Verify disabled config startup still passes existing backend tests.

- [x] 3. Implement shared scope guard and result shaping
  - [x] Create shared helpers in `backend-v2/app/mcp/tools/aliyun.py`.
  - [x] Implement region validation.
  - [x] Implement required tag matching.
  - [x] Implement optional resource ID allowlists.
  - [x] Implement SLS mapping resolution.
  - [x] Implement bounded result shaping for list, metrics, logs, and health outputs.
  - [x] Add tests for rejection and filtering paths.

- [x] 4. Register ECS read tools
  - [x] Add `aliyun-ecs-list-instances`.
  - [x] Add `aliyun-ecs-describe-instance`.
  - [x] Add `aliyun-ecs-list-security-groups`.
  - [x] Add `aliyun-ecs-describe-security-group-rules`.
  - [x] Add metadata with category, tags, danger level, execution policy, and input schema.
  - [x] Preserve existing `ecs-*` tools and decide whether they delegate to the new Aliyun client layer.
  - [x] Add fake-response tests in `backend-v2/tests/test_aliyun_tools.py`.

- [x] 5. Register CMS read tools
  - [x] Add `aliyun-cms-get-ecs-metrics`.
  - [x] Add `aliyun-cms-get-alerts`.
  - [x] Add `aliyun-cms-get-event-history`.
  - [x] Summarize metrics with max, avg, latest, and sample count.
  - [x] Bound alert and event results.
  - [x] Add tests for metric normalization and time-window defaults.

- [x] 6. Register SLS read tools
  - [x] Add `aliyun-sls-list-logstores`.
  - [x] Add `aliyun-sls-query-logs`.
  - [x] Add `aliyun-sls-query-error-summary`.
  - [x] Enforce mapping before direct project/logstore access.
  - [x] Bound log rows and avoid storing large raw log bodies.
  - [x] Add tests for mapping match, missing mapping, query defaults, and row limits.

- [x] 7. Register load-balancing read tools
  - [x] Add `aliyun-lb-list-instances`.
  - [x] Add `aliyun-lb-describe-health`.
  - [x] Support SLB/ALB/NLB through a facade that normalizes output.
  - [x] Apply region and tag filters where product APIs support tags.
  - [x] Add tests for mixed healthy/unhealthy backend summaries.

- [x] 7a. Register lightweight application server read tool
  - [x] Add `aliyun-swas-list-instances`.
  - [x] Use SWAS OpenAPI `ListInstances` only; no start, stop, reboot, renewal, or firewall mutation.
  - [x] Add fake-response test in `backend-v2/tests/test_aliyun_tools.py`.

- [x] 8. Wire policy and audit
  - [x] Update `backend-v2/app/mcp/policy.py` so `aliyun-*` requires `operator` or `admin`.
  - [x] Ensure `viewer` denial is structured and audited.
  - [x] Extend existing audit call sites to record Aliyun region, resource IDs, service/env, time range, result status, and result count.
  - [x] Add `backend-v2/tests/test_aliyun_policy_audit.py`.

- [x] 9. Update ToolSearch catalog metadata
  - [x] Add the 13 Aliyun tools to generated or normalized catalog output.
  - [x] Ensure all 13 use `dangerLevel = read`.
  - [x] Ensure all 13 include tags for Chinese and English search terms.
  - [x] Verify ToolSearch returns Aliyun tools for queries such as `查 ECS CPU`, `查服务错误日志`, and `负载均衡后端健康`.

- [x] 10. Update MCP config frontend
  - [x] Extend `frontend-v3/src/types/index.ts` with public Aliyun config types.
  - [x] Extend `frontend-v3/src/views/MCPConfig.vue` with the Aliyun config section.
  - [x] Add fields for enablement, credential replacement, allowed regions, required tags JSON, and SLS mappings JSON.
  - [x] Make credential replacement admin-only.
  - [x] Show Aliyun tool health grouped by `aliyun-` prefix.
  - [x] Preserve current Claude-like warm style and avoid a separate cloud-console visual language.

- [x] 11. Update chat result handling
  - [x] Confirm existing `AssistantRunCard.vue` renders Aliyun tool chips and execution rows without new UI.
  - [x] Add output labels or summaries only if generic rendering is unclear.
  - [x] Ensure large raw SLS results live under technical details or are omitted by backend result shaping.
  - [x] Smoke test one chat question that selects an Aliyun read tool after credentials are available.
    - 2026-05-25: credentials and `aliyun-swas-list-instances` runtime availability were verified, but the chat smoke did not reach tool selection because the selected LLM provider returned `Service is too busy`.
    - 2026-05-25: after tightening Aliyun/SWAS intent anchoring, the chat smoke selected only `aliyun-swas-list-instances` and returned a bounded read-only answer.

- [x] 12. Verification and rollout
  - [x] Run `cd backend-v2 && poetry run pytest tests/test_aliyun_config.py tests/test_aliyun_tools.py tests/test_aliyun_policy_audit.py tests/test_chat_toolsearch_orchestration.py tests/test_mcp_stdio_toolsearch.py tests/test_ecs_monitor_tool.py -q`.
    - 2026-05-25: `32 passed in 2.62s`.
    - 2026-05-25: full backend suite passed with `62 passed, 1 warning in 4.23s`.
  - [x] Run `cd backend-v2 && poetry run ruff check app/mcp app/api/config.py app/core/config.py tests/test_aliyun_config.py tests/test_aliyun_tools.py tests/test_aliyun_policy_audit.py`.
    - 2026-05-25: scoped ruff check passed after formatting existing `app/mcp` and config files.
  - [x] Run `PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH npm run build` in `frontend-v3`.
  - [x] Log in as `admin/admin` and open `/spa/mcp-config`.
  - [x] Verify Aliyun config state, hidden secret behavior, and tool health.
  - [x] Log in as or simulate `viewer` and verify Aliyun tool denial.
  - [x] Run a controlled manual smoke with a read-only RAM AccessKey after credentials are available.
    - 2026-05-25: API-level smoke passed for ECS list, ECS security groups, CloudMonitor alerts/events, SLB/ALB/NLB list calls, and SWAS lightweight application server list calls. See `self-test-report-aliyun-readonly-smoke.md`.

## Done Definition

1. `project_document/specs/aliyun-readonly-mcp/*` documents are complete and current.
2. The backend exposes exactly the 13 phase-1 `aliyun-*` read tools when configured.
3. Missing credentials mark tools unavailable without breaking app startup.
4. Region, tag, SLS mapping, and role restrictions are enforced before cloud API calls.
5. Secrets are never returned through public config, chat output, audit logs, or frontend state.
6. MCP config UI shows Aliyun status and allows admin-only credential replacement.
7. Chat can use Aliyun read tools and produce a final natural-language answer with bounded evidence.
8. Backend tests, frontend build, and manual smoke verification pass.
