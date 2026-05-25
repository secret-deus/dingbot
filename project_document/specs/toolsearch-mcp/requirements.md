# ToolSearch MCP Spec - Requirements

## Background

The current rewrite has `backend-v2` and `frontend-v3`, and ToolSearch now reconciles the old root `config/mcp_config.json` catalog with current built-in tools. The old catalog still describes 21 historically important tools, including richer Kubernetes metrics, topology, endpoint, history, and ECS monitor tools; the generated runtime catalog currently contains 68 executable tool entries after the Aliyun read-only adapter expansion.

ToolSearch should become a local MCP server that searches the internal tool catalog on demand. It must not execute real operations. Its job is to return the most relevant tool candidates, their purpose, input schema, category, server, risk level, and execution policy so the LLM can select the next real tool with less context pressure.

## Goals

1. Reduce LLM tool context bloat by loading tool metadata on demand.
2. Restore the richer tool inventory from the old catalog into the new architecture.
3. Keep tool discovery separate from tool execution.
4. Make risk control, IAM checks, user confirmation, and audit logging first-class requirements.
5. Provide a clear implementation backlog for ToolSearch and the surrounding MCP cleanup.

## Non-Goals

1. ToolSearch will not run `kubectl`, ECS APIs, shell commands, or any write operation.
2. ToolSearch will not replace IAM, confirmation, audit, or execution routing.
3. ToolSearch will not require remote SaaS infrastructure; it should run locally through stdio MCP first.

## Requirements

### Requirement 1: Tool Catalog Search

**User Story:** As an AI operations assistant, I want to search a large internal tool catalog by natural language, so that I only load relevant tools into the active reasoning context.

#### Acceptance Criteria

1. WHEN the LLM calls `toolsearch` with a query THEN the MCP server SHALL return ranked tool candidates.
2. WHEN a category is provided THEN results SHALL be filtered to that category before ranking.
3. WHEN a limit is provided THEN results SHALL return no more than that limit.
4. WHEN no tool matches THEN the response SHALL be a valid empty result with a helpful reason.

### Requirement 2: Complete Tool Metadata

**User Story:** As a developer/operator, I want every search result to include enough metadata to decide whether and how to call a real tool.

#### Acceptance Criteria

1. EACH result SHALL include `name`, `title`, `category`, `description`, `tags`, `dangerLevel`, `score`, `matchedFields`, `inputSchema`, `examples`, `server`, and `executionPolicy`.
2. Tool names SHALL follow the current project convention, such as `k8s-get-logs`, not a second underscore naming convention.
3. The catalog SHALL distinguish searchable-only tools from executable tools.
4. The catalog SHALL preserve source information from `config/mcp_config.json` and built-in registry definitions.

### Requirement 3: Safe Execution Boundary

**User Story:** As a platform owner, I want ToolSearch to be discovery-only, so that searching for tools cannot accidentally mutate production resources.

#### Acceptance Criteria

1. ToolSearch SHALL never execute a real operational tool.
2. Tools with `dangerLevel = write` or `dangerLevel = dangerous` SHALL be marked clearly in the result.
3. The backend SHALL enforce IAM, risk judgement, user confirmation, and audit before executing write or dangerous tools.
4. Audit logs SHALL record the search query, selected tool candidate, executed tool, risk level, and caller identity.

### Requirement 4: Backend MCP Integration

**User Story:** As a backend maintainer, I want ToolSearch integrated through the existing MCP manager, so that it can be managed like other local MCP servers.

#### Acceptance Criteria

1. The backend SHALL support local stdio MCP server configuration for `toolsearch`.
2. `MCPManager` SHALL correctly load stdio server tools and merge them with built-in and remote tools.
3. Local dev SHALL resolve `MCP_CONFIG_PATH` consistently from the repository root or absolute paths.
4. The backend SHALL expose catalog health, connected server count, and tool count through existing config/health APIs.

### Requirement 5: Tool Inventory Recovery

**User Story:** As an operator, I want the new system to keep the previous tool breadth, so that the rewrite does not make the assistant less capable.

#### Acceptance Criteria

1. The tool catalog SHALL include the 21 tools currently present in `config/mcp_config.json`.
2. Missing executable implementations SHALL be marked as `catalog_only` until implemented.
3. Built-in K8s and ECS tools SHALL be reconciled against the old catalog to avoid duplicate or inconsistent definitions.
4. The UI SHALL display catalog total, executable total, and unavailable/catalog-only total.

### Requirement 6: Frontend Experience

**User Story:** As a user, I want the chat and MCP configuration pages to explain selected tools cleanly, so that tool discovery feels like part of the workflow instead of a debug artifact.

#### Acceptance Criteria

1. Chat SHALL show compact ToolSearch result cards when a search happens.
2. MCP configuration SHALL show ToolSearch server status and catalog statistics.
3. MCP enablement SHALL separate "server is running" from "include MCP context in this conversation".
4. Tool discovery UI SHALL use the current unified theme rather than old blue-heavy colors.

### Requirement 7: Developer Operations

**User Story:** As a maintainer, I want ToolSearch to be independently testable and documented, so future tool additions do not break ranking or safety.

#### Acceptance Criteria

1. ToolSearch SHALL have unit tests for catalog loading, schema validation, ranking, synonyms, and category filtering.
2. Backend SHALL have integration tests for stdio connection and execution boundary behavior.
3. The implementation SHALL include a repeatable local build/run command.
4. Documentation SHALL describe the ranking logic, catalog schema, backend integration, and rollout plan.
