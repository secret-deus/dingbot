# Self-Test Report - ECS Monitor Recovery

## Summary

- Slice: `ecs-describe-instance-monitor-data` recovery, ToolSearch audit stabilization, and live read-only Kubernetes smoke.
- Date: 2026-05-18
- Tester: Codex
- Result: PASS

## Scope

- Added built-in execution for `ecs-describe-instance-monitor-data`.
- Regenerated `config/tool_catalog.json`; current catalog is `55` total, `55` executable, `0` catalog-only.
- Updated ToolSearch lockfile so production `npm audit --omit=dev` resolves `0` vulnerabilities.
- Added one retry around ToolSearch audit in `scripts/verify.sh` to tolerate transient npm registry timeouts without weakening the gate.
- Fixed runtime behavior when a catalog-executable tool is not loaded in the current process: `MCPManager.call_tool` now returns `tool_unavailable` / `tool_not_loaded`.
- Fixed `K8sClient.unavailable_reason()` so it returns empty after config has successfully loaded.

## Automated Checks

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| ECS monitor tests | `cd backend-v2 && poetry run pytest tests/test_ecs_monitor_tool.py` | PASS | 3 passed |
| MCP stdio contract | `cd backend-v2 && poetry run pytest tests/test_mcp_stdio_toolsearch.py::test_mcp_manager_loads_toolsearch_stdio` | PASS | Verifies ToolSearch stdio and `tool_not_loaded` fallback |
| Full local gate | `PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH npm_config_fetch_timeout=120000 scripts/verify.sh` | PASS | Backend 41 passed, frontend build passed, ToolSearch 7 passed, audit 0 vulnerabilities, Compose config passed, diff check passed |

## Live Smoke

| Scenario | Result | Evidence |
| --- | --- | --- |
| Start minikube | PASS | `minikube start` completed and configured `kubectl` context `minikube` |
| Kubernetes read-only tools | PASS | `K8sClient` returned namespaces=10, nodes=1, pods_all_namespaces=10, services_default=1, events_default=8 |
| Metrics read-only tool | PASS | `k8s-get-cluster-metrics` returned `source=metrics.k8s.io`, `node_count=1`, `pod_count=10` after metrics-server became ready |

## Residual Risk

- ECS monitor execution is unit-tested with a fake ECS SDK client; it still needs validation with real Alibaba Cloud ECS credentials before production use.
- Full `docker compose up --build` browser smoke was not rerun in this slice; `docker compose config` and frontend build passed.
