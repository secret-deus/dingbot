# Frontend Refactor Notes

更新时间：2026-04-29

## 本次前端迁移

- `/dashboard` 已迁移为深色运维指挥台，主布局包含 Command Center、Tool Trace、Live Context、Topology、Risk Radar、Incident Timeline 和 Automation Queue。
- 全局壳层左侧导航改为紧凑模式，`/dashboard` 不再显示旧白色顶栏，顶部环境/模式状态由指挥台自身承载。
- `/chat` 页面和 `StreamChat` 协议解析未改动，Dashboard 的输入区只作为轻量入口，会跳转到 `/chat` 继续完整对话。

## 后端接口依赖

前端现在通过 `api.ops.getOverview()` 请求：

```text
GET /api/v2/ops/overview
```

响应必须使用统一 envelope：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

`frontend-v2/src/api/client.js` 中的 `unwrapApiResponse` 会严格检查 `success` 字段：

- `success === true`：返回 `{ data, meta }`
- `success !== true`：抛出 `ApiEnvelopeError`
- 缺少标准 envelope：抛出 `ApiEnvelopeError`

## 建议 data 字段

当前 Dashboard 会优先读取以下字段；字段缺失时使用明确标注的本地 fallback 数据。

```json
{
  "summary": "prod 环境摘要",
  "environment": "prod-cn-hz",
  "environments": ["prod-cn-hz", "prod-cn-bj", "staging"],
  "mode": "只读取证 / 审计开启",
  "healthLevel": "warning",
  "contextNote": "最近 15 分钟摘要",
  "metrics": [],
  "messages": [],
  "toolTraces": [],
  "topology": { "nodes": [], "edges": [] },
  "risks": [],
  "timeline": [],
  "automationQueue": []
}
```

兼容别名：

- `currentEnvironment` -> `environment`
- `health_level` -> `healthLevel`
- `context_note` -> `contextNote`
- `commandMessages` -> `messages`
- `tool_traces` -> `toolTraces`
- `incidentTimeline` -> `timeline`
- `automation_queue` -> `automationQueue`

## Fallback 行为

后端未启动、接口 404、非标准 envelope 或 `success !== true` 时，Dashboard 会：

- 显示顶部黄色提示条，说明当前为本地 fallback 数据
- 保持页面可用，避免阻塞前端联调
- 不弹出全局错误 toast，避免后端接口未合并时干扰体验
