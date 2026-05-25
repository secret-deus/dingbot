# Aliyun Read-Only MCP Self-Test Report

- Date: 2026-05-25
- Slice: controlled read-only RAM AccessKey and ToolSearch chat smoke
- Region: `cn-hangzhou`
- Credential handling: AccessKey values were injected only into the current process through stdin/environment and were not written to repository files.

## Scope

This smoke verifies that the dedicated RAM user can call the project-owned read-only Aliyun adapter APIs. The account is expected to have few or no cloud resources, so empty result sets are acceptable.

Covered calls:

- `aliyun-ecs-list-instances`
- `aliyun-ecs-list-security-groups`
- `aliyun-cms-get-alerts`
- `aliyun-cms-get-event-history`
- `aliyun-lb-list-instances` with `type=slb`
- `aliyun-lb-list-instances` with `type=alb`
- `aliyun-lb-list-instances` with `type=nlb`
- `aliyun-swas-list-instances`
- Chat discovery prompt for Aliyun lightweight application server tools

Not covered:

- `aliyun-ecs-describe-instance`: requires an instance ID.
- `aliyun-cms-get-ecs-metrics`: requires an instance ID.
- `aliyun-sls-*`: requires configured SLS `project/logstore` mappings.
- `aliyun-lb-describe-health`: requires a load balancer ID.

## Findings

Initial live smoke exposed two SDK-boundary issues:

1. ECS client construction used the imported SDK module as a callable instead of `Client(config)`.
2. CloudMonitor defaulted to `cms.aliyuncs.com`, which did not resolve locally; the region endpoint `metrics.cn-hangzhou.aliyuncs.com` resolved.

Fixes applied:

- `backend-v2/app/mcp/tools/ecs.py` now constructs `ecs_client.Client(config)`.
- `backend-v2/app/mcp/tools/aliyun_clients.py` now sets the CloudMonitor endpoint to `metrics.<region>.aliyuncs.com`.

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| ECS list instances | PASS | `summary.total=0`, `returned=0` |
| ECS list security groups | PASS | `summary.total=1`, `returned=1` |
| CloudMonitor alerts | PASS | `summary.total=0`, `returned=0` |
| CloudMonitor event history | PASS | `summary.total=0`, `returned=0` |
| SLB list | PASS | `summary.total=0`, `returned=0` |
| ALB list | PASS | `summary.total=0`, `returned=0` |
| NLB list | PASS | `summary.total=0`, `returned=0` |
| SWAS list `cn-beijing` | PASS | `summary.total=1`, `returned=1`; resource name `Docker-jtmg`, status `Running` |
| SWAS list other sampled regions | PASS | `summary.total=0`, `returned=0` for `cn-hangzhou`, `cn-shanghai`, `cn-shenzhen`, `cn-hongkong`, `ap-southeast-1` |
| Chat discovery prompt | PASS | Prompt: `只搜索工具：有哪些工具可以查询阿里云轻量应用服务器？先不要执行具体资源查询。`; backend normalized the model-supplied category to `aliyun`, returned `aliyun-swas-list-instances` as the top ToolSearch candidate, and did not execute a concrete resource query. |
| MCP config browser smoke | PASS | `/spa/mcp-config` rendered ToolSearch connected, catalog total `68`, executable `68`, catalog-only `0`, and Aliyun tools `13/13` after starting the backend with the read-only credentials in process environment only. |

## Regression

Command:

```bash
cd backend-v2 && poetry run pytest tests/test_aliyun_config.py tests/test_aliyun_tools.py tests/test_aliyun_policy_audit.py tests/test_chat_toolsearch_orchestration.py tests/test_ecs_monitor_tool.py -q
```

Result:

```text
32 passed in 2.62s
```

Full backend suite:

```bash
cd backend-v2 && poetry run pytest -q
```

Result:

```text
63 passed, 1 warning in 4.24s
```

Scoped lint:

```bash
cd backend-v2 && poetry run ruff check app/mcp app/api/config.py app/core/config.py tests/test_aliyun_config.py tests/test_aliyun_tools.py tests/test_aliyun_policy_audit.py
```

Result:

```text
All checks passed
```

ToolSearch catalog regression:

```bash
cd mcp-servers/toolsearch && PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH npm test
```

Result:

```text
7 passed
```

Full local release gate:

```bash
PATH=/Users/xhang/.nvm/versions/node/v24.14.0/bin:$PATH scripts/verify.sh
```

Result:

```text
PASS: backend 63 tests, frontend build, ToolSearch 7 tests, ToolSearch production audit 0 vulnerabilities, docker compose config, and git diff --check.
```

## Residual Risk

- The RAM AccessKey appeared in chat before this smoke. Rotate or delete it after validation.
- SLS and detail/health tools still need a real `project/logstore`, ECS instance ID, or load balancer ID to verify end-to-end.
- Runtime process environment is intentionally not persisted; restart commands must provide the Aliyun credentials or use the ignored local MCP config.
