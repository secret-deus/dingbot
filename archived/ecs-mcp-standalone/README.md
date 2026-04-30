# ECS MCP Server（阿里云 ECS 巡检 MCP 服务）

ECS MCP 是一个独立的 Model Context Protocol 工具服务，面向阿里云 ECS 的只读巡检场景，提供：
- 列出实例（支持过滤、分页）
- 获取实例监控数据（Period 自动选择、分片聚合、下采样、统计）
- REST API（同步/异步工具调用）与 SSE 实时事件
- 默认启用热重载，开发体验友好

---

## 目录
- 项目结构
- 环境与安装
- 启动与热重载
- 配置与环境变量
- 调用流程（客户端交互）
- API 端点说明
- 工具清单与 Schema 与示例
- 权限要求（RAM 策略）
- 错误处理与故障排查
- SSE 事件说明
- Roadmap

---

## 项目结构
```
ecs-mcp/
  ├─ pyproject.toml
  ├─ start_ecs_mcp_http_server.py         # 启动脚本（默认开启热重载开关）
  └─ src/ecs_mcp/
      ├─ server.py                        # FastAPI + Uvicorn + MCP 工具注册
      ├─ config.py                        # 配置与多源 .env 加载
      ├─ core/
      │   ├─ mcp_protocol.py              # MCP 类型定义
      │   └─ tool_registry.py             # 工具注册与执行
      ├─ tools/
      │   ├─ __init__.py                  # 工具注册入口
      │   ├─ ecs_list_instances.py        # 工具：列出实例（RPC 签名调用）
      │   └─ ecs_monitor_data.py          # 工具：实例监控数据（仅云监控 CMS 查询）
      └─ clients/
          ├─ ecs_client.py                # 官方 SDK 封装（当前不走该路径）
          ├─ ecs_rpc.py                   # 通用 RPC 签名 GET 调用（用于 DescribeInstances）
          └─ cms_rpc.py                   # CloudMonitor (CMS) RPC 签名 GET 调用
```

## 环境与安装
要求：Python 3.11+、Poetry
```bash
cd ecs-mcp
poetry install
```

## 启动与热重载
- 默认开启热重载（等效 `uvicorn --reload`）。
- 端口默认 8002；设置 `ECS_MCP_PORT` 可切换端口。
- 关闭热重载：设置 `ECS_MCP_RELOAD=false`。

```bash
# 默认端口启动（热重载开启）
poetry run python start_ecs_mcp_http_server.py

# 指定端口
ECS_MCP_PORT=8003 poetry run python start_ecs_mcp_http_server.py

# 关闭热重载
ECS_MCP_RELOAD=false poetry run python start_ecs_mcp_http_server.py
```

健康检查：
```bash
curl -s http://localhost:8002/health | jq .
```

## 配置与环境变量
运行时按顺序尝试加载（不覆盖已存在变量）：
1) `ecs-mcp/config.env`
2) `ecs-mcp/.env`
3) 仓库根：`k8s-mcp/config.env`（与 K8s MCP 共享）
4) 仓库根：`backend/config.env`
5) 仓库根：`.env`

关键变量：
- `ALIBABA_CLOUD_ACCESS_KEY_ID`（必需）
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`（必需）
- `ALIBABA_CLOUD_SECURITY_TOKEN`（可选，STS）
- `ALIBABA_CLOUD_ECS_REGION_ID`（默认 `cn-hangzhou`）
- `ECS_MAX_CONCURRENCY`（默认 3）
- `ECS_CALL_TIMEOUT`（默认 30）
- `ECS_RETRY_ATTEMPTS`（默认 3）

监控数据默认走云监控（CMS）端点，优先区域域名：`https://metrics.{region}.aliyuncs.com`，其次公共域名：`https://metrics.aliyuncs.com`。

## 调用流程（客户端交互）
1) 客户端发现工具：`GET /tools`
2) 选择工具：
   - 同步 `POST /tools/run`
   - 异步 `POST /tools/call`（结果通过 SSE 推送）
3) 订阅 `GET /events` 获取执行完成/错误等通知（SSE）

## API 端点说明
- `GET /health`
  - 返回服务健康状态
- `GET /tools`
  - 列出可用工具：名称、描述、输入 schema
- `POST /tools/run`
  - 同步执行工具
  - Body：`{"id": "...", "name": "tool-name", "arguments": { ... }}`
  - 返回：`{"result": { "content": [{"type":"text","text":"<JSON字符串>"}], "is_error": false }}`
- `POST /tools/call`
  - 异步执行，立即返回 `accepted`，结果通过 SSE 推送
- `GET /events`
  - SSE 事件流：`connected`、`tools_list`、`tool_complete`、`tool_error`

> 注意：`/tools/run` 返回体中的业务 JSON 在 `result.content[0].text`（字符串）里，建议用 `jq` 解析。

## 工具清单与 Schema 与示例
### 1) ecs-list-instances（列出实例）
- 描述：列出指定地域 ECS 实例，返回 `instance_id / instance_name / status / zone_id`。
- 输入 Schema：
```json
{
  "type": "object",
  "properties": {
    "region_id": { "type": "string", "description": "地域ID（默认配置值）" },
    "status": { "type": "string", "description": "实例状态过滤，如 Running/Stopped" },
    "page_number": { "type": "integer", "default": 1 },
    "page_size": { "type": "integer", "default": 50 }
  },
  "required": []
}
```
- 调用示例：
```bash
curl -s -X POST http://localhost:8002/tools/run \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "list-1",
    "name": "ecs-list-instances",
    "arguments": {"status": "Running", "page_size": 3}
  }' | jq -r '.result.content[0].text | fromjson'
```
- 返回字段：
  - `region_id / page_number / page_size / total_count`
  - `items[]`: `instance_id / instance_name / status / zone_id`
- 实现要点：使用 RPC 签名 `DescribeInstances`，解析 `Instances.Instance[*]`。

### 2) ecs-describe-instance-monitor-data（实例监控数据）
- 描述：获取单实例的监控点，Period 自动选择、分片聚合；下采样控制体量；输出 summary（CPU均值/P95/峰值、CPUCreditBalance最小值等）与采样点。数据来源为云监控（CMS）
- 限制：一次最多 400 点、最大 30 天；EBM/Windows 实例可能不支持，请优先选择 Linux 非 EBM 实例。
- 输入 Schema：
```json
{
  "type": "object",
  "properties": {
    "instance_id": {"type": "string", "description": "ECS 实例 ID"},
    "start_time": {"type": "string", "description": "ISO8601 UTC，如 2024-10-29T23:00:00Z"},
    "end_time": {"type": "string", "description": "ISO8601 UTC，默认当前 UTC"},
    "relative_range": {"type": "string", "description": "相对范围：1h/6h/24h/7d/30d"},
    "period": {"type": "integer", "enum": [60, 600, 3600], "description": "不填自动选择"},
    "metrics": {"type": "array", "items": {"type": "string"}, "description": "需要字段过滤"},
    "max_points": {"type": "integer", "default": 400, "description": "最大返回点数，超出下采样"}
  },
  "required": ["instance_id"]
}
```
- 调用示例：
```bash
IID="$(curl -s -X POST http://localhost:8002/tools/run -H 'Content-Type: application/json' \
  -d '{"id":"list","name":"ecs-list-instances","arguments":{"status":"Running","page_size":1}}' \
  | jq -r '.result.content[0].text | fromjson | .items[0].instance_id')"

curl -s -X POST http://localhost:8002/tools/run \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "mon-1",
    "name": "ecs-describe-instance-monitor-data",
    "arguments": {"instance_id": "'"$IID"'", "relative_range": "1h"}
  }' | jq -r '.result.content[0].text | fromjson'
```
- 返回字段：
  - `window`: `start/end/period/windows/total_points`
  - `summary`: `cpu_avg/cpu_p95/cpu_max/credit_min/points_truncated`
  - `data_sample`: 采样点（最多 50 条），每个点可能包含：
    - `CPU`（%）
    - `InternetRX/InternetTX`（公网入/出速率，bps；如该地域/实例无公开指标，可能为 null）
    - `IntranetInRate/IntranetOutRate`（内网入/出速率，bps）
    - `IOPSRead/IOPSWrite`（读写 IOPS，ops/s）
    - `MemoryUtilization`（内存利用率，%；需安装云监控 Agent）
    - `DiskUsageUtilization`（磁盘使用率，%；需安装云监控 Agent）
  - `warnings`: 提示窗口过大/分片等
- 实现要点：
  - 仅使用云监控（CMS）API：优先 `DescribeMetricList`（旧）→ 失败回退 `QueryMetricList`（新）；端点优先区域域名
  - 自动 Period：在 {60, 600, 3600} 中择最小且点数 ≤ 400；超出则分片
  - 向上取整到整分；支持 `relative_range`
  - 指标单位与取值以云监控定义为准（通常为百分比或速率），不同实例/地域可能为空

## 权限要求（RAM 策略）
最小权限通常需要：
- `ecs:DescribeInstances`（列出实例）
- `cms:QueryMetricList`（云监控新接口）
- `cms:DescribeMetricList`（云监控旧接口，作兜底）

示例策略（按需收窄到指定地域/实例）：
```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeInstances",
        "cms:QueryMetricList",
        "cms:DescribeMetricList"
      ],
      "Resource": "*"
    }
  ]
}
```

## 错误处理与故障排查
- 返回格式：MCP 风格；错误时 `is_error=true`，`result.content[0].text` 中提供 `{"error":"..."}`。
- 常见问题：
  - `403 Forbidden/404 Not Found`：RAM 权限不足或端点不匹配。
    - 处理：为调用主体授予 CMS 读权限；优选区域域名 `https://metrics.{region}.aliyuncs.com`；确认实例安装了云监控 Agent（内存/磁盘类指标）。
  - 时间窗口过大导致 0 点：缩小窗口或增大 period（如 3600）；服务会自动分片，但仍可能为空。
  - 结果体量过大：`max_points` 控制下采样；`points_truncated` 标记是否截断。
- 日志：
  - 控制台与 `ecs-mcp/logs/ecs-mcp.log`

## SSE 事件说明（/events）
- 连接后事件：
  - `connected`: `{ client_id, timestamp, server }`
  - `tools_list`: `{ tools: [...]}（当前可用工具列表）`
- 工具执行事件：
  - `tool_complete`: `{ id, tool, result, success, execution_time, timestamp }`
  - `tool_error`: `{ id, tool, error, success:false, execution_time, timestamp }`

## Roadmap
- 批量巡检（多实例并发聚合报告）
- 报告 Markdown 生成与钉钉通知
- 前端适配（图表/仪表）
- 更多指标与过滤条件（OS 类型、实例族过滤等）

---
如需帮助或新功能，请在仓库提交 Issue。本文档将随功能迭代持续更新。

## 架构流程图

```mermaid
flowchart TD
    Client[[Client\n(LLM/CLI/Frontend)]]
    API[/REST API\nGET /tools\nPOST /tools/run\nPOST /tools/call/]
    SSE[SSE /events]
    Server[FastAPI + Uvicorn\nECS MCP Server]
    Registry[Tool Registry]
    T1[ecs-list-instances\nRPC: DescribeInstances]
    T2[ecs-describe-instance-monitor-data\nCMS: DescribeMetricList / QueryMetricList\nAutoPeriod / Split / Downsample / Summary]
    Config[(Config Loader\nconfig.env / .env\nk8s-mcp/config.env\nbackend/config.env)]
    AliyunECS[ECS OpenAPI\nhttps://ecs.aliyuncs.com]
    AliyunCMS[CloudMonitor (CMS)\nhttps://metrics.<region>.aliyuncs.com]

    Client -->|HTTP| API --> Server
    Server --> SSE
    Server --> Registry
    Server --> Config

    Registry --> T1 --> AliyunECS
    Registry --> T2 --> AliyunCMS

    %% 回传路径
    T1 --> Registry --> Server --> API --> Client
    T2 --> Registry --> Server --> API --> Client
    Server -->|events| SSE --> Client
```

