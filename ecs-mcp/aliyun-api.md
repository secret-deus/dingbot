## 阿里云 ECS/云监控 API 概述（本项目实现）

本文档概述本项目调用阿里云 ECS 与云监控（CMS）相关接口的核心逻辑、参数映射与返回值要点，便于排查问题与对接联调。

### 1. 列出实例（ECS）
- 接口：`DescribeInstances`（ECS OpenAPI 2014-05-26）
- 入口函数：`ecs_list_instances` 与 `ecs_inspect` 列表阶段
- 签名与请求：自研签名 + HTTP GET（`rpc_ecs.rpc_get`），`endpoint=https://ecs.aliyuncs.com`
- 关键参数（Query）：
  - **Action**: `DescribeInstances`
  - **RegionId**: 如未传则使用配置 `cfg.region_id`
  - **PageNumber**: 默认 1
  - **PageSize**: 默认 50，1-100
  - 可选过滤：**Status**、**ZoneId**、`InstanceIds`（在地域解析时用于校验实例是否在该地域）
- 关键返回解析：
  - `Instances.Instance[]` → 映射为 `{ instance_id, instance_name, status, zone_id }`
  - `TotalCount`

### 2. 监控数据（优先 CMS，CPU 兜底 ECS）
- 入口函数：`ecs_describe_instance_monitor_data`
- 目标：返回 CPU/网络/内网/IOPS/内存/磁盘等常用指标，统一时间窗聚合与采样。

#### 2.1 地域解析
- 目的：避免 `RegionId` 传错导致空数据。
- 步骤：
  1) 如果传入 `region_id` 或配置 `cfg.region_id` 能在该地域通过 `DescribeInstances` 命中实例，则采用之；
  2) 否则遍历候选地域（环境变量 `ALIBABA_CLOUD_REGION_CANDIDATES` + 常见地域列表）逐一校验；
  3) 若仍未命中，用初始 `region_id` 兜底。
- 影响范围：CMS 与 ECS 的后续查询均使用解析出的 `rid`。

#### 2.2 时间窗与 period
- 输入：
  - `start_time`/`end_time`（ISO，可无 Z，默认视为展示时区 `timezone_name`，再转 UTC）
  - 或 `relative_range`（默认 `1h`，支持 `m/h/d`）
  - `period`（可选；若未指定，自动按窗口大小选择 60/600/3600，保证每窗点数≤400）
- 拆窗：将整体时间窗按 `period*400` 分片逐窗请求并合并。

#### 2.3 CMS 拉数（优先）
- 接口族：`DescribeMetricList` / `QueryMetricList`（CloudMonitor 2019-01-01）
- 入口与签名：`rpc_cms.rpc_get`（自研签名 + HTTP GET）
- Endpoint：优先地域化 `https://metrics.{rid}.aliyuncs.com`，失败回退 `https://metrics.aliyuncs.com`
- Namespace/Dimensions：
  - 对于 `vm.*` 与 `diskusage_utilization`：`Namespace=acs_ecs_dashboard`，`Dimensions=[{"instanceId":"<iid>"}]`
  - 其他：`Namespace=acs_ecs`，`Dimensions={"instanceId":"<iid>"}`
- 关键参数：
  - **MetricName**：见下方指标映射与多候选策略
  - **Period**：按 period 传递；个别指标在 CMS 仅 300s 粒度，代码中已兼容
  - **Statistics**：`Average,Maximum,Minimum`（确保返回多口径）
  - **StartTime/EndTime**：UTC 字符串，格式 `YYYY-MM-DD HH:MM:SS`
  - **RegionId**：解析出的 `rid`
- 指标映射与候选：
  - CPUUtilization → [`CPUUtilization`]
  - MemoryUtilization → [`vm.MemoryUtilization`]
  - DiskUsageUtilization → [`diskusage_utilization`]
  - InternetInRate/InternetOutRate/IntranetInRate/IntranetOutRate → 同名
- 数据点解析：兼容返回 `Datapoints` 为 JSON 字符串或数组；时间戳字段支持：`timestamp`(ms)、`Timestamp`/`TimeStamp`(ISO)。
- 数值选择：优先 `statistic` 指定口径（默认 `Average`），缺失时回退 `Value/Maximum/Minimum`。

#### 2.4 ECS 兜底（仅 CPU）
- 接口：`DescribeInstanceMonitorData`（ECS 2014-05-26）
- 入口与签名：`rpc_ecs.rpc_get`（自研签名 + HTTP GET，endpoint `https://ecs.aliyuncs.com`）
- 关键参数：
  - **InstanceId**
  - **StartTime/EndTime**：ISO UTC（`YYYY-MM-DDTHH:MM:SSZ`）
  - **Period**：与上文一致
  - **RegionId**：解析出的 `rid`
- 返回解析：`MonitorData.InstanceMonitorData[]`，取 `TimeStamp` 与 `CPU` 填充。

#### 2.5 指标汇总与输出
- 统一将各指标按 `TimeStamp` 合并为 `window_map`
- 统计项：`cpu_avg`、`cpu_p95`、`cpu_max`；内存 p95、最大；磁盘当前值（优先 `DescribeMetricLast` 取当前）
- 采样下发：`data_sample` 最多 50 条；`window.total_points` 记录合并后点数；`summary.points_truncated` 指示是否被抽样
- `meta.units` 标注各指标单位

### 3. 批量巡检（ecs_inspect）与并发
- 流程：
  1) 先使用 `DescribeInstances` 分页拉取候选实例（可按 `Status/ZoneId` 过滤，`name_contains` 模糊）
  2) 使用信号量限制并发（默认 `max_concurrency=5`），对每个实例调用 `ecs_describe_instance_monitor_data`
  3) two_phase=true 时：先用 `quick_window`（默认 15m）拉取 CPU/内外网三项；若 CPU 无 p95，再补一次完整窗口
  4) 风险评分：基于 CPU p95、内存 p95/最大、磁盘当前值，产出 high/medium/low
  5) 生成 Markdown/JSON 报告到 `project_document/reports/ecs`

### 4. 环境变量与配置要点
- `ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET`：鉴权必需
- `ECS_TIMEZONE`：展示/解析无时区输入用（默认 `Asia/Shanghai`），实际请求统一转 UTC
- `ALIBABA_CLOUD_REGION_CANDIDATES`：地域候选（英文逗号分隔）
- `ECS_RETRY_ATTEMPTS`（若在上层调用处使用）：重试次数
- 其他配置见 `config.ECSConfig`（如 `call_timeout_seconds`、`host/port` 等）

### 5. 错误处理与兼容
- CMS 与 ECS 请求均记录关键日志（不含 AK/SK），便于问题定位；CMS 日志额外打印本地时区的 Start/End 以便人工核对
- 兼容 `Datapoints`/`Datapoint` 多形态；时间戳兼容 `ms/ISO` 多形态
- 数值越界（<0 或 >100 的百分比）进行限幅
- 当内存/磁盘缺失时给出可操作性告警（Agent 未安装/未上报等）

### 6. 相关代码位置
- `server.py`：
  - `ecs_list_instances`、`ecs_describe_instance_monitor_data`、`ecs_inspect`
- `rpc_ecs.py`：ECS OpenAPI 自研签名与 GET 请求
- `rpc_cms.py`：CMS OpenAPI 自研签名与 GET 请求，含时间格式工具 `format_cms_time`

### 7. 快速对照：主要接口与参数

| 领域 | 接口 | 版本 | 关键参数 | 备注 |
|---|---|---|---|---|
| ECS | DescribeInstances | 2014-05-26 | RegionId, PageNumber, PageSize, Status, ZoneId, InstanceIds | 列表/地域校验 |
| CMS | DescribeMetricList/QueryMetricList | 2019-01-01 | Namespace, MetricName, Period, Statistics, StartTime, EndTime, Dimensions, RegionId | 指标优先通道 |
| ECS | DescribeInstanceMonitorData | 2014-05-26 | InstanceId, StartTime(ISO Z), EndTime(ISO Z), Period, RegionId | CPU 兜底 |

以上为当前实现的真实行为与参数映射，可据此核对控制台、OpenAPI 文档或抓包结果。

### 8. 调用示例

以下示例用于本地或集成环境调试，演示三种典型路径：

#### 8.1 通过 FastMCP Client 调用工具（推荐）

```python
import asyncio, json, os
from fastmcp import Client

async def main():
    # 后端以 SSE 方式启动时的地址（见 server.run）
    base = os.getenv('ECS_MCP_BASE','http://127.0.0.1:8012/sse')
    async with Client(base) as c:
        # 1) 列出实例
        res = await c.call_tool('ecs_list_instances', {'page_size': 5})
        data = json.loads(res[0].text) if isinstance(res, list) and hasattr(res[0], 'text') else res
        items = (data.get('items') or [])
        print('instances:', len(items))
        if not items:
            return
        iid = items[0]['instance_id']

        # 2) 单实例监控（1h/60s）
        mon = await c.call_tool('ecs_describe_instance_monitor_data', {
            'instance_id': iid,
            'relative_range': '1h',
            'period': 60,
        })
        mon = json.loads(mon[0].text) if isinstance(mon, list) and hasattr(mon[0], 'text') else mon
        print('summary:', mon.get('summary'))

        # 3) 批量巡检（两阶段示例）
        inspect = await c.call_tool('ecs_inspect', {
            'two_phase': True,
            'quick_window': '15m',
            'relative_range': '12h',
            'period': 600,
            'max_concurrency': 5,
        })
        inspect = json.loads(inspect[0].text) if isinstance(inspect, list) and hasattr(inspect[0], 'text') else inspect
        print('inspect summary:', inspect.get('summary'))

asyncio.run(main())
```

#### 8.2 在应用内嵌跑（无需 HTTP/SSE 绑定）

```python
import asyncio
from fastmcp import Client
from ecs_mcp_fastmcp.server import build_server

async def main():
    app = build_server()
    async with Client(app) as c:
        res = await c.call_tool('ecs_list_instances', {'page_size': 1})
        print(res)

asyncio.run(main())
```

#### 8.3 直接调用阿里云 OpenAPI（调试用）

注意：生产环境请优先通过上述工具调用（统一了地域解析、分片聚合与指标兼容），以下仅供排障定位：

```python
import asyncio
import os
from ecs_mcp_fastmcp.rpc_ecs import rpc_get as ecs_rpc_get
from ecs_mcp_fastmcp.rpc_cms import rpc_get as cms_rpc_get

AK = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
SK = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
REGION = 'cn-beijing'
INSTANCE_ID = '<your-instance-id>'

async def main():
    # ECS: DescribeInstances
    inst = await ecs_rpc_get({
        'Action': 'DescribeInstances',
        'RegionId': REGION,
        'PageNumber': 1,
        'PageSize': 1,
        'InstanceIds': f'[
            "{INSTANCE_ID}"
        ]',
    }, AK, SK)
    print('DescribeInstances keys:', inst.keys())

    # CMS: DescribeMetricList（CPUUtilization 示例）
    dps = await cms_rpc_get({
        'Action': 'DescribeMetricList',
        'Namespace': 'acs_ecs',
        'MetricName': 'CPUUtilization',
        'Period': 60,
        'Statistics': 'Average,Maximum,Minimum',
        'StartTime': '2025-09-25 00:00:00',  # UTC
        'EndTime': '2025-09-25 01:00:00',    # UTC
        'Dimensions': '{"instanceId":"%s"}' % INSTANCE_ID,
        'RegionId': REGION,
    }, AK, SK, endpoint=f'https://metrics.{REGION}.aliyuncs.com')
    print('DescribeMetricList keys:', dps.keys())

asyncio.run(main())
```


