# 资源告警配置指南

本文档介绍K8s MCP服务器中新增的资源告警功能配置选项。

## 功能概述

资源告警功能能够：
- 监控Kubernetes集群中deployment的资源利用率
- 当资源利用率超过设定阈值时自动触发告警
- 使用LLM智能分析资源问题并生成处理建议
- 通过钉钉Webhook发送格式化的告警消息

## 配置选项

### 基础告警配置

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `RESOURCE_ALERT_ENABLED` | `true` | 是否启用资源告警功能 |
| `MEMORY_ALERT_THRESHOLD` | `0.7` | 内存告警阈值（0.0-1.0，即70%） |
| `CPU_ALERT_THRESHOLD` | `0.8` | CPU告警阈值（0.0-1.0，即80%） |
| `ALERT_COOLDOWN_SECONDS` | `300` | 告警冷却时间（秒），防止频繁告警 |

### LLM智能分析配置

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `ENABLE_LLM_ANALYSIS` | `true` | 是否启用LLM智能分析 |
| `LLM_ANALYSIS_TIMEOUT` | `30` | LLM分析超时时间（秒） |

### 钉钉告警配置

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `ENABLE_DINGTALK_ALERT` | `true` | 是否启用钉钉告警推送 |
| `DINGTALK_WEBHOOK_URL` | - | 钉钉Webhook URL（必填） |
| `DINGTALK_SECRET` | - | 钉钉机器人签名密钥（可选） |
| `DINGTALK_RETRY_ATTEMPTS` | `3` | 钉钉消息发送重试次数 |
| `DINGTALK_RETRY_DELAY` | `2.0` | 钉钉消息重试延迟（秒） |
| `ALERT_MESSAGE_MAX_LENGTH` | `3500` | 告警消息最大长度（字符） |

## 配置示例

### 基础配置
```bash
# 启用资源告警功能
RESOURCE_ALERT_ENABLED=true

# 设置告警阈值
MEMORY_ALERT_THRESHOLD=0.75  # 75%内存使用率触发告警
CPU_ALERT_THRESHOLD=0.85     # 85%CPU使用率触发告警

# 设置冷却时间（10分钟）
ALERT_COOLDOWN_SECONDS=600
```

### 钉钉告警配置
```bash
# 启用钉钉告警
ENABLE_DINGTALK_ALERT=true

# 配置钉钉Webhook（替换为你的实际URL）
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your_token

# 配置签名密钥（如果启用了签名验证）
DINGTALK_SECRET=your_secret_key

# 自定义重试配置
DINGTALK_RETRY_ATTEMPTS=5
DINGTALK_RETRY_DELAY=3.0
```

### 生产环境建议配置
```bash
# 资源告警配置
RESOURCE_ALERT_ENABLED=true
MEMORY_ALERT_THRESHOLD=0.8   # 生产环境建议较高阈值
CPU_ALERT_THRESHOLD=0.85
ALERT_COOLDOWN_SECONDS=600   # 10分钟冷却期

# LLM分析配置
ENABLE_LLM_ANALYSIS=true
LLM_ANALYSIS_TIMEOUT=45      # 生产环境可适当延长超时

# 钉钉告警配置
ENABLE_DINGTALK_ALERT=true
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your_production_token
DINGTALK_SECRET=your_production_secret
DINGTALK_RETRY_ATTEMPTS=3
DINGTALK_RETRY_DELAY=2.0
ALERT_MESSAGE_MAX_LENGTH=3500
```

## 告警流程

1. **资源监控**: MetricsAggregator定期收集Prometheus指标数据
2. **阈值检查**: 比较14天平均利用率与配置的阈值
3. **冷却期检查**: 确保在冷却时间内不重复告警
4. **LLM分析**: 调用LLM生成智能分析和处理建议
5. **钉钉推送**: 发送格式化的告警消息到钉钉群

## 告警消息格式

告警消息包含以下信息：
- **紧急程度**: 自动计算的优先级（P0-P3）
- **资源信息**: 应用名称、命名空间、资源类型
- **利用率数据**: 当前内存和CPU利用率
- **智能分析**: LLM生成的问题诊断和优化建议
- **处理指南**: 具体的操作步骤和时间建议

## 配置验证

启动服务时，系统会自动验证配置：

```bash
# 查看配置验证日志
poetry run python k8s-mcp/start_k8s_mcp_http_server.py
```

验证内容包括：
- 阈值范围检查（0.0-1.0）
- URL格式验证
- 参数合理性检查

## 故障排查

### 常见问题

1. **告警未触发**
   - 检查 `RESOURCE_ALERT_ENABLED` 是否为 `true`
   - 确认资源利用率确实超过阈值
   - 检查是否在冷却期内

2. **LLM分析失败**
   - 检查 `ENABLE_LLM_ANALYSIS` 设置
   - 验证LLM处理器是否正常工作
   - 检查网络连接和超时设置

3. **钉钉消息发送失败**
   - 验证 `DINGTALK_WEBHOOK_URL` 格式
   - 检查钉钉机器人是否启用
   - 确认签名密钥配置正确

### 调试模式

开启调试模式获取详细日志：
```bash
K8S_MCP_DEBUG=true
```

## 性能建议

- **告警阈值**: 根据实际业务需求调整，避免过于敏感
- **冷却时间**: 建议不少于5分钟，避免告警风暴
- **重试配置**: 适度设置重试次数，避免过度重试影响性能
- **消息长度**: 保持在3500字符以内，确保钉钉正常显示

## 安全注意事项

1. **敏感信息保护**
   - 钉钉Webhook URL和密钥应妥善保管
   - 避免在日志中泄露敏感配置

2. **访问控制**
   - 限制钉钉机器人的群组范围
   - 定期轮换密钥

3. **监控告警**
   - 监控告警功能本身的健康状态
   - 设置告警失败的备用通知方式
