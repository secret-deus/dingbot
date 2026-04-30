# 后端 API 设计标准

更新时间：2026-04-29

## 适用范围

本标准适用于新增的正式后端接口，尤其是 `/api/v2/**` 下供前端工作台直接消费的接口。历史兼容接口可以逐步迁移，但新增接口必须遵循本标准。

## 统一响应格式

成功响应统一使用 envelope：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "6f0d1d4e7e9f4e5b8f3a2f9e5b6c1d2a",
    "timestamp": 1777392000.123
  }
}
```

失败响应统一使用：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "资源不存在",
    "details": {}
  },
  "meta": {
    "request_id": "6f0d1d4e7e9f4e5b8f3a2f9e5b6c1d2a",
    "timestamp": 1777392000.123
  }
}
```

`request_id` 优先使用请求头 `X-Request-ID`，没有时由后端生成。响应里的 `timestamp` 使用 Unix 秒级浮点时间。

## 分页和元信息

列表接口的 `data` 放业务数组或对象，分页信息放 `meta.pagination`：

```json
{
  "data": {
    "items": []
  },
  "meta": {
    "request_id": "...",
    "timestamp": 1777392000.123,
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "has_next": true
    }
  }
}
```

非分页但需要补充来源、只读状态、兼容性说明时，放在 `meta`，不要混入业务字段。

## 命名风格

- URL 使用小写 kebab-case，例如 `/api/v2/ops/overview`。
- JSON 字段使用 snake_case。
- 布尔字段使用明确语义，例如 `read_only`、`enabled`、`has_next`。
- 枚举值使用小写 snake_case，例如 `degraded`、`fallback_no_runtime`。

## 错误码

错误码使用大写 snake case：

- `INVALID_REQUEST`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `RESOURCE_NOT_FOUND`
- `RUNTIME_UNAVAILABLE`
- `UPSTREAM_ERROR`
- `INTERNAL_ERROR`

HTTP 状态码表达协议层结果，`error.code` 表达业务可处理原因。

## 只读和变更接口边界

- `GET` 接口必须只读，不写配置、不触发工具变更、不启动长任务。
- `POST` 可用于命令式动作，例如 refresh、run、validate。
- `PUT/PATCH` 用于更新完整或部分配置。
- `DELETE` 用于删除资源。
- 变更接口需要在响应 `meta` 中返回 `request_id`，并在日志中使用脱敏后的参数。

## 安全和脱敏

日志、响应、调试接口不得输出完整敏感字段。至少以下字段必须脱敏：

- `api_key`
- `token`
- `secret`
- `webhook`
- `sessionWebhook`
- `Authorization`
- `auth_token`
- `access_key_secret`

新增日志应调用 `src.security.redaction.redact()` 或 `redact_for_log()`。

## 当前正式示例

`GET /api/v2/ops/overview` 是 Phase 1 新增的只读聚合接口，返回统一 envelope，并通过 `meta.read_only=true` 标记不会产生后端变更。

该接口同时返回 `data.mcp_runtime` / `data.mcpRuntime`，用于前端展示本地 MCP runtime 状态。该对象必须保持只读，只表达 `transport`、`status`、`tool_count`、`providers` 和 `remote_connections` 等运行时摘要，不返回敏感配置。
