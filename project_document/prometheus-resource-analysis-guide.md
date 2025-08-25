# Prometheus资源利用率分析工具指南

## 概述

`k8s-prometheus-resource-analysis`工具通过直接调用Prometheus API获取集群中Pod的实际资源利用率数据，分析14天内按应用名称(selector=appname)统计的CPU和内存使用情况，识别平均利用率低于阈值的应用，并提供具体的资源优化建议。

## 功能特性

### 🎯 核心功能

1. **直接调用Prometheus API** - 获取准确的资源使用数据
2. **14天历史分析** - 基于长期数据进行分析，避免短期波动影响
3. **按应用分组统计** - 支持自定义标签选择器(默认为app)
4. **智能阈值检测** - 可配置CPU和内存利用率阈值
5. **详细优化建议** - 提供具体的资源配置调整建议
6. **资源节省预估** - 计算优化后可节省的资源量

### 📊 分析指标

- **CPU利用率** = 实际CPU使用量 / CPU请求量 × 100%
- **内存利用率** = 实际内存使用量 / 内存请求量 × 100%
- **优化潜力** = (阈值 - 当前利用率) × 请求量

## 工具参数

### 必需参数

无必需参数（所有参数都可以通过环境变量提供）

### 可选参数

| 参数 | 类型 | 默认值 | 环境变量 | 描述 |
|------|------|--------|----------|------|
| `prometheus_url` | string | - | `PROMETHEUS_URL` | Prometheus服务器URL |
| `access_key` | string | - | `PROMETHEUS_ACCESS_KEY` | 阿里云AccessKey |
| `secret_key` | string | - | `PROMETHEUS_SECRET_KEY` | 阿里云SecretKey |
| `auth_type` | string | "none" | - | 认证类型：none/basic/bearer |
| `days` | integer | 14 | - | 分析天数(1-30) |
| `cpu_threshold` | number | 60.0 | - | CPU利用率阈值(%) |
| `memory_threshold` | number | 60.0 | - | 内存利用率阈值(%) |
| `namespace_filter` | string | - | - | 命名空间过滤器(正则表达式) |
| `app_selector` | string | "app" | - | 应用选择器标签名 |
| `deployment_name` | string | - | - | 指定Deployment名称(支持正则表达式) |
| `analysis_mode` | string | "app" | - | 分析模式：deployment或app |
| `custom_queries` | object | - | - | 自定义Prometheus查询语句 |

### 环境变量配置

支持通过环境变量配置常用参数，优先级：**请求参数 > 环境变量 > 默认值**

#### 阿里云ARMS配置
```bash
export PROMETHEUS_URL='https://arms-prometheus.cn-hangzhou.aliyuncs.com'
export PROMETHEUS_ACCESS_KEY='your_access_key'
export PROMETHEUS_SECRET_KEY='your_secret_key'
```

#### 自建Prometheus配置
```bash
export PROMETHEUS_URL='http://prometheus.monitoring.svc.cluster.local:9090'
# 自建Prometheus通常不需要ACCESS_KEY和SECRET_KEY
```

## 分析模式

### 🎯 Deployment模式 (推荐)

基于您提供的精确查询语句，通过ReplicaSet精确关联Pod和Deployment关系：

**特点**:
- ✅ 精确关联Pod和Deployment关系
- ✅ 实时资源利用率计算
- ✅ 支持复杂的Kubernetes对象关联
- ✅ 适合精确的资源优化分析
- ⚠️ 需要完整的kube-state-metrics数据

**使用场景**: 针对特定Deployment进行精确的资源利用率分析

### 🏷️ App模式 (传统)

基于应用标签的传统查询方式：

**特点**:
- ✅ 基于应用标签简单分组
- ✅ 14天历史数据平均分析
- ✅ 适合大范围资源趋势分析
- ⚠️ 依赖应用标签的一致性

**使用场景**: 大范围应用的资源使用趋势分析

## 阿里云ARMS Prometheus配置

### 🔐 认证配置

阿里云ARMS Prometheus需要使用Basic认证，支持两种配置方式：

#### 方式1: 环境变量 (推荐)
```bash
export PROMETHEUS_ACCESS_KEY='your_access_key'
export PROMETHEUS_SECRET_KEY='your_secret_key'
```

#### 方式2: 请求参数
```json
{
  "prometheus_url": "https://arms-prometheus.cn-hangzhou.aliyuncs.com",
  "auth_type": "basic",
  "access_key": "your_access_key",
  "secret_key": "your_secret_key"
}
```

### 📡 API请求格式

阿里云ARMS Prometheus使用以下格式：

- **方法**: POST (不是GET)
- **URL**: `{prometheus_url}/api/v1/query`
- **头部**:
  - `Accept: application/json`
  - `Content-Type: application/json`
  - `Authorization: Basic <base64Encode(accessKey:secretKey)>`
- **请求体**:
  ```json
  {
    "query": "your_prometheus_query",
    "time": "1635302655",
    "timeout": "30000"
  }
  ```

### 🌐 阿里云地域端点

| 地域 | Prometheus端点 |
|------|----------------|
| 华东1(杭州) | `https://arms-prometheus.cn-hangzhou.aliyuncs.com` |
| 华东2(上海) | `https://arms-prometheus.cn-shanghai.aliyuncs.com` |
| 华北2(北京) | `https://arms-prometheus.cn-beijing.aliyuncs.com` |
| 华南1(深圳) | `https://arms-prometheus.cn-shenzhen.aliyuncs.com` |

## 使用方法

### 1. 阿里云ARMS Prometheus (推荐)

基于您提供的精确查询语句和阿里云ARMS认证：

```json
{
  "prometheus_url": "https://arms-prometheus.cn-hangzhou.aliyuncs.com",
  "auth_type": "basic",
  "analysis_mode": "deployment",
  "namespace_filter": "test",
  "deployment_name": "med-marketing",
  "cpu_threshold": 60.0,
  "memory_threshold": 60.0,
  "days": 14
}
```

### 2. 自建Prometheus

```json
{
  "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
  "auth_type": "none",
  "analysis_mode": "deployment",
  "namespace_filter": "test",
  "deployment_name": "med-marketing",
  "cpu_threshold": 60.0,
  "memory_threshold": 60.0,
  "days": 14
}
```

### 2. 使用您的原始查询语句

```json
{
  "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
  "analysis_mode": "deployment",
  "namespace_filter": "test",
  "deployment_name": "med-marketing",
  "custom_queries": {
    "memory_usage_query": "label_replace(max(kube_pod_info{namespace=\"test\",created_by_kind=\"ReplicaSet\", pod_ip!=\"\"}) by (created_by_name, uid, pod, pod_ip, node), \"replicaset\", \"$1\", \"created_by_name\", \"(.+)\") * on(replicaset) group_left() max(kube_replicaset_owner{namespace=\"test\",owner_kind=\"Deployment\",owner_name=\"med-marketing\"}) by (replicaset) * on(pod) group_right() max by(container, pod) (container_memory_working_set_bytes{namespace=\"test\", container!=\"\", image!=\"\", container!=\"POD\"})/max by(container, pod) (kube_pod_container_resource_requests{resource=\"memory\", namespace=\"test\"})"
  }
}
```

### 3. App模式 (传统)

```json
{
  "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
  "analysis_mode": "app",
  "days": 14,
  "cpu_threshold": 60.0,
  "memory_threshold": 60.0,
  "namespace_filter": "test|prod",
  "app_selector": "app"
}
```

### 4. 简化配置 (使用环境变量)

当环境变量已配置时，请求可以大大简化：

#### 阿里云ARMS (环境变量已设置)
```json
{
  "auth_type": "basic",
  "analysis_mode": "deployment",
  "namespace_filter": "test",
  "deployment_name": "med-marketing"
}
```

#### 自建Prometheus (环境变量已设置)
```json
{
  "analysis_mode": "deployment",
  "namespace_filter": "test",
  "deployment_name": "med-marketing"
}
```

### 2. 自定义查询

如果您有特定的Prometheus查询语句，可以使用`custom_queries`参数：

```json
{
  "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
  "days": 7,
  "cpu_threshold": 50.0,
  "memory_threshold": 70.0,
  "custom_queries": {
    "cpu_usage_query": "您的自定义CPU使用率查询语句",
    "memory_usage_query": "您的自定义内存使用率查询语句",
    "cpu_request_query": "您的自定义CPU请求量查询语句",
    "memory_request_query": "您的自定义内存请求量查询语句"
  }
}
```

## 默认Prometheus查询语句

### Deployment模式查询语句 (基于您的查询)

#### 内存使用率查询 (您提供的原始查询)
```promql
label_replace(
  max(kube_pod_info{namespace="$namespace",created_by_kind="ReplicaSet", pod_ip!=""}) by (created_by_name, uid, pod, pod_ip, node),
  "replicaset",
  "$1",
  "created_by_name",
  "(.+)"
) * on(replicaset) group_left() max(kube_replicaset_owner{namespace="$namespace",owner_kind="Deployment",owner_name="$name"}) by (replicaset)
* on(pod) group_right() max by(container, pod) (container_memory_working_set_bytes{namespace="$namespace", container!="", image!="", container!="POD"})/max by(container, pod) (kube_pod_container_resource_requests{resource="memory", namespace="$namespace"})
```

#### CPU使用率查询 (对应的CPU版本)
```promql
label_replace(
  max(kube_pod_info{namespace="$namespace",created_by_kind="ReplicaSet", pod_ip!=""}) by (created_by_name, uid, pod, pod_ip, node),
  "replicaset",
  "$1",
  "created_by_name",
  "(.+)"
) * on(replicaset) group_left() max(kube_replicaset_owner{namespace="$namespace",owner_kind="Deployment",owner_name="$name"}) by (replicaset)
* on(pod) group_right() rate(container_cpu_usage_seconds_total{namespace="$namespace", container!="", image!="", container!="POD"}[5m])/max by(container, pod) (kube_pod_container_resource_requests{resource="cpu", namespace="$namespace"})
```

#### 内存请求量查询
```promql
label_replace(
  max(kube_pod_info{namespace="$namespace",created_by_kind="ReplicaSet", pod_ip!=""}) by (created_by_name, uid, pod, pod_ip, node),
  "replicaset",
  "$1",
  "created_by_name",
  "(.+)"
) * on(replicaset) group_left() max(kube_replicaset_owner{namespace="$namespace",owner_kind="Deployment",owner_name="$name"}) by (replicaset)
* on(pod) group_right() max by(container, pod) (kube_pod_container_resource_requests{resource="memory", namespace="$namespace"}) / 1024 / 1024 / 1024
```

#### CPU请求量查询
```promql
label_replace(
  max(kube_pod_info{namespace="$namespace",created_by_kind="ReplicaSet", pod_ip!=""}) by (created_by_name, uid, pod, pod_ip, node),
  "replicaset",
  "$1",
  "created_by_name",
  "(.+)"
) * on(replicaset) group_left() max(kube_replicaset_owner{namespace="$namespace",owner_kind="Deployment",owner_name="$name"}) by (replicaset)
* on(pod) group_right() max by(container, pod) (kube_pod_container_resource_requests{resource="cpu", namespace="$namespace"})
```

> **注意**: `$namespace`和`$name`变量会被工具自动替换为实际的命名空间和Deployment名称。

### App模式查询语句 (传统方式)

#### CPU使用率查询
```promql
avg_over_time(
  (
    sum by (namespace, pod, app) (
      rate(container_cpu_usage_seconds_total{container!="POI",container!="",app!=""}[5m])
    )
  )[14d:5m]
) * 100
```

#### CPU请求量查询
```promql
avg_over_time(
  (
    sum by (namespace, pod, app) (
      kube_pod_container_resource_requests{resource="cpu",app!=""}
    )
  )[14d:5m]
) * 100
```

#### 内存使用率查询
```promql
avg_over_time(
  (
    sum by (namespace, pod, app) (
      container_memory_working_set_bytes{container!="POI",container!="",app!=""}
    )
  )[14d:5m]
) / 1024 / 1024 / 1024
```

#### 内存请求量查询
```promql
avg_over_time(
  (
    sum by (namespace, pod, app) (
      kube_pod_container_resource_requests{resource="memory",app!=""}
    )
  )[14d:5m]
) / 1024 / 1024 / 1024
```

## 输出报告格式

### 报告结构

```json
{
  "analysis_period": {
    "days": 14,
    "start_time": "2024-01-07T10:00:00",
    "end_time": "2024-01-21T10:00:00"
  },
  "thresholds": {
    "cpu_threshold_percent": 60.0,
    "memory_threshold_percent": 60.0
  },
  "summary": {
    "total_applications": 25,
    "low_cpu_utilization_apps": 8,
    "low_memory_utilization_apps": 12,
    "both_low_utilization_apps": 5
  },
  "applications": [
    {
      "app_name": "web-frontend",
      "namespace": "prod",
      "cpu_usage_cores": 0.15,
      "cpu_requests_cores": 0.5,
      "cpu_utilization_percent": 30.0,
      "memory_usage_gb": 0.8,
      "memory_requests_gb": 2.0,
      "memory_utilization_percent": 40.0,
      "needs_optimization": {
        "cpu": true,
        "memory": true,
        "overall": true
      },
      "optimization_potential": {
        "cpu_reduction_percent": 30.0,
        "memory_reduction_percent": 20.0
      }
    }
  ],
  "recommendations": [
    {
      "type": "cpu_optimization",
      "title": "CPU资源优化建议 - 可节省约2.5核",
      "description": "发现8个应用的CPU利用率低于60%",
      "applications": [
        {
          "name": "prod/web-frontend",
          "current_request": "0.5核",
          "utilization": "30.0%",
          "suggested_request": "0.25核"
        }
      ]
    }
  ]
}
```

### 关键字段说明

- **applications**: 所有应用的详细分析结果，按利用率排序
- **needs_optimization**: 标识是否需要优化
- **optimization_potential**: 优化潜力百分比
- **recommendations**: 具体的优化建议和预估节省量

## 使用场景

### 1. 阿里云ARMS Prometheus分析 (推荐)
```bash
# 使用阿里云ARMS Prometheus分析特定Deployment
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-prometheus-resource-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "prometheus_url": "https://arms-prometheus.cn-hangzhou.aliyuncs.com",
    "auth_type": "basic",
    "analysis_mode": "deployment",
    "namespace_filter": "test",
    "deployment_name": "med-marketing",
    "cpu_threshold": 60.0,
    "memory_threshold": 60.0,
    "days": 14
  }'
```

### 2. 批量Deployment分析
```bash
# 分析命名空间下所有web相关的Deployment
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-prometheus-resource-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
    "analysis_mode": "deployment",
    "namespace_filter": "prod",
    "deployment_name": "web-.*",
    "cpu_threshold": 50.0,
    "memory_threshold": 60.0
  }'
```

### 3. 使用原始查询语句
```bash
# 使用您提供的精确查询语句
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-prometheus-resource-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
    "analysis_mode": "deployment",
    "namespace_filter": "test",
    "deployment_name": "med-marketing",
    "custom_queries": {
      "memory_usage_query": "label_replace(max(kube_pod_info{namespace=\"test\",created_by_kind=\"ReplicaSet\", pod_ip!=\"\"}) by (created_by_name, uid, pod, pod_ip, node), \"replicaset\", \"$1\", \"created_by_name\", \"(.+)\") * on(replicaset) group_left() max(kube_replicaset_owner{namespace=\"test\",owner_kind=\"Deployment\",owner_name=\"med-marketing\"}) by (replicaset) * on(pod) group_right() max by(container, pod) (container_memory_working_set_bytes{namespace=\"test\", container!=\"\", image!=\"\", container!=\"POD\"})/max by(container, pod) (kube_pod_container_resource_requests{resource=\"memory\", namespace=\"test\"})"
    }
  }'
```

### 4. 传统应用标签分析
```bash
# 基于应用标签的传统分析方式
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-prometheus-resource-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "prometheus_url": "http://prometheus.monitoring.svc.cluster.local:9090",
    "analysis_mode": "app",
    "days": 7,
    "app_selector": "service",
    "namespace_filter": "microservices"
  }'
```

## 前端界面使用

在钉钉K8s运维机器人的前端界面中，您可以通过以下方式使用：

1. **聊天界面**: 直接输入"分析资源利用率"或"优化资源配置"
2. **工具调用**: 在工具列表中选择"k8s-prometheus-resource-analysis"
3. **参数配置**: 在界面中配置Prometheus URL和分析参数

## 配置建议

### Prometheus连接

#### 阿里云ARMS Prometheus (推荐)
1. **华东1(杭州)**: `https://arms-prometheus.cn-hangzhou.aliyuncs.com`
2. **华东2(上海)**: `https://arms-prometheus.cn-shanghai.aliyuncs.com`
3. **华北2(北京)**: `https://arms-prometheus.cn-beijing.aliyuncs.com`
4. **华南1(深圳)**: `https://arms-prometheus.cn-shenzhen.aliyuncs.com`

#### 自建Prometheus
1. **集群内访问**: `http://prometheus.monitoring.svc.cluster.local:9090`
2. **NodePort访问**: `http://node-ip:30090`
3. **Ingress访问**: `https://prometheus.your-domain.com`

### 查询优化

1. **标签一致性**: 确保Pod都有统一的应用标签
2. **时间范围**: 建议使用7-14天的数据进行分析
3. **命名空间过滤**: 使用正则表达式过滤相关命名空间

### 阈值设置

- **保守策略**: CPU 70%, Memory 80%
- **积极策略**: CPU 50%, Memory 60%
- **平衡策略**: CPU 60%, Memory 70%

## 故障排查

### 常见问题

1. **Prometheus连接失败**
   - 检查URL是否正确
   - 确认网络连通性
   - 验证认证配置

2. **查询无结果**
   - 检查标签选择器是否正确
   - 确认时间范围内有数据
   - 验证Prometheus中是否有相关指标

3. **数据不准确**
   - 检查Prometheus数据完整性
   - 确认指标收集是否正常
   - 验证查询语句是否适合您的环境

### 调试方法

#### 阿里云ARMS Prometheus调试
```bash
# 测试阿里云ARMS连接 (需要Basic认证)
curl -X POST "https://arms-prometheus.cn-hangzhou.aliyuncs.com/api/v1/query" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'access_key:secret_key' | base64)" \
  -d '{
    "query": "up",
    "time": "'$(date +%s)'",
    "timeout": "30000"
  }'

# 检查可用指标
curl -X POST "https://arms-prometheus.cn-hangzhou.aliyuncs.com/api/v1/label/__name__/values" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'access_key:secret_key' | base64)" \
  -d '{
    "timeout": "30000"
  }'
```

#### 自建Prometheus调试
```bash
# 测试Prometheus连接
curl "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up"

# 检查可用指标
curl "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/label/__name__/values"

# 验证应用标签
curl "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/label/app/values"
```

## 最佳实践

### 配置管理
1. **环境变量优先**: 使用环境变量配置URL和认证信息，提高安全性
2. **分环境配置**: 为不同环境(dev/test/prod)设置不同的环境变量
3. **敏感信息保护**: 避免在请求参数中直接传递AccessKey和SecretKey

### 分析策略
1. **定期分析**: 建议每月执行一次资源利用率分析
2. **渐进优化**: 不要一次性大幅调整资源配置
3. **监控影响**: 优化后持续监控应用性能
4. **文档记录**: 记录优化决策和效果
5. **团队协作**: 与开发团队协商资源调整

### 环境变量配置建议
```bash
# 在.bashrc或.zshrc中添加
export PROMETHEUS_URL='https://arms-prometheus.cn-hangzhou.aliyuncs.com'
export PROMETHEUS_ACCESS_KEY='your_access_key'
export PROMETHEUS_SECRET_KEY='your_secret_key'

# 或使用.env文件管理
echo "PROMETHEUS_URL=https://arms-prometheus.cn-hangzhou.aliyuncs.com" >> .env
echo "PROMETHEUS_ACCESS_KEY=your_access_key" >> .env
echo "PROMETHEUS_SECRET_KEY=your_secret_key" >> .env
```

---

## 更新日志

- **2025-01-21**: 生产就绪版本 v1.1.0
  - ✅ 完整功能实现，开发进度98%
  - ✅ 集成到钉钉K8s运维机器人MCP工具集
  - ✅ 支持前端界面和聊天交互调用
  - ✅ 完整的错误处理和日志记录
  - ✅ 生产环境部署就绪

- **2025-01-21**: 环境变量支持版本
  - 添加环境变量支持(`PROMETHEUS_URL`, `PROMETHEUS_ACCESS_KEY`, `PROMETHEUS_SECRET_KEY`)
  - 集成阿里云ARMS Prometheus认证
  - 支持POST请求格式和Basic认证
  - 简化配置，提高安全性
  - 更新文档和使用示例

- **2025-01-21**: 初始版本发布
  - 支持Prometheus API直接查询
  - 14天历史数据分析
  - 自定义查询语句支持
  - 详细优化建议生成
  - 基于用户提供的精确查询语句
