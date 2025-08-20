# MCP 配置管理系统使用指南

## 系统概述

MCP (Model Context Protocol) 配置管理系统是一个支持多种通信协议的工具配置平台，能够管理和调度各种MCP服务器和工具。

## 支持的通信协议

### 1. WebSocket
- **用途**: 双向实时通信
- **适用场景**: 需要实时交互的工具，如日志监控、事件推送
- **配置示例**:
```json
{
  "name": "k8s-websocket",
  "type": "websocket",
  "host": "localhost",
  "port": 8766,
  "path": "/",
  "timeout": 30
}
```

### 2. HTTP
- **用途**: 请求/响应模式
- **适用场景**: 标准的REST API调用，如CRUD操作
- **配置示例**:
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

### 3. SSE (Server-Sent Events)
- **用途**: 服务器推送事件流
- **适用场景**: 实时监控、日志流、状态更新
- **配置示例**:
```json
{
  "name": "k8s-sse",
  "type": "sse",
  "host": "localhost",
  "port": 8766,
  "path": "/events",
  "timeout": 60
}
```

### 4. Stream HTTP
- **用途**: 流式HTTP响应
- **适用场景**: 大数据传输、流式处理、实时数据流
- **配置示例**:
```json
{
  "name": "stream-http",
  "type": "stream_http",
  "host": "localhost",
  "port": 8768,
  "path": "/stream",
  "timeout": 60
}
```

### 5. Subprocess
- **用途**: 本地子进程通信
- **适用场景**: 本地工具集成、命令行工具包装
- **配置示例**:
```json
{
  "name": "subprocess-server",
  "type": "subprocess",
  "command": "python",
  "args": ["-m", "mcp_server"],
  "cwd": "/path/to/server",
  "env": {
    "PYTHONPATH": "/path/to/server"
  }
}
```

### 6. Local
- **用途**: 本地模块直接调用
- **适用场景**: 本地文件系统操作、内存操作
- **配置示例**:
```json
{
  "name": "filesystem",
  "type": "local",
  "enabled_tools": [
    "fs-read-file",
    "fs-write-file"
  ]
}
```

## 认证支持

系统支持多种认证方式：

### Bearer Token
```json
{
  "auth_type": "bearer",
  "auth_token": "your-bearer-token"
}
```

### Basic Auth
```json
{
  "auth_type": "basic",
  "auth_headers": {
    "Authorization": "Basic base64(username:password)"
  }
}
```

### 自定义Headers
```json
{
  "auth_headers": {
    "X-API-Key": "your-api-key",
    "X-Custom-Header": "custom-value"
  }
}
```

## 配置模板

系统提供了多种预设模板：

### Kubernetes 模板
- **k8s-websocket**: WebSocket连接的K8s服务器
- **k8s-http**: HTTP API连接的K8s服务器  
- **k8s-sse**: SSE事件流的K8s监控服务器

### SSH 模板
- **ssh-jumpserver**: WebSocket连接的SSH跳板机
- **ssh-http**: HTTP API连接的SSH服务器

### 通用模板
- **stream-http**: 流式HTTP服务器
- **subprocess**: 子进程服务器
- **filesystem**: 本地文件系统服务器

## 工具路由

系统支持智能工具路由，根据工具类型自动选择最佳服务器：

```json
{
  "tool_routing": {
    "k8s-*": "k8s-websocket",
    "ssh-*": "ssh-jumpserver",
    "stream-*": "stream-http"
  }
}
```

## 连接健康检查

各协议的健康检查机制：

- **WebSocket**: 使用ping/pong机制
- **HTTP**: 定期GET /health端点
- **SSE**: 监控连接状态和事件流
- **Stream HTTP**: 检查流连接状态
- **Subprocess**: 检查进程是否存活

## 错误处理和重试

系统提供统一的错误处理和重试机制：

```json
{
  "timeout": 30,
  "retry_attempts": 3,
  "retry_delay": 1
}
```

## 使用示例

### 1. 创建WebSocket服务器
```bash
curl -X POST http://localhost:8000/api/v2/mcp-config/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-websocket-server",
    "type": "websocket",
    "host": "localhost",
    "port": 8766,
    "path": "/",
    "enabled": true
  }'
```

### 2. 创建HTTP服务器
```bash
curl -X POST http://localhost:8000/api/v2/mcp-config/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-http-server",
    "type": "http",
    "base_url": "http://localhost:8766",
    "auth_type": "bearer",
    "auth_token": "your-token",
    "enabled": true
  }'
```

### 3. 创建SSE服务器
```bash
curl -X POST http://localhost:8000/api/v2/mcp-config/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-sse-server",
    "type": "sse",
    "host": "localhost",
    "port": 8766,
    "path": "/events",
    "timeout": 60,
    "enabled": true
  }'
```

## 最佳实践

1. **协议选择**:
   - 实时双向通信使用WebSocket
   - 简单请求/响应使用HTTP
   - 服务器推送使用SSE
   - 流式数据使用Stream HTTP
   - 本地工具使用Subprocess

2. **认证安全**:
   - 使用环境变量存储敏感信息
   - 定期轮换认证令牌
   - 使用HTTPS传输敏感数据

3. **性能优化**:
   - 合理设置超时时间
   - 使用连接池复用连接
   - 启用缓存减少重复请求

4. **监控告警**:
   - 监控连接状态
   - 设置健康检查
   - 记录错误日志

## 故障排除

### 常见问题

1. **连接失败**:
   - 检查网络连通性
   - 验证端口是否开放
   - 确认认证信息正确

2. **超时错误**:
   - 增加超时时间
   - 检查服务器响应时间
   - 优化网络环境

3. **认证失败**:
   - 检查认证类型配置
   - 验证令牌有效性
   - 确认权限设置

### 调试技巧

1. 启用详细日志：
```bash
export LOG_LEVEL=DEBUG
```

2. 测试连接：
```bash
curl -X POST http://localhost:8000/api/v2/mcp-config/servers/test-connection \
  -H "Content-Type: application/json" \
  -d '{"name": "server-name"}'
```

3. 查看服务器状态：
```bash
curl http://localhost:8000/api/v2/mcp-config/servers/status
```

## 扩展开发

系统支持自定义协议扩展：

1. 实现协议适配器
2. 注册到客户端
3. 更新配置模板
4. 添加前端支持

详细的扩展开发指南请参考开发文档。 