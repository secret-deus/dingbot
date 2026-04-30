# K8s MCP 部署运维指南

本文档提供K8s MCP服务器在各种环境下的部署、运维和监控指南。

## 📋 目录

- [部署概览](#部署概览)
- [本地开发部署](#本地开发部署)
- [Docker部署](#docker部署)
- [Kubernetes部署](#kubernetes部署)
- [生产环境部署](#生产环境部署)
- [监控和运维](#监控和运维)
- [备份和恢复](#备份和恢复)
- [性能调优](#性能调优)
- [故障处理](#故障处理)

## 🔧 部署概览

### 支持的部署方式

| 部署方式 | 适用场景 | 复杂度 | 推荐指数 |
|----------|----------|--------|----------|
| 本地开发 | 开发调试 | ⭐ | ⭐⭐⭐⭐⭐ |
| Docker单机 | 测试环境 | ⭐⭐ | ⭐⭐⭐⭐ |
| Kubernetes | 生产环境 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 系统服务 | 传统部署 | ⭐⭐ | ⭐⭐⭐ |

### 系统要求

**最低要求:**
- CPU: 2核
- 内存: 2GB RAM
- 存储: 10GB
- Python: 3.11+
- 网络: 访问K8s API服务器

**推荐配置:**
- CPU: 4核
- 内存: 8GB RAM
- 存储: 50GB SSD
- 网络: 千兆网络

**智能功能额外要求:**
- 内存: +2GB (知识图谱)
- CPU: +1核 (同步引擎)
- 存储: +5GB (指标历史)

## 💻 本地开发部署

### 快速开始

**1. 环境准备**
```bash
# 安装Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 克隆项目
git clone <repository-url>
cd k8s-mcp

# 安装依赖
poetry install
```

**2. 配置环境**
```bash
# 复制配置模板
cp config.env.example .env

# 编辑配置
vim .env
```

**基础开发配置 (.env):**
```env
# K8s配置
KUBECONFIG_PATH=/Users/your-name/.kube/config
K8S_NAMESPACE=default

# 服务器配置
K8S_MCP_HOST=localhost
K8S_MCP_PORT=8766
K8S_MCP_DEBUG=true

# 智能功能 (开发时可选)
ENABLE_KNOWLEDGE_GRAPH=true
SYNC_INTERVAL=300

# 监控功能
MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=30

# 开发特定配置
LOG_LEVEL=DEBUG
ENABLE_HOT_RELOAD=true
```

**3. 启动服务**
```bash
# 使用Poetry启动
poetry run python start_k8s_mcp_http_server.py

# 或者激活环境后启动
poetry shell
python start_k8s_mcp_http_server.py

# 使用开发脚本
./scripts/dev.sh run
```

**4. 验证部署**
```bash
# 检查健康状态
curl http://localhost:8766/health

# 检查智能功能
curl http://localhost:8766/intelligent/status

# 查看工具列表
curl http://localhost:8766/tools
```

### 开发环境优化

**热重载配置:**
```env
ENABLE_HOT_RELOAD=true
RELOAD_DIRS=src/k8s_mcp
RELOAD_EXCLUDES=tests,logs
```

**调试配置:**
```env
LOG_LEVEL=DEBUG
ENABLE_DEBUG_ROUTES=true
ENABLE_API_DOCS=true
ENABLE_SWAGGER_UI=true
```

## 🐳 Docker部署

### 单机Docker部署

**1. 创建Dockerfile**
```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 配置Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs config

# 设置权限
RUN useradd -m -u 1000 k8s-mcp && \
    chown -R k8s-mcp:k8s-mcp /app
USER k8s-mcp

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

# 暴露端口
EXPOSE 8766

# 启动命令
CMD ["python", "start_k8s_mcp_http_server.py"]
```

**2. 构建镜像**
```bash
# 构建镜像
docker build -t k8s-mcp:latest .

# 多阶段构建（生产优化）
docker build -f Dockerfile.prod -t k8s-mcp:prod .
```

**3. 运行容器**
```bash
# 基础运行
docker run -d \
  --name k8s-mcp \
  -p 8766:8766 \
  -v ~/.kube:/home/k8s-mcp/.kube:ro \
  -v ./logs:/app/logs \
  -e KUBECONFIG_PATH=/home/k8s-mcp/.kube/config \
  -e K8S_NAMESPACE=default \
  -e ENABLE_KNOWLEDGE_GRAPH=true \
  -e MONITORING_ENABLED=true \
  k8s-mcp:latest

# 使用环境文件
docker run -d \
  --name k8s-mcp \
  -p 8766:8766 \
  -v ~/.kube:/home/k8s-mcp/.kube:ro \
  -v ./logs:/app/logs \
  --env-file .env.docker \
  k8s-mcp:latest
```

**4. Docker Compose部署**

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  k8s-mcp:
    build: .
    container_name: k8s-mcp
    restart: unless-stopped
    ports:
      - "8766:8766"
    volumes:
      - ~/.kube:/home/k8s-mcp/.kube:ro
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - KUBECONFIG_PATH=/home/k8s-mcp/.kube/config
      - K8S_NAMESPACE=default
      - ENABLE_KNOWLEDGE_GRAPH=true
      - MONITORING_ENABLED=true
      - K8S_MCP_HOST=0.0.0.0
    env_file:
      - .env.docker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8766/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - k8s-mcp-network

  # 可选：添加监控组件
  prometheus:
    image: prom/prometheus:latest
    container_name: k8s-mcp-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - k8s-mcp-network

networks:
  k8s-mcp-network:
    driver: bridge
```

**启动服务:**
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f k8s-mcp

# 停止服务
docker-compose down
```

### 生产Docker配置

**Dockerfile.prod:**
```dockerfile
# 多阶段构建
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

FROM python:3.11-slim as runtime

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# 复制Python环境
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建用户
RUN useradd -m -u 1000 k8s-mcp && \
    mkdir -p logs config && \
    chown -R k8s-mcp:k8s-mcp /app

USER k8s-mcp

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

EXPOSE 8766

CMD ["python", "start_k8s_mcp_http_server.py"]
```

## ☸️ Kubernetes部署

### 基础K8s部署

**1. 创建命名空间**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: k8s-mcp
  labels:
    name: k8s-mcp
```

**2. 创建ServiceAccount和RBAC**
```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: k8s-mcp-sa
  namespace: k8s-mcp
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8s-mcp-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes", "events", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "patch"]
- apiGroups: ["extensions"]
  resources: ["deployments", "ingresses"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses", "networkpolicies"]
  verbs: ["get", "list", "watch"]
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
  name: k8s-mcp-sa
  namespace: k8s-mcp
```

**3. 创建ConfigMap**
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8s-mcp-config
  namespace: k8s-mcp
data:
  K8S_NAMESPACE: "default"
  K8S_MCP_HOST: "0.0.0.0"
  K8S_MCP_PORT: "8766"
  ENABLE_KNOWLEDGE_GRAPH: "true"
  MONITORING_ENABLED: "true"
  SYNC_INTERVAL: "300"
  METRICS_COLLECTION_INTERVAL: "30"
  LOG_LEVEL: "INFO"
```

**4. 创建Deployment**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-mcp-server
  namespace: k8s-mcp
  labels:
    app: k8s-mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: k8s-mcp-server
  template:
    metadata:
      labels:
        app: k8s-mcp-server
    spec:
      serviceAccountName: k8s-mcp-sa
      containers:
      - name: k8s-mcp-server
        image: k8s-mcp:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8766
          name: http
        envFrom:
        - configMapRef:
            name: k8s-mcp-config
        env:
        - name: KUBECONFIG_PATH
          value: "/var/run/secrets/kubernetes.io/serviceaccount"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8766
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8766
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: config
          mountPath: /app/config
      volumes:
      - name: logs
        emptyDir: {}
      - name: config
        emptyDir: {}
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

**5. 创建Service**
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: k8s-mcp-service
  namespace: k8s-mcp
  labels:
    app: k8s-mcp-server
spec:
  type: ClusterIP
  ports:
  - port: 8766
    targetPort: 8766
    protocol: TCP
    name: http
  selector:
    app: k8s-mcp-server
---
apiVersion: v1
kind: Service
metadata:
  name: k8s-mcp-metrics
  namespace: k8s-mcp
  labels:
    app: k8s-mcp-server
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8766"
    prometheus.io/path: "/metrics/prometheus"
spec:
  type: ClusterIP
  ports:
  - port: 8766
    targetPort: 8766
    protocol: TCP
    name: metrics
  selector:
    app: k8s-mcp-server
```

**6. 创建Ingress（可选）**
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: k8s-mcp-ingress
  namespace: k8s-mcp
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - k8s-mcp.your-domain.com
    secretName: k8s-mcp-tls
  rules:
  - host: k8s-mcp.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: k8s-mcp-service
            port:
              number: 8766
```

**7. 部署到集群**
```bash
# 应用所有配置
kubectl apply -f namespace.yaml
kubectl apply -f rbac.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# 检查部署状态
kubectl get all -n k8s-mcp

# 查看Pod日志
kubectl logs -f -n k8s-mcp deployment/k8s-mcp-server

# 端口转发测试
kubectl port-forward -n k8s-mcp service/k8s-mcp-service 8766:8766
```

### Helm部署

**Chart.yaml:**
```yaml
apiVersion: v2
name: k8s-mcp
description: Kubernetes MCP Server Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"
```

**values.yaml:**
```yaml
replicaCount: 2

image:
  repository: k8s-mcp
  tag: latest
  pullPolicy: IfNotPresent

serviceAccount:
  create: true
  name: k8s-mcp-sa

service:
  type: ClusterIP
  port: 8766

ingress:
  enabled: false
  annotations: {}
  hosts:
    - host: k8s-mcp.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2"

config:
  k8sNamespace: "default"
  enableKnowledgeGraph: true
  monitoringEnabled: true
  logLevel: "INFO"

monitoring:
  prometheus:
    enabled: true
    serviceMonitor:
      enabled: true

autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

**安装Helm Chart:**
```bash
# 创建Chart
helm create k8s-mcp-chart

# 安装
helm install k8s-mcp ./k8s-mcp-chart \
  --namespace k8s-mcp \
  --create-namespace \
  --values values.yaml

# 升级
helm upgrade k8s-mcp ./k8s-mcp-chart \
  --namespace k8s-mcp \
  --values values.yaml

# 卸载
helm uninstall k8s-mcp --namespace k8s-mcp
```

## 🏢 生产环境部署

### 高可用部署架构

```yaml
# 生产环境高可用部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-mcp-server
  namespace: k8s-mcp
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - k8s-mcp-server
              topologyKey: kubernetes.io/hostname
      containers:
      - name: k8s-mcp-server
        image: k8s-mcp:v1.0.0
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "8Gi"
            cpu: "4"
        env:
        - name: WORKER_THREADS
          value: "8"
        - name: CONNECTION_POOL_SIZE
          value: "50"
        - name: MAX_MEMORY_USAGE
          value: "6144MB"
        - name: ENABLE_PROMETHEUS_EXPORT
          value: "true"
```

### 存储配置

**持久化存储:**
```yaml
# 持久化卷声明
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: k8s-mcp-logs-pvc
  namespace: k8s-mcp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast-ssd
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: k8s-mcp-config-pvc
  namespace: k8s-mcp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: fast-ssd
```

### 网络策略

**网络安全配置:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: k8s-mcp-network-policy
  namespace: k8s-mcp
spec:
  podSelector:
    matchLabels:
      app: k8s-mcp-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8766
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # K8s API
    - protocol: TCP
      port: 6443 # K8s API
```

### 自动扩缩容

**HPA配置:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: k8s-mcp-hpa
  namespace: k8s-mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: k8s-mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

## 📊 监控和运维

### Prometheus监控配置

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'k8s-mcp'
    static_configs:
      - targets: ['k8s-mcp-service:8766']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'k8s-mcp-health'
    static_configs:
      - targets: ['k8s-mcp-service:8766']
    metrics_path: '/health'
    scrape_interval: 60s

rule_files:
  - "k8s-mcp-rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

**告警规则 (k8s-mcp-rules.yml):**
```yaml
groups:
- name: k8s-mcp-alerts
  rules:
  - alert: K8sMCPServerDown
    expr: up{job="k8s-mcp"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "K8s MCP Server is down"
      description: "K8s MCP Server has been down for more than 1 minute."

  - alert: K8sMCPHighCPU
    expr: k8s_mcp_system_cpu_percent > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "K8s MCP Server high CPU usage"
      description: "CPU usage is {{ $value }}% for more than 5 minutes."

  - alert: K8sMCPHighMemory
    expr: k8s_mcp_system_memory_percent > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "K8s MCP Server high memory usage"
      description: "Memory usage is {{ $value }}% for more than 5 minutes."

  - alert: K8sMCPHighErrorRate
    expr: rate(k8s_mcp_api_errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "K8s MCP Server high error rate"
      description: "Error rate is {{ $value }} errors/sec for more than 2 minutes."

  - alert: K8sMCPSyncUnhealthy
    expr: k8s_mcp_intelligent_sync_health_score < 0.5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "K8s MCP cluster sync unhealthy"
      description: "Cluster sync health score is {{ $value }} for more than 10 minutes."
```

### Grafana仪表板

**仪表板JSON配置:**
```json
{
  "dashboard": {
    "id": null,
    "title": "K8s MCP Server Dashboard",
    "tags": ["k8s", "mcp"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Server Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"k8s-mcp\"}",
            "legendFormat": "Server Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "k8s_mcp_system_cpu_percent",
            "legendFormat": "CPU %"
          },
          {
            "expr": "k8s_mcp_system_memory_percent",
            "legendFormat": "Memory %"
          }
        ],
        "yAxes": [
          {
            "max": 100,
            "min": 0,
            "unit": "percent"
          }
        ]
      },
      {
        "id": 3,
        "title": "API Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(k8s_mcp_api_requests_total[5m])",
            "legendFormat": "Requests/sec"
          },
          {
            "expr": "k8s_mcp_api_response_time",
            "legendFormat": "Response Time"
          }
        ]
      },
      {
        "id": 4,
        "title": "Knowledge Graph",
        "type": "stat",
        "targets": [
          {
            "expr": "k8s_mcp_intelligent_kg_nodes",
            "legendFormat": "Nodes"
          },
          {
            "expr": "k8s_mcp_intelligent_kg_edges",
            "legendFormat": "Edges"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### 日志管理

**Fluent Bit配置:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: k8s-mcp
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /app/logs/*.log
        Parser            json
        Tag               k8s-mcp.*
        Refresh_Interval  5

    [FILTER]
        Name                kubernetes
        Match               k8s-mcp.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token

    [OUTPUT]
        Name  es
        Match *
        Host  elasticsearch.logging.svc.cluster.local
        Port  9200
        Index k8s-mcp
```

## 🔄 备份和恢复

### 配置备份

**备份脚本:**
```bash
#!/bin/bash

BACKUP_DIR="/backup/k8s-mcp"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR/$DATE"

# 备份K8s配置
kubectl get all -n k8s-mcp -o yaml > "$BACKUP_DIR/$DATE/k8s-resources.yaml"
kubectl get configmap -n k8s-mcp -o yaml > "$BACKUP_DIR/$DATE/configmaps.yaml"
kubectl get secret -n k8s-mcp -o yaml > "$BACKUP_DIR/$DATE/secrets.yaml"

# 备份应用配置
cp -r /app/config "$BACKUP_DIR/$DATE/"

# 备份日志（最近7天）
find /app/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/$DATE/" \;

# 压缩备份
tar -czf "$BACKUP_DIR/k8s-mcp-backup-$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"

# 清理临时目录
rm -rf "$BACKUP_DIR/$DATE"

echo "备份完成: $BACKUP_DIR/k8s-mcp-backup-$DATE.tar.gz"
```

### 数据恢复

**恢复脚本:**
```bash
#!/bin/bash

BACKUP_FILE=$1
RESTORE_DIR="/tmp/k8s-mcp-restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <backup-file>"
    exit 1
fi

# 解压备份
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# 恢复K8s资源
kubectl apply -f "$RESTORE_DIR"/*/k8s-resources.yaml
kubectl apply -f "$RESTORE_DIR"/*/configmaps.yaml
kubectl apply -f "$RESTORE_DIR"/*/secrets.yaml

# 恢复配置文件
cp -r "$RESTORE_DIR"/*/config/* /app/config/

echo "恢复完成"
```

### 自动备份

**CronJob配置:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: k8s-mcp-backup
  namespace: k8s-mcp
spec:
  schedule: "0 2 * * *"  # 每天凌晨2点
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: k8s-mcp-backup-sa
          containers:
          - name: backup
            image: backup-tools:latest
            command:
            - /bin/bash
            - -c
            - |
              /backup-scripts/backup.sh
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
            - name: backup-scripts
              mountPath: /backup-scripts
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          - name: backup-scripts
            configMap:
              name: backup-scripts
              defaultMode: 0755
          restartPolicy: OnFailure
```

## ⚡ 性能调优

### 应用层优化

**内存优化:**
```env
# 增加内存限制
GRAPH_MEMORY_LIMIT=2048
MAX_MEMORY_USAGE=4096MB

# 启用内存优化
ENABLE_MEMORY_OPTIMIZATION=true
MEMORY_CLEANUP_INTERVAL=300
GC_THRESHOLD=80

# 缓存优化
CACHE_MAX_SIZE=2000
CACHE_TTL=600
ENABLE_DISTRIBUTED_CACHE=true
```

**并发优化:**
```env
# 增加工作线程
WORKER_THREADS=16
CONNECTION_POOL_SIZE=50

# 并发控制
MAX_CONCURRENT_REQUESTS=200
RATE_LIMIT_PER_SECOND=20

# 网络优化
KEEP_ALIVE_TIMEOUT=60
MAX_CONNECTIONS=2000
SOCKET_TIMEOUT=30
```

### 容器优化

**资源限制调优:**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2"
  limits:
    memory: "16Gi"
    cpu: "8"
```

**JVM优化（如使用）:**
```env
JAVA_OPTS="-Xms2g -Xmx8g -XX:+UseG1GC -XX:MaxGCPauseMillis=200"
```

### 集群层优化

**节点亲和性:**
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node-type
          operator: In
          values:
          - high-memory
          - compute-optimized
```

**优先级类:**
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: k8s-mcp-priority
value: 1000
globalDefault: false
description: "Priority class for K8s MCP server"
```

## 🚨 故障处理

### 常见故障排查

**1. 服务启动失败**
```bash
# 检查Pod状态
kubectl get pods -n k8s-mcp

# 查看详细错误
kubectl describe pod <pod-name> -n k8s-mcp

# 查看日志
kubectl logs <pod-name> -n k8s-mcp
```

**2. K8s连接问题**
```bash
# 检查ServiceAccount权限
kubectl auth can-i get pods --as=system:serviceaccount:k8s-mcp:k8s-mcp-sa

# 检查网络连接
kubectl exec -it <pod-name> -n k8s-mcp -- curl -k https://kubernetes.default.svc
```

**3. 性能问题**
```bash
# 检查资源使用
kubectl top pods -n k8s-mcp

# 查看性能指标
curl http://<pod-ip>:8766/performance

# 分析慢查询
curl http://<pod-ip>:8766/metrics/history?metric_name=api.response_time
```

### 故障恢复流程

**自动恢复配置:**
```yaml
# 设置合适的重启策略
restartPolicy: Always
terminationGracePeriodSeconds: 30

# 配置健康检查
livenessProbe:
  httpGet:
    path: /health
    port: 8766
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8766
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**紧急恢复脚本:**
```bash
#!/bin/bash

echo "=== K8s MCP 紧急恢复 ==="

# 重启Deployment
kubectl rollout restart deployment/k8s-mcp-server -n k8s-mcp

# 等待重启完成
kubectl rollout status deployment/k8s-mcp-server -n k8s-mcp

# 检查服务状态
kubectl get pods -n k8s-mcp

# 验证健康状态
kubectl exec -it $(kubectl get pods -n k8s-mcp -l app=k8s-mcp-server -o jsonpath='{.items[0].metadata.name}') -n k8s-mcp -- curl -f http://localhost:8766/health

echo "紧急恢复完成"
```

---

**💡 建议**: 生产环境部署前请先在测试环境验证所有配置，并制定详细的监控和应急响应计划。