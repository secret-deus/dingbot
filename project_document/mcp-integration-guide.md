# MCP协议集成完整指南

**最后更新**: 2025-01-21 15:30:00 +08:00
**适用版本**: v1.1.0+
**状态**: 生产就绪

---

## 📋 概述

Model Context Protocol (MCP) 是本项目的核心协议，实现了LLM与外部工具的标准化集成。本指南整合了MCP协议支持、兼容性分析、配置管理和自动同步等所有相关内容。

## 🏗️ MCP架构概览

### 系统架构
```
LLM处理器 → EnhancedMCPClient → LocalMCPRuntime → K8s/ECS Provider
    ↓              ↓                 ↓
  脱敏层       工具过滤/审计       进程内只读工具
    ↓              ↓
  恢复层       远程 MCP Adapter（扩展）
```

### 核心组件

#### 1. MCP客户端 (后端集成)
**位置**: `backend/src/mcp/`

- **EnhancedMCPClient**: 增强MCP客户端实现
- **MCPConfigManager**: MCP配置管理
- **LocalMCPRuntime**: 本地 K8s/ECS 工具注册、枚举和执行主路径
- **工具发现**: 本地 provider 枚举工具 schema；远程 MCP 作为扩展适配
- **智能路由**: 根据用户意图选择合适工具

#### 2. MCP 工具来源
**K8s 工具（进程内）**: `backend/src/k8s_mcp/`
- 25+ K8s管理工具
- Prometheus资源分析工具
- 集群监控和分析功能
- 原独立 HTTP 服务写法见 `archived/k8s-mcp-standalone/`

当前推荐配置：

```json
{
  "name": "k8s-mcp",
  "type": "local",
  "provider": "k8s",
  "implementation": "builtin",
  "enabled": true
}
```

`type=local` 表示由主 FastAPI 进程内的 `LocalMCPRuntime` 注册和执行工具，不再连接历史 SSE 端口。

**远程 MCP 扩展**:
- SSE / stdio 仍作为扩展 adapter 保留
- 不作为 K8s/ECS 默认启动链路
- 添加写操作或高危工具前必须接入只读/确认/审计策略

## 🔧 MCP配置管理

### 配置文件结构
**位置**: `config/mcp_config.json`

```json
{
  "servers": [
    {
      "name": "k8s-mcp",
      "type": "local",
      "provider": "k8s",
      "implementation": "builtin",
      "enabled": true,
      "enabled_tools": ["k8s-get-pods", "k8s-get-services"]
    },
    {
      "name": "ecs-sse-server",
      "type": "local",
      "provider": "ecs",
      "implementation": "builtin",
      "enabled": true,
      "disabled_tools": []
    }
  ],
  "tools": [
    {
      "name": "k8s-get-pods",
      "enabled": true,
      "server_name": "k8s-mcp",
      "input_schema": {"type": "object", "properties": {}},
      "category": "monitoring"
    }
  ]
}
```

### 配置API端点
- `GET /api/v2/mcp/config` - 获取完整配置
- `POST /api/v2/mcp/config` - 更新配置
- `POST /api/v2/mcp/config/import` - 导入配置
- `GET /api/v2/mcp/config/export` - 导出配置

## 🔄 自动同步机制

### 工具自动发现
```python
async def auto_sync_tools():
    """从 LocalMCPRuntime 发现和同步本地工具"""
    runtime = LocalMCPRuntime()
    tools = runtime.connect()
    await update_tools_config(tools)
```

### 配置热重载
- 监控配置文件变化
- 重新加载本地 provider 的 allow/deny 过滤
- 远程 MCP adapter 仅在显式启用时重连

## 🛠️ 支持的通信协议

| 协议类型 | 状态 | 用途 | 示例 |
|---------|------|------|------|
| **local** | ✅ 默认主路径 | K8s/ECS 本地 provider | `type=local provider=k8s` |
| **STDIO** | 扩展保留 | 外部 MCP 子进程 | `python start_mcp_server.py` |
| **SSE** | 扩展保留 | 外部远程 MCP | Server-Sent Events |

## 🔍 LLM提供商兼容性

### 工具调用支持

| 提供商 | 工具调用支持 | 解决方案 | 状态 |
|--------|-------------|----------|------|
| **OpenAI** | ✅ 原生支持 | Function Calling | 已支持 |
| **Anthropic** | ✅ 原生支持 | Tool Use | 已支持 |
| **Azure OpenAI** | ✅ 原生支持 | Function Calling | 已支持 |
| **智谱AI** | ✅ 原生支持 | Function Calling | 已支持 |
| **Ollama** | ❌ 不支持 | Prompt Engineering + 结构化输出 | ✅ 已实现 |

### Ollama本地LLM支持
- **特性**: 完全免费，无API调用费用，数据安全
- **模型**: 支持qwen、llama、codellama等开源模型
- **实现**: 通过Prompt Engineering实现"伪工具调用"
- **位置**: `backend/src/k8s_mcp/llm/ollama_adapter.py`

## 📊 工具分类和功能

### Kubernetes工具（本地只读）
**查询工具**:
- `k8s-get-pods` - Pod列表查询
- `k8s-get-deployments` - Deployment查询
- `k8s-get-services` - Service查询
- `k8s-get-nodes` - 节点信息查询
**分析工具**:
- `k8s-cluster-summary` - 集群概览
- `k8s-prometheus-resource-analysis` - 资源利用率分析 **NEW**
- `k8s-relation-query` - 资源关系查询

### 远程工具扩展
- 远程命令执行、文件传输等能力需要作为独立 adapter 接入
- 默认不进入 K8s/ECS 本地 MCP 主路径
- 写操作和高危动作必须走人工确认与审计

## 🔒 安全集成

### 数据脱敏
MCP工具调用过程中的敏感信息自动脱敏：
- **IP地址**: `192.168.1.100` → `10.0.abc1.100`
- **主机名**: `prod-server-01` → `host-def2a-01`
- **人名**: `张三` → `用户A`

### 双阶段恢复
- **阶段1**: 实时流式恢复 (用户即时反馈)
- **阶段2**: 完整响应恢复 (解决分块问题)

## 📈 监控和调试

### 统计信息
- 工具调用次数统计
- 成功率监控
- 响应时间分析
- 错误日志记录

### 调试工具
- 单个工具测试接口
- 工具调用日志
- 参数验证测试
- 连接状态检查

## 🚀 开发指南

### 添加本地 MCP Provider
1. 在 `backend/src/mcp/builtin/providers.py` 增加 provider 实现
2. 在 `LocalMCPRuntime` 中注册 provider
3. 在 `config/mcp_config.json` 中增加 `type=local` / `provider=...`
4. 补充工具 allow/deny、错误语义、超时和审计测试
5. 更新本指南和 `project_document/local-mcp-runtime.md`

### 添加新工具
```python
@tool("tool-name")
async def tool_function(param1: str, param2: int = 10) -> dict:
    """
    工具描述

    Args:
        param1: 参数1描述
        param2: 参数2描述，默认值10

    Returns:
        dict: 工具执行结果
    """
    try:
        # 工具实现逻辑
        result = await perform_operation(param1, param2)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 工具开发最佳实践
1. **清晰命名**: 使用描述性的工具名称
2. **完整文档**: 提供详细的参数和返回值说明
3. **异步支持**: 使用async/await实现异步操作
4. **错误处理**: 完善的异常处理和错误信息
5. **类型安全**: 使用类型注解和Pydantic验证

## 🔧 故障排查

### 常见问题
1. **MCP服务器连接失败**
   - 检查服务器是否正常启动
   - 验证端口是否占用
   - 确认配置文件格式正确

2. **工具调用失败**
   - 检查工具参数格式
   - 验证权限配置
   - 查看详细错误日志

3. **配置同步问题**
   - 检查文件监控状态
   - 验证配置文件权限
   - 重启配置管理服务

### 调试步骤
1. 检查服务状态: `GET /health`
2. 查看MCP配置: `GET /api/v2/mcp/config`
3. 测试工具连接: 使用单个工具测试接口
4. 查看系统日志: `logs/` 目录

## 📝 更新日志

- **v1.1.0** (2025-01-21):
  - 新增Prometheus资源分析工具
  - 整合MCP相关文档
  - 优化配置管理流程

- **v1.0.0** (2025-01-16):
  - 完整MCP协议支持
  - 多通信协议实现
  - LLM提供商兼容性
  - 自动同步机制

---

**维护者**: AI Assistant
**技术支持**: 通过钉钉机器人或项目Issue
