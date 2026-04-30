# Frontend-v2 - 钉钉K8s运维机器人前端

基于 Vue 3 + Vite + Element Plus 的现代化前端界面。

## 🎨 特性

### 核心功能
- ✅ **智能对话** - SSE流式响应，实时对话体验
- ✅ **会话管理** - 创建、切换、删除、导出、导入会话
- ✅ **工具调用** - 可视化工具执行状态和结果
- ✅ **Markdown渲染** - 支持代码高亮、数学公式
- ✅ **MCP服务器管理** - 动态启用/禁用MCP工具

### UI/UX优化
- 🎨 **现代化设计** - 圆角卡片、毛玻璃效果
- 🌊 **优雅动画** - 波浪加载动画、转圈动画
- 📱 **响应式布局** - 适配各种屏幕尺寸
- 🎯 **智能预览** - 会话历史智能截断和清理

### 技术特性
- ⚡ **Vite构建** - 快速热重载开发体验
- 📦 **按需加载** - 代码分割优化加载速度
- 🔄 **状态管理** - Pinia集中管理应用状态
- 🎯 **TypeScript友好** - 类型推断支持

## 📁 项目结构

```
frontend-v2/
├── src/
│   ├── components/        # 组件
│   │   ├── StreamChat.vue      # 聊天主界面
│   │   ├── ChatHistory.vue     # 会话历史
│   │   ├── ToolCallCard.vue    # 工具卡片
│   │   └── MarkdownRenderer.vue # Markdown渲染
│   ├── views/             # 页面视图
│   │   ├── Chat.vue            # 对话页面
│   │   ├── Dashboard.vue       # 仪表板
│   │   ├── MCPConfig.vue       # MCP配置
│   │   └── Scheduler.vue       # 定时任务
│   ├── stores/            # 状态管理
│   │   ├── chat.js             # 聊天状态
│   │   ├── auth.js             # 认证状态
│   │   └── mcp.js              # MCP状态
│   ├── router/            # 路由
│   ├── utils/             # 工具函数
│   ├── api/               # API调用
│   ├── App.vue            # 根组件
│   └── main.js            # 入口文件
├── public/                # 静态资源
├── package.json           # 依赖配置
├── vite.config.js         # Vite配置
└── README.md
```

## 🚀 开发指南

### 环境要求
- Node.js >= 16
- npm >= 7

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```
访问: http://localhost:3000

### 构建生产版本
```bash
npm run build
```

构建产物将输出到 `../backend/static/spa/` 目录，后端会自动提供这些静态文件。

### 预览生产版本
```bash
npm run preview
```

## 🔧 配置说明

### Vite配置 (vite.config.js)

#### 构建输出
```javascript
build: {
  outDir: '../backend/static/spa',  // 输出到后端静态目录
  emptyOutDir: true,                 // 清空目标目录
}
```

#### 开发代理
```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

#### 基础路径
```javascript
base: '/spa/',  // 生产环境路由前缀
```

## 🎯 核心组件说明

### StreamChat.vue
聊天主界面，包含:
- SSE流式消息处理
- 工具调用可视化
- Markdown渲染
- 加载动画

**关键功能**:
- `handleStructuredEvent()` - 处理后端结构化事件
- `filterToolCallMessages()` - 过滤工具调用文本
- 波浪加载动画 (AI思考)
- 转圈动画 (工具执行、AI打字)

### ChatHistory.vue
会话历史管理，包含:
- 会话列表显示
- 智能消息预览
- 会话操作 (删除、导出、导入)

**关键功能**:
- `getLastMessagePreview()` - 智能消息截断
- Markdown清理
- 工具调用过滤

### ToolCallCard.vue
工具调用卡片，显示:
- 工具名称和状态
- 执行动画 (转圈)
- 执行结果或错误
- 执行时长

## 🎨 样式规范

### 主题色
- 主色: `#0969da` (蓝色)
- 成功: `#28a745` (绿色)
- 错误: `#dc3545` (红色)
- 警告: `#ffc107` (黄色)

### 布局
- 侧边栏: `240px`
- 聊天区域: `flex-grow`
- 卡片圆角: `8px`
- 卡片间距: `12px`

### 动画
- 波浪动画: `@keyframes wave` - AI思考
- 转圈动画: `@keyframes spin` - 工具执行、AI打字
- 过渡: `transition: all 0.3s ease`

## 📦 依赖说明

### 核心依赖
- `vue@^3.4.0` - Vue 3框架
- `vue-router@^4.2.0` - 路由管理
- `pinia@^2.1.0` - 状态管理
- `element-plus@^2.4.0` - UI组件库
- `axios@^1.6.0` - HTTP客户端

### Markdown渲染
- `marked@^16.3.0` - Markdown解析
- `highlight.js@^11.11.1` - 代码高亮
- `katex@^0.16.22` - 数学公式

## 🔄 与后端集成

### API端点
- `POST /api/v2/chat/stream` - 流式对话
- `GET /api/v2/chat/sessions` - 获取会话列表
- `POST /api/v2/chat/sessions` - 创建会话
- `GET /api/v2/mcp/servers` - 获取MCP服务器列表

### SSE消息格式

#### 文本消息
```
data: 这是普通文本消息\n\n
```

#### 结构化事件
```
data: {"type": "tool_call_start", "tool_call": {...}}\n\n
data: {"type": "tool_call_update", "tool_call": {...}}\n\n
data: {"type": "error", "message": "..."}\n\n
```

## 🐛 调试技巧

### 查看SSE消息
打开浏览器控制台，查看 `handleSSEMessage` 日志:
```javascript
console.log('收到SSE消息:', data)
```

### 查看状态变化
使用Vue Devtools查看Pinia store状态:
- `chatStore` - 聊天状态
- `mcpStore` - MCP配置

### 常见问题

**Q: 工具执行动画不显示？**
A: 检查后端是否发送了 `tool_call_start` 和 `tool_call_update` 事件。

**Q: 会话历史显示工具调用信息？**
A: 确保 `getLastMessagePreview()` 包含了工具调用过滤逻辑。

**Q: 构建后页面空白？**
A: 检查 `vite.config.js` 中的 `base` 路径是否为 `/spa/`。

## 📝 开发规范

### 组件命名
- 使用 PascalCase: `StreamChat.vue`
- 导出名称与文件名一致

### 状态管理
- 使用 Pinia stores 管理全局状态
- 避免在组件中直接操作 store

### API调用
- 统一在 `src/api/` 中定义
- 使用 axios 实例

### 样式
- 优先使用 Element Plus 组件
- 自定义样式使用 scoped CSS
- 使用 CSS变量管理主题色

## 🚀 部署

### 生产构建
```bash
npm run build
```

构建产物会自动输出到 `../backend/static/spa/`，后端会提供这些静态文件。

### 访问地址
- 生产环境: http://localhost:8000
- 直接访问: http://localhost:8000/spa/

### 回滚旧版本
如需回滚到旧版前端:
```bash
cd /path/to/ding-robot
rm -rf backend/static/spa
mv backend/static/spa.old backend/static/spa
```

## 📚 更多文档

- [项目总览](../README.md)
- [后端API文档](../backend/README.md)
- [迁移说明](../FRONTEND_MIGRATION.md)
- [开发指南](../project_document/development-deployment-guide.md)

## 🎉 版本历史

### v2.0.0 (2025-11-24)
- ✅ 完全替代旧版 frontend
- ✅ 优化工具执行动画
- ✅ 改进会话历史预览
- ✅ 增强 Markdown 渲染
- ✅ 统一构建流程

---

**💡 提示**: 这是项目的主要前端，已集成到后端构建流程中。开发时可以单独运行前端服务以获得热重载体验。
