# 钉钉K8s运维机器人 - 项目状态与计划

**最后更新**: 2025-12-18 19:52:00 +08:00
**版本**: v2.0.0
**状态**: 生产就绪 ✅

---

## 📋 项目概述

钉钉K8s运维机器人是一个基于现代Web技术的智能运维平台，通过自然语言交互和MCP协议，为企业提供强大的Kubernetes集群管理和ECS云服务器运维能力。

### 技术栈
| 层级 | 技术 |
|------|------|
| **前端** | Vue.js 3 + Element Plus + Pinia + Vite |
| **后端** | FastAPI + Pydantic + Python 3.11+ |
| **包管理** | Poetry (统一管理) |
| **协议** | MCP (Model Context Protocol) |
| **部署** | Docker + K8s |

### 项目规模
- **代码量**: ~28,000行
- **模块数**: 前端(frontend-v2) + 后端（进程内 K8s/ECS MCP 工具 + 可选远程 MCP）
- **工具数**: 25+ K8s工具 + ECS监控工具 + Prometheus分析工具

---

## 🏗️ 系统架构

```
用户界面(Vue3) → API路由层(FastAPI) → LLM处理器 → 脱敏层 → MCP客户端 → 恢复层 → MCP服务器集群 → 外部系统
```

### 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **前端** | `frontend-v2/` | Vue3 SPA，企业风浅色主题 |
| **后端** | `backend/` | FastAPI REST API + SSE流式响应 |
| **K8s 工具** | `backend/src/k8s_mcp/` | Kubernetes管理工具集(25+)，进程内注册 |
| **ECS 工具** | `backend/src/ecs_mcp/` | 阿里云ECS监控和巡检，进程内注册 |
| **归档（旧独立服务）** | `archived/k8s-mcp-standalone/`、`archived/ecs-mcp-standalone/` | 仅供参考，不再作为运行路径 |
| **配置** | `config/` | 统一配置目录 |

---

## ✅ 已完成功能

### 1. 前端系统 (frontend-v2)
- ✅ **企业风UI设计** - 浅灰背景 + 白色卡片 + 浅蓝高亮
- ✅ **流式聊天** - SSE实时响应，打字动画
- ✅ **工具调用可视化** - 工具卡片+转圈动画
- ✅ **会话管理** - 创建、切换、导出、导入
- ✅ **Markdown渲染** - 代码高亮、表格渲染修复
- ✅ **MCP服务器开关** - 动态启用/禁用工具

### 2. 后端API系统
- ✅ **统一API路由** - `/api/v2/` 前缀
- ✅ **SSE流式响应** - 30%性能提升
- ✅ **MCP动态初始化** - 支持按需启用MCP
- ✅ **配置热重载** - watchdog实时监控

### 3. 配置管理系统
- ✅ **统一配置路径** - `config/` 目录
- ✅ **LLM多提供商** - OpenAI、Azure、智谱等
- ✅ **MCP配置管理** - 服务器/工具启用控制
- ✅ **自动迁移** - 环境变量→文件配置

### 4. 数据安全系统
- ✅ **数据脱敏** - IP/主机名/人名脱敏
- ✅ **双阶段恢复** - 流式+完整响应恢复
- ✅ **日志安全** - 脱敏后日志记录

### 5. MCP工具集
- ✅ **K8s管理** - Pod/Service/Deployment等25+工具
- ✅ **Prometheus分析** - 资源利用率分析
- ✅ **ECS监控** - 实例监控+巡检报告

---

## 🔧 最近修复 (2025-12-18)

### 前端优化
1. **配色方案调整** - 企业风浅色主题
   - 历史对话当前项: 浅蓝高亮 (`#eff6ff`)
   - 用户消息气泡: 浅蓝背景 (`#e0edff`)
   - 整体背景: 浅灰 (`#f5f7fb`)

2. **Markdown渲染修复**
   - 修复代码块语言标记被拆分问题
   - 增加常见语言白名单自动合并

### 后端修复
1. **MCP动态初始化** - 支持启动时禁用MCP，后续按需启用
2. **工具调用结构化** - 移除冗余文本消息，仅保留工具卡片

---

## 📁 目录结构

```
ding-robot/
├── backend/                 # FastAPI后端
│   ├── src/
│   │   ├── api/v2/         # API路由
│   │   ├── config/         # 配置管理
│   │   ├── llm/            # LLM处理 + 安全
│   │   ├── mcp/            # MCP客户端 + 进程内工具注册
│   │   ├── k8s_mcp/        # 进程内 K8s 工具
│   │   └── ecs_mcp/        # 进程内 ECS 工具
│   ├── static/spa/         # 前端构建产物
│   └── config.env          # 环境配置
├── frontend-v2/            # Vue.js 3 前端 (当前使用)
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   └── stores/         # 状态管理
│   └── vite.config.js      # 构建配置
├── config/                  # 统一配置目录
│   ├── mcp_config.json     # MCP配置
│   └── llm_providers.json  # LLM配置
├── archived/               # 历史独立 K8s/ECS MCP 工程归档
├── scripts/                # 构建脚本
└── project_document/       # 项目文档
```

---

## 🚀 快速启动

### 1. 安装依赖
```bash
# Python依赖
poetry install

# 前端依赖 (仅开发时需要)
cd frontend-v2 && npm install
```

### 2. 配置
```bash
cp backend/config.env.example backend/config.env
# 编辑 config.env 配置LLM API Key等
```

### 3. 启动服务
```bash
# K8s/ECS 工具默认在主进程内（BUILTIN_K8S_ECS_TOOLS=true），无需单独起子服务
poetry run start-all
# 或
poetry run serve
```

### 4. 访问
- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 📋 下一步计划

### 短期 (1-2周)
- [ ] **性能优化** - 大量工具调用响应速度
- [ ] **错误处理** - 更友好的错误提示
- [ ] **单元测试** - 提高测试覆盖率

### 中期 (1个月)
- [ ] **监控系统** - Prometheus + Grafana集成
- [ ] **权限管理** - 基于角色的访问控制
- [ ] **审计日志** - 完整操作审计

### 长期 (3个月)
- [ ] **多集群支持** - 管理多个K8s集群
- [ ] **插件系统** - 支持第三方MCP工具
- [ ] **移动端** - 钉钉小程序版本
- [ ] **RDS监控** - 云数据库运维工具

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [技术架构与配置指南](./技术架构与配置指南.md) | 系统架构详解、配置管理 |
| [归档说明](../archived/README.md) | 原独立 k8s-mcp / ecs-mcp 工程说明 |
| [API文档](./api-documentation.md) | REST API参考 |

---

## 🔧 故障排查

### 常见问题

1. **MCP连接失败**
   ```bash
   # 检查后端健康；远程 MCP 端口以 config/mcp_config.json 为准
   curl http://localhost:8000/health
   ```

2. **工具无法使用**
   ```bash
   # 检查MCP配置
   curl http://localhost:8000/api/v2/mcp/config
   ```

3. **流式响应异常**
   ```bash
   # 检查后端日志
   tail -f backend/logs/app.log
   ```

---

*本文档随项目进展持续更新*

