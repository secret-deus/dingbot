# 钉钉K8s运维机器人

一个基于钉钉的智能Kubernetes运维机器人，支持通过自然语言进行K8s集群管理和运维操作。

## ✨ 核心特性

- 🤖 **智能对话**: 自然语言交互，理解运维意图
- ⚙️ **K8s管理**: Pod、Service、Deployment等资源管理
- 📊 **实时监控**: 集群状态、资源使用情况监控
- 🔧 **MCP协议**: 可扩展的工具系统
- 🌐 **Web界面**: 现代化聊天界面
- 📱 **钉钉集成**: 机器人webhook推送
- 🔐 **安全可控**: 权限控制和操作审计
- 💾 **会话持久化**: 对话历史自动保存，刷新不丢失
- ⚡ **流式响应**: 优化的SSE格式，实时响应体验

## 🚀 最新功能

### 会话持久化系统 (v0.9.0) ⭐ 最新更新
- ✅ **自动数据恢复** - 刷新页面后对话历史完整保留
- ✅ **智能会话管理** - 多会话支持，历史记录搜索
- ✅ **数据完整性** - 自动修复和验证机制
- ✅ **存储优化** - 渐进式加载，大数据集支持

### 流式响应优化 (v0.8.0)
- ✅ **优化SSE格式** - 改进分隔符，提升响应速度
- ✅ **智能错误处理** - 11种错误类型分类和建议
- ✅ **实时监控** - 性能统计和调试端点
- ✅ **健壮连接** - 自动重连和状态管理

### MCP工具系统
- ✅ **K8s-MCP服务器** - 8个完整的K8s管理工具
- ✅ **工具路由** - 智能路由和负载均衡
- ✅ **动态配置** - 热重载和运行时更新

## 🎯 项目进度

**当前完成度: 80%** 🎉

- ✅ **基础架构** (95%) - 前后端分离架构完成
- ✅ **MCP工具集成** (90%) - K8s工具完整实现
- ✅ **流式对话** (90%) - 实时聊天和工具调用
- ✅ **会话管理** (85%) - 持久化和历史管理
- 🔄 **MCP连接** (80%) - 最后配置问题修复中

## 架构设计

![project_document/architechture-diagrams/arch.png]

## 快速开始

### 1. 环境准备（30秒启动）

> 📋 **项目管理**: 本项目使用 [Poetry](https://python-poetry.org/) 进行Python依赖管理，所有Python命令必须使用 `poetry run` 前缀

```bash
# 克隆项目
git clone <repository-url>
cd ding-robot

# 安装Poetry依赖
poetry install

### 2. 配置文件

编辑 `backend/config.env` 文件：

```env
# LLM配置
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-3.5-turbo

# Kubernetes配置
KUBECONFIG_PATH=/path/to/kubeconfig
K8S_NAMESPACE=default

# MCP配置 (重要: 使用localhost而不是环境变量)
K8S_MCP_HOST=localhost
K8S_MCP_PORT=8766

# 钉钉配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your_token
DINGTALK_SECRET=your_secret
```

### 3. 启动MCP工具服务器

```bash
# 启动K8s MCP服务器
cd k8s-mcp
poetry run python -m k8s_mcp.server

# SSH-Jumpserver MCP (开发中，暂不可用)
# cd ssh-jumpserver-mcp
# poetry run python -m ssh_jumpserver_mcp.server
```

### 4. 启动主服务

```bash
# 开发环境（前后端分离）
poetry run dev

# 生产环境（单端口集成）
poetry run build && poetry run serve
```

### 5. 访问应用

**开发环境**:
- 🌐 前端: http://localhost:3000 (热重载)
- 🔧 后端: http://localhost:8000
- 📚 API文档: http://localhost:8000/docs

**生产环境**:
- 🌐 主页: http://localhost:8000
- 📱 SPA应用: http://localhost:8000/spa/
- 📚 API文档: http://localhost:8000/docs

## 📚 详细文档

```
project_document/
```

## 🛠️ 支持的工具

### Kubernetes工具 (8个)
- `k8s-get-pods` - 获取Pod列表和状态
- `k8s-get-services` - 获取Service列表  
- `k8s-get-deployments` - 获取Deployment列表
- `k8s-get-nodes` - 获取Node节点信息
- `k8s-scale-deployment` - 扩缩容Deployment
- `k8s-get-logs` - 获取Pod日志
- `k8s-describe-pod` - 获取Pod详细信息
- `k8s-get-events` - 获取集群事件

### SSH工具集 (计划中)
- `ssh-execute` - 远程命令执行 (开发中)
- `ssh-asset-list` - 服务器资产管理 (规划中)
- `ssh-session-manager` - SSH会话管理 (规划中)

## ⚡ 可用命令

| 命令 | 功能 | 使用场景 |
|------|------|----------|
| `poetry run dev` | 启动开发环境 | 日常开发 |
| `poetry run build` | 构建项目 | 部署前准备 |
| `poetry run serve` | 启动生产服务 | 生产部署 |
| `poetry run setup` | 项目初始化 | 第一次设置 |

## 🔧 故障排除

### 常见问题

1. **MCP连接失败** 
   ```bash
   # 检查配置文件 backend/config/mcp_config.json
   # 确保 "host": "localhost" 而不是 "${K8S_MCP_HOST}"
   ```

2. **会话数据丢失**
   ```bash
   # 已修复：现在支持自动数据恢复
   # 刷新页面后对话历史完整保留
   ```

3. **流式响应异常**
   ```bash
   # 已修复：优化了SSE格式
   # 支持更快的实时响应
   ```

### 监控端点
- **健康检查**: `GET /api/v2/health`
- **性能统计**: `GET /api/v2/debug/performance`
- **系统状态**: `GET /api/status`
- **可用工具**: `GET /api/v2/tools`

## 🎯 下一步计划

### 即将发布 (v1.0.0)
- ✅ MCP连接配置修复
- ✅ 生产部署优化
- ✅ 监控和告警系统
- ✅ 用户权限管理

### 未来功能
- 🔧 **SSH-Jumpserver MCP** - 企业级SSH运维工具集
  - SSH命令执行和会话管理
  - JumpServer平台集成
  - 服务器资产管理
  - 安全审计和权限控制
- 📊 可视化运维面板
- 🔄 批量操作支持
- 📱 移动端适配
- 🤖 更多AI工具集成

## 📄 许可证

MIT License

---

**🎉 项目已接近完成！目前85%功能就绪，期待你的体验和反馈！**