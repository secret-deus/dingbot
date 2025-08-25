# 钉钉K8s运维机器人 - 开发与部署完整指南

**最后更新**: 2025-01-21 15:30:00 +08:00  
**适用版本**: v1.1.0+  
**目标用户**: 开发者、运维人员、系统管理员

---

## 🎯 快速开始

### 环境要求
- **Python**: 3.11+
- **Node.js**: 16+
- **Poetry**: 最新版本
- **操作系统**: macOS/Linux/Windows

### 一键启动
```bash
# 1. 克隆项目
git clone <repository-url>
cd ding-robot

# 2. 安装依赖
poetry install
cd frontend && npm install && cd ..

# 3. 配置环境
cp backend/config.env.example backend/config.env
cp k8s-mcp/config.env.example k8s-mcp/config.env

# 4. 启动所有服务
./scripts/dev.py  # 或者手动启动各个服务
```

### 访问地址
- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 🏗️ 开发环境搭建

### 1. 依赖安装

#### Python依赖 (Poetry)
```bash
# 安装Poetry (如果未安装)
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 验证安装
poetry run python --version
```

#### Node.js前端依赖
```bash
cd frontend
npm install

# 验证安装
npm run build
```

### 2. 配置文件设置

#### 后端配置
```bash
# 复制配置模板
cp backend/config.env.example backend/config.env

# 编辑配置文件
vim backend/config.env
```

**主要配置项**:
```env
# LLM配置
OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint

# MCP服务器配置
K8S_MCP_SERVER_URL=http://localhost:8001
SSH_MCP_SERVER_URL=http://localhost:8002

# Prometheus配置 (可选)
PROMETHEUS_URL=https://arms-prometheus.cn-hangzhou.aliyuncs.com
PROMETHEUS_ACCESS_KEY=your_access_key
PROMETHEUS_SECRET_KEY=your_secret_key
```

#### MCP服务器配置
```bash
# K8s MCP服务器
cp k8s-mcp/config.env.example k8s-mcp/config.env

# SSH MCP服务器
cp ssh-jumpserver-mcp/config.env.example ssh-jumpserver-mcp/config.env
```

### 3. 服务启动顺序

#### 方式1: 自动化脚本 (推荐)
```bash
# 开发模式启动
poetry run python scripts/dev.py

# 生产模式启动
poetry run python scripts/serve.py
```

#### 方式2: 手动启动
```bash
# 1. 启动MCP服务器
poetry run python k8s-mcp/start_k8s_mcp_http_server.py &
poetry run python ssh-jumpserver-mcp/start_mcp_server.py &

# 2. 启动后端API
poetry run python backend/main.py &

# 3. 启动前端 (新终端)
cd frontend && npm run dev
```

---

## 🔧 开发工作流

### 代码结构
```
ding-robot/
├── backend/                 # FastAPI后端
│   ├── src/api/v2/         # API路由
│   ├── src/config/         # 配置管理
│   ├── src/llm/            # LLM处理 + 安全
│   └── src/mcp/            # MCP客户端
├── frontend/               # Vue.js前端
│   ├── src/components/     # 组件
│   ├── src/views/          # 页面
│   └── src/stores/         # 状态管理
├── k8s-mcp/               # Kubernetes MCP服务器
├── ssh-jumpserver-mcp/    # SSH MCP服务器
└── config/                # 统一配置目录
```

### 开发规范

#### Python后端开发
```bash
# 运行测试
poetry run python -m pytest backend/tests/ -v

# 代码格式化
poetry run black backend/
poetry run isort backend/

# 类型检查
poetry run mypy backend/src/
```

#### 前端开发
```bash
cd frontend

# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

#### MCP工具开发
```bash
# 测试K8s MCP工具
poetry run python k8s-mcp/tests/test_k8s_cluster_summary_tool.py

# 添加新工具
# 1. 在 k8s-mcp/src/k8s_mcp/tools/ 创建新工具文件
# 2. 在 __init__.py 中注册工具
# 3. 更新配置文件
```

### 调试和测试

#### 后端API测试
```bash
# 健康检查
curl http://localhost:8000/health

# LLM配置测试
curl http://localhost:8000/api/v2/llm/config/current

# MCP配置测试
curl http://localhost:8000/api/v2/mcp/config

# 流式聊天测试
curl -N http://localhost:8000/api/v2/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "获取Pod列表"}'
```

#### MCP工具测试
```bash
# 测试K8s工具
curl -X POST http://localhost:8001/mcp/tools/k8s-get-pods \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default"}'

# 测试Prometheus分析工具
curl -X POST http://localhost:8001/mcp/tools/k8s-prometheus-resource-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "prometheus_url": "http://prometheus:9090",
    "days": 7,
    "cpu_threshold": 60.0
  }'
```

---

## 🚀 生产部署

### Docker部署

#### 构建镜像
```bash
# 构建后端镜像
docker build -t ding-robot-backend -f backend/Dockerfile .

# 构建前端镜像
docker build -t ding-robot-frontend -f frontend/Dockerfile .

# 构建MCP服务器镜像
docker build -t ding-robot-k8s-mcp -f k8s-mcp/Dockerfile .
```

#### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    image: ding-robot-backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./config:/app/config
    depends_on:
      - k8s-mcp
      
  frontend:
    image: ding-robot-frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
      
  k8s-mcp:
    image: ding-robot-k8s-mcp
    ports:
      - "8001:8001"
    environment:
      - KUBECONFIG=/app/.kube/config
    volumes:
      - ~/.kube:/app/.kube:ro
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### Kubernetes部署

#### 部署配置
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ding-robot-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ding-robot-backend
  template:
    metadata:
      labels:
        app: ding-robot-backend
    spec:
      containers:
      - name: backend
        image: ding-robot-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ding-robot-secrets
              key: openai-api-key
        volumeMounts:
        - name: config
          mountPath: /app/config
      volumes:
      - name: config
        configMap:
          name: ding-robot-config
---
apiVersion: v1
kind: Service
metadata:
  name: ding-robot-backend-service
spec:
  selector:
    app: ding-robot-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

```bash
# 部署到K8s
kubectl apply -f k8s-deployment.yaml

# 查看部署状态
kubectl get pods -l app=ding-robot-backend
kubectl logs -f deployment/ding-robot-backend
```

### 生产环境配置

#### 环境变量配置
```bash
# 生产环境变量
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export OPENAI_API_KEY=your_production_key
export PROMETHEUS_URL=https://arms-prometheus.cn-hangzhou.aliyuncs.com
export PROMETHEUS_ACCESS_KEY=your_access_key
export PROMETHEUS_SECRET_KEY=your_secret_key
```

#### 安全配置
```bash
# 设置文件权限
chmod 600 config/*.json
chmod 600 backend/config.env

# 配置防火墙
ufw allow 8000/tcp  # 后端API
ufw allow 5173/tcp  # 前端界面
```

---

## 📊 监控和维护

### 日志管理
```bash
# 查看应用日志
tail -f logs/app.log

# 查看MCP服务器日志
tail -f k8s-mcp/logs/server.log

# 日志轮转配置
logrotate /etc/logrotate.d/ding-robot
```

### 性能监控
```bash
# 检查系统资源
htop
df -h
free -m

# 检查服务状态
systemctl status ding-robot-backend
systemctl status ding-robot-k8s-mcp

# API性能测试
ab -n 1000 -c 10 http://localhost:8000/health
```

### 备份和恢复
```bash
# 配置备份
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# 数据库备份 (如果使用)
pg_dump ding_robot > backup-$(date +%Y%m%d).sql

# 恢复配置
tar -xzf config-backup-20250121.tar.gz
```

---

## 🔧 故障排查

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173

# 检查依赖
poetry show
npm list

# 检查配置文件
poetry run python -c "from backend.src.config import get_config; print(get_config())"
```

#### 2. MCP连接失败
```bash
# 检查MCP服务器状态
curl http://localhost:8001/health

# 检查MCP配置
cat config/mcp_config.json

# 重启MCP服务器
pkill -f k8s_mcp
poetry run python k8s-mcp/start_k8s_mcp_http_server.py
```

#### 3. 前端无法访问后端
```bash
# 检查网络连接
curl http://localhost:8000/health

# 检查CORS配置
grep -r "allow_origins" backend/

# 检查代理配置
cat frontend/vite.config.js
```

### 调试工具
```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=DEBUG

# 使用调试器
poetry run python -m pdb backend/main.py

# 前端调试
npm run dev -- --debug
```

---

## 📝 开发最佳实践

### 代码质量
1. **类型安全**: 使用TypeScript和Python类型注解
2. **测试覆盖**: 保持80%+的测试覆盖率
3. **代码审查**: 所有PR必须经过审查
4. **文档更新**: 功能变更同步更新文档

### 性能优化
1. **异步处理**: 使用async/await处理IO操作
2. **缓存机制**: 合理使用Redis缓存
3. **连接池**: 数据库和HTTP连接池管理
4. **资源监控**: 定期检查内存和CPU使用

### 安全考虑
1. **敏感信息**: 使用环境变量存储API密钥
2. **数据脱敏**: 日志中不包含敏感信息
3. **权限控制**: 最小权限原则
4. **定期更新**: 及时更新依赖包

---

## 📞 支持与反馈

### 技术支持
- **文档**: 查看项目文档目录
- **Issue**: 提交GitHub Issue
- **讨论**: 项目讨论区

### 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request
5. 等待代码审查

---

**维护者**: AI Assistant  
**最新更新**: 2025-01-21 15:30:00 +08:00
