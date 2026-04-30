# K8s资源监控使用指南

## 概述

K8s MCP服务器V2版本提供了强大的资源监控和智能告警功能，能够自动监控Kubernetes应用的资源利用率，并在超过阈值时触发智能分析和通知。

## 功能特性

### 🔍 智能监控
- **实时监控**: 持续监控K8s应用的CPU和内存利用率
- **阈值检测**: 可配置的资源利用率阈值（默认CPU 80%，内存 70%）
- **多维度分析**: 支持多天历史数据分析和趋势预测

### 🧠 智能分析
- **LLM驱动**: 使用大语言模型分析资源问题
- **专业建议**: 生成具体的优化建议和操作步骤
- **问题诊断**: 自动识别资源瓶颈和潜在问题

### 🔔 智能告警
- **多渠道通知**: 支持钉钉、邮件等多种通知方式
- **冷却机制**: 防止频繁告警的智能冷却系统
- **格式化消息**: 结构化的告警消息，包含详细分析

### 🏗️ 架构优势
- **职责分离**: MCP服务器专注监控，后端处理分析
- **高可用**: 服务间故障隔离，监控不受影响
- **可扩展**: 易于添加新的监控指标和通知渠道

## 快速开始

### 1. 环境准备

确保以下服务正常运行：
- K8s MCP服务器
- 后端API服务 (处理LLM分析和钉钉发送)
- Prometheus服务器 (可选，用于历史数据)

### 2. 配置设置

**MCP服务器配置** (`k8s-mcp/config.env`):
```bash
# 启用资源告警
RESOURCE_ALERT_ENABLED=true

# 告警阈值 (0.0-1.0)
MEMORY_ALERT_THRESHOLD=0.7
CPU_ALERT_THRESHOLD=0.8

# 冷却时间 (秒)
ALERT_COOLDOWN_SECONDS=300

# 后端API配置
BACKEND_API_URL=http://localhost:8000
ENABLE_BACKEND_NOTIFICATIONS=true
API_TIMEOUT=30
API_MAX_RETRIES=3
```

**后端API配置** (`backend/config.env`):
```bash
# LLM配置
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-3.5-turbo

# 钉钉配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your-secret-key
```

### 3. 启动服务

```bash
# 1. 启动后端API服务
cd backend
poetry run python main.py

# 2. 启动MCP服务器
cd k8s-mcp
poetry run python start_k8s_mcp_http_server.py
```

### 4. 验证功能

```bash
# 检查服务状态
curl http://localhost:8000/health
curl http://localhost:8766/health

# 测试告警功能
curl -X POST http://localhost:8000/api/v2/alerts/test
```

## 使用方法

### 手动触发监控

使用MCP工具手动触发资源监控：

```python
# 通过MCP客户端调用
result = await mcp_client.call_tool(
    "k8s-resource-monitor",
    {
        "action": "monitor",
        "app_name": "my-app",
        "namespace": "production"
    }
)
```

### 查看监控统计

```python
# 获取监控统计信息
stats = await mcp_client.call_tool(
    "k8s-resource-monitor",
    {"action": "get-stats"}
)

print(f"告警触发次数: {stats['tool_stats']['alerts_triggered']}")
print(f"监控执行次数: {stats['tool_stats']['monitors_triggered']}")
```

### 测试告警功能

```python
# 测试告警功能
test_result = await mcp_client.call_tool(
    "k8s-resource-monitor",
    {
        "action": "test-alert",
        "app_name": "test-app",
        "namespace": "default",
        "force_alert": True
    }
)
```

### 获取应用列表

```python
# 获取可监控的应用列表
apps = await mcp_client.call_tool(
    "k8s-resource-monitor",
    {"action": "list-apps"}
)

for app in apps['applications']:
    print(f"应用: {app['name']}, 命名空间: {app['namespace']}")
```

## 告警流程

### 1. 监控检测
```
K8s资源监控 → 指标收集 → 阈值检查 → 告警触发
```

### 2. 智能分析
```
告警数据 → HTTP API → 后端服务 → LLM分析 → 生成建议
```

### 3. 通知发送
```
分析结果 → 格式化消息 → 钉钉发送 → 用户接收
```

## 告警消息示例

### 钉钉告警消息格式

```markdown
## 🔥 K8s资源告警 🚨

### 📋 资源信息
- **资源ID**: `deployment/production/web-app`
- **告警时间**: 2025-01-01 12:00:00
- **紧急度**: P1 (高 - 优先处理)

### 📊 资源利用率
- **CPU**: 85%
- **内存**: 78%
- **分析周期**: 7天

### ⚠️ 告警原因
- CPU利用率过高: 85.0% > 80.0%
- 内存利用率过高: 78.0% > 70.0%

### 🤖 智能分析
检测到严重的资源利用率问题。建议：
1. 立即增加Pod副本数到3个
2. 检查应用是否存在内存泄漏
3. 优化数据库查询性能
4. 考虑垂直扩容增加资源配额

### 🚀 快速处理
1. **立即检查**: `kubectl top pods -n production`
2. **扩容应用**: `kubectl scale deployment web-app --replicas=3`
3. **查看日志**: `kubectl logs -f deployment/web-app`
4. **监控趋势**: 观察资源使用趋势变化
```

## 配置详解

### 阈值配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MEMORY_ALERT_THRESHOLD` | 0.7 | 内存告警阈值（70%） |
| `CPU_ALERT_THRESHOLD` | 0.8 | CPU告警阈值（80%） |
| `ALERT_COOLDOWN_SECONDS` | 300 | 告警冷却时间（5分钟） |

### API通信配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `BACKEND_API_URL` | http://localhost:8000 | 后端API地址 |
| `API_TIMEOUT` | 30 | API请求超时时间（秒） |
| `API_MAX_RETRIES` | 3 | API请求最大重试次数 |

### 紧急度分级

| 利用率范围 | 紧急度 | 处理时间 | 说明 |
|------------|--------|----------|------|
| 90%+ | P0 🚨 | 立即处理 | 紧急情况，可能影响服务 |
| 80-90% | P1 🔥 | 优先处理 | 高优先级，需要关注 |
| 70-80% | P2 ⚠️ | 及时处理 | 中等优先级，计划处理 |
| <70% | P3 ℹ️ | 正常处理 | 低优先级，观察即可 |

## 最佳实践

### 1. 阈值设置建议

**生产环境**:
```bash
MEMORY_ALERT_THRESHOLD=0.75  # 75%
CPU_ALERT_THRESHOLD=0.80     # 80%
ALERT_COOLDOWN_SECONDS=600   # 10分钟
```

**测试环境**:
```bash
MEMORY_ALERT_THRESHOLD=0.85  # 85%
CPU_ALERT_THRESHOLD=0.90     # 90%
ALERT_COOLDOWN_SECONDS=300   # 5分钟
```

### 2. 监控策略

- **关键应用**: 设置较低阈值，快速响应
- **批处理任务**: 设置较高阈值，避免误报
- **开发环境**: 禁用告警或设置高阈值

### 3. 告警处理流程

1. **立即响应**: 收到P0/P1告警立即检查
2. **问题诊断**: 查看应用日志和资源使用情况
3. **快速处理**: 根据LLM建议进行扩容或优化
4. **跟踪观察**: 持续监控处理效果
5. **总结改进**: 分析告警原因，优化配置

### 4. 性能优化

- **合理设置冷却时间**: 避免告警风暴
- **优化API超时**: 根据网络环境调整
- **监控后端性能**: 确保LLM分析及时响应

## 故障排查

### 常见问题

#### 1. 告警未触发
```bash
# 检查配置
grep RESOURCE_ALERT_ENABLED k8s-mcp/config.env

# 检查阈值设置
grep ALERT_THRESHOLD k8s-mcp/config.env

# 查看日志
tail -f k8s-mcp/logs/k8s-mcp.log | grep -i alert
```

#### 2. 后端API连接失败
```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查网络连通性
ping localhost

# 查看API调用日志
tail -f k8s-mcp/logs/k8s-mcp.log | grep -i "api请求"
```

#### 3. 钉钉消息未发送
```bash
# 检查后端钉钉配置
grep DINGTALK backend/config.env

# 测试钉钉webhook
curl -X POST http://localhost:8000/api/v2/alerts/test

# 查看后端日志
tail -f backend/logs/app.log | grep -i dingtalk
```

### 调试命令

```bash
# 查看MCP服务器统计
curl http://localhost:8766/stats | jq '.alert_service'

# 查看后端告警统计
curl http://localhost:8000/api/v2/alerts/stats

# 手动触发告警测试
curl -X POST http://localhost:8000/api/v2/alerts/test

# 查看HTTP客户端统计
curl http://localhost:8766/stats | jq '.http_client'
```

## 扩展开发

### 添加新的监控指标

1. **扩展MetricsAggregator**:
```python
class CustomMetricsAggregator(K8sMetricsAggregator):
    async def collect_custom_metrics(self):
        # 收集自定义指标
        pass
```

2. **更新告警检测逻辑**:
```python
def _check_custom_thresholds(self, metrics_data):
    # 添加新的阈值检测
    pass
```

### 添加新的通知渠道

1. **扩展后端API**:
```python
@router.post("/alerts/slack")
async def send_slack_alert(alert_data: AlertData):
    # 发送Slack通知
    pass
```

2. **更新MCP配置**:
```bash
# 添加新的通知配置
ENABLE_SLACK_NOTIFICATIONS=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## 总结

K8s资源监控系统V2版本通过架构重构实现了：

- ✅ **智能监控**: 自动化的资源利用率监控
- ✅ **职责分离**: 清晰的服务边界和功能划分
- ✅ **智能分析**: LLM驱动的问题诊断和建议
- ✅ **可靠通知**: 多渠道、多格式的告警通知
- ✅ **易于扩展**: 模块化设计，便于功能扩展

该系统为K8s集群提供了全面的资源监控和智能告警能力，帮助运维团队及时发现和解决资源问题，确保应用的稳定运行。
