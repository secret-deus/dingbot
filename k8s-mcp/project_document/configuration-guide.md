# K8s MCP 配置指南

本文档详细介绍K8s MCP服务器的所有配置选项、最佳实践和配置示例。

## 📋 目录

- [配置概览](#配置概览)
- [基础配置](#基础配置)
- [智能功能配置](#智能功能配置)
- [监控配置](#监控配置)
- [安全配置](#安全配置)
- [性能调优](#性能调优)
- [环境配置](#环境配置)
- [配置验证](#配置验证)

## 🔧 配置概览

K8s MCP服务器支持多层次配置：

1. **环境变量** - 最高优先级
2. **`.env`文件** - 开发环境推荐
3. **配置文件** - 企业环境推荐
4. **默认值** - 后备配置

### 配置加载顺序
```
环境变量 > .env文件 > config.yaml > 默认值
```

### 配置文件位置
- 开发环境: `.env` (项目根目录)
- 生产环境: `/etc/k8s-mcp/config.yaml`
- 容器环境: 环境变量注入

## 🔨 基础配置

### 必需配置

| 配置项 | 环境变量 | 描述 | 示例 |
|--------|----------|------|------|
| Kubeconfig路径 | `KUBECONFIG_PATH` | K8s配置文件路径 | `/home/user/.kube/config` |
| 默认命名空间 | `K8S_NAMESPACE` | 默认操作命名空间 | `default` |

### 服务器配置

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| 绑定地址 | `K8S_MCP_HOST` | `localhost` | 服务器监听地址 |
| 端口 | `K8S_MCP_PORT` | `8766` | 服务器监听端口 |
| 调试模式 | `K8S_MCP_DEBUG` | `false` | 是否启用调试输出 |

### 基础配置示例 (.env)
```env
# =============================================================================
# 🔧 基础必需配置
# =============================================================================

# Kubernetes配置 (必需)
KUBECONFIG_PATH=/Users/username/.kube/config
K8S_NAMESPACE=default

# 服务器配置
K8S_MCP_HOST=localhost
K8S_MCP_PORT=8766
K8S_MCP_DEBUG=false

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/k8s-mcp.log
```

### 高级基础配置
```env
# K8s客户端配置
K8S_REQUEST_TIMEOUT=30
K8S_CONNECTION_POOL_SIZE=10
K8S_MAX_RETRY_DELAY=60

# 资源限制
K8S_MAX_RESOURCES=100
K8S_MAX_LOG_LINES=1000

# 缓存配置
K8S_CACHE_TTL=300
K8S_CACHE_MAX_SIZE=1000
```

## 🧠 智能功能配置

### 知识图谱配置

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| 启用知识图谱 | `ENABLE_KNOWLEDGE_GRAPH` | `false` | 是否启用智能功能 |
| 同步间隔 | `SYNC_INTERVAL` | `300` | 集群同步间隔(秒) |
| 图查询深度 | `GRAPH_MAX_DEPTH` | `3` | 关系查询最大深度 |
| 节点TTL | `GRAPH_TTL` | `3600` | 图节点生存时间(秒) |
| 内存限制 | `GRAPH_MEMORY_LIMIT` | `1024` | 图谱内存限制(MB) |

### 同步引擎配置

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| Watch超时 | `WATCH_TIMEOUT` | `600` | Watch API超时(秒) |
| 最大重试 | `MAX_RETRY_COUNT` | `3` | 同步失败最大重试次数 |
| 重试延迟 | `RETRY_DELAY` | `5` | 重试间隔(秒) |

### 摘要生成配置

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| 最大摘要大小 | `MAX_SUMMARY_SIZE_KB` | `10` | 摘要最大大小(KB) |
| 异常检测阈值 | `ANOMALY_THRESHOLD` | `5` | 异常检测敏感度 |
| 压缩算法 | `SUMMARY_COMPRESSION` | `gzip` | 摘要压缩算法 |

### 智能功能配置示例
```env
# =============================================================================
# 🧠 智能功能配置
# =============================================================================

# 启用智能功能
ENABLE_KNOWLEDGE_GRAPH=true

# 知识图谱配置
GRAPH_MAX_DEPTH=3
GRAPH_TTL=3600
GRAPH_MEMORY_LIMIT=1024

# 同步引擎配置
SYNC_INTERVAL=300
WATCH_TIMEOUT=600
MAX_RETRY_COUNT=3
RETRY_DELAY=5

# 摘要生成配置
MAX_SUMMARY_SIZE_KB=10
ANOMALY_THRESHOLD=5
SUMMARY_COMPRESSION=gzip

# 高级智能配置
ENABLE_PREDICTIVE_SCALING=false
ENABLE_ANOMALY_DETECTION=true
ENABLE_RELATIONSHIP_ANALYSIS=true

# 缓存优化
GRAPH_CACHE_SIZE=500
RELATIONSHIP_CACHE_TTL=1800
SUMMARY_CACHE_SIZE=100
```

### 智能功能性能调优
```env
# 性能优化配置
GRAPH_UPDATE_BATCH_SIZE=50
SYNC_WORKER_THREADS=4
PARALLEL_QUERY_LIMIT=10

# 内存管理
GRAPH_GC_INTERVAL=300
MEMORY_CLEANUP_THRESHOLD=80

# 网络优化
WATCH_BUFFER_SIZE=1024
HTTP_KEEP_ALIVE=true
CONNECTION_TIMEOUT=30
```

## 📊 监控配置

### 基础监控配置

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| 启用监控 | `MONITORING_ENABLED` | `true` | 是否启用监控功能 |
| 指标收集间隔 | `METRICS_COLLECTION_INTERVAL` | `30` | 指标收集间隔(秒) |
| 历史数据大小 | `METRICS_HISTORY_SIZE` | `1000` | 历史数据最大保存数量 |
| 健康检查间隔 | `HEALTH_CHECK_INTERVAL` | `30` | 健康检查间隔(秒) |

### 报警阈值配置

| 配置项 | 环境变量 | 默认值 | 描述 |
|--------|----------|--------|------|
| API响应时间 | `ALERT_API_RESPONSE_TIME_MAX` | `5.0` | API响应时间阈值(秒) |
| CPU使用率 | `ALERT_CPU_PERCENT_MAX` | `80.0` | CPU使用率阈值(%) |
| 内存使用率 | `ALERT_MEMORY_PERCENT_MAX` | `85.0` | 内存使用率阈值(%) |
| 错误率 | `ALERT_ERROR_RATE_MAX` | `5.0` | 错误率阈值(%) |
| 同步延迟 | `ALERT_SYNC_DELAY_MAX` | `300.0` | 同步延迟阈值(秒) |

### 监控配置示例
```env
# =============================================================================
# 📊 监控系统配置
# =============================================================================

# 基础监控配置
MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=30
METRICS_HISTORY_SIZE=1000
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# 报警阈值配置
ALERT_API_RESPONSE_TIME_MAX=5.0
ALERT_CPU_PERCENT_MAX=80.0
ALERT_MEMORY_PERCENT_MAX=85.0
ALERT_ERROR_RATE_MAX=5.0
ALERT_SYNC_DELAY_MAX=300.0

# 高级监控配置
ENABLE_CUSTOM_METRICS=true
ENABLE_PROMETHEUS_EXPORT=true
PROMETHEUS_EXPORT_INTERVAL=60

# 报警配置
ALERT_COOLDOWN_SECONDS=300
ALERT_MAX_HISTORY=100
ENABLE_EMAIL_ALERTS=false
ENABLE_SLACK_ALERTS=false

# 性能监控
ENABLE_PERFORMANCE_PROFILING=false
PROFILING_SAMPLE_RATE=0.1
ENABLE_MEMORY_PROFILING=false
```

### Prometheus集成配置
```env
# Prometheus集成
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
PROMETHEUS_METRICS_PATH=/metrics/prometheus
PROMETHEUS_NAMESPACE=k8s_mcp

# 自定义标签
PROMETHEUS_LABELS_ENVIRONMENT=production
PROMETHEUS_LABELS_CLUSTER=main
PROMETHEUS_LABELS_REGION=us-west-2
```

## 🔒 安全配置

### 访问控制配置

| 配置项 | 环境变量 | 描述 | 示例 |
|--------|----------|------|------|
| 允许的命名空间 | `K8S_ALLOWED_NAMESPACES` | 允许访问的命名空间 | `default,app,monitoring` |
| 禁止的命名空间 | `K8S_FORBIDDEN_NAMESPACES` | 禁止访问的命名空间 | `kube-system,kube-public` |
| 操作审计 | `K8S_AUDIT_ENABLED` | 是否启用操作审计 | `true` |
| 审计日志文件 | `K8S_AUDIT_LOG_FILE` | 审计日志文件路径 | `logs/audit.log` |

### RBAC配置示例

**ServiceAccount (k8s-mcp-sa.yaml):**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: k8s-mcp-service-account
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8s-mcp-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "patch"]
- apiGroups: ["extensions"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: k8s-mcp-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: k8s-mcp-role
subjects:
- kind: ServiceAccount
  name: k8s-mcp-service-account
  namespace: default
```

### 安全配置示例
```env
# =============================================================================
# 🔒 安全配置
# =============================================================================

# 访问控制
K8S_ALLOWED_NAMESPACES=default,monitoring,logging
K8S_FORBIDDEN_NAMESPACES=kube-system,kube-public,kube-node-lease
K8S_ENABLE_RBAC_CHECK=true

# 操作审计
K8S_AUDIT_ENABLED=true
K8S_AUDIT_LOG_FILE=logs/audit.log
K8S_AUDIT_LOG_LEVEL=INFO
K8S_AUDIT_MAX_FILE_SIZE=100MB
K8S_AUDIT_MAX_BACKUPS=5

# 资源限制
K8S_MAX_RESOURCES=100
K8S_MAX_LOG_LINES=1000
K8S_MAX_REQUEST_SIZE=10MB
K8S_REQUEST_RATE_LIMIT=100

# 网络安全
ENABLE_CORS=false
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
ENABLE_HTTPS=false
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# 身份认证 (可选)
ENABLE_AUTHENTICATION=false
AUTH_METHOD=jwt
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=3600

# API限制
ENABLE_API_RATE_LIMITING=true
API_RATE_LIMIT_PER_MINUTE=60
ENABLE_REQUEST_LOGGING=true
```

## ⚡ 性能调优

### 系统性能配置

| 配置项 | 环境变量 | 默认值 | 调优建议 |
|--------|----------|--------|----------|
| 工作线程数 | `WORKER_THREADS` | `4` | CPU核数 × 2 |
| 连接池大小 | `CONNECTION_POOL_SIZE` | `10` | 并发请求数 × 1.5 |
| 请求超时 | `REQUEST_TIMEOUT` | `30` | 根据网络延迟调整 |
| 缓存大小 | `CACHE_MAX_SIZE` | `1000` | 根据内存大小调整 |

### 内存优化配置
```env
# =============================================================================
# ⚡ 性能调优配置
# =============================================================================

# 系统性能
WORKER_THREADS=8
CONNECTION_POOL_SIZE=20
REQUEST_TIMEOUT=30
RESPONSE_TIMEOUT=60

# 内存管理
MAX_MEMORY_USAGE=2048MB
GC_THRESHOLD=80
ENABLE_MEMORY_OPTIMIZATION=true
MEMORY_CLEANUP_INTERVAL=300

# 缓存配置
CACHE_MAX_SIZE=2000
CACHE_TTL=600
ENABLE_DISTRIBUTED_CACHE=false
REDIS_URL=redis://localhost:6379

# 数据库连接 (如使用)
DB_POOL_SIZE=10
DB_TIMEOUT=30
DB_RETRY_ATTEMPTS=3

# 并发控制
MAX_CONCURRENT_REQUESTS=100
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_SECOND=10

# 网络优化
KEEP_ALIVE_TIMEOUT=60
MAX_CONNECTIONS=1000
SOCKET_TIMEOUT=30
```

### 智能功能性能优化
```env
# 知识图谱性能
GRAPH_INDEX_ENABLED=true
GRAPH_CACHE_STRATEGY=lru
GRAPH_PARALLEL_PROCESSING=true

# 同步性能
SYNC_BATCH_SIZE=100
SYNC_PARALLEL_WORKERS=4
WATCH_RECONNECT_DELAY=5

# 查询优化
ENABLE_QUERY_CACHE=true
QUERY_CACHE_SIZE=500
QUERY_TIMEOUT=30
```

## 🌍 环境配置

### 开发环境配置 (.env.development)
```env
# 开发环境配置
K8S_MCP_DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_HOT_RELOAD=true

# 智能功能 (开发时可关闭以提高启动速度)
ENABLE_KNOWLEDGE_GRAPH=false
MONITORING_ENABLED=true

# 开发工具
ENABLE_API_DOCS=true
ENABLE_SWAGGER_UI=true
ENABLE_DEBUG_ROUTES=true

# 测试配置
ENABLE_MOCK_K8S=false
MOCK_DATA_PATH=tests/fixtures
```

### 测试环境配置 (.env.testing)
```env
# 测试环境配置
K8S_MCP_DEBUG=false
LOG_LEVEL=WARNING
ENABLE_KNOWLEDGE_GRAPH=true
MONITORING_ENABLED=true

# 测试特定配置
K8S_NAMESPACE=test
K8S_MAX_RESOURCES=50
SYNC_INTERVAL=60

# 安全配置 (宽松)
K8S_ALLOWED_NAMESPACES=test,test-app
ENABLE_AUTHENTICATION=false
```

### 生产环境配置 (.env.production)
```env
# 生产环境配置
K8S_MCP_DEBUG=false
LOG_LEVEL=INFO
ENABLE_KNOWLEDGE_GRAPH=true
MONITORING_ENABLED=true

# 生产性能配置
WORKER_THREADS=16
CONNECTION_POOL_SIZE=50
MAX_MEMORY_USAGE=4096MB

# 生产安全配置
K8S_AUDIT_ENABLED=true
ENABLE_AUTHENTICATION=true
ENABLE_HTTPS=true
ENABLE_CORS=true

# 监控和报警
ENABLE_PROMETHEUS_EXPORT=true
ENABLE_EMAIL_ALERTS=true
ALERT_EMAIL_RECIPIENTS=ops@company.com
```

### Docker环境配置
```env
# Docker特定配置
K8S_MCP_HOST=0.0.0.0
KUBECONFIG_PATH=/root/.kube/config
LOG_FILE=/app/logs/k8s-mcp.log

# 容器优化
ENABLE_GRACEFUL_SHUTDOWN=true
SHUTDOWN_TIMEOUT=30
HEALTH_CHECK_PATH=/health
```

## ✅ 配置验证

### 配置检查脚本
```bash
#!/bin/bash

# 配置验证脚本
echo "=== K8s MCP 配置验证 ==="

# 检查必需配置
if [ -z "$KUBECONFIG_PATH" ]; then
    echo "❌ 错误: KUBECONFIG_PATH 未设置"
    exit 1
fi

if [ ! -f "$KUBECONFIG_PATH" ]; then
    echo "❌ 错误: Kubeconfig 文件不存在: $KUBECONFIG_PATH"
    exit 1
fi

if [ -z "$K8S_NAMESPACE" ]; then
    echo "❌ 错误: K8S_NAMESPACE 未设置"
    exit 1
fi

# 检查可选配置
echo "✅ 基础配置检查通过"

# 验证K8s连接
kubectl --kubeconfig="$KUBECONFIG_PATH" cluster-info > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ K8s集群连接正常"
else
    echo "⚠️  警告: K8s集群连接失败"
fi

# 检查权限
kubectl --kubeconfig="$KUBECONFIG_PATH" auth can-i get pods -n "$K8S_NAMESPACE" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ K8s权限检查通过"
else
    echo "⚠️  警告: K8s权限不足"
fi

echo "配置验证完成！"
```

### 配置测试API
```bash
# 启动服务器后验证配置
curl -s http://localhost:8766/health | jq .

# 检查智能功能配置
curl -s http://localhost:8766/intelligent/status | jq .

# 检查监控配置
curl -s http://localhost:8766/metrics | jq .
```

### Python配置验证工具
```python
#!/usr/bin/env python3
"""
K8s MCP 配置验证工具
"""

import os
import sys
from pathlib import Path
from kubernetes import client, config

def validate_basic_config():
    """验证基础配置"""
    print("🔧 验证基础配置...")
    
    # 检查必需环境变量
    required_vars = ['KUBECONFIG_PATH', 'K8S_NAMESPACE']
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ 错误: {var} 环境变量未设置")
            return False
    
    # 检查kubeconfig文件
    kubeconfig_path = os.getenv('KUBECONFIG_PATH')
    if not Path(kubeconfig_path).exists():
        print(f"❌ 错误: Kubeconfig文件不存在: {kubeconfig_path}")
        return False
    
    print("✅ 基础配置验证通过")
    return True

def validate_k8s_connection():
    """验证K8s连接"""
    print("🔗 验证K8s连接...")
    
    try:
        config.load_kube_config(config_file=os.getenv('KUBECONFIG_PATH'))
        v1 = client.CoreV1Api()
        
        # 测试连接
        v1.get_api_resources()
        print("✅ K8s API连接成功")
        
        # 测试权限
        namespace = os.getenv('K8S_NAMESPACE', 'default')
        pods = v1.list_namespaced_pod(namespace=namespace, limit=1)
        print("✅ K8s权限验证通过")
        
        return True
        
    except Exception as e:
        print(f"❌ K8s连接失败: {e}")
        return False

def validate_intelligent_config():
    """验证智能功能配置"""
    print("🧠 验证智能功能配置...")
    
    if os.getenv('ENABLE_KNOWLEDGE_GRAPH', 'false').lower() == 'true':
        print("✅ 知识图谱功能已启用")
        
        # 检查内存配置
        memory_limit = int(os.getenv('GRAPH_MEMORY_LIMIT', '1024'))
        if memory_limit < 512:
            print("⚠️  警告: 图谱内存限制可能过低")
        
        # 检查同步间隔
        sync_interval = int(os.getenv('SYNC_INTERVAL', '300'))
        if sync_interval < 60:
            print("⚠️  警告: 同步间隔可能过短")
    else:
        print("ℹ️  智能功能未启用")
    
    return True

def validate_monitoring_config():
    """验证监控配置"""
    print("📊 验证监控配置...")
    
    if os.getenv('MONITORING_ENABLED', 'true').lower() == 'true':
        print("✅ 监控功能已启用")
        
        # 检查报警阈值
        cpu_threshold = float(os.getenv('ALERT_CPU_PERCENT_MAX', '80.0'))
        if cpu_threshold > 95:
            print("⚠️  警告: CPU报警阈值可能过高")
        
        memory_threshold = float(os.getenv('ALERT_MEMORY_PERCENT_MAX', '85.0'))
        if memory_threshold > 95:
            print("⚠️  警告: 内存报警阈值可能过高")
    else:
        print("ℹ️  监控功能未启用")
    
    return True

def main():
    """主函数"""
    print("=== K8s MCP 配置验证工具 ===\n")
    
    # 加载.env文件
    env_file = Path('.env')
    if env_file.exists():
        print(f"📄 加载配置文件: {env_file}")
        from dotenv import load_dotenv
        load_dotenv()
    
    # 执行验证
    checks = [
        validate_basic_config,
        validate_k8s_connection,
        validate_intelligent_config,
        validate_monitoring_config
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            all_passed = False
        print()
    
    # 输出结果
    if all_passed:
        print("🎉 所有配置验证通过！")
        sys.exit(0)
    else:
        print("⚠️  配置验证发现问题，请检查上述错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 📚 最佳实践

### 配置管理最佳实践

1. **环境分离**: 为不同环境使用不同的配置文件
2. **敏感信息**: 使用环境变量或密钥管理系统
3. **配置验证**: 启动前验证所有关键配置
4. **默认值**: 为所有配置项提供合理的默认值
5. **文档同步**: 保持配置文档与代码同步

### 安全配置最佳实践

1. **最小权限**: 只授予必需的K8s权限
2. **命名空间隔离**: 限制可访问的命名空间
3. **审计日志**: 启用操作审计和监控
4. **网络安全**: 使用防火墙和网络策略
5. **定期审查**: 定期审查和更新配置

### 性能配置最佳实践

1. **资源监控**: 持续监控资源使用情况
2. **缓存策略**: 合理配置缓存大小和TTL
3. **连接池**: 根据负载调整连接池大小
4. **并发控制**: 避免过度并发导致资源竞争
5. **定期优化**: 根据监控数据调整配置

---

**💡 提示**: 配置更改后建议重启服务器以确保所有设置生效。生产环境配置更改前请先在测试环境验证。