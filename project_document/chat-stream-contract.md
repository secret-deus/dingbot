# Chat Stream Contract

更新时间：2026-04-29

## 目标

聊天流式协议必须成为后端和前端的稳定契约。后端只输出事件，前端只解析事件，不再依赖组件内部的临时字符串约定。

## 传输格式

HTTP 端点：

```text
POST /api/v2/chat/stream
```

响应使用 `text/event-stream` 兼容格式。每个事件以一行 `data: <json>` 表示，空行结束事件：

```text
data: {"type":"message_delta","content":"正在查询"}

data: {"type":"final","content":"查询完成"}

```

## 事件类型

### message_delta

LLM 文本增量。

```json
{
  "type": "message_delta",
  "content": "文本片段"
}
```

### tool_call_start

工具开始执行。

```json
{
  "type": "tool_call_start",
  "id": "call_001",
  "tool": "k8s-get-pods",
  "arguments": {
    "namespace": "default"
  }
}
```

### tool_call_progress

工具执行过程更新，可选。

```json
{
  "type": "tool_call_progress",
  "id": "call_001",
  "content": "正在读取 Pod 列表"
}
```

### tool_call_result

工具执行完成。

```json
{
  "type": "tool_call_result",
  "id": "call_001",
  "tool": "k8s-get-pods",
  "success": true,
  "result": {
    "summary": "共 12 个 Pod"
  }
}
```

### error

可恢复或不可恢复错误。

```json
{
  "type": "error",
  "code": "TOOL_EXECUTION_FAILED",
  "message": "工具执行失败",
  "recoverable": true
}
```

### final

一次回复结束。

```json
{
  "type": "final",
  "content": "最终回复",
  "tool_call_count": 1
}
```

## 前端解析规则

- 只解析 `data:` 开头的行。
- `data:` 后允许无空格或一个空格。
- 每条 `data` 必须是 JSON；旧的纯文本 chunk 在 Phase 1 期间由兼容层包装为 `message_delta`。
- 工具事件必须使用后端提供的 `id` 做状态关联，不允许通过工具名和消息内容猜测匹配。
- UI 组件不得直接处理 ReadableStream，统一通过 `shared/stream`。

## 后端编码规则

- API 层只负责把事件编码为 SSE 文本。
- use case 层产出结构化事件对象。
- tool runtime 层负责生成稳定 tool call id。
- 所有错误都要进入 `error` 事件，不直接拼接到自然语言文本里。
