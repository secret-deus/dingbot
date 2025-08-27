# Prometheus应用资源分析工具使用指南

## 概述

K8s Prometheus应用资源分析工具 (`k8s-prometheus-app-metrics`) 是一个专门用于查询特定应用Pod资源使用情况的工具。它基于Prometheus指标，提供14天内CPU和内存使用率与请求比例的平均值分析。

## 功能特性

- **应用级别查询**: 通过应用名称查询特定Deployment的资源使用情况
- **14天平均值**: 提供长期资源使用趋势分析
- **CPU/内存双重指标**: 同时分析CPU和内存的使用率与请求比例
- **Pod级别详情**: 提供每个Pod的详细资源使用数据
- **智能优化建议**: 根据使用率自动生成资源优化建议

## 工具参数

### 必填参数

- **app_name** (string): 应用名称（Deployment名称）

### 可选参数

- **namespace** (string): 命名空间，默认为 `default`
- **days** (integer): 查询天数，默认14天，范围1-30天
- **step** (string): 查询步长，默认 `1h`

## 环境配置

使用此工具前需要配置以下环境变量：

```bash
# Prometheus服务器地址（必填）
export PROMETHEUS_URL="http://your-prometheus-server:9090"

# 认证配置（可选，根据Prometheus配置决定）
export PROMETHEUS_ACCESS_KEY="your-access-key"
export PROMETHEUS_SECRET_KEY="your-secret-key"
export PROMETHEUS_AUTH_TYPE="basic"  # 支持: none, basic, bearer
```

## 使用示例

### 基本查询

```json
{
  "app_name": "nginx"
}
```

### 指定命名空间和时间范围

```json
{
  "app_name": "web-server",
  "namespace": "production",
  "days": 7
}
```

### 自定义查询步长

```json
{
  "app_name": "api-service",
  "namespace": "staging",
  "days": 3,
  "step": "30m"
}
```

## 返回结果结构

```json
{
  "app_name": "nginx",
  "namespace": "default",
  "query_days": 14,
  "query_time": "2025-08-26T17:00:00.000Z",
  "metrics": {
    "cpu_utilization_avg": 0.65,
    "memory_utilization_avg": 0.72,
    "cpu_requests_avg": 0.5,
    "memory_requests_avg": 1.0
  },
  "pod_details": [
    {
      "pod_name": "nginx-deployment-abc123",
      "cpu_utilization_avg": 0.63,
      "memory_utilization_avg": 0.70,
      "cpu_data_points": 336,
      "memory_data_points": 336
    }
  ],
  "summary": {
    "total_pods": 3,
    "data_points_cpu": 1008,
    "data_points_memory": 1008,
    "time_range": {
      "start": "2025-08-12T17:00:00.000Z",
      "end": "2025-08-26T17:00:00.000Z"
    }
  },
  "analysis": {
    "cpu_utilization_status": "利用率正常",
    "memory_utilization_status": "利用率正常",
    "recommendations": [
      "资源配置合理，无需调整"
    ]
  }
}
```

## 指标说明

### CPU/内存利用率

- **计算方式**: 实际使用量 / 请求量
- **数值范围**: 0.0 - N (可能超过1.0，表示超出请求量)
- **状态判断**:
  - 无数据: 0.0
  - 利用率过低: < 0.3 (30%)
  - 利用率较低: 0.3 - 0.6 (30%-60%)
  - 利用率正常: 0.6 - 0.8 (60%-80%)
  - 利用率较高: 0.8 - 1.0 (80%-100%)
  - 利用率过高: > 1.0 (>100%)

### 优化建议

工具会根据利用率自动生成建议：

- **CPU利用率 < 30%**: 建议减少CPU请求量
- **CPU利用率 > 90%**: 建议增加CPU请求量或优化应用性能
- **内存利用率 < 30%**: 建议减少内存请求量
- **内存利用率 > 90%**: 建议增加内存请求量
- **利用率正常**: 资源配置合理，无需调整

## Prometheus查询语句

工具基于以下Grafana查询语句构建：

### CPU使用率查询

```promql
label_replace(
  max(kube_pod_info{namespace="$namespace",created_by_kind="ReplicaSet", pod_ip!=""}) by (created_by_name, uid, pod, pod_ip, node),
  "replicaset",
  "$1",
  "created_by_name",
  "(.+)"
) * on(replicaset) group_left() max(kube_replicaset_owner{namespace="$namespace",owner_kind="Deployment",owner_name="$name"}) by (replicaset)
* on(pod) group_right() max(rate(container_cpu_usage_seconds_total{namespace="$namespace",container!="",container!="POD"}[5m])) by (pod, container) / max by(container, pod) (kube_pod_container_resource_requests{resource="cpu", namespace="$namespace"})
```

### 内存使用率查询

```promql
label_replace(
  max(kube_pod_info{namespace="$namespace",created_by_kind="ReplicaSet", pod_ip!=""}) by (created_by_name, uid, pod, pod_ip, node),
  "replicaset",
  "$1",
  "created_by_name",
  "(.+)"
) * on(replicaset) group_left() max(kube_replicaset_owner{namespace="$namespace",owner_kind="Deployment",owner_name="$name"}) by (replicaset)
* on(pod) group_right() max(container_memory_working_set_bytes{namespace="$namespace",container!="",container!="POD"}) by (pod, container) / max by(container, pod) (kube_pod_container_resource_requests{resource="memory", namespace="$namespace"})
```

## 故障排查

### 常见问题

1. **未配置Prometheus URL**
   - 错误信息: "未配置Prometheus URL，请设置PROMETHEUS_URL环境变量"
   - 解决方案: 设置正确的PROMETHEUS_URL环境变量

2. **认证失败**
   - 错误信息: HTTP 401/403错误
   - 解决方案: 检查PROMETHEUS_ACCESS_KEY和PROMETHEUS_SECRET_KEY配置

3. **查询无结果**
   - 可能原因: 应用名称不存在、命名空间错误、时间范围内无数据
   - 解决方案: 验证应用名称和命名空间，检查Prometheus中是否有相关指标

4. **查询超时**
   - 可能原因: Prometheus服务器响应慢、查询时间范围过大
   - 解决方案: 减少查询天数、检查Prometheus服务器状态

### 调试模式

启用调试日志查看详细查询过程：

```bash
export LOG_LEVEL=DEBUG
```

## 最佳实践

1. **合理设置查询时间范围**: 建议使用7-14天获得稳定的平均值
2. **定期监控**: 建议每周运行一次进行资源优化分析
3. **结合其他工具**: 配合k8s-resource-metrics-query工具进行综合分析
4. **关注趋势**: 重点关注利用率变化趋势而非单次数值

## 集成到MCP服务器

此工具已自动集成到K8s MCP服务器中，可通过以下方式调用：

- **工具名称**: `k8s-prometheus-app-metrics`
- **分类**: `kubernetes`
- **安全级别**: 只读查询（安全工具）

## 更新日志

- **v1.0.0** (2025-08-26): 初始版本，支持基本的应用资源分析功能