# MCP 通信协议支持总结

## 概述

钉钉K8s运维机器人的MCP系统现已支持6种主要通信协议，提供了完整的MCP服务器连接和工具调用能力。同时实现了LLM驱动的智能化Kubernetes配置生成，支持自然语言到YAML的转换。

## LLM集成方案

### Ollama本地LLM支持
- **状态**: ✅ 已实现
- **用途**: 本地化LLM推理，无需外部API
- **特性**:
  - 完全免费，无API调用费用
  - 数据安全，完全本地处理
  - 支持多种开源模型（qwen、llama、codellama等）
  - 通过Prompt Engineering实现"伪工具调用"
  
### LLM驱动的工具
- `k8s-llm-generate-deployment` - 自然语言生成Deployment YAML
- `k8s-generate-deployment-yaml` - 结构化参数生成YAML
- `k8s-create-deployment` - 部署验证和应用

### LLM提供商兼容性
| 提供商 | 工具调用支持 | 解决方案 | 状态 |
|--------|-------------|----------|------|
| OpenAI | ✅ 原生支持 | Function Calling | 已支持 |
| Anthropic | ✅ 原生支持 | Tool Use | 已支持 |
| Ollama | ❌ 不支持 | Prompt Engineering + 结构化输出 | ✅ 已实现 |
| 其他本地LLM | ❌ 不支持 | 自定义协议 | 🔄 可扩展 |

## 支持的协议列表

### 1. WebSocket 协议
- **状态**: ✅ 完全支持
- **用途**: 双向实时通信
- **实现**: 基于 `websockets` 库
- **特性**:
  - 实时双向通信
  - 心跳检测 (ping/pong)
  - 自动重连机制
  - 支持自定义认证头

**配置示例**:
```json
{
  "name": "k8s-websocket",
  "type": "websocket",
  "host": "localhost",
  "port": 8766,
  "path": "/",
  "timeout": 30,
  "auth_headers": {
    "Authorization": "Bearer token"
  }
}
```

### 2. HTTP 协议
- **状态**: ✅ 完全支持
- **用途**: 标准REST API调用
- **实现**: 基于 `aiohttp` 库
- **特性**:
  - RESTful API调用
  - 支持多种认证方式
  - 连接池复用
  - 健康检查端点

**配置示例**:
```json
{
  "name": "k8s-http",
  "type": "http",
  "base_url": "http://localhost:8766",
  "timeout": 30,
  "auth_type": "bearer",
  "auth_token": "your-token"
}
```

### 3. SSE (Server-Sent Events) 协议
- **状态**: ✅ 新增支持
- **用途**: 服务器推送事件流
- **实现**: 基于 `aiohttp` 流式处理
- **特性**:
  - 单向服务器推送
  - 事件流处理
  - 自动重连
  - 支持事件过滤

**配置示例**:
```json
{
  "name": "k8s-sse",
  "type": "sse",
  "host": "localhost",
  "port": 8766,
  "path": "/events",
  "timeout": 60,
  "auth_headers": {
    "Authorization": "Bearer token"
  }
}
```

### 4. Stream HTTP 协议
- **状态**: ✅ 新增支持
- **用途**: 流式HTTP响应
- **实现**: 基于 `aiohttp` 流式处理
- **特性**:
  - 流式数据传输
  - 大数据处理
  - 实时数据流
  - 支持分块传输

**配置示例**:
```json
{
  "name": "stream-http",
  "type": "stream_http",
  "host": "localhost",
  "port": 8768,
  "path": "/stream",
  "timeout": 60,
  "auth_type": "bearer",
  "auth_token": "your-token"
}
```

### 5. Subprocess 协议
- **状态**: ✅ 完全支持
- **用途**: 本地子进程通信
- **实现**: 基于 `asyncio.subprocess`
- **特性**:
  - 本地进程管理
  - 环境变量配置
  - 进程生命周期管理
  - 标准输入输出处理

**配置示例**:
```json
{
  "name": "subprocess-server",
  "type": "subprocess",
  "command": "python",
  "args": ["-m", "mcp_server"],
  "cwd": "/path/to/server",
  "env": {
    "PYTHONPATH": "/path/to/server",
    "MCP_SERVER_PORT": "8769"
  }
}
```

### 6. Local 协议
- **状态**: ✅ 完全支持
- **用途**: 本地模块直接调用
- **实现**: 直接模块导入
- **特性**:
  - 零延迟调用
  - 本地文件系统操作
  - 内存共享
  - 同步/异步支持

**配置示例**:
```json
{
  "name": "filesystem",
  "type": "local",
  "enabled_tools": [
    "fs-read-file",
    "fs-write-file",
    "fs-list-directory"
  ]
}
```

## 协议选择指南

### 实时性需求
- **高实时性**: WebSocket, SSE
- **中等实时性**: HTTP, Stream HTTP
- **低实时性**: Subprocess, Local

### 数据传输量
- **大数据量**: Stream HTTP, Subprocess
- **中等数据量**: HTTP, WebSocket
- **小数据量**: SSE, Local

### 部署方式
- **远程服务**: WebSocket, HTTP, SSE, Stream HTTP
- **本地服务**: Subprocess, Local

### 复杂度
- **简单**: HTTP, Local
- **中等**: WebSocket, SSE
- **复杂**: Stream HTTP, Subprocess

## 认证支持

### 支持的认证类型
1. **Bearer Token**: 所有HTTP类协议
2. **Basic Auth**: HTTP, SSE, Stream HTTP
3. **自定义Headers**: 所有协议
4. **环境变量**: Subprocess

### 认证配置示例
```json
{
  "auth_type": "bearer",
  "auth_token": "${MCP_AUTH_TOKEN}",
  "auth_headers": {
    "X-API-Key": "${API_KEY}",
    "X-Client-ID": "dingtalk-k8s-bot"
  }
}
```

## 错误处理和重试

### 统一错误处理
- 连接超时处理
- 认证失败处理
- 网络异常处理
- 协议错误处理

### 重试机制
```json
{
  "retry_attempts": 3,
  "retry_delay": 1,
  "timeout": 30
}
```

## 健康检查

### 各协议的健康检查方式
- **WebSocket**: ping/pong 心跳
- **HTTP**: GET /health 端点
- **SSE**: 连接状态监控
- **Stream HTTP**: 流连接状态
- **Subprocess**: 进程存活检查
- **Local**: 模块可用性检查

## 性能优化

### 连接池管理
- HTTP连接复用
- WebSocket连接保持
- 资源自动清理

### 缓存机制
- 工具发现结果缓存
- 认证令牌缓存
- 配置缓存

## 监控和日志

### 监控指标
- 连接状态
- 请求响应时间
- 错误率
- 吞吐量

### 日志记录
- 连接建立/断开
- 工具调用记录
- 错误详情
- 性能指标

## 配置模板

系统提供了针对不同协议的预设模板：

### Kubernetes 相关
- `k8s-websocket`: WebSocket连接
- `k8s-http`: HTTP API连接
- `k8s-sse`: SSE事件监控

### SSH 相关
- `ssh-jumpserver`: WebSocket连接
- `ssh-http`: HTTP API连接

### 通用模板
- `stream-http`: 流式HTTP服务
- `subprocess`: 子进程服务
- `filesystem`: 本地文件系统

## 扩展开发

### 添加新协议支持
1. 在 `MCPServerConfig` 中添加新类型
2. 在 `MCPServerConnection` 中实现连接逻辑
3. 添加工具发现和调用方法
4. 更新前端配置界面
5. 添加配置模板

### 协议适配器接口
```python
class MCPProtocolAdapter:
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def discover_tools(self) -> List[MCPTool]
    async def call_tool(self, name: str, params: dict) -> Any
    async def health_check(self) -> bool
```

## 总结

钉钉K8s运维机器人的MCP系统现已支持6种主要通信协议，提供了完整的MCP服务器连接和工具调用能力。每种协议都有其特定的使用场景和优势，用户可以根据实际需求选择合适的协议。

系统设计考虑了易用性、可扩展性和性能，提供了统一的配置管理、错误处理、监控和日志记录功能。通过丰富的配置模板和直观的Web界面，用户可以轻松管理各种MCP服务器和工具。

未来可以根据需要继续扩展新的通信协议，如gRPC、MQTT等，以满足更多样化的使用场景。 