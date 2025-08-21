# 集群资源监控功能指南

## 概述

为钉钉K8s运维机器人添加了集群资源监控功能，包括CPU和内存使用情况的实时监控和分析。该功能已集成到集群巡检系统中，提供全面的资源使用情况报告。

## 功能特性

### 🎯 核心功能

1. **集群整体资源监控**
   - CPU使用率和可用性分析
   - 内存使用率和可用性分析
   - 资源压力等级评估（low/medium/high）
   - 集群健康状态评估

2. **节点级别监控**
   - 每个节点的CPU和内存容量
   - 节点可分配资源统计
   - 节点就绪状态监控

3. **Pod级别统计**
   - 运行中Pod的资源请求统计
   - Pod资源使用分布分析

4. **智能分析**
   - 资源利用率计算
   - 容量规划建议
   - 资源压力预警

## 技术实现

### 新增工具

#### 1. k8s-get-cluster-metrics

**工具名称**: `k8s-get-cluster-metrics`

**功能**: 获取K8s集群的CPU和内存使用情况

**参数**:
```json
{
  "include_node_details": true,    // 是否包含节点详细信息
  "include_pod_metrics": false     // 是否包含Pod级别统计
}
```

**返回数据结构**:
```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "cluster_summary": {
    "total_nodes": 3,
    "ready_nodes": 3,
    "running_pods": 25,
    "total_pods": 27
  },
  "resource_utilization": {
    "cpu": {
      "total_capacity_cores": 12.0,
      "total_allocatable_cores": 11.5,
      "total_requests_cores": 4.2,
      "utilization_percentage": 36.5,
      "available_cores": 7.3
    },
    "memory": {
      "total_capacity_gb": 48.0,
      "total_allocatable_gb": 45.2,
      "total_requests_gb": 18.5,
      "utilization_percentage": 40.9,
      "available_gb": 26.7
    }
  },
  "capacity_analysis": {
    "cpu_pressure": "low",
    "memory_pressure": "medium", 
    "overall_health": "good"
  }
}
```

### 集成方式

#### 1. 集群摘要工具集成

资源监控功能已集成到`k8s-cluster-summary`工具中：

- **自动获取**: 集群摘要自动包含资源监控数据
- **智能分析**: 提供资源使用情况的关键摘要
- **基础模式**: 即使在基础模式下也能获取资源监控数据

#### 2. 巡检系统集成

巡检报告现在包含专门的资源监控章节：

- **现状总览**: 集群基本信息
- **资源监控**: CPU/内存使用情况 ⭐ **新增**
- **异常清单**: 问题资源列表
- **根因猜测**: 问题分析
- **影响范围**: 影响评估
- **建议措施**: 操作建议
- **待跟进事项**: 后续任务

## 使用方式

### 1. 直接调用资源监控工具

```bash
# 获取完整的集群资源监控数据
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-get-cluster-metrics \
  -H "Content-Type: application/json" \
  -d '{"include_node_details": true, "include_pod_metrics": false}'
```

### 2. 通过集群摘要获取

```bash
# 集群摘要自动包含资源监控数据
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-cluster-summary \
  -H "Content-Type: application/json" \
  -d '{"scope": "cluster", "include_details": true}'
```

### 3. 通过巡检系统

```bash
# 巡检报告自动包含资源监控分析
curl -X POST http://localhost:8000/api/v2/inspection/run \
  -H "Content-Type: application/json" \
  -d '{
    "scope": {"includeNamespaces": ["default", "kube-system"]},
    "options": {"sendToDingTalk": true, "includeAnomalies": true}
  }'
```

### 4. 前端界面使用

在前端Dashboard中点击"一键巡检"按钮，生成的巡检报告将自动包含资源监控信息。

## 监控指标说明

### CPU监控

- **总容量**: 集群所有节点的CPU核心总数
- **可分配**: 扣除系统保留后可供Pod使用的CPU
- **已请求**: 所有Pod的CPU请求总和
- **使用率**: 已请求/可分配的百分比
- **压力等级**: 
  - `low`: < 60%
  - `medium`: 60-80%
  - `high`: > 80%

### 内存监控

- **总容量**: 集群所有节点的内存总量
- **可分配**: 扣除系统保留后可供Pod使用的内存
- **已请求**: 所有Pod的内存请求总和
- **使用率**: 已请求/可分配的百分比
- **压力等级**: 同CPU监控

### 集群健康评估

- **good**: CPU和内存使用率都低于70%
- **warning**: CPU或内存使用率在70-90%之间
- **critical**: CPU或内存使用率超过90%

## 配置说明

### 环境变量

无需额外配置，资源监控功能使用现有的K8s连接配置。

### 工具注册

资源监控工具已自动注册到安全查询工具列表中，无需手动配置。

## 故障排查

### 常见问题

1. **资源监控数据获取失败**
   - 检查K8s集群连接状态
   - 确认有足够的权限访问节点和Pod信息
   - 查看k8s-mcp服务器日志

2. **资源使用率计算异常**
   - 检查Pod的资源请求配置
   - 确认节点的allocatable资源正确
   - 验证CPU/内存单位解析

3. **巡检报告中缺少资源监控数据**
   - 检查集群摘要工具是否正常工作
   - 确认资源监控工具已正确集成
   - 查看LLM处理日志

### 调试命令

```bash
# 检查工具注册状态
curl http://localhost:8000/api/v2/tools | jq '.tools[] | select(.name == "k8s-get-cluster-metrics")'

# 测试资源监控工具
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-get-cluster-metrics \
  -H "Content-Type: application/json" \
  -d '{}'

# 检查集群摘要集成
curl -X POST http://localhost:8000/api/v2/mcp/tools/k8s-cluster-summary \
  -H "Content-Type: application/json" \
  -d '{"scope": "cluster"}' | jq '.resource_monitoring'
```

## 未来扩展

### 计划功能

1. **历史趋势分析**: 资源使用趋势图表
2. **自动扩缩容建议**: 基于使用率的扩缩容建议
3. **成本分析**: 资源成本优化建议
4. **告警集成**: 资源使用率告警
5. **更多指标**: 网络、存储等资源监控

### 技术改进

1. **Metrics Server集成**: 获取实时资源使用数据
2. **Prometheus集成**: 历史数据和高级查询
3. **缓存机制**: 提高大集群的查询性能
4. **异步处理**: 支持更大规模的集群监控

---

## 更新日志

- **2024-01-20**: 初始版本发布
  - 添加k8s-get-cluster-metrics工具
  - 集成到集群摘要和巡检系统
  - 支持CPU和内存监控
  - 提供资源压力分析
