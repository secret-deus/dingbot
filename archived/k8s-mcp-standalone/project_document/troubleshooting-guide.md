# K8s MCP 故障排查指南

本文档提供K8s MCP服务器常见问题的诊断和解决方案。

## 📋 目录

- [故障诊断流程](#故障诊断流程)
- [连接问题](#连接问题)
- [配置问题](#配置问题)
- [性能问题](#性能问题)
- [智能功能问题](#智能功能问题)
- [监控问题](#监控问题)
- [部署问题](#部署问题)
- [日志分析](#日志分析)
- [工具和命令](#工具和命令)

## 🔍 故障诊断流程

### 基础诊断步骤

**1. 快速状态检查**
```bash
# 检查服务器是否运行
curl -s http://localhost:8766/health | jq .

# 检查进程状态
ps aux | grep k8s-mcp

# 检查端口占用
netstat -tlnp | grep 8766
```

**2. 系统资源检查**
```bash
# 检查CPU和内存使用
top -p $(pgrep -f k8s-mcp)

# 检查磁盘空间
df -h

# 检查网络连接
netstat -an | grep ESTABLISHED
```

**3. 日志检查**
```bash
# 查看应用日志
tail -f logs/k8s-mcp.log

# 查看错误日志
tail -f logs/error.log

# 搜索错误信息
grep -i error logs/k8s-mcp.log | tail -20
```

### 诊断决策树

```
服务器无响应?
├─ 是 → 检查进程是否运行
│   ├─ 进程不存在 → 检查启动脚本和配置
│   └─ 进程存在 → 检查端口和防火墙
└─ 否 → 检查具体功能
    ├─ K8s操作失败 → 检查K8s连接和权限
    ├─ 智能功能异常 → 检查智能模块状态
    ├─ 监控数据缺失 → 检查监控配置
    └─ 性能问题 → 检查资源使用和配置
```

## 🔌 连接问题

### K8s集群连接失败

**症状表现:**
- 工具调用返回连接错误
- 健康检查显示K8s客户端不健康
- 日志显示"连接被拒绝"或"认证失败"

**诊断步骤:**

**1. 检查kubeconfig文件**
```bash
# 验证kubeconfig文件存在且可读
ls -la $KUBECONFIG_PATH
cat $KUBECONFIG_PATH | head -20

# 使用kubectl测试连接
kubectl --kubeconfig=$KUBECONFIG_PATH cluster-info
kubectl --kubeconfig=$KUBECONFIG_PATH get nodes
```

**2. 检查网络连接**
```bash
# 获取API服务器地址
kubectl --kubeconfig=$KUBECONFIG_PATH config view --raw | grep server

# 测试网络连通性
curl -k https://your-k8s-api-server:6443/api/v1

# 检查DNS解析
nslookup your-k8s-api-server
```

**3. 检查认证信息**
```bash
# 验证当前用户身份
kubectl --kubeconfig=$KUBECONFIG_PATH auth whoami

# 检查权限
kubectl --kubeconfig=$KUBECONFIG_PATH auth can-i get pods
kubectl --kubeconfig=$KUBECONFIG_PATH auth can-i list services
```

**解决方案:**

**kubeconfig文件问题:**
```bash
# 重新生成kubeconfig文件
kubectl config set-cluster my-cluster --server=https://k8s-api-server:6443
kubectl config set-credentials my-user --client-certificate=client.crt --client-key=client.key
kubectl config set-context my-context --cluster=my-cluster --user=my-user
kubectl config use-context my-context

# 或者从管理员获取新的kubeconfig文件
```

**网络连接问题:**
```bash
# 检查防火墙设置
sudo iptables -L | grep 6443

# 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 如果使用代理，配置无代理列表
export NO_PROXY=kubernetes.default.svc,10.0.0.0/8,localhost,127.0.0.1
```

**权限问题:**
```bash
# 创建适当的RBAC配置
kubectl apply -f - <<EOF
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
EOF
```

### 服务器端口连接问题

**症状表现:**
- 无法访问http://localhost:8766
- 连接超时或拒绝连接
- 其他机器无法访问服务器

**诊断步骤:**

**1. 检查服务器绑定**
```bash
# 检查端口监听状态
netstat -tlnp | grep 8766
ss -tlnp | grep 8766

# 检查进程绑定地址
lsof -i :8766
```

**2. 检查防火墙配置**
```bash
# Ubuntu/Debian
sudo ufw status
sudo iptables -L

# CentOS/RHEL
sudo firewall-cmd --list-all
sudo iptables -L
```

**解决方案:**

**端口绑定问题:**
```env
# 确保绑定到正确的地址
K8S_MCP_HOST=0.0.0.0  # 允许外部访问
K8S_MCP_PORT=8766     # 确认端口未被占用
```

**防火墙配置:**
```bash
# Ubuntu/Debian - 开放端口
sudo ufw allow 8766/tcp

# CentOS/RHEL - 开放端口
sudo firewall-cmd --permanent --add-port=8766/tcp
sudo firewall-cmd --reload
```

## ⚙️ 配置问题

### 环境变量未生效

**症状表现:**
- 配置更改后服务器行为未改变
- 默认值被使用而非自定义值
- 功能开关无效

**诊断步骤:**

**1. 检查环境变量加载**
```bash
# 检查当前环境变量
env | grep K8S_MCP
env | grep ENABLE_KNOWLEDGE_GRAPH

# 检查.env文件
cat .env | grep -v '^#' | grep -v '^$'

# 验证Poetry环境
poetry run python -c "import os; print(os.getenv('ENABLE_KNOWLEDGE_GRAPH'))"
```

**2. 检查配置文件语法**
```bash
# 检查.env文件语法
# 确保没有多余的空格和引号
grep -n "=" .env

# 验证YAML配置文件（如果使用）
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**解决方案:**

**环境变量格式问题:**
```bash
# 正确的.env文件格式
ENABLE_KNOWLEDGE_GRAPH=true    # ✓ 正确
ENABLE_KNOWLEDGE_GRAPH = true  # ✗ 错误，有空格
ENABLE_KNOWLEDGE_GRAPH="true"  # ✓ 可以，但不必要

# 重新加载环境变量
source .env
poetry shell
```

**配置加载顺序问题:**
```bash
# 确认配置加载优先级
# 1. 环境变量（最高）
export ENABLE_KNOWLEDGE_GRAPH=true

# 2. .env文件
echo "ENABLE_KNOWLEDGE_GRAPH=true" >> .env

# 3. 配置文件
# 4. 默认值（最低）
```

### 配置验证失败

**症状表现:**
- 服务器启动时报配置错误
- 功能初始化失败
- 配置验证脚本报错

**诊断脚本:**
```python
#!/usr/bin/env python3
"""配置诊断脚本"""

import os
import sys
from pathlib import Path

def check_required_config():
    """检查必需配置"""
    required = {
        'KUBECONFIG_PATH': '必需：Kubernetes配置文件路径',
        'K8S_NAMESPACE': '必需：默认命名空间'
    }

    missing = []
    for key, desc in required.items():
        if not os.getenv(key):
            missing.append(f"❌ {key}: {desc}")

    if missing:
        print("缺少必需配置:")
        for item in missing:
            print(f"  {item}")
        return False

    print("✅ 必需配置检查通过")
    return True

def check_file_paths():
    """检查文件路径"""
    kubeconfig = os.getenv('KUBECONFIG_PATH')
    if kubeconfig and not Path(kubeconfig).exists():
        print(f"❌ Kubeconfig文件不存在: {kubeconfig}")
        return False

    print("✅ 文件路径检查通过")
    return True

def check_numeric_configs():
    """检查数值配置"""
    numeric_configs = {
        'K8S_MCP_PORT': (1, 65535),
        'SYNC_INTERVAL': (30, 3600),
        'GRAPH_MAX_DEPTH': (1, 10),
        'GRAPH_MEMORY_LIMIT': (128, 8192)
    }

    errors = []
    for key, (min_val, max_val) in numeric_configs.items():
        value = os.getenv(key)
        if value:
            try:
                num_val = int(value)
                if not (min_val <= num_val <= max_val):
                    errors.append(f"❌ {key}={value} 超出范围 [{min_val}, {max_val}]")
            except ValueError:
                errors.append(f"❌ {key}={value} 不是有效数字")

    if errors:
        print("数值配置错误:")
        for error in errors:
            print(f"  {error}")
        return False

    print("✅ 数值配置检查通过")
    return True

if __name__ == "__main__":
    print("=== K8s MCP 配置诊断 ===")

    checks = [check_required_config, check_file_paths, check_numeric_configs]
    all_passed = all(check() for check in checks)

    if all_passed:
        print("\n🎉 所有配置检查通过！")
    else:
        print("\n⚠️ 发现配置问题，请修复后重试")
        sys.exit(1)
```

## 🐌 性能问题

### 响应时间过长

**症状表现:**
- API调用超时
- 工具执行缓慢
- 界面响应延迟

**诊断步骤:**

**1. 检查系统资源**
```bash
# 检查CPU使用率
top -p $(pgrep -f k8s-mcp)
htop

# 检查内存使用
free -h
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable)"

# 检查磁盘I/O
iostat -x 1 5
iotop
```

**2. 分析应用性能**
```bash
# 检查性能指标
curl -s http://localhost:8766/performance | jq .

# 查看慢查询
curl -s "http://localhost:8766/metrics/history?metric_name=api.response_time&last_minutes=30" | jq .

# 检查连接池状态
curl -s http://localhost:8766/metrics | jq '.tool_stats'
```

**3. 分析网络延迟**
```bash
# 测试到K8s API服务器的延迟
time kubectl get nodes

# 测试网络连接
ping k8s-api-server
traceroute k8s-api-server
```

**解决方案:**

**资源优化:**
```env
# 增加工作线程
WORKER_THREADS=8

# 优化连接池
CONNECTION_POOL_SIZE=20
K8S_REQUEST_TIMEOUT=30

# 内存优化
MAX_MEMORY_USAGE=4096MB
ENABLE_MEMORY_OPTIMIZATION=true

# 缓存优化
CACHE_MAX_SIZE=2000
CACHE_TTL=300
```

**应用优化:**
```env
# 智能功能优化
SYNC_INTERVAL=600  # 增加同步间隔
GRAPH_MEMORY_LIMIT=2048  # 增加图谱内存
MAX_SUMMARY_SIZE_KB=5  # 减少摘要大小

# 并发控制
MAX_CONCURRENT_REQUESTS=50
RATE_LIMIT_PER_SECOND=10
```

### 内存泄漏

**症状表现:**
- 内存使用持续增长
- 系统变慢或崩溃
- OOM (Out of Memory) 错误

**诊断工具:**
```bash
# 使用内存分析工具
poetry run python -m memory_profiler start_k8s_mcp_http_server.py

# 监控内存使用趋势
while true; do
    ps -p $(pgrep -f k8s-mcp) -o pid,vsz,rss,pcpu,pmem,etime,args
    sleep 60
done
```

**内存使用分析脚本:**
```python
#!/usr/bin/env python3
"""内存使用分析工具"""

import psutil
import requests
import json
import time
from datetime import datetime

def monitor_memory(duration_minutes=60):
    """监控内存使用情况"""
    end_time = time.time() + (duration_minutes * 60)

    while time.time() < end_time:
        try:
            # 获取进程信息
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                if 'k8s-mcp' in proc.info['name']:
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    print(f"{datetime.now()}: PID {proc.info['pid']} 内存使用: {memory_mb:.1f}MB")

            # 获取应用指标
            try:
                response = requests.get('http://localhost:8766/metrics', timeout=5)
                data = response.json()
                process_memory = data['metrics'].get('process.memory_rss_mb', 0)
                print(f"{datetime.now()}: 应用报告内存: {process_memory:.1f}MB")
            except:
                pass

        except Exception as e:
            print(f"监控错误: {e}")

        time.sleep(60)

if __name__ == "__main__":
    monitor_memory(60)  # 监控60分钟
```

**解决方案:**
```env
# 内存限制
MAX_MEMORY_USAGE=2048MB
GRAPH_MEMORY_LIMIT=1024

# 垃圾回收优化
GC_THRESHOLD=80
MEMORY_CLEANUP_INTERVAL=300

# 缓存大小限制
CACHE_MAX_SIZE=1000
METRICS_HISTORY_SIZE=500

# 启用内存优化
ENABLE_MEMORY_OPTIMIZATION=true
```

## 🧠 智能功能问题

### 知识图谱初始化失败

**症状表现:**
- 智能功能状态显示不可用
- 关联查询工具报错
- 同步引擎无法启动

**诊断步骤:**

**1. 检查智能功能状态**
```bash
# 检查智能功能配置
curl -s http://localhost:8766/intelligent/status | jq .

# 检查详细健康状态
curl -s http://localhost:8766/intelligent/health | jq .

# 查看启动日志
grep -i "intelligent\|graph\|sync" logs/k8s-mcp.log
```

**2. 检查配置和依赖**
```bash
# 验证智能功能配置
echo "ENABLE_KNOWLEDGE_GRAPH: $ENABLE_KNOWLEDGE_GRAPH"
echo "GRAPH_MEMORY_LIMIT: $GRAPH_MEMORY_LIMIT"

# 检查Python依赖
poetry run python -c "import networkx; print('NetworkX版本:', networkx.__version__)"
poetry run python -c "import kubernetes; print('Kubernetes客户端版本:', kubernetes.__version__)"
```

**解决方案:**

**配置问题:**
```env
# 确保智能功能已启用
ENABLE_KNOWLEDGE_GRAPH=true

# 合理的内存配置
GRAPH_MEMORY_LIMIT=1024
GRAPH_TTL=3600

# 同步配置
SYNC_INTERVAL=300
WATCH_TIMEOUT=600
MAX_RETRY_COUNT=3
```

**依赖问题:**
```bash
# 重新安装依赖
poetry install

# 检查特定依赖
poetry add networkx>=2.8
poetry add kubernetes>=24.0.0
```

### 集群同步异常

**症状表现:**
- 同步健康状态为"degraded"或"stale"
- 知识图谱数据过期
- Watch连接频繁断开

**诊断步骤:**

**1. 检查同步状态**
```bash
# 获取详细同步状态
curl -s http://localhost:8766/intelligent/health | jq '.components.cluster_sync'

# 检查同步指标
curl -s http://localhost:8766/metrics | jq '. | to_entries | map(select(.key | contains("sync")))'

# 查看同步日志
grep -i "sync\|watch" logs/k8s-mcp.log | tail -50
```

**2. 测试K8s Watch API**
```bash
# 手动测试Watch API
kubectl get pods --watch &
sleep 10
kill %1

# 检查API服务器连接
curl -k "https://k8s-api-server:6443/api/v1/pods?watch=true" \
  --header "Authorization: Bearer $(kubectl get secret -o jsonpath='{.data.token}' | base64 -d)"
```

**解决方案:**

**网络问题:**
```env
# 增加超时时间
WATCH_TIMEOUT=1200
REQUEST_TIMEOUT=60

# 重连配置
MAX_RETRY_COUNT=5
RETRY_DELAY=10

# 网络优化
KEEP_ALIVE_TIMEOUT=120
SOCKET_TIMEOUT=60
```

**同步优化:**
```env
# 调整同步间隔
SYNC_INTERVAL=600  # 10分钟

# 批处理优化
SYNC_BATCH_SIZE=100
SYNC_PARALLEL_WORKERS=4

# 内存管理
GRAPH_GC_INTERVAL=300
MEMORY_CLEANUP_THRESHOLD=80
```

## 📊 监控问题

### 指标收集异常

**症状表现:**
- 监控API返回空数据
- Prometheus端点无响应
- 性能报告显示不准确

**诊断步骤:**

**1. 检查监控服务状态**
```bash
# 检查监控功能是否启用
curl -s http://localhost:8766/metrics | jq 'keys'

# 检查指标收集器状态
curl -s http://localhost:8766/performance | jq '.summary_stats'

# 查看监控相关日志
grep -i "metrics\|monitor" logs/k8s-mcp.log
```

**2. 验证系统资源监控**
```bash
# 检查psutil依赖
poetry run python -c "import psutil; print('psutil版本:', psutil.__version__)"

# 测试系统指标收集
poetry run python -c "
import psutil
print('CPU:', psutil.cpu_percent())
print('内存:', psutil.virtual_memory().percent)
"
```

**解决方案:**

**监控配置:**
```env
# 启用监控功能
MONITORING_ENABLED=true

# 调整收集间隔
METRICS_COLLECTION_INTERVAL=30
HEALTH_CHECK_INTERVAL=30

# 历史数据配置
METRICS_HISTORY_SIZE=1000

# 报警配置
ALERT_CPU_PERCENT_MAX=80.0
ALERT_MEMORY_PERCENT_MAX=85.0
```

**依赖修复:**
```bash
# 安装监控依赖
poetry add psutil>=5.9.0

# 重新安装所有依赖
poetry install --no-cache
```

### Prometheus集成问题

**症状表现:**
- /metrics/prometheus端点返回错误
- Prometheus无法抓取指标
- 指标格式不正确

**诊断步骤:**
```bash
# 检查Prometheus端点
curl -s http://localhost:8766/metrics/prometheus

# 验证指标格式
curl -s http://localhost:8766/metrics/prometheus | head -20

# 检查Prometheus配置
curl -s http://prometheus:9090/api/v1/targets
```

**解决方案:**
```env
# Prometheus集成配置
ENABLE_PROMETHEUS_EXPORT=true
PROMETHEUS_NAMESPACE=k8s_mcp
PROMETHEUS_EXPORT_INTERVAL=60

# 自定义标签
PROMETHEUS_LABELS_ENVIRONMENT=production
PROMETHEUS_LABELS_CLUSTER=main
```

## 🚀 部署问题

### Docker容器问题

**症状表现:**
- 容器无法启动
- 容器频繁重启
- 健康检查失败

**诊断步骤:**

**1. 检查容器状态**
```bash
# 查看容器状态
docker ps -a
docker inspect k8s-mcp

# 查看容器日志
docker logs k8s-mcp
docker logs --tail 50 k8s-mcp
```

**2. 检查资源限制**
```bash
# 检查容器资源使用
docker stats k8s-mcp

# 查看详细资源信息
docker inspect k8s-mcp | jq '.[0].HostConfig | {Memory, CpuShares, CpuQuota}'
```

**解决方案:**

**启动问题:**
```bash
# 交互式启动进行调试
docker run -it --rm k8s-mcp:latest /bin/bash

# 检查入口点脚本
docker run --rm k8s-mcp:latest cat start_k8s_mcp_http_server.py
```

**资源问题:**
```bash
# 增加资源限制
docker run -d \
  --name k8s-mcp \
  --memory=4g \
  --cpus=2 \
  -p 8766:8766 \
  k8s-mcp:latest
```

### Kubernetes部署问题

**症状表现:**
- Pod处于Pending状态
- Pod频繁重启
- Service无法访问

**诊断步骤:**

**1. 检查Pod状态**
```bash
# 查看Pod详细信息
kubectl describe pod -n k8s-mcp -l app=k8s-mcp-server

# 查看Pod日志
kubectl logs -n k8s-mcp -l app=k8s-mcp-server --tail=100

# 查看事件
kubectl get events -n k8s-mcp --sort-by=.metadata.creationTimestamp
```

**2. 检查资源和权限**
```bash
# 检查节点资源
kubectl top nodes
kubectl describe nodes

# 检查RBAC权限
kubectl auth can-i get pods --as=system:serviceaccount:k8s-mcp:k8s-mcp-sa
```

**解决方案:**

**资源不足:**
```yaml
# 调整资源请求
resources:
  requests:
    memory: "1Gi"   # 降低请求
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2"
```

**权限问题:**
```bash
# 重新应用RBAC配置
kubectl apply -f rbac.yaml

# 验证ServiceAccount
kubectl get serviceaccount k8s-mcp-sa -n k8s-mcp
```

## 📝 日志分析

### 日志级别和格式

**日志级别配置:**
```env
# 开发环境
LOG_LEVEL=DEBUG

# 生产环境
LOG_LEVEL=INFO

# 故障排查
LOG_LEVEL=ERROR
```

**日志格式示例:**
```
2025-08-04 12:00:00.123 | INFO     | src.k8s_mcp.server:initialize:145 - ✅ K8s客户端连接成功
2025-08-04 12:00:05.456 | WARNING  | src.k8s_mcp.core.cluster_sync:_handle_watch_error:234 - Watch连接断开，尝试重连
2025-08-04 12:00:10.789 | ERROR    | src.k8s_mcp.tools.k8s_get_pods:execute:67 - 获取Pod列表失败: 连接超时
```

### 常见错误模式

**连接错误:**
```bash
# 搜索连接相关错误
grep -E "(连接|connection|timeout)" logs/k8s-mcp.log

# K8s API连接错误
grep -E "(Unauthorized|Forbidden|SSL|TLS)" logs/k8s-mcp.log
```

**内存错误:**
```bash
# 内存相关错误
grep -E "(memory|OOM|MemoryError)" logs/k8s-mcp.log

# 垃圾回收日志
grep -E "(gc|garbage)" logs/k8s-mcp.log
```

**智能功能错误:**
```bash
# 智能功能相关错误
grep -E "(intelligent|graph|sync)" logs/k8s-mcp.log | grep -i error

# 同步错误
grep -E "(sync.*error|watch.*error)" logs/k8s-mcp.log
```

### 日志分析脚本

```bash
#!/bin/bash
# 日志分析脚本

LOG_FILE="logs/k8s-mcp.log"
HOURS=${1:-24}

echo "=== K8s MCP 日志分析 (最近${HOURS}小时) ==="

# 错误统计
echo "错误统计:"
grep -E "(ERROR|CRITICAL)" "$LOG_FILE" | \
  grep "$(date -d "${HOURS} hours ago" '+%Y-%m-%d')" | \
  wc -l | xargs printf "  总错误数: %d\n"

# 连接错误
echo "连接错误:"
grep -E "(连接|connection)" "$LOG_FILE" | \
  grep -i error | \
  grep "$(date -d "${HOURS} hours ago" '+%Y-%m-%d')" | \
  wc -l | xargs printf "  连接错误: %d\n"

# 性能问题
echo "性能问题:"
grep -E "(timeout|slow|延迟)" "$LOG_FILE" | \
  grep "$(date -d "${HOURS} hours ago" '+%Y-%m-%d')" | \
  wc -l | xargs printf "  性能问题: %d\n"

# 最频繁的错误
echo "最频繁的错误 (Top 5):"
grep -E "(ERROR|CRITICAL)" "$LOG_FILE" | \
  grep "$(date -d "${HOURS} hours ago" '+%Y-%m-%d')" | \
  sed 's/.*ERROR.*- //' | \
  sort | uniq -c | sort -nr | head -5 | \
  sed 's/^/  /'
```

## 🛠️ 工具和命令

### 快速诊断命令

**一键状态检查:**
```bash
#!/bin/bash
# k8s-mcp-check.sh

echo "=== K8s MCP 快速诊断 ==="

# 1. 服务状态
echo "1. 服务状态:"
if curl -s http://localhost:8766/health > /dev/null; then
    echo "  ✅ 服务器响应正常"
else
    echo "  ❌ 服务器无响应"
fi

# 2. 进程状态
if pgrep -f k8s-mcp > /dev/null; then
    echo "  ✅ 进程运行中"
    ps aux | grep k8s-mcp | grep -v grep
else
    echo "  ❌ 进程未运行"
fi

# 3. 端口状态
if netstat -tlnp | grep 8766 > /dev/null; then
    echo "  ✅ 端口8766已监听"
else
    echo "  ❌ 端口8766未监听"
fi

# 4. K8s连接
if kubectl cluster-info > /dev/null 2>&1; then
    echo "  ✅ K8s集群连接正常"
else
    echo "  ❌ K8s集群连接失败"
fi

# 5. 智能功能
if curl -s http://localhost:8766/intelligent/status | jq -e '.intelligent_mode_enabled' > /dev/null 2>&1; then
    echo "  ✅ 智能功能已启用"
else
    echo "  ⚠️  智能功能未启用或异常"
fi

# 6. 监控功能
if curl -s http://localhost:8766/metrics > /dev/null; then
    echo "  ✅ 监控功能正常"
else
    echo "  ⚠️  监控功能异常"
fi
```

**性能分析脚本:**
```bash
#!/bin/bash
# performance-check.sh

echo "=== K8s MCP 性能分析 ==="

# CPU和内存使用
echo "1. 系统资源:"
echo "  CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"
echo "  内存使用率: $(free | grep Mem | awk '{printf("%.1f%%"), ($3/$2)*100}')"

# 进程资源使用
echo "2. 进程资源:"
PID=$(pgrep -f k8s-mcp)
if [ ! -z "$PID" ]; then
    ps -p $PID -o pid,pcpu,pmem,rss,vsz,etime --no-headers | \
    awk '{printf("  PID: %s, CPU: %s%%, MEM: %s%%, RSS: %sKB, VSZ: %sKB, 运行时间: %s\n", $1, $2, $3, $4, $5, $6)}'
fi

# API性能
echo "3. API性能:"
curl -s http://localhost:8766/performance | jq -r '
  "  健康评分: " + (.health_score | tostring) + "/100",
  "  性能状态: " + .performance_status,
  "  平均响应时间: " + (.key_metrics.avg_api_response_time | tostring) + "s",
  "  错误率: " + (.key_metrics.api_error_rate | tostring) + "%"
'

# 最近报警
echo "4. 最近报警:"
ALERT_COUNT=$(curl -s "http://localhost:8766/alerts?last_hours=1" | jq '.total_count')
echo "  最近1小时报警数: $ALERT_COUNT"
```

### 调试工具

**配置验证工具:**
```python
#!/usr/bin/env python3
# config-validator.py

import os
import sys
from pathlib import Path

def validate_config():
    print("=== 配置验证工具 ===")

    # 检查必需配置
    required_configs = {
        'KUBECONFIG_PATH': '必需：K8s配置文件路径',
        'K8S_NAMESPACE': '必需：默认命名空间'
    }

    for key, desc in required_configs.items():
        value = os.getenv(key)
        if not value:
            print(f"❌ {key}: {desc}")
            return False
        else:
            print(f"✅ {key}: {value}")

    # 检查文件存在性
    kubeconfig = os.getenv('KUBECONFIG_PATH')
    if not Path(kubeconfig).exists():
        print(f"❌ Kubeconfig文件不存在: {kubeconfig}")
        return False

    # 检查可选配置
    optional_configs = {
        'ENABLE_KNOWLEDGE_GRAPH': '智能功能开关',
        'MONITORING_ENABLED': '监控功能开关',
        'K8S_MCP_DEBUG': '调试模式'
    }

    print("\n可选配置:")
    for key, desc in optional_configs.items():
        value = os.getenv(key, '未设置')
        print(f"  {key}: {value} ({desc})")

    return True

if __name__ == "__main__":
    # 加载.env文件
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

    if validate_config():
        print("\n🎉 配置验证通过！")
        sys.exit(0)
    else:
        print("\n❌ 配置验证失败！")
        sys.exit(1)
```

**网络连接测试:**
```bash
#!/bin/bash
# network-test.sh

echo "=== K8s MCP 网络连接测试 ==="

# 测试本地端口
echo "1. 本地端口测试:"
if nc -z localhost 8766; then
    echo "  ✅ localhost:8766 可访问"
else
    echo "  ❌ localhost:8766 不可访问"
fi

# 测试K8s API
echo "2. K8s API测试:"
K8S_SERVER=$(kubectl config view --raw | grep server | head -1 | awk '{print $2}')
if [ ! -z "$K8S_SERVER" ]; then
    echo "  API服务器: $K8S_SERVER"
    if curl -k --connect-timeout 5 "$K8S_SERVER" > /dev/null 2>&1; then
        echo "  ✅ K8s API服务器可访问"
    else
        echo "  ❌ K8s API服务器不可访问"
    fi
fi

# 测试DNS解析
echo "3. DNS解析测试:"
if nslookup kubernetes.default.svc.cluster.local > /dev/null 2>&1; then
    echo "  ✅ 集群DNS解析正常"
else
    echo "  ⚠️  集群DNS解析失败（可能在集群外运行）"
fi

# 测试网络延迟
echo "4. 网络延迟测试:"
if command -v kubectl > /dev/null; then
    START_TIME=$(date +%s%N)
    kubectl get nodes > /dev/null 2>&1
    END_TIME=$(date +%s%N)
    LATENCY=$(( (END_TIME - START_TIME) / 1000000 ))
    echo "  kubectl get nodes 延迟: ${LATENCY}ms"
fi
```

---

**💡 提示**: 遇到问题时，建议按照诊断流程逐步排查，并保存相关日志以便进一步分析。如果问题持续存在，可以启用DEBUG日志级别获取更详细的信息。