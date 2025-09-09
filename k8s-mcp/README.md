# K8s MCP 智能服务器

> **注意**: 这是钉钉K8s运维机器人项目的MCP服务器组件。完整项目信息请查看：**[主项目README](../README.md)**

一个功能强大的Kubernetes MCP服务器，提供智能化的集群管理和自然语言交互能力。

## 🌟 主要特性

### 🧠 智能功能
- **知识图谱**: K8s资源关系图谱，智能分析资源依赖关系
- **实时同步**: 基于Watch API的增量同步机制
- **智能摘要**: 自动生成集群状态摘要，适配LLM上下文限制
- **关联查询**: 支持复杂的资源关联查询和依赖分析
- **自然语言**: 通过MCP协议支持自然语言K8s操作

### 📊 监控系统
- **性能指标**: 实时收集系统、API、工具执行性能指标
- **智能报警**: 基于阈值的自动报警系统，支持CPU、内存、错误率监控
- **健康评分**: 综合系统健康评分算法 (0-100分)
- **Prometheus集成**: 支持Prometheus格式指标导出
- **监控API**: 完整的RESTful监控API接口

### 🔔 资源告警系统 (V2)
- **智能监控**: 自动监控K8s应用的CPU和内存利用率
- **阈值告警**: 可配置的资源利用率阈值检测（默认CPU 80%，内存 70%）
- **冷却机制**: 防止频繁告警的智能冷却系统
- **LLM分析**: 集成LLM智能分析资源问题并生成优化建议
- **钉钉推送**: 自动发送格式化告警消息到钉钉群
- **架构分离**: MCP服务器专注监控检测，后端API处理分析和通知

### 🚀 基础能力
- **真实K8s操作**: 使用kubernetes Python客户端进行真实的K8s操作
- **安全配置**: 支持命名空间权限控制和操作审计
- **SSE支持**: 基于Server-Sent Events的实时通信协议
- **丰富的工具**: 支持Pod、Service、Deployment、Node等资源管理
- **配置灵活**: 支持多种配置方式和智能功能开关
- **Poetry管理**: 使用Poetry进行依赖管理和环境隔离

## 🔧 支持的工具 (25+个)

### 基础K8s工具 (8个)
- `k8s-get-pods` - 获取Pod列表和状态
- `k8s-get-services` - 获取Service列表
- `k8s-get-deployments` - 获取Deployment列表
- `k8s-get-nodes` - 获取Node列表和状态
- `k8s-scale-deployment` - 扩缩容Deployment
- `k8s-get-logs` - 获取Pod日志
- `k8s-describe-pod` - 获取Pod详细信息
- `k8s-get-events` - 获取集群事件

### 智能分析工具 🧠 (5个)
- `k8s-relation-query` - 资源关联查询和依赖分析
- `k8s-cluster-summary` - 智能集群状态摘要生成
- `k8s-create-deployment` - 智能部署创建
- `k8s-resource-analysis` - 资源使用分析
- `k8s-troubleshoot` - 智能故障诊断

### Prometheus监控工具 🔔 (12+个)
- `k8s-resource-monitor` - 资源监控和告警测试
- `k8s-prometheus-app-metrics` - 获取应用Prometheus指标
- `k8s-update-knowledge-graph-metrics` - 更新知识图谱指标
- `k8s-prometheus-resource-analysis` - Prometheus资源分析 ⭐ **NEW**
- `k8s-arms-prometheus-query` - 阿里云ARMS Prometheus查询
- 以及更多监控和分析工具...

## 🚀 快速开始

### 1. 环境准备

**安装Poetry（如果没有安装）:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
# 或者使用pip
pip install poetry
```

**进入项目目录:**
```bash
cd k8s-mcp
```

### 2. 安装和配置

**安装依赖:**
```bash
poetry install
```

**配置环境:**
```bash
# 复制配置模板
cp config.env.example .env

# 编辑配置文件
vim .env
```

**基础配置 (.env):**
```env
# =============================================================================
# 🔧 基础配置
# =============================================================================

# Kubernetes配置文件路径 (必需)
KUBECONFIG_PATH=/Users/your-name/.kube/config

# 默认命名空间 (必需)
K8S_NAMESPACE=default

# 服务器配置
K8S_MCP_HOST=localhost
K8S_MCP_PORT=8766
K8S_MCP_DEBUG=false

# =============================================================================
# 🧠 智能功能配置 (可选)
# =============================================================================

# 启用知识图谱功能
ENABLE_KNOWLEDGE_GRAPH=true

# 集群同步间隔 (秒)
SYNC_INTERVAL=300

# 图查询最大深度
GRAPH_MAX_DEPTH=3

# 图节点TTL (秒)
GRAPH_TTL=3600

# 摘要最大大小 (KB)
MAX_SUMMARY_SIZE_KB=10

# =============================================================================
# 📊 监控配置 (可选)
# =============================================================================

# 启用监控功能
MONITORING_ENABLED=true

# 指标收集间隔 (秒)
METRICS_COLLECTION_INTERVAL=30

# 报警阈值
ALERT_CPU_PERCENT_MAX=80.0
ALERT_MEMORY_PERCENT_MAX=85.0
ALERT_ERROR_RATE_MAX=5.0
ALERT_SYNC_DELAY_MAX=300.0

# =============================================================================
# 🔔 资源告警配置 (V2) - 可选
# =============================================================================

# 启用资源告警功能
RESOURCE_ALERT_ENABLED=true

# 告警阈值设置 (0.0-1.0)
MEMORY_ALERT_THRESHOLD=0.7
CPU_ALERT_THRESHOLD=0.8

# 告警冷却时间 (秒)
ALERT_COOLDOWN_SECONDS=300

# 启用LLM智能分析
ENABLE_LLM_ANALYSIS=true
LLM_ANALYSIS_TIMEOUT=30

# 后端API通信配置
BACKEND_API_URL=http://localhost:8000
ENABLE_BACKEND_NOTIFICATIONS=true
API_TIMEOUT=30
API_MAX_RETRIES=3
```

### 3. 启动服务器

**标准启动:**
```bash
# 方式1: 使用Poetry运行
poetry run python start_k8s_mcp_http_server.py

# 方式2: 激活虚拟环境后运行
poetry shell
python start_k8s_mcp_http_server.py

# 方式3: 使用简化脚本
python run.py

# 方式4: 使用shell脚本
./scripts/start.sh
```

**启动成功示例:**
```
🚀 K8s MCP智能服务器启动中...
📡 监听地址: localhost:8766
🔧 调试模式: 禁用
📁 Kubeconfig: /Users/your-name/.kube/config
🎯 默认命名空间: default
🧠 智能模式已启用
📊 监控系统已启用
✅ 知识图谱初始化完成 (节点: 45, 边: 78)
✅ 集群同步引擎已启动
✅ 指标收集器已启动
🎯 Poetry虚拟环境: k8s-mcp-py3.11
🌐 服务器运行在: http://localhost:8766
```

### 4. 验证功能

**健康检查:**
```bash
curl http://localhost:8766/health
```

**监控指标:**
```bash
# 获取性能指标
curl http://localhost:8766/metrics

# 获取性能报告
curl http://localhost:8766/performance

# 获取智能功能状态
curl http://localhost:8766/intelligent/health
```

## 📊 监控和运维

### 监控API端点

| 端点 | 描述 | 示例 |
|------|------|------|
| `/health` | 系统健康检查 | `curl /health` |
| `/metrics` | 当前性能指标 | `curl /metrics` |
| `/metrics/history` | 指标历史数据 | `curl /metrics/history?last_minutes=60` |
| `/metrics/summary` | 指标汇总统计 | `curl /metrics/summary` |
| `/performance` | 性能报告和健康评分 | `curl /performance` |
| `/alerts` | 报警历史 | `curl /alerts?last_hours=24` |
| `/metrics/prometheus` | Prometheus格式指标 | `curl /metrics/prometheus` |
| `/intelligent/status` | 智能功能状态 | `curl /intelligent/status` |
| `/intelligent/health` | 智能功能健康检查 | `curl /intelligent/health` |

### 监控指标说明

**系统指标:**
- `system.cpu_percent` - CPU使用率
- `system.memory_percent` - 内存使用率
- `process.memory_rss_mb` - 进程内存使用

**应用指标:**
- `api.*.response_time` - API响应时间
- `api.*.requests` - API请求次数
- `tool.*.execution_time` - 工具执行时间

**智能功能指标:**
- `intelligent.kg_nodes` - 知识图谱节点数
- `intelligent.kg_edges` - 知识图谱边数
- `intelligent.sync_health_score` - 同步健康评分

### 健康评分算法

系统健康评分综合考虑以下因素：
- **CPU使用率** (权重20%): >80%开始扣分
- **内存使用率** (权重20%): >80%开始扣分  
- **API错误率** (权重30%): >0%开始扣分
- **同步健康状态** (权重20%): 同步状态评分
- **响应时间** (权重10%): >1秒开始扣分

评分区间：
- **90-100**: 优秀 (excellent)
- **75-89**: 良好 (good)
- **60-74**: 警告 (warning)
- **40-59**: 关键 (critical)
- **0-39**: 紧急 (emergency)

## 🧠 智能功能详解

### 知识图谱

**功能描述:**
- 自动构建K8s资源关系图谱
- 分析Pod、Service、Deployment等资源依赖关系
- 支持图谱查询和关联分析

**使用示例:**
```bash
# 通过MCP客户端调用关联查询工具
{
  "id": "req-rel-001",
  "name": "k8s-relation-query",
  "arguments": {
    "query_type": "dependencies",
    "resource_type": "pod",
    "resource_name": "my-app-pod",
    "max_depth": 2
  }
}
```

### 集群同步引擎

**功能描述:**
- 基于K8s Watch API的实时同步
- 增量更新，高效资源利用
- 自动重连和错误恢复

**同步状态监控:**
```bash
curl http://localhost:8766/intelligent/health
```

### 智能摘要生成

**功能描述:**
- 自动生成集群状态摘要
- 异常检测和优先级排序
- 数据大小控制，适配LLM上下文限制

**摘要示例:**
```bash
# 通过MCP客户端调用集群摘要工具
{
  "id": "req-sum-001",
  "name": "k8s-cluster-summary",
  "arguments": {
    "summary_type": "overview",
    "max_size_kb": 10,
    "include_anomalies": true
  }
}
```

## ⚙️ 配置详解

### 基础配置

| 配置项 | 描述 | 默认值 | 示例 |
|--------|------|--------|------|
| `KUBECONFIG_PATH` | K8s配置文件路径 | `~/.kube/config` | `/path/to/kubeconfig` |
| `K8S_NAMESPACE` | 默认命名空间 | `default` | `my-namespace` |
| `K8S_MCP_HOST` | 服务器绑定地址 | `localhost` | `0.0.0.0` |
| `K8S_MCP_PORT` | 服务器端口 | `8766` | `8080` |
| `K8S_MCP_DEBUG` | 调试模式 | `false` | `true` |

### 智能功能配置

| 配置项 | 描述 | 默认值 | 推荐值 |
|--------|------|--------|--------|
| `ENABLE_KNOWLEDGE_GRAPH` | 启用知识图谱 | `false` | `true` |
| `SYNC_INTERVAL` | 同步间隔(秒) | `300` | `300-600` |
| `GRAPH_MAX_DEPTH` | 图查询最大深度 | `3` | `2-5` |
| `GRAPH_TTL` | 图节点TTL(秒) | `3600` | `1800-7200` |
| `GRAPH_MEMORY_LIMIT` | 图内存限制(MB) | `1024` | `512-2048` |
| `MAX_SUMMARY_SIZE_KB` | 摘要最大大小(KB) | `10` | `5-20` |
| `WATCH_TIMEOUT` | Watch超时(秒) | `600` | `300-1200` |
| `MAX_RETRY_COUNT` | 最大重试次数 | `3` | `3-5` |

### 监控配置

| 配置项 | 描述 | 默认值 | 推荐值 |
|--------|------|--------|--------|
| `MONITORING_ENABLED` | 启用监控 | `true` | `true` |
| `METRICS_COLLECTION_INTERVAL` | 指标收集间隔(秒) | `30` | `15-60` |
| `METRICS_HISTORY_SIZE` | 历史数据保存数量 | `1000` | `500-2000` |
| `HEALTH_CHECK_ENABLED` | 启用健康检查 | `true` | `true` |
| `HEALTH_CHECK_INTERVAL` | 健康检查间隔(秒) | `30` | `10-60` |

### 报警阈值配置

| 配置项 | 描述 | 默认值 | 推荐值 |
|--------|------|--------|--------|
| `ALERT_API_RESPONSE_TIME_MAX` | API响应时间阈值(秒) | `5.0` | `2.0-10.0` |
| `ALERT_CPU_PERCENT_MAX` | CPU使用率阈值(%) | `80.0` | `70.0-90.0` |
| `ALERT_MEMORY_PERCENT_MAX` | 内存使用率阈值(%) | `85.0` | `80.0-95.0` |
| `ALERT_ERROR_RATE_MAX` | 错误率阈值(%) | `5.0` | `1.0-10.0` |
| `ALERT_SYNC_DELAY_MAX` | 同步延迟阈值(秒) | `300.0` | `60.0-600.0` |

## 🏗️ 项目结构

```
k8s-mcp/
├── 📁 配置和文档
│   ├── pyproject.toml              # Poetry配置
│   ├── poetry.lock                 # 依赖锁定
│   ├── README.md                   # 项目文档
│   ├── kubegraph.md               # 智能功能设计文档
│   └── config.env.example         # 配置模板
│
├── 📁 启动脚本
│   ├── start_k8s_mcp_http_server.py # HTTP服务器启动
│   ├── run.py                      # 简化启动脚本
│   └── scripts/                    # 脚本目录
│       ├── start.sh               # 启动脚本
│       └── dev.sh                 # 开发脚本
│
├── 📁 核心代码
│   └── src/k8s_mcp/
│       ├── 📄 基础模块
│       ├── server.py              # 服务器主逻辑
│       ├── config.py              # 配置管理
│       ├── k8s_client.py          # K8s客户端
│       │
│       ├── 📁 core/               # 核心模块
│       │   ├── tool_registry.py  # 工具注册表
│       │   ├── mcp_protocol.py   # MCP协议支持
│       │   ├── k8s_graph.py      # 知识图谱引擎
│       │   ├── cluster_sync.py   # 集群同步引擎
│       │   ├── summary_generator.py # 摘要生成器
│       │   ├── relation_query_handler.py # 关联查询处理器
│       │   ├── metrics_collector.py # 指标收集器
│       │   └── monitoring_middleware.py # 监控中间件
│       │
│       └── 📁 tools/              # K8s工具集
│           ├── k8s_get_pods.py   # 基础工具
│           ├── k8s_get_services.py
│           ├── k8s_relation_query.py # 智能工具
│           └── k8s_cluster_summary.py
│
├── 📁 测试
│   └── tests/
│       ├── test_server.py         # 服务器测试
│       ├── test_k8s_graph.py     # 知识图谱测试
│       ├── test_cluster_sync.py  # 同步引擎测试
│       ├── test_monitoring.py    # 监控系统测试
│       └── test_server_integration.py # 集成测试
│
├── 📁 配置和数据
│   ├── config/                   # 配置文件目录
│   └── logs/                     # 日志文件目录
│
└── 📁 项目文档
    └── project_document/         # 项目文档库
        ├── 技术架构与配置指南.md
        ├── mcp-config-guide.md
        └── architecture-diagrams/
```

## 🔒 安全配置

### 权限控制
```env
# 允许的命名空间（逗号分隔）
K8S_ALLOWED_NAMESPACES=default,kube-system,monitoring

# 禁止的命名空间（逗号分隔）
K8S_FORBIDDEN_NAMESPACES=kube-system,kube-public

# 最大资源数量限制
K8S_MAX_RESOURCES=100

# 启用操作审计
K8S_AUDIT_ENABLED=true
```

### 网络安全
- 确保服务器只在信任的网络环境中运行
- 使用防火墙限制访问端口
- 考虑使用TLS加密通信

### 身份认证
- 确保kubeconfig中的认证信息安全
- 定期轮换K8s访问凭据
- 使用最小权限原则配置RBAC

## 🧪 开发和测试

### 开发环境设置

```bash
# 安装开发依赖
poetry install

# 使用开发脚本
./scripts/dev.sh dev    # 安装开发依赖
./scripts/dev.sh test   # 运行测试
./scripts/dev.sh format # 代码格式化
./scripts/dev.sh type   # 类型检查
./scripts/dev.sh info   # 显示环境信息
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试模块
poetry run pytest tests/test_monitoring.py

# 运行集成测试
poetry run pytest tests/test_server_integration.py

# 生成覆盖率报告
poetry run pytest --cov=src/k8s_mcp --cov-report=html

# 运行性能测试
poetry run pytest tests/ -m performance
```

### 调试模式

```env
# 启用调试模式
K8S_MCP_DEBUG=true

# 启用详细日志
LOG_LEVEL=DEBUG
```

### Poetry命令速查

```bash
# 查看依赖
poetry show
poetry show --tree

# 添加依赖
poetry add <package>
poetry add --group dev <package>

# 更新依赖
poetry update
poetry update <package>

# 虚拟环境管理
poetry env info
poetry env list
poetry shell

# 运行命令
poetry run <command>

# 导出依赖
poetry export -f requirements.txt --output requirements.txt
```

## 🚀 部署指南

### 生产环境部署

**1. 使用Docker部署:**
```dockerfile
FROM python:3.11-slim

# 安装Poetry
RUN pip install poetry

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装依赖
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8766

# 启动命令
CMD ["poetry", "run", "python", "start_k8s_mcp_http_server.py"]
```

**构建和运行:**
```bash
# 构建镜像
docker build -t k8s-mcp:latest .

# 运行容器
docker run -d \
  --name k8s-mcp \
  -p 8766:8766 \
  -v ~/.kube:/root/.kube:ro \
  -v ./config:/app/config \
  -e ENABLE_KNOWLEDGE_GRAPH=true \
  -e MONITORING_ENABLED=true \
  k8s-mcp:latest
```

**2. 使用Kubernetes部署:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-mcp-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: k8s-mcp-server
  template:
    metadata:
      labels:
        app: k8s-mcp-server
    spec:
      containers:
      - name: k8s-mcp-server
        image: k8s-mcp:latest
        ports:
        - containerPort: 8766
        env:
        - name: ENABLE_KNOWLEDGE_GRAPH
          value: "true"
        - name: MONITORING_ENABLED
          value: "true"
        - name: K8S_NAMESPACE
          value: "default"
        volumeMounts:
        - name: kubeconfig
          mountPath: /root/.kube
          readOnly: true
      volumes:
      - name: kubeconfig
        secret:
          secretName: kubeconfig-secret
---
apiVersion: v1
kind: Service
metadata:
  name: k8s-mcp-service
spec:
  selector:
    app: k8s-mcp-server
  ports:
  - port: 8766
    targetPort: 8766
  type: ClusterIP
```

**3. 使用systemd服务:**
```ini
# /etc/systemd/system/k8s-mcp.service
[Unit]
Description=K8s MCP智能服务器
After=network.target

[Service]
Type=simple
User=k8s-mcp
WorkingDirectory=/opt/k8s-mcp
Environment=PATH=/opt/k8s-mcp/.venv/bin
ExecStart=/opt/k8s-mcp/.venv/bin/python start_k8s_mcp_http_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用和启动服务
sudo systemctl enable k8s-mcp.service
sudo systemctl start k8s-mcp.service
sudo systemctl status k8s-mcp.service
```

### 监控集成

**Prometheus配置:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'k8s-mcp'
    static_configs:
      - targets: ['localhost:8766']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 30s
```

**Grafana仪表板:**
```json
{
  "dashboard": {
    "title": "K8s MCP Monitor",
    "panels": [
      {
        "title": "System Health Score",
        "type": "stat",
        "targets": [
          {
            "expr": "k8s_mcp_performance_health_score"
          }
        ]
      },
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "k8s_mcp_api_response_time"
          }
        ]
      }
    ]
  }
}
```

## 🛠️ 故障排除

### 常见问题

**1. 连接问题**
```bash
# 检查kubeconfig文件
kubectl cluster-info

# 验证权限
kubectl auth can-i get pods

# 检查网络连接
curl -k https://your-k8s-api-server/api/v1
```

**2. 智能功能问题**
```bash
# 检查智能功能状态
curl http://localhost:8766/intelligent/health

# 查看同步状态
curl http://localhost:8766/intelligent/status

# 检查知识图谱
curl http://localhost:8766/metrics | grep intelligent
```

**3. 监控问题**
```bash
# 检查监控状态
curl http://localhost:8766/performance

# 查看指标收集
curl http://localhost:8766/metrics

# 检查报警历史
curl http://localhost:8766/alerts
```

**4. Poetry问题**
```bash
# 重新安装依赖
poetry install --no-cache

# 清除缓存
poetry cache clear pypi --all

# 重新创建虚拟环境
poetry env remove python
poetry install
```

**5. 性能问题**
```bash
# 检查系统资源
curl http://localhost:8766/metrics/summary

# 查看详细指标
curl http://localhost:8766/metrics/history?last_minutes=60

# 分析性能瓶颈
curl http://localhost:8766/performance
```

### 日志分析

**启用详细日志:**
```env
K8S_MCP_DEBUG=true
LOG_LEVEL=DEBUG
```

**日志位置:**
- 应用日志: `logs/k8s-mcp.log`
- 错误日志: `logs/error.log`
- 审计日志: `logs/audit.log`

**日志级别:**
- `ERROR`: 错误信息
- `WARNING`: 警告信息
- `INFO`: 一般信息
- `DEBUG`: 调试信息

### 性能优化

**内存优化:**
```env
# 减少图内存限制
GRAPH_MEMORY_LIMIT=512

# 减少历史数据保存
METRICS_HISTORY_SIZE=500

# 增加TTL以减少重建频率
GRAPH_TTL=7200
```

**同步优化:**
```env
# 调整同步间隔
SYNC_INTERVAL=600

# 调整Watch超时
WATCH_TIMEOUT=300

# 减少最大重试次数
MAX_RETRY_COUNT=2
```

## 📚 相关文档

- [技术架构设计](project_document/技术架构与配置指南.md)
- [MCP配置指南](project_document/mcp-config-guide.md)
- [项目状态文档](kubegraph.md)
- [Poetry使用指南](POETRY_GUIDE.md)

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Poetry文档](https://python-poetry.org/docs/)
- [FastAPI文档](https://fastapi.tiangolo.com/)

---

**⭐ 如果这个项目对你有帮助，请给个Star！**