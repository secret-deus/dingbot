# Sustainable Delivery Spec - Requirements

## Background

The v3 rewrite has a working backend and frontend skeleton, but the repository is not yet safe for repeated delivery. A fresh checkout must be able to install dependencies, run tests, build the UI, and understand the next delivery slices from specs.

This spec defines the delivery system around the product work. Product features such as ToolSearch remain in their own specs.

## Goals

1. Make the repository reproducible from a clean checkout.
2. Keep development driven by explicit specs and task checklists.
3. Add verification gates that can run locally before every commit.
4. Separate runtime secrets from versioned configuration.
5. Provide a roadmap that can be delivered in small, testable slices.

## Non-Goals

1. This spec does not implement ToolSearch itself.
2. This spec does not deploy to a remote environment.
3. This spec does not introduce production secrets, kubeconfig, or cloud credentials.

## Requirements

### Requirement 1: Reproducible Repository

**User Story:** As a maintainer, I want a fresh clone to include all dependency manifests and build metadata, so that the project can be installed and built without local-only files.

#### Acceptance Criteria

1. `frontend-v3/package.json`, lockfile, and TypeScript configs SHALL be eligible for version control.
2. Backend dependency metadata SHALL remain versioned through Poetry files.
3. Runtime JSON configs SHALL remain ignored except for `*.example.json`.
4. Generated logs, databases, caches, and local credentials SHALL remain ignored.

### Requirement 2: Container Build Baseline

**User Story:** As an operator, I want Docker Compose to build both backend and frontend services, so that local deployment can be verified consistently.

#### Acceptance Criteria

1. `docker-compose.yml` SHALL reference existing Dockerfiles.
2. The frontend container SHALL serve the SPA under `/spa/`.
3. The frontend container SHALL proxy `/api/` to the backend service.
4. Backend and frontend services SHALL be documented with local URLs.
5. The backend image SHALL include the ToolSearch stdio runtime needed by `config/mcp_config.json`.
6. Docker build context SHALL exclude local secrets, runtime databases, logs, dependency directories, and archived code.

### Requirement 3: Verification Gates

**User Story:** As a developer, I want quick validation commands, so that each delivery slice can prove it did not break the baseline.

#### Acceptance Criteria

1. Backend SHALL have at least one pytest suite collected by `poetry run pytest`.
2. Frontend SHALL pass `npm run build`.
3. The README SHALL document the verification commands.
4. Future slices SHALL add tests matching their changed behavior.
5. A single local script SHALL run the backend, frontend, ToolSearch, compose config, and whitespace verification gates.

### Requirement 4: Spec-Driven Delivery

**User Story:** As a project owner, I want a durable delivery plan, so that future agents can continue without rediscovering project state.

#### Acceptance Criteria

1. Delivery planning SHALL live in `project_document/DELIVERY_PLAN.md`.
2. Each major slice SHALL have a spec under `project_document/specs/`.
3. Task lists SHALL separate completed work from backlog.
4. The plan SHALL identify verification gates and residual risks.

### Requirement 5: Secret Hygiene

**User Story:** As a platform owner, I want local credentials excluded from git, so delivery artifacts never leak secrets.

#### Acceptance Criteria

1. `.env`, runtime JSON configs, cloud credentials, kubeconfig, logs, and databases SHALL stay ignored.
2. Example configs SHALL stay versioned.
3. Documentation SHALL tell users to copy examples into local runtime config files.
