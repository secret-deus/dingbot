# 07 ECS 工具手册

[← Wiki 首页](./README.md)

本章说明 **ECS 侧三个 builtin 工具** 的参数、调用的阿里云 API、RAM、副作用与超时。

**前提**：配置 `ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET`，否则各工具 `execute` 开头会返回明确错误文案。

---

## 1. `ecs-list-instances`

| 项 | 内容 |
|----|------|
| 源码 | `backend/src/ecs_mcp/tools/ecs_list_instances.py` |
| 行为 | 分页调用 **DescribeInstances**，返回实例 ID 与少量元数据。 |
| 协议 | `ecs_rpc.rpc_get` → `https://ecs.aliyuncs.com`，`Version=2014-05-26` |
| RAM | `ecs:DescribeInstances` |
| 主要参数 | `region_id`（默认 `ALIBABA_CLOUD_ECS_REGION_ID`）、`status`、`page_number`、`page_size` |
| 副作用 | 无本地写文件 |
| 超时 | 依赖 `ecs_rpc` 内 httpx `timeout=30` |

---

## 2. `ecs-describe-instance-monitor-data`

| 项 | 内容 |
|----|------|
| 源码 | `backend/src/ecs_mcp/tools/ecs_monitor_data.py` |
| 行为 | ① **DescribeInstances** 解析实例所在地域；② **CMS** `DescribeMetricList` / `QueryMetricList` 拉 CPU 及可选网络/内存/磁盘等指标；③ 分片、下采样、summary。 |
| 协议 | `ecs_rpc` + `cms_rpc` |
| RAM | `ecs:DescribeInstances` + `cms:DescribeMetricList`、`cms:QueryMetricList`（以控制台为准） |
| 主要参数 | `instance_id`（必填）、`region_id`、`start_time`/`end_time`/`relative_range`、`period`、`metrics` |
| 限制 | 时间窗最大约 **30 天**（代码校验）；点数控制与 `max_points` 相关。 |
| 地域 | 未指定时按 `ALIBABA_CLOUD_REGION_CANDIDATES` 与默认列表多地域探测。 |
| 副作用 | 无本地写文件 |
| SDK | `ECSSDKClient` 已 import，主路径 **未**用 `DescribeInstanceMonitorData`；若未来改用 SDK，需增加 `ecs:DescribeInstanceMonitorData`。 |

---

## 3. `ecs-inspect`

| 项 | 内容 |
|----|------|
| 源码 | `backend/src/ecs_mcp/tools/ecs_inspection.py` |
| 行为 | 多地域/多条件 **DescribeInstances** 筛选实例 → 并发调用 `EcsDescribeInstanceMonitorDataTool` → 阈值规则 → **Markdown 报告写入磁盘**。 |
| RAM | 同 **DescribeInstances** + **CMS**（见上） |
| 主要参数 | `region_id` / `region_ids`、`status`、`name_contains`、`zone_id`、`max_instances`、`page_size`、`scan_all_pages`、`max_concurrency`、`thresholds`、`relative_range`、`period` 等 |
| **超时** | 类上 **`timeout=120`**（秒），与 `MCPToolSchema` 一致；编排需预留。 |
| **副作用** | 报告路径默认在 **`project_document/reports/ecs/`**（见源码内 `Path` 拼接）；联调时注意目录权限与 Git 忽略策略。 |

---

## 4. 研发自检顺序

1. `ecs-list-instances` 仅测 RAM **ECS 读**。
2. `ecs-describe-instance-monitor-data` 测 **ECS + CMS**。
3. `ecs-inspect` 小 `max_instances`、单地域，确认报告生成与磁盘路径。

---

## 5. 与阿里云控制台的对应关系

| 需求 | 控制台 |
|------|--------|
| 查 Action 是否授权 | RAM → 权限策略 → 脚本配置 → 搜索 `DescribeInstances`、`DescribeMetricList` |
| 查实例是否跨地域 | ECS 控制台实例列表看地域，与 `region_ids` 对齐 |

下一章：[08 研发对接指南](./08-integration-for-developers.md)
