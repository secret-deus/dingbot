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
LLM处理器 → MCP客户端 → MCP服务器集群 → 外部系统
    ↓           ↓            ↓
  脱敏层    工具发现      K8s/SSH工具
    ↓           ↓            ↓
  恢复层    智能路由      Prometheus
```

### 核心组件

#### 1. MCP客户端 (后端集成)
**位置**: `backend/src/mcp/`

- **EnhancedMCPClient**: 增强MCP客户端实现
- **MCPConfigManager**: MCP配置管理
- **工具发现**: 自动扫描和注册MCP工具
- **智能路由**: 根据用户意图选择合适工具

#### 2. MCP服务器集群
**K8s MCP服务器**: `k8s-mcp/`
- 25+ K8s管理工具
- Prometheus资源分析工具
- 集群监控和分析功能

**SSH MCP服务器**: `ssh-jumpserver-mcp/`
- 远程命令执行
- 文件传输操作
- 系统资源监控

## 🔧 MCP配置管理

### 配置文件结构
**位置**: `config/mcp_config.json`

```json
{
  "servers": {
    "k8s-server": {
      "enabled": true,
      "connection": {
        "type": "http",
        "url": "http://localhost:8001/mcp"
      }
    },
    "ssh-server": {
      "enabled": true,
      "connection": {
        "type": "stdio",
        "command": "python",
        "args": ["ssh-jumpserver-mcp/start_mcp_server.py"]
      }
    }
  },
  "tools": {
    "k8s-get-pods": {
      "enabled": true,
      "server_name": "k8s-server",
      "category": "kubernetes"
    },
    "k8s-prometheus-resource-analysis": {
      "enabled": true,
      "server_name": "k8s-server",
      "category": "monitoring"
    }
  }
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
    """自动发现和同步MCP工具"""
    for server_name, server_config in mcp_servers.items():
        if server_config.get("enabled"):
            # 连接MCP服务器
            tools = await discover_tools(server_config)
            # 更新工具配置
            await update_tools_config(tools)
            # 注册到工具注册表
            await register_tools(tools)
```

### 配置热重载
- 监控配置文件变化
- 自动重新加载MCP连接
- 无缝更新工具列表

## 🛠️ 支持的通信协议

| 协议类型 | 状态 | 用途 | 示例 |
|---------|------|------|------|
| **HTTP** | ✅ 已支持 | K8s MCP服务器 | `http://localhost:8001/mcp` |
| **STDIO** | ✅ 已支持 | SSH MCP服务器 | `python start_mcp_server.py` |
| **WebSocket** | ✅ 已支持 | 实时通信 | `ws://localhost:8001/ws` |
| **SSE** | ✅ 已支持 | 流式响应 | Server-Sent Events |
| **Unix Socket** | ✅ 已支持 | 本地进程通信 | `/tmp/mcp.sock` |
| **TCP Socket** | ✅ 已支持 | 网络通信 | `tcp://localhost:8001` |

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
- **位置**: `k8s-mcp/src/k8s_mcp/llm/ollama_adapter.py`

## 📊 工具分类和功能

### Kubernetes工具 (25+)
**查询工具**:
- `k8s-get-pods` - Pod列表查询
- `k8s-get-deployments` - Deployment查询
- `k8s-get-services` - Service查询
- `k8s-get-nodes` - 节点信息查询

**操作工具**:
- `k8s-create-deployment` - 创建Deployment
- `k8s-scale-deployment` - 扩缩容Deployment
- `k8s-restart-deployment` - 重启Deployment

**分析工具**:
- `k8s-cluster-summary` - 集群概览
- `k8s-prometheus-resource-analysis` - 资源利用率分析 **NEW**
- `k8s-relation-query` - 资源关系查询

### SSH工具集
- 远程命令执行
- 文件传输操作
- 系统资源监控
- 多跳板机管理

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

### 添加新MCP服务器
1. 创建服务器目录结构
2. 实现MCP协议处理
3. 开发具体工具功能
4. 配置服务器连接信息
5. 测试和文档更新

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
