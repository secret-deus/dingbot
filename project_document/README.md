# 钉钉K8s运维机器人 - 项目文档导航

**最后更新**: 2025-01-16 18:00:00 +08:00  
**项目版本**: v1.0.0  
**项目状态**: 95%完成，生产就绪 🚀

---

## 📋 核心文档 (必读)

### 🎯 项目总览
- **[项目总览与最新状态](./项目总览与最新状态.md)** ⭐ **最重要文档**
  - 完整项目概述和架构
  - 最新功能完成状态
  - 技术亮点和部署指南

### 🔧 技术文档  
- **[技术架构与配置指南](./技术架构与配置指南.md)** 🏗️ **开发必读**
  - 详细系统架构说明
  - 配置管理完整指南
  - 开发环境搭建和部署

### 📚 专项指南
- **[LLM配置迁移指南](./llm-config-migration-guide.md)** 🔄 **配置管理**
  - 环境变量到文件配置迁移
  - 自动化迁移脚本使用
  - 配置备份和恢复

- **[LLM数据脱敏实现状态](./llm-data-masking-implementation-status.md)** 🔒 **安全功能**
  - K8s敏感信息脱敏与恢复
  - 双阶段恢复机制详解
  - 脱敏效果验证

- **[MCP自动同步指南](./mcp-auto-sync-guide.md)** 🔗 **MCP集成**
  - MCP工具自动发现和同步
  - 配置自动更新机制

### 🚀 实用工具
- **[API接口文档](./api-documentation.md)** 📖 **API参考**
  - 完整API端点说明
  - 请求响应格式
  - 认证和错误处理

---

## 🗂️ 文档分类

### 📊 已完成功能
- ✅ **配置管理系统** - 统一配置路径，热重载，自动迁移
- ✅ **数据脱敏系统** - IP/主机名/人名脱敏，双阶段恢复
- ✅ **会话持久化** - 页面刷新后保持对话历史
- ✅ **LLM多提供商支持** - OpenAI、Azure、智谱等
- ✅ **MCP协议集成** - K8s和SSH工具集成

### 🔄 历史参考文档
以下文档包含历史信息，主要用于参考：
- `mcp-protocol-support.md` - MCP协议支持详情
- `mcp-compatibility-analysis.md` - MCP兼容性分析
- `mcp-config-guide.md` - MCP配置向导
- `secret.md` - 保密信息和配置

---

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
poetry install
cd frontend && npm install
```

### 2. 配置文件
```bash
# 复制配置模板
cp backend/config.env.example backend/config.env
```

### 3. 启动服务
```bash
# 启动后端
poetry run python backend/main.py

# 启动前端 (新终端)
cd frontend && npm run dev

# 启动MCP服务器 (新终端)
poetry run python k8s-mcp/start_k8s_mcp_http_server.py
```

### 4. 访问应用
- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 📞 支持与反馈

- **技术问题**: 查看 [技术架构与配置指南](./技术架构与配置指南.md) 的故障排除部分
- **配置问题**: 参考 [LLM配置迁移指南](./llm-config-migration-guide.md)
- **功能建议**: 通过钉钉机器人反馈

---

## 📝 文档维护

本文档库会随着项目功能的完善持续更新。主要更新节点：
- ✅ v1.0.0 - 完整功能发布 (当前)
- 🔄 v1.1.0 - 性能优化和监控系统
- 🔄 v1.2.0 - 多集群支持和权限管理

**文档贡献者**: AI Assistant  
**最新更新**: 2025-01-16 18:00:00 +08:00 