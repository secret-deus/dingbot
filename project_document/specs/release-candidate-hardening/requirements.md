# Release Candidate Hardening Spec - Requirements

## Background

`ding-robot` now has the core local ChatOps stack working: `backend-v2`, `frontend-v3`,
ToolSearch stdio MCP, K8s tools, scheduler, DingTalk notification plumbing, and the
Aliyun read-only adapter. The latest local acceptance showed ToolSearch connected with
`68` catalog tools, `68` executable tools, and `13/13` Aliyun tools when the backend is
started with read-only credentials.

The next milestone is not a new feature family. It is a release-candidate hardening
slice that turns the current local MVP into a repeatable, inspectable package that can
be tested from a clean runtime without relying on one-off terminal state.

## Reference Inputs

1. `project_document/DELIVERY_PLAN.md` defines the completed S0-S5 delivery sequence and
   still calls out full Compose smoke and release self-test as follow-up work.
2. `project_document/specs/sustainable-delivery/release-checklist.md` defines the common
   handoff checklist.
3. `project_document/specs/sustainable-delivery/self-test-report-aliyun-readonly-mcp.md`
   records the latest local Aliyun/ToolSearch smoke and skipped checks.
4. `project_document/specs/aliyun-readonly-mcp/self-test-report-aliyun-readonly-smoke.md`
   records live Aliyun read-only API coverage and remaining real-resource gaps.

## Goals

1. Produce a repeatable release-candidate verification path for local and Docker Compose
   runtime.
2. Prove the SPA, backend, ToolSearch MCP, scheduler, and config pages work together from
   a fresh start.
3. Remove avoidable local-environment friction from the verification path.
4. Keep cloud credentials, kubeconfig, databases, logs, and generated local state out of
   version control.
5. Record a concise RC self-test report with exact commands, outputs, screenshots or
   smoke notes, skipped checks, and residual risks.

## Non-Goals

1. No new cloud write or dangerous operations.
2. No expansion beyond the current 13 Aliyun read-only tools in this slice.
3. No production deployment automation.
4. No public CI/CD migration unless it is needed to make local release verification
   repeatable.
5. No automatic credential rotation implementation; the slice only documents and verifies
   the operator handoff expectation.

## Requirements

### Requirement 1: Clean Local Verification

**User Story:** As a maintainer, I want one reliable local verification command path, so
that release readiness does not depend on hidden shell state.

#### Acceptance Criteria

1. The project SHALL document the expected Node.js and Python entry points for local
   verification.
2. `scripts/verify.sh` SHALL pass on the documented local toolchain.
3. ToolSearch tests SHALL not fail because the wrong system Node.js shadows the working
   Node.js runtime.
4. The verification report SHALL record any machine-specific workaround that still exists.

### Requirement 2: Docker Compose Runtime Smoke

**User Story:** As an operator, I want Docker Compose to start the whole app, so that a
clean runtime can be tested without relying on dev servers.

#### Acceptance Criteria

1. `docker compose config` SHALL pass.
2. `docker compose build` SHALL pass when Docker runtime is available.
3. `docker compose up --build` SHALL serve the frontend under `/spa/` and the backend API.
4. ToolSearch SHALL start inside the backend container and expose catalog stats.
5. The smoke report SHALL record exact startup commands and ports.

### Requirement 3: Browser Smoke Coverage

**User Story:** As a tester, I want a short browser smoke checklist, so that the critical
operator paths are verified before handoff.

#### Acceptance Criteria

1. Login as `admin/admin` SHALL work in the local smoke runtime.
2. `/spa/mcp-config` SHALL show ToolSearch health, catalog totals, and Aliyun tool counts.
3. `/spa/chat` SHALL render ToolSearch execution details for a discovery-only prompt.
4. `/spa/scheduler` SHALL allow creating and manually running a harmless local task.
5. The execution history SHALL show status, result or error, start time, and finish time.
6. Screenshots or written smoke notes SHALL be saved under `project_document/specs/`.

### Requirement 4: Credential And Secret Handoff

**User Story:** As a project owner, I want cloud credentials handled explicitly, so that
release-candidate smoke does not accidentally persist secrets.

#### Acceptance Criteria

1. Release smoke SHALL use ignored local config or process environment for credentials.
2. No AccessKey, webhook token, kubeconfig content, SQLite DB, or log file SHALL be staged.
3. The report SHALL state whether Aliyun live-resource smoke used real credentials.
4. The report SHALL remind the operator to rotate or delete any AccessKey that was pasted
   into chat or terminal history during testing.

### Requirement 5: Real Resource Gap Tracking

**User Story:** As an operator, I want unverified cloud tools tracked honestly, so that
empty accounts do not create false confidence.

#### Acceptance Criteria

1. ECS detail and metrics checks SHALL be marked skipped unless an ECS instance ID is
   available.
2. Load balancer health SHALL be marked skipped unless a load balancer ID is available.
3. SLS log queries SHALL be marked skipped unless `project/logstore` mappings are
   configured.
4. Each skipped check SHALL include the exact missing input and how to verify later.

### Requirement 6: RC Handoff Report

**User Story:** As the next maintainer, I want one RC report, so that I can see what was
verified, what was skipped, and what remains risky.

#### Acceptance Criteria

1. A report SHALL be created from `self-test-report-template.md`.
2. The report SHALL include automated checks, browser smoke, Docker Compose state,
   DingTalk state, skipped checks, and residual risks.
3. The report SHALL include the current branch and commit.
4. The report SHALL classify changed files as commit-now, ignore, or follow-up.
