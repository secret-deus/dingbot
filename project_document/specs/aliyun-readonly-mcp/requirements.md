# Aliyun Read-Only MCP Adapter Spec - Requirements

## Background

`ding-robot` already has `backend-v2` as the active backend, `frontend-v3` as the active SPA, and an MCP aggregation layer that merges built-in K8s/ECS tools, configured MCP servers, ToolSearch metadata, tool policy, and audit. The current Alibaba Cloud surface is a small built-in ECS read path. The next step is to make Alibaba Cloud a first-class ChatOps evidence source without exposing broad cloud mutation APIs to the LLM.

Alibaba Cloud provides official MCP options such as OpenAPI MCP Server, OSS MCP Server, CloudMonitor/Observability MCP, and the open-source CloudOps MCP Server. This project will not expose those full tool surfaces directly to the LLM in phase 1. Instead, it will add a local read-only Aliyun adapter that presents a reviewed, narrow, auditable tool whitelist.

## Reference Inputs

1. [Alibaba Cloud OpenAPI MCP Server](https://www.alibabacloud.com/help/en/openapi/user-guide/openapi-mcp-server-guide) describes MCP access to Alibaba Cloud APIs and recommends no more than 30 APIs in a single MCP server because of context length and tool selection limits.
2. [`aliyun/alibaba-cloud-ops-mcp-server`](https://github.com/aliyun/alibaba-cloud-ops-mcp-server) includes broad cloud operations across products such as ECS, CloudMonitor, OSS, RDS, VPC, and OOS, including write-capable tools. This supports the local whitelist decision.
3. [Alibaba Cloud OSS MCP Server Alpha](https://www.alibabacloud.com/help/en/oss/developer-reference/oss-mcp-server-alpha) exposes read-oriented OSS tools such as bucket listing, bucket info, and bucket stats, and shows that product-specific MCP servers may be narrower than CloudOps.
4. [Alibaba Cloud CloudMonitor 2.0 MCP](https://www.alibabacloud.com/help/doc-detail/2987178.html) warns not to expose MCP SSE or HTTP endpoints publicly without proper authentication and access control.

## Decisions From Product Discussion

1. Phase 1 is read-only diagnostics only.
2. Use a local read-only adapter; do not expose official Alibaba Cloud MCP tools directly to the LLM.
3. Product scope is ECS, CloudMonitor/CMS, SLS, SLB/ALB/NLB, and lightweight application servers.
4. Credentials use a dedicated read-only RAM AccessKey stored server-side; secrets are never returned to the frontend.
5. The first tool whitelist contains 13 read-only tools.
6. SLS uses service-to-project/logstore mapping instead of making users provide raw SLS coordinates every time.
7. Resource exposure is limited by allowed regions plus tag filters, with optional resource ID allowlists.
8. Results are shown in the current conversation and saved as lightweight session summaries; phase 1 does not automatically write Alibaba Cloud inventory into the knowledge graph.
9. The MCP config page gets an Aliyun section with config state, JSON mappings, and tool health.
10. Only `operator` and `admin` may call Aliyun tools; `viewer` cannot call them.
11. Write operations, CloudControl mutations, and OOS execution are out of scope for phase 1.

## Goals

1. Add Alibaba Cloud as a safe ChatOps evidence source for infrastructure troubleshooting.
2. Keep the LLM tool surface small, deterministic, and explicitly read-only.
3. Preserve existing `backend-v2` MCP manager, policy, audit, chat, and frontend routing contracts.
4. Support common cloud-to-K8s incident flows: unhealthy service, degraded instance, metric spike, log error, and load balancer backend health.
5. Make credentials, region scope, tag filters, SLS mappings, and role permissions inspectable by operators without leaking secrets.

## Non-Goals

1. No cloud resource mutations, including start, stop, restart, delete, scale, security group modification, or OOS execution.
2. No direct full exposure of Alibaba Cloud official MCP or CloudControl tool catalogs to the LLM.
3. No automatic RAM user, policy, or AccessKey creation.
4. No automatic knowledge graph inventory sync in phase 1.
5. No full cloud management console or resource browser in the frontend.
6. No cross-account federation or STS AssumeRole in phase 1.

## Requirements

### Requirement 1: Local Read-Only Adapter

**User Story:** As a platform owner, I want Alibaba Cloud capabilities exposed through a local reviewed adapter, so that the assistant cannot accidentally discover or call broad cloud mutation tools.

#### Acceptance Criteria

1. WHEN the backend starts THEN the adapter SHALL register only reviewed `aliyun-*` tools.
2. WHEN official Alibaba Cloud MCP servers are configured behind the scenes THEN their raw tool list SHALL NOT be passed directly to the LLM.
3. EACH phase-1 Aliyun tool SHALL have `dangerLevel = read` and `executionPolicy = executable` only when its implementation and credentials are available.
4. Tool names SHALL use the `aliyun-` prefix for policy, audit, and UI grouping.
5. Disabled or unconfigured tools SHALL stay visible as unavailable metadata only when useful for operators.

### Requirement 2: Phase-1 Tool Whitelist

**User Story:** As an operator, I want a focused set of Alibaba Cloud read tools, so that common troubleshooting flows work without overwhelming the model.

#### Acceptance Criteria

1. The ECS group SHALL expose:
   - `aliyun-ecs-list-instances`
   - `aliyun-ecs-describe-instance`
   - `aliyun-ecs-list-security-groups`
   - `aliyun-ecs-describe-security-group-rules`
2. The CloudMonitor/CMS group SHALL expose:
   - `aliyun-cms-get-ecs-metrics`
   - `aliyun-cms-get-alerts`
   - `aliyun-cms-get-event-history`
3. The SLS group SHALL expose:
   - `aliyun-sls-list-logstores`
   - `aliyun-sls-query-logs`
   - `aliyun-sls-query-error-summary`
4. The load balancing group SHALL expose:
   - `aliyun-lb-list-instances`
   - `aliyun-lb-describe-health`
5. The lightweight application server group SHALL expose:
   - `aliyun-swas-list-instances`
6. Tool results SHALL be bounded by explicit limits suitable for LLM summarization.

### Requirement 3: Credentials And Secret Handling

**User Story:** As an admin, I want to configure a dedicated read-only RAM AccessKey safely, so that cloud secrets are not exposed through the UI or logs.

#### Acceptance Criteria

1. AccessKey ID and Secret SHALL be stored server-side through config or environment.
2. The public config API SHALL return only configured booleans and masked identifiers, never the AccessKey Secret.
3. The frontend SHALL allow replacing credentials but SHALL NOT display the current secret.
4. Tool calls, audit logs, errors, and chat messages SHALL NOT include secret values.
5. Missing or placeholder credentials SHALL mark Aliyun tools unavailable with a clear reason.

### Requirement 4: Scope Controls

**User Story:** As a platform owner, I want region and tag controls, so that ChatOps users only see the cloud resources intended for this assistant.

#### Acceptance Criteria

1. Config SHALL include `allowed_regions`.
2. Tool calls with a region outside `allowed_regions` SHALL be rejected before calling Alibaba Cloud APIs.
3. Config SHALL include `required_tags` for returned resource filtering.
4. Returned ECS and load balancer resources SHALL be filtered by configured tags where Alibaba Cloud APIs provide tags.
5. Optional allowlists such as `allowed_instance_ids` SHALL further restrict results when configured.
6. Audit logs SHALL record filter counts without leaking filtered resource details.

### Requirement 5: SLS Mapping

**User Story:** As an operator, I want to query service logs by service and environment, so that I do not need to remember SLS project/logstore coordinates.

#### Acceptance Criteria

1. Config SHALL support SLS mappings with `service`, `env`, `region_id`, `project`, `logstore`, and optional `default_query`.
2. `aliyun-sls-query-logs` SHALL resolve mappings by `service` and optional `env`.
3. WHEN no mapping matches THEN the tool SHALL return a structured clarification error instead of guessing.
4. Direct `project` and `logstore` inputs MAY be accepted only if they match configured mappings.
5. Log query output SHALL be limited by time range, row count, and selected fields.

### Requirement 6: Role Policy And Audit

**User Story:** As an admin, I want Aliyun tool calls governed by existing roles and audit, so that read access is traceable.

#### Acceptance Criteria

1. `admin` and `operator` SHALL be allowed to call `aliyun-*` tools.
2. `viewer` SHALL be denied from calling `aliyun-*` tools.
3. Every Aliyun tool call SHALL create an audit record containing caller, role, tool name, region, resource identifiers, time range, result status, and error class when applicable.
4. Audit payloads SHALL mask secrets and avoid storing large raw SLS log bodies.
5. Denied calls SHALL be audited with `tool_execution_denied`.

### Requirement 7: Chat And Session Context

**User Story:** As a user, I want Alibaba Cloud evidence summarized in chat, so that troubleshooting conclusions are grounded without dumping raw API payloads.

#### Acceptance Criteria

1. Chat SHALL show Aliyun tool calls in the existing assistant run card execution chain.
2. ECS, metrics, SLS, and load balancer results SHALL be summarized into compact content blocks.
3. Large raw payloads SHALL be available only under technical details or omitted according to result size limits.
4. The backend SHALL save lightweight session summaries for follow-up questions.
5. Phase 1 SHALL NOT automatically write Alibaba Cloud inventory into the knowledge graph.

### Requirement 8: MCP Config UI

**User Story:** As an admin/operator, I want to see Aliyun configuration and health in the MCP page, so that I can diagnose missing credentials, scope filters, and tool availability.

#### Acceptance Criteria

1. The MCP config API SHALL include an `aliyun` public config section.
2. The MCP config page SHALL show enabled state, credential state, default region, allowed regions, tag filters, SLS mapping count, and tool health.
3. Admins SHALL be able to update Aliyun config fields through the existing config API.
4. Operators SHALL be able to view health but not replace credentials.
5. The UI SHALL preserve the current Claude-like warm theme and avoid adding a separate cloud-console visual language.

### Requirement 9: Verification

**User Story:** As a maintainer, I want repeatable tests for the adapter, so future Alibaba Cloud tool additions do not break safety or prompt behavior.

#### Acceptance Criteria

1. Unit tests SHALL cover config normalization, secret masking, region rejection, tag filtering, SLS mapping resolution, and viewer denial.
2. Tool tests SHALL use fake Alibaba Cloud client responses rather than live cloud dependencies by default.
3. Existing backend orchestration tests SHALL prove Aliyun tools route through policy and audit.
4. Frontend build SHALL pass after adding the config UI.
5. Manual smoke verification SHALL include login as `admin`, MCP config status, and one chat flow that calls Aliyun read tools.
