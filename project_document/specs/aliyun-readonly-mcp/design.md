# Aliyun Read-Only MCP Adapter Spec - Design

## Overview

The Aliyun read-only adapter adds a narrow Alibaba Cloud evidence layer to `ding-robot`. It follows the existing project pattern: tools are registered through `backend-v2` MCP infrastructure, discovered by ToolSearch, gated by `ToolCatalogPolicy`, audited through existing config/chat APIs, and rendered in `frontend-v3` chat cards.

The adapter is intentionally not a generic Alibaba Cloud MCP proxy. Official Alibaba Cloud MCP servers may be used as reference implementations or hidden backends in a future phase, but phase 1 exposes only project-owned `aliyun-*` tools.

```text
User question
  -> ChatOrchestrator
  -> ToolSearch finds approved aliyun-* tools
  -> ToolCatalogPolicy checks role and read-only metadata
  -> AliyunReadOnlyRegistry calls Aliyun SDK clients
  -> Scope filters apply before results are returned
  -> Audit records the read call
  -> Assistant summarizes bounded evidence
```

## Baseline

Current relevant owners:

| Area | Current owner |
|------|---------------|
| MCP aggregation | `backend-v2/app/mcp/manager.py` |
| Built-in tools | `backend-v2/app/mcp/builtin.py` |
| ECS client | `backend-v2/app/mcp/tools/ecs.py` |
| Config normalization | `backend-v2/app/mcp/config_store.py` and `backend-v2/app/core/config.py` |
| Tool policy | `backend-v2/app/mcp/policy.py` |
| Config API | `backend-v2/app/api/config.py` |
| Chat orchestration | `backend-v2/app/services/chat_service.py` |
| MCP config UI | `frontend-v3/src/views/MCPConfig.vue` |
| Chat run card | `frontend-v3/src/components/chat/AssistantRunCard.vue` |

## Proposed File Layout

```text
project_document/specs/aliyun-readonly-mcp/
  requirements.md
  design.md
  tasks.md

backend-v2/app/mcp/tools/
  aliyun.py
  aliyun_clients.py

backend-v2/tests/
  test_aliyun_config.py
  test_aliyun_tools.py
  test_aliyun_policy_audit.py

frontend-v3/src/views/
  MCPConfig.vue

config/
  mcp_config.json
  mcp_config.example.json
  tool_catalog.json
```

`aliyun.py` owns tool definitions and bounded tool output. `aliyun_clients.py` owns thin SDK wrappers and is replaceable in tests. Existing `ecs.py` can be preserved for compatibility, then either delegated to the new Aliyun client layer or retired after the new ECS tools cover its behavior.

## Configuration Model

Add an `aliyun` block under the existing `builtin` config area:

```json
{
  "builtin": {
    "aliyun": {
      "enabled": false,
      "access_key_id": null,
      "access_key_secret": null,
      "default_region_id": "cn-hangzhou",
      "allowed_regions": ["cn-hangzhou"],
      "required_tags": {
        "Environment": ["prod", "staging"]
      },
      "allowed_instance_ids": [],
      "sls": {
        "mappings": [
          {
            "service": "ding-robot",
            "env": "prod",
            "region_id": "cn-hangzhou",
            "project": "example-prod-logs",
            "logstore": "app-log",
            "default_query": "level: ERROR or exception"
          }
        ]
      }
    }
  }
}
```

Public config shape:

```json
{
  "aliyun": {
    "enabled": true,
    "configured": true,
    "available": true,
    "default_region_id": "cn-hangzhou",
    "allowed_regions": ["cn-hangzhou"],
    "required_tags": {"Environment": ["prod"]},
    "sls_mapping_count": 3,
    "access_key_id_configured": true,
    "access_key_secret_configured": true,
    "unavailable_reason": ""
  }
}
```

The public shape never returns `access_key_secret`. It may return a masked AccessKey ID suffix only if useful for admin diagnostics.

## Tool Definitions

### ECS

| Tool | Inputs | Output limit |
|------|--------|--------------|
| `aliyun-ecs-list-instances` | `region_id?`, `status?`, `name?`, `tag_filters?`, `page_size?` | max 50 items |
| `aliyun-ecs-describe-instance` | `instance_id`, `region_id?` | one instance |
| `aliyun-ecs-list-security-groups` | `region_id?`, `vpc_id?`, `instance_id?` | max 50 groups |
| `aliyun-ecs-describe-security-group-rules` | `security_group_id`, `region_id?`, `direction?` | max 100 rules |

### CloudMonitor / CMS

| Tool | Inputs | Output limit |
|------|--------|--------------|
| `aliyun-cms-get-ecs-metrics` | `instance_id`, `region_id?`, `metrics?`, `relative_range?`, `period?` | summary plus bounded samples |
| `aliyun-cms-get-alerts` | `region_id?`, `resource_id?`, `state?`, `relative_range?` | max 50 alerts |
| `aliyun-cms-get-event-history` | `region_id?`, `resource_id?`, `relative_range?`, `event_type?` | max 50 events |

### SLS

| Tool | Inputs | Output limit |
|------|--------|--------------|
| `aliyun-sls-list-logstores` | `service?`, `env?`, `region_id?` | configured mappings only |
| `aliyun-sls-query-logs` | `service?`, `env?`, `query?`, `relative_range?`, `limit?` | max 50 rows |
| `aliyun-sls-query-error-summary` | `service`, `env?`, `relative_range?` | grouped error summary |

### Load Balancing

| Tool | Inputs | Output limit |
|------|--------|--------------|
| `aliyun-lb-list-instances` | `region_id?`, `type?`, `name?`, `tag_filters?` | max 50 load balancers |
| `aliyun-lb-describe-health` | `load_balancer_id`, `region_id?`, `type?` | listeners plus backend health |

### Lightweight Application Server / SWAS

| Tool | Inputs | Output limit |
|------|--------|--------------|
| `aliyun-swas-list-instances` | `region_id?`, `status?`, `name?`, `tag_filters?`, `page_size?` | max 50 instances |

## Scope Enforcement

Every tool call uses a shared guard before SDK calls:

1. Resolve `region_id` from input or default.
2. Reject if region is not in `allowed_regions`.
3. Resolve and validate resource ID allowlists if configured.
4. For list calls, request tags where possible and filter returned resources by `required_tags`.
5. For direct resource calls, fetch tags when needed before returning details.
6. Return structured errors:
   - `aliyun_not_configured`
   - `aliyun_region_not_allowed`
   - `aliyun_resource_not_allowed`
   - `aliyun_sls_mapping_not_found`
   - `aliyun_api_error`

## SDK Boundary

Use Alibaba Cloud Python SDK clients inside `backend-v2`:

| Product | Client wrapper |
|---------|----------------|
| ECS | `alibabacloud-ecs20140526` |
| CMS | `alibabacloud-cms20190101` for metrics, alerts, and events |
| SLS | `alibabacloud-sls20201230` for logstore and query APIs |
| SLB/ALB/NLB | `alibabacloud-slb20140515`, `alibabacloud-alb20200616`, and `alibabacloud-nlb20220430` behind one load-balancer tool facade |
| SWAS | `alibabacloud-swas-open20200601` for lightweight application server inventory |

Tests should fake wrapper responses. Live cloud calls are manual smoke tests, not default CI.

## Tool Catalog And Policy

Generated or normalized tool metadata must include:

```json
{
  "name": "aliyun-cms-get-ecs-metrics",
  "title": "查询 ECS 监控指标",
  "category": "aliyun",
  "tags": ["aliyun", "ecs", "cms", "metrics", "监控", "指标"],
  "dangerLevel": "read",
  "executionPolicy": "executable",
  "server": "builtin",
  "inputSchema": {}
}
```

Policy rule:

```text
allow aliyun-* when role in {"admin", "operator"} and dangerLevel == "read"
deny aliyun-* for viewer
deny any aliyun tool with write/dangerous metadata in phase 1
```

## Audit Design

Audit record fields:

| Field | Notes |
|-------|-------|
| `user` | current auth username |
| `role` | current auth role |
| `tool` | exact `aliyun-*` tool name |
| `region_id` | resolved region |
| `resource_ids` | instance/load balancer/security group IDs if provided |
| `service` / `env` | for SLS mapping calls |
| `time_range` | relative or resolved range |
| `status` | success, denied, unavailable, api_error |
| `result_count` | bounded count only |
| `filtered_count` | count of omitted resources when known |

Do not store AccessKey secrets or large raw log bodies.

## Frontend Design

`MCPConfig.vue` adds an Aliyun section with the same warm UI style:

1. Status cards: enabled, configured, allowed regions, SLS mappings, available tools.
2. Credential controls: AccessKey ID and Secret replacement fields with masked state.
3. JSON editors or textareas for `required_tags` and SLS mappings in phase 1.
4. Tool table filtered by `aliyun-` prefix.
5. Role behavior:
   - `admin`: edit config and replace credentials.
   - `operator`: view config health and tool status.
   - `viewer`: no Aliyun tool invocation and no credential controls.

`AssistantRunCard.vue` does not need a new card type in phase 1. It should display Aliyun tool chips and execution rows through the existing generic assistant message card. Future polish can add product-specific summary rows only after backend output stabilizes.

## Result Shaping

Each tool should return compact JSON optimized for summarization:

```json
{
  "summary": {
    "total": 10,
    "returned": 10,
    "abnormal": 1
  },
  "items": [],
  "filters": {
    "region_id": "cn-hangzhou",
    "required_tags": {"Environment": ["prod"]}
  }
}
```

For metrics:

```json
{
  "summary": {
    "CPU": {"max": 92.4, "avg": 61.2, "latest": 88.1}
  },
  "samples": []
}
```

For SLS:

```json
{
  "mapping": {"service": "ding-robot", "env": "prod", "project": "example-prod-logs", "logstore": "app-log"},
  "summary": {"returned": 20, "top_errors": []},
  "logs": []
}
```

## Compatibility Boundary

1. Do not change existing route paths, auth roles, session store schema, or chat SSE event names.
2. Preserve existing ECS tool names until migration is explicitly complete.
3. Existing `ecs-*` tools may delegate to the new Aliyun client layer but must keep their old input shape.
4. Existing ToolSearch and K8s tools must keep working.
5. If Aliyun config is disabled or missing, app startup must still succeed.

## Rollout

1. Add config schema and public config output.
2. Add Aliyun client wrappers and fake-client tests.
3. Register the 13 read-only tools as built-in tools.
4. Add policy and audit coverage.
5. Update frontend MCP config UI.
6. Smoke test one chat flow per product group using fake or controlled credentials.

## Risks

| Risk | Mitigation |
|------|------------|
| Tool surface grows too quickly | Keep a reviewed 13-tool whitelist for phase 1. |
| Secrets leak through config or logs | Public config masking and test coverage. |
| SLS queries return too much data | Enforce limit, time range, and selected fields. |
| LLM repeats broad list calls | Tool result summaries and orchestration stop rules. |
| Region/tag filters hide needed resources | Audit filtered counts and make config visible to admin. |
| Alibaba SDK install increases build risk | Add explicit dependency and import tests before UI work. |

## Future Extensions

1. STS AssumeRole / RoleArn credential mode.
2. Read-only RDS, OSS, NAT, DNS, WAF, and ACK diagnostics.
3. Explicit `aliyun-sync-inventory-to-graph` read-only graph sync with confirmation.
4. Optional hidden official MCP backend for tools that are hard to maintain directly.
5. Separate product-specific summary cards in chat.
