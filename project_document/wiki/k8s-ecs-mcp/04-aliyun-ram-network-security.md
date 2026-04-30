# 04 阿里云 RAM、网络与安全

[← Wiki 首页](./README.md)

本章面向**研发联调 + 安全评审**：说明「代码实际调用了哪些 API」「RAM 要怎么开」「机器要访问哪些域名」「凭证怎么管」。

---

## 1. 调用路径总览

| 模块 | 协议 | 端点 | 说明 |
|------|------|------|------|
| ECS OpenAPI | 阿里云 RPC（GET + 签名） | `https://ecs.aliyuncs.com` | `ecs_rpc.sign_parameters` + `Version=2014-05-26` |
| 云监控 CMS | 阿里云 RPC（GET + 签名） | `https://metrics.{region}.aliyuncs.com` 或 `https://metrics.aliyuncs.com` | `cms_rpc`，`Version=2019-01-01` |

**未使用**阿里云 SDK 完成全部链路的场景：列表实例、监控主路径以 **自签名 RPC** 为主；`ecs_client.ECSSDKClient` 仍保留 **DescribeInstanceMonitorData** 能力，但当前监控工具主逻辑以 **CMS** 为主（见 `ecs_monitor_data.py`）。

---

## 2. 工具 → OpenAPI Action → RAM Action

以下为 **RAM 策略里填写的 Action 名**（与 OpenAPI 文档一致）。**若控制台检索名称不同，以阿里云 RAM 控制台「权限策略编辑器」为准**。

### 2.1 ECS

| 工具名 | 代码中的 Action | 典型 RAM Action |
|--------|-----------------|-----------------|
| `ecs-list-instances` | `DescribeInstances` | `ecs:DescribeInstances` |
| `ecs-describe-instance-monitor-data` | `DescribeInstances`（地域探测） | `ecs:DescribeInstances` |
| `ecs-inspect` | `DescribeInstances` + 调用监控工具 | `ecs:DescribeInstances` + CMS 见下 |

可选（仅当走 SDK `describe_instance_monitor_data`）：`ecs:DescribeInstanceMonitorData`。

### 2.2 云监控 CMS

| 代码中的 Action | 典型 RAM Action |
|-----------------|-----------------|
| `DescribeMetricList` | `cms:DescribeMetricList` |
| `QueryMetricList` | `cms:QueryMetricList` |

监控工具会**依次尝试**两种 Action 与多个 `Namespace`/`MetricName` 组合，直到拿到数据。

---

## 3. 最小只读策略示例（JSON）

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeInstances"
      ],
      "Resource": [
        "acs:ecs:*:*:instance/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cms:DescribeMetricList",
        "cms:QueryMetricList"
      ],
      "Resource": "*"
    }
  ]
}
```

**收紧建议**：

- 用 **资源组**、**标签** 在 RAM 上限制 ECS 实例范围（`Condition` 键以阿里云文档为准）。
- **多地域**：`DescribeInstances` 必须带 `RegionId`；若只授权单地域，请将 `ALIBABA_CLOUD_ECS_REGION_ID` 与 `ALIBABA_CLOUD_REGION_CANDIDATES` 限制在已授权地域，否则地域探测会失败。

---

## 4. 网络出站（防火墙 / 代理）

运行 `backend` 的机器需能 **HTTPS 访问**：

| 目的 | URL 模式 |
|------|----------|
| ECS | `https://ecs.aliyuncs.com` |
| CMS 区域 | `https://metrics.<region>.aliyuncs.com` |
| CMS 公共 | `https://metrics.aliyuncs.com` |

若使用 **VPC Endpoint**、**固定出口 IP** 或 **企业代理**，需在代理上放行 SNI/目标域名；**无控制台权限时**只能通过抓包或连通性脚本验证。

---

## 5. 凭证形态

| 形态 | 环境变量 | 本仓库支持情况 |
|------|----------|----------------|
| 长期 AK/SK | `ALIBABA_CLOUD_ACCESS_KEY_ID` / `SECRET` | **RPC 主路径使用** |
| STS 临时 | `ALIBABA_CLOUD_SECURITY_TOKEN` + AK/SK | `ECSConfig` 与 `ECSSDKClient` 支持 Token；**`ecs_rpc` / `cms_rpc` 当前未把 Token 拼进请求** → 纯 RPC 场景需改造或继续用长期 AK |

**研发注意**：若安全策略要求 **仅用 STS**，需要二选一：

1. 改造 `ecs_rpc`/`cms_rpc` 支持 `SecurityToken` 公共参数；或
2. 全部改用官方 SDK 凭证链（与现有「绕过 SDK 凭证链」注释权衡）。

---

## 6. 审计与限流

- 建议在阿里云开启 **ActionTrail**，记录 `ecs` / `cms` API。
- 阿里云侧可能有 **QPS/流控**；`ecs-inspect` 高并发拉监控时注意 `max_concurrency` 与 RAM 账号配额。

---

## 7. 自检命令思路（研发本地）

以下为**思路**，非仓库强制脚本：

1. 配置 AK 后调用 `ecs-list-instances`，`region_id` 与线上一致。
2. 对同一实例调用 `ecs-describe-instance-monitor-data`，`relative_range` 设为 `1h`。
3. 若报 RAM 拒绝，在控制台查看具体 **Action** 名称并补策略。

下一章：[05 Kubernetes RBAC](./05-kubernetes-rbac-and-kubeconfig.md)
