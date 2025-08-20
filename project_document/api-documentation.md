# 钉钉K8s运维机器人 API 文档 (核心功能)

## 📄 文档信息

- **API版本**: v2.0 (核心功能)
- **文档更新**: 2025年01月15日
- **服务地址**: `http://localhost:8000`
- **项目重点**: LLM对话 + MCP工具集成

## 🎯 核心API概览

专注于两大核心功能：
1. **LLM流式对话** - 与AI进行实时对话
2. **MCP工具集成** - 调用K8s/SSH等运维工具

### 🏗️ 基础信息

**服务器配置**
- **基础URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **字符编码**: `UTF-8`
- **流式协议**: Server-Sent Events (SSE)

## 📋 核心API端点

### 🚀 系统状态API

| 方法 | 端点 | 描述 |
|------|------|------|
| `GET` | `/api/v2/status` | 系统状态检查 |
| `GET` | `/api/v2/health` | 健康检查 |
| `GET` | `/api/v2/tools` | 获取MCP工具列表 |

### 💬 LLM对话API

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v2/chat/stream` | 流式LLM对话 (SSE) |

---

## 🔧 详细API说明

### 1. 系统状态检查

**GET /api/v2/status**

```bash
curl -X GET "http://localhost:8000/api/v2/status"
```

**响应**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "components": {
    "llm": "connected",
    "mcp_tools": "active",
    "database": "connected"
  }
}
```

### 2. 获取MCP工具列表

**GET /api/v2/tools**

```bash
curl -X GET "http://localhost:8000/api/v2/tools"
```

**响应**:
```json
{
  "tools": [
    {
      "name": "kubernetes-client",
      "description": "K8s集群操作工具",
      "status": "active",
      "capabilities": ["pods", "deployments", "services"]
    },
    {
      "name": "ssh-jumpserver",
      "description": "SSH跳板机连接工具",
      "status": "active", 
      "capabilities": ["connect", "execute", "transfer"]
    }
  ]
}
```

### 3. 流式LLM对话 (核心功能)

**POST /api/v2/chat/stream**

**请求体**:
```json
{
  "message": "帮我查看pod状态",
  "stream": true,
  "tools_enabled": true
}
```

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v2/chat/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "帮我查看pod状态",
    "stream": true,
    "tools_enabled": true
  }'
```

**SSE响应流**:
```
data: {"type": "message_start", "content": ""}

data: {"type": "content_delta", "content": "我来帮你查看"}

data: {"type": "tool_use", "tool": "kubernetes-client", "action": "list_pods", "status": "running"}

data: {"type": "tool_result", "tool": "kubernetes-client", "result": {"pods": [...]}}

data: {"type": "content_delta", "content": "查看到以下pod..."}

data: {"type": "message_end"}
```

### 4. SSE事件类型说明

| 事件类型 | 描述 | 数据格式 |
|---------|------|---------|
| `message_start` | 消息开始 | `{"type": "message_start", "content": ""}` |
| `content_delta` | 流式文本内容 | `{"type": "content_delta", "content": "文本"}` |
| `tool_use` | 工具调用开始 | `{"type": "tool_use", "tool": "工具名", "action": "操作", "status": "running"}` |
| `tool_result` | 工具调用结果 | `{"type": "tool_result", "tool": "工具名", "result": {...}}` |
| `message_end` | 消息结束 | `{"type": "message_end"}` |
| `error` | 错误信息 | `{"type": "error", "error": "错误描述"}` |

## 🛠️ MCP工具说明

### K8s工具 (kubernetes-client)

**支持操作**:
- `list_pods` - 列出Pod
- `get_pod_logs` - 获取Pod日志
- `describe_pod` - 描述Pod详情
- `scale_deployment` - 扩缩容部署

### SSH工具 (ssh-jumpserver)

**支持操作**:
- `connect` - 建立SSH连接
- `execute_command` - 执行命令
- `transfer_file` - 文件传输
- `disconnect` - 断开连接

## 🔗 前端集成

### Vue3组件集成示例

```javascript
// 流式聊天组件
const eventSource = new EventSource('/api/v2/chat/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'content_delta':
      // 更新聊天内容
      updateChatContent(data.content);
      break;
    case 'tool_use':
      // 显示工具调用状态
      showToolStatus(data.tool, data.action);
      break;
    case 'tool_result':
      // 显示工具结果
      showToolResult(data.tool, data.result);
      break;
  }
};
```

## 📈 性能指标

- **流式响应延迟**: < 100ms
- **工具调用延迟**: < 2s
- **并发连接数**: 50+
- **消息吞吐量**: 1000+/min

## 🔧 错误处理

### 常见错误码

| 状态码 | 描述 | 解决方案 |
|--------|------|---------|
| `400` | 请求参数错误 | 检查请求体格式 |
| `500` | 服务器内部错误 | 检查服务状态 |
| `503` | 服务不可用 | 等待服务恢复 |

### 错误响应格式

```json
{
  "error": "错误描述",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-15T10:30:00Z",
  "details": {
    "component": "llm|mcp|system",
    "message": "详细错误信息"
  }
}
```

## 🚀 部署说明

### 开发环境
```bash
# 启动后端
cd python_backend
python main.py

# 启动前端
cd frontend
npm run dev
```

### 生产环境
```bash
# 前端独立部署
cd frontend
npm run build
# 部署dist/到Nginx

# 后端独立部署
cd backend
python main.py
```

**服务地址**:
- 前端: http://localhost:3000 (开发) / Nginx部署地址 (生产)
- 后端: http://localhost:8000 (开发) / 后端部署地址 (生产)

---

## 📝 更新日志

- **v2.0.0** (2025-01-15): 核心功能聚焦版本
  - 专注LLM对话和MCP工具集成
  - 简化API结构
  - 优化流式响应性能 