# 资源告警配置指南 V2

## 概述

本文档详细说明了K8s MCP服务器V2版本的资源告警系统配置选项。V2版本实现了架构重构，将告警检测与业务处理分离，提升了系统的可维护性和扩展性。

## 🔄 V2版本重要变更

### 架构优化
- ✅ **职责分离**: MCP服务器专注K8s资源监控和告警检测
- ✅ **后端处理**: LLM分析和钉钉发送移至后端API服务
- ✅ **HTTP通信**: 通过标准HTTP API实现服务间通信
- ✅ **配置简化**: 移除钉钉相关配置，减少60%配置项

### 数据流变更
```
旧版本: K8s监控 → 告警检测 → LLM分析 → 钉钉发送
新版本: K8s监控 → 告警检测 → HTTP API → [后端: LLM分析 → 钉钉发送]
```

## 配置选项

### 基础告警配置

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `RESOURCE_ALERT_ENABLED` | `true` | 是否启用资源告警功能 |
| `MEMORY_ALERT_THRESHOLD` | `0.7` | 内存告警阈值（0.0-1.0，即70%） |
| `CPU_ALERT_THRESHOLD` | `0.8` | CPU告警阈值（0.0-1.0，即80%） |
| `ALERT_COOLDOWN_SECONDS` | `300` | 告警冷却时间（秒），防止频繁告警 |

### LLM分析配置

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `ENABLE_LLM_ANALYSIS` | `true` | 启用LLM智能分析（后端处理） |
| `LLM_ANALYSIS_TIMEOUT` | `30` | LLM分析超时时间（秒） |

### 后端API通信配置（新增）

| 环境变量 | 默认值 | 描述 |
|---------|--------|------|
| `BACKEND_API_URL` | `http://localhost:8000` | 后端API服务地址 |
| `ENABLE_BACKEND_NOTIFICATIONS` | `true` | 启用后端通知功能 |
| `API_TIMEOUT` | `30` | API请求超时时间（秒） |
| `API_MAX_RETRIES` | `3` | API请求最大重试次数 |

### 已移除的配置项

以下配置项已移至后端管理，无需在MCP服务器配置：

| 移除的环境变量 | 说明 |
|-------------|------|
| `ENABLE_DINGTALK_ALERT` | 钉钉功能统一由后端管理 |
| `DINGTALK_WEBHOOK_URL` | 钉钉配置移至后端 |
| `DINGTALK_SECRET` | 钉钉配置移至后端 |
| `DINGTALK_RETRY_ATTEMPTS` | 重试逻辑移至后端 |
| `DINGTALK_RETRY_DELAY` | 重试逻辑移至后端 |
| `ALERT_MESSAGE_MAX_LENGTH` | 消息格式化移至后端 |

## 配置示例

### 完整配置文件示例

```bash
# k8s-mcp/config.env

# ===== 基础K8s配置 =====
KUBECONFIG_PATH=/path/to/kubeconfig
K8S_NAMESPACE=default

# ===== 资源告警配置 =====
RESOURCE_ALERT_ENABLED=true
MEMORY_ALERT_THRESHOLD=0.7
CPU_ALERT_THRESHOLD=0.8
ALERT_COOLDOWN_SECONDS=300

# ===== LLM智能分析配置 =====
ENABLE_LLM_ANALYSIS=true
LLM_ANALYSIS_TIMEOUT=30

# ===== 后端API通信配置 =====
BACKEND_API_URL=http://localhost:8000
ENABLE_BACKEND_NOTIFICATIONS=true
API_TIMEOUT=30
API_MAX_RETRIES=3
```

### 开发环境配置

```bash
# 本地开发环境
BACKEND_API_URL=http://localhost:8000
ENABLE_BACKEND_NOTIFICATIONS=true
API_TIMEOUT=10
API_MAX_RETRIES=2
```

### 生产环境配置

```bash
# 生产环境
BACKEND_API_URL=https://api.company.com
ENABLE_BACKEND_NOTIFICATIONS=true
API_TIMEOUT=30
API_MAX_RETRIES=5
```

## 配置验证

### 自动验证规则

系统启动时会自动验证配置合理性：

1. **阈值验证**:
   - 内存和CPU阈值必须在0.0-1.0之间
   - 告警冷却时间不能为负数

2. **API配置验证**:
   - 后端API URL格式检查
   - 超时时间合理范围验证（5-120秒）
   - 重试次数合理范围验证（0-10次）

3. **依赖性检查**:
   - 启用后端通知时必须配置API URL
   - LLM功能依赖后端API可用性

### 配置测试命令

```bash
# 验证配置有效性
poetry run python -c "
from k8s_mcp.config import get_config
config = get_config()
print('配置验证成功' if config.validate_config() else '配置验证失败')
"

# 测试后端API连接
curl -f http://localhost:8000/health || echo "后端API不可达"

# 测试告警功能
curl -X POST http://localhost:8000/api/v2/alerts/test
```

## 功能特性详解

### 告警检测机制

1. **阈值检查**:
   - 支持CPU和内存利用率独立配置
   - 百分比格式输入，自动转换为小数

2. **冷却机制**:
   - 防止相同资源频繁告警
   - 每个资源独立的冷却计时器
   - 可配置的冷却时间

3. **统计信息**:
   - 告警触发次数统计
   - 后端API调用成功/失败统计
   - 冷却抑制统计

### HTTP API通信

1. **异步请求**:
   - 非阻塞的HTTP客户端
   - 异步处理提升性能

2. **重试机制**:
   - 自动重试失败的请求
   - 指数退避算法
   - 可配置重试次数和延迟

3. **错误处理**:
   - 优雅的降级策略
   - 详细的错误日志
   - 统计信息记录

### 后端API端点

V2版本引入的新API端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v2/alerts/resource` | POST | 处理资源告警请求 |
| `/api/v2/alerts/stats` | GET | 获取告警处理统计 |
| `/api/v2/alerts/test` | POST | 测试告警处理功能 |

## 迁移指南

### 从V1迁移到V2

1. **更新配置文件**:
```bash
# 备份原配置
cp k8s-mcp/config.env k8s-mcp/config.env.v1.backup

# 使用新的配置模板
cp k8s-mcp/config.env.example k8s-mcp/config.env

# 迁移基础配置
grep -E "RESOURCE_ALERT_ENABLED|MEMORY_ALERT_THRESHOLD|CPU_ALERT_THRESHOLD|ALERT_COOLDOWN_SECONDS" \
  k8s-mcp/config.env.v1.backup >> k8s-mcp/config.env
```

2. **启动服务顺序**:
```bash
# 1. 先启动后端API服务
poetry run python backend/main.py

# 2. 等待后端服务就绪
while ! curl -f http://localhost:8000/health >/dev/null 2>&1; do
  echo "等待后端服务启动..."
  sleep 2
done

# 3. 启动MCP服务器
poetry run python k8s-mcp/start_k8s_mcp_http_server.py
```

3. **验证迁移结果**:
```bash
# 检查告警功能
curl -X POST http://localhost:8000/api/v2/alerts/test

# 查看MCP服务器统计
curl http://localhost:8766/stats | jq '.alert_service'
```

### 配置兼容性

| 配置项 | V1版本 | V2版本 | 迁移说明 |
|-------|--------|--------|----------|
| 告警阈值 | ✅ 保持 | ✅ 保持 | 无需更改 |
| 冷却时间 | ✅ 保持 | ✅ 保持 | 无需更改 |
| LLM分析 | ✅ 保持 | ✅ 保持 | 移至后端处理 |
| 钉钉配置 | ❌ 移除 | 🔄 后端 | 移至后端配置 |

## 故障排查

### 常见问题及解决方案

1. **后端API连接失败**
```bash
# 检查症状
grep "API请求最终失败" k8s-mcp/logs/k8s-mcp.log

# 解决方案
- 确认后端服务已启动: curl http://localhost:8000/health
- 检查网络连通性: ping localhost
- 验证端口占用: lsof -i :8000
- 检查防火墙设置
```

2. **告警未发送到钉钉**
```bash
# 检查后端告警统计
curl http://localhost:8000/api/v2/alerts/stats

# 查看后端日志
tail -f backend/logs/app.log | grep -i dingtalk

# 验证钉钉配置（在后端）
grep DINGTALK backend/config.env
```

3. **配置验证失败**
```bash
# 检查配置有效性
poetry run python -c "
from k8s_mcp.config import get_config
config = get_config()
if not config.validate_config():
    print('配置验证失败，请检查参数范围')
"
```

### 日志分析

V2版本的关键日志标识：

```bash
# MCP服务器日志
grep "ResourceAlertService V2" k8s-mcp/logs/k8s-mcp.log

# HTTP客户端日志
grep "HttpApiClient" k8s-mcp/logs/k8s-mcp.log

# 后端告警处理日志
grep "接收到资源告警" backend/logs/app.log
```

## 性能优化建议

### MCP服务器优化

1. **合理设置重试参数**:
```bash
# 高延迟网络环境
API_TIMEOUT=60
API_MAX_RETRIES=5

# 低延迟网络环境
API_TIMEOUT=15
API_MAX_RETRIES=2
```

2. **冷却时间优化**:
```bash
# 生产环境（减少告警频率）
ALERT_COOLDOWN_SECONDS=600

# 测试环境（快速响应）
ALERT_COOLDOWN_SECONDS=60
```

### 后端API优化

1. **启用异步处理**: 后端默认使用异步处理，无需额外配置
2. **监控API响应时间**: 通过 `/api/v2/alerts/stats` 端点监控
3. **配置适当的工作进程数**: 根据负载调整后端服务器配置

## 总结

V2版本的资源告警系统通过架构重构实现了：

- ✅ **职责清晰**: MCP专注监控，后端专注业务
- ✅ **配置简化**: 减少60%的配置项
- ✅ **错误隔离**: 服务间故障不相互影响
- ✅ **扩展性强**: 便于添加新的通知渠道

新架构为未来功能扩展奠定了良好基础，建议在生产环境中采用V2版本。
