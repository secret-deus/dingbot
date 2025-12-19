# 钉钉K8s运维机器人 - 项目文档

**最后更新**: 2025-12-18

---

## 📋 核心文档

| 文档 | 说明 |
|------|------|
| **[项目状态与计划](./PROJECT_STATUS.md)** ⭐ | 项目概述、已完成功能、下一步计划 |
| **[技术架构与配置指南](./技术架构与配置指南.md)** | 系统架构详解、配置管理、部署指南 |
| **[API接口文档](./api-documentation.md)** | REST API端点参考 |

---

## 📚 专项指南

| 文档 | 说明 |
|------|------|
| [Prometheus资源分析指南](./prometheus-resource-analysis-guide.md) | K8s资源利用率分析 |
| [MCP集成指南](./mcp-integration-guide.md) | MCP协议集成详解 |
| [数据脱敏实现](./llm-data-masking-implementation-status.md) | 敏感信息脱敏机制 |

---

## 🚀 快速开始

```bash
# 1. 安装依赖
poetry install

# 2. 配置
cp backend/config.env.example backend/config.env

# 3. 启动
poetry run serve

# 4. 访问
open http://localhost:8000
```

详细说明请查看 [项目状态与计划](./PROJECT_STATUS.md)

---

## 📁 架构图

- `architecture-diagrams/arch.png` - 系统架构图
- `architecture-diagrams/LLM2MCP.png` - LLM到MCP流程图

---

## 📞 支持

- **技术问题**: 查看 [技术架构与配置指南](./技术架构与配置指南.md)
- **API问题**: 查看 [API接口文档](./api-documentation.md)
