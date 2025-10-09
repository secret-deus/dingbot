# 钉钉K8s运维机器人 - 设计系统 v2.0

## 🎨 设计理念

**现代化 · 统一 · 舒适 · 专业**

frontend-v2采用全新的设计系统，结合Glassmorphism（毛玻璃）和圆角矩形，打造现代化、专业化的运维管理界面。

---

## 📐 圆角系统

### 圆角尺寸标准

我们使用CSS变量定义统一的圆角尺寸：

```css
--radius-xs: 6px;    /* 极小圆角 - 代码片段 */
--radius-sm: 8px;    /* 小圆角 - 小标签 */
--radius-md: 12px;   /* 中等圆角 - 菜单项、按钮(小) */
--radius-lg: 16px;   /* 大圆角 - 按钮、输入框、卡片 */
--radius-xl: 20px;   /* 超大圆角 - 徽章、对话框 */
--radius-2xl: 24px;  /* 特大圆角 - 大型对话框 */
```

### 圆角应用规则

| 组件类型 | 圆角大小 | 使用场景 |
|---------|---------|---------|
| **主要交互** | 16px | 按钮、输入框、选择框、卡片 |
| **次要交互** | 12px | 菜单项、下拉项、标签页、Tree节点 |
| **微小元素** | 6-8px | 代码片段、面包屑、小标签 |
| **大型容器** | 20-24px | 对话框、抽屉、大型卡片 |

---

## 🎭 Glassmorphism（毛玻璃效果）

### 应用位置

1. **侧边栏**
   ```css
   background: rgba(30, 41, 59, 0.85);
   backdrop-filter: blur(20px);
   border-right: 1px solid rgba(255, 255, 255, 0.15);
   ```

2. **顶部栏**
   ```css
   background: rgba(255, 255, 255, 0.85);
   backdrop-filter: blur(20px);
   border-bottom: 1px solid rgba(0, 0, 0, 0.06);
   ```

3. **对话历史卡片**
   ```css
   background: rgba(255, 255, 255, 0.05);
   backdrop-filter: blur(8px);
   border: 1px solid rgba(255, 255, 255, 0.1);
   ```

### 毛玻璃设计原则

- ✅ **半透明背景**: 使用rgba颜色，alpha通道在0.05-0.95之间
- ✅ **模糊效果**: backdrop-filter: blur(8px-20px)
- ✅ **微妙边框**: 使用半透明边框区分层级
- ✅ **层次叠加**: 多层毛玻璃产生深度感

---

## 🌈 配色方案

### 主色调

```css
/* 渐变背景 */
background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c);

/* 主题色 */
--primary: #667eea;    /* 紫蓝色 */
--secondary: #764ba2;  /* 深紫色 */
--accent-1: #f093fb;   /* 粉紫色 */
--accent-2: #f5576c;   /* 珊瑚红 */
```

### 语义色

```css
/* 文本颜色 */
--text-dark: #1f2937;          /* 深色文本 */
--text-light: rgba(255, 255, 255, 0.95);  /* 浅色文本 */
--text-muted: rgba(255, 255, 255, 0.6);   /* 弱化文本 */

/* 功能色 */
--success: #10b981;   /* 成功 */
--warning: #f59e0b;   /* 警告 */
--danger: #ef4444;    /* 危险 */
--info: #3b82f6;      /* 信息 */
```

### 背景层级

```css
/* 透明度层级 */
Level 1: rgba(255, 255, 255, 0.05)  /* 最低层 */
Level 2: rgba(255, 255, 255, 0.1)   /* 悬停层 */
Level 3: rgba(255, 255, 255, 0.15)  /* 激活层 */
Level 4: rgba(255, 255, 255, 0.85)  /* 实体层 */
```

---

## 🎯 布局结构

### 主要布局区域

```
┌──────────────────────────────────────────────────┐
│  顶部导航栏 (毛玻璃 85% + 模糊 20px)              │
│  - 无圆角，贴合边缘                               │
├─────────┬────────────────────────────────────────┤
│ 侧边栏  │  主内容区                              │
│ (毛玻璃 │  - 动态渐变背景                        │
│  85%)   │  - 内容卡片带圆角                      │
│         │                                        │
│ 菜单项  │  页面内容                              │
│ 12px圆  │                                        │
│         │                                        │
└─────────┴────────────────────────────────────────┘
```

### 间距系统

```css
/* 标准间距 */
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 12px;
--spacing-lg: 16px;
--spacing-xl: 24px;
--spacing-2xl: 32px;
```

---

## 💬 聊天界面专属设计

### 对话历史列表

**设计特点**:
- 12px圆角卡片
- 毛玻璃背景 (5%透明度)
- 悬停时向右平移4px
- 激活状态带紫色高亮

```css
.chat-history-panel .el-card {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

.chat-history-panel .el-card:hover {
  transform: translateX(4px);
  background: rgba(255, 255, 255, 0.1);
}
```

### 消息气泡

#### 用户消息
- **圆角**: 16px 16px 4px 16px (右下角小圆角)
- **背景**: 紫色渐变
- **位置**: 右对齐
- **最大宽度**: 75%

```css
.message-user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px 16px 4px 16px;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);
}
```

#### AI消息
- **圆角**: 16px 16px 16px 4px (左下角小圆角)
- **背景**: 白色毛玻璃
- **位置**: 左对齐
- **最大宽度**: 85%

```css
.message-ai .message-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
```

### 输入框
- **圆角**: 16px
- **背景**: 纯白
- **边框**: 轻微阴影
- **聚焦**: 紫色光晕

```css
.chat-input-container .el-textarea__inner:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
```

---

## 🔘 按钮系统

### 按钮层级

1. **主要按钮** (Primary)
   ```css
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   border-radius: 16px;
   padding: 12px 32px;
   ```

2. **次要按钮** (Secondary)
   ```css
   border: 1px solid rgba(102, 126, 234, 0.2);
   background: rgba(102, 126, 234, 0.05);
   border-radius: 12px;
   ```

3. **文本按钮** (Text)
   ```css
   background: transparent;
   color: #667eea;
   border-radius: 8px;
   ```

### 按钮状态

```css
/* 悬停 */
:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 按下 */
:active {
  transform: translateY(0);
}

/* 禁用 */
:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## 📝 表单系统

### 输入控件统一规范

| 控件 | 圆角 | 高度 | 边框 |
|-----|------|------|------|
| Input | 16px | 40px | 1px solid rgba(0,0,0,0.08) |
| Textarea | 16px | auto | 1px solid rgba(0,0,0,0.08) |
| Select | 16px | 40px | 1px solid rgba(0,0,0,0.08) |
| DatePicker | 16px | 40px | 1px solid rgba(0,0,0,0.08) |

### 聚焦状态
```css
:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  outline: none;
}
```

---

## 📊 数据展示

### 表格设计

**特点**:
- 16px外圆角
- 表头浅紫色背景
- 悬停行高亮
- 无内部边框圆角

```css
.el-table {
  border-radius: 16px;
  overflow: hidden;
}

.el-table th {
  background: rgba(102, 126, 234, 0.05);
}

.el-table tr:hover > td {
  background: rgba(102, 126, 234, 0.02);
}
```

### 卡片设计

```css
.el-card {
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.el-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
```

---

## 🎬 动画系统

### 标准过渡

```css
/* 全局过渡曲线 */
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

### 关键动画

1. **渐变流动**
   ```css
   @keyframes gradientFlow {
     0% { background-position: 0% 50%; }
     50% { background-position: 100% 50%; }
     100% { background-position: 0% 50%; }
   }
   animation: gradientFlow 20s ease infinite;
   ```

2. **悬浮上升**
   ```css
   :hover {
     transform: translateY(-2px);
   }
   ```

3. **侧滑进入**
   ```css
   :hover {
     transform: translateX(4px);
   }
   ```

4. **脉冲呼吸**
   ```css
   @keyframes pulse {
     0%, 100% { opacity: 1; }
     50% { opacity: 0.6; }
   }
   ```

---

## 🔍 细节优化

### 代码块
```css
pre {
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.05);
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

code {
  border-radius: 6px;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 2px 6px;
}
```

### 滚动条
```css
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
```

### 标签徽章
```css
.el-tag {
  border-radius: 12px;
  padding: 4px 12px;
  border: none;
  font-weight: 500;
}

.mcp-tool-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 4px 12px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}
```

---

## 📱 响应式设计

### 断点系统

```css
/* 移动端 */
@media (max-width: 480px) {
  --radius-lg: 14px;
  --radius-xl: 18px;
  --radius-2xl: 20px;
}

/* 平板 */
@media (max-width: 768px) {
  --radius-lg: 14px;
  --radius-xl: 18px;
  
  .sidebar {
    backdrop-filter: blur(12px);
  }
}

/* 桌面 */
@media (min-width: 1200px) {
  /* 完整设计 */
}
```

---

## ✅ 设计检查清单

### 视觉一致性
- [ ] 所有按钮使用统一圆角 (16px)
- [ ] 所有输入框使用统一圆角 (16px)
- [ ] 所有卡片使用统一圆角 (20px)
- [ ] 所有对话框使用统一圆角 (24px)

### 交互反馈
- [ ] 所有可点击元素有悬停效果
- [ ] 按钮有上浮动画
- [ ] 输入框有聚焦光晕
- [ ] 菜单项有背景高亮

### 层级清晰
- [ ] 毛玻璃效果层次分明
- [ ] 阴影使用恰当
- [ ] 边框颜色统一
- [ ] 文字对比度足够

### 性能优化
- [ ] 使用CSS变量
- [ ] 动画使用transform
- [ ] 避免重绘重排
- [ ] 图片适当压缩

---

## 🎉 设计亮点总结

### ✨ 核心特色

1. **毛玻璃美学** - 现代、轻盈、有深度
2. **统一圆角** - 柔和、友好、专业
3. **渐变背景** - 动态、活力、吸引力
4. **微交互** - 流畅、自然、愉悦

### 🎯 设计目标达成

✅ **视觉统一** - 所有组件遵循同一设计语言  
✅ **布局协调** - 圆角不影响功能和布局  
✅ **交互流畅** - 所有动画过渡自然  
✅ **专业形象** - 现代化企业级UI标准  

---

## 📚 设计参考

- **iOS Human Interface Guidelines** - 圆角与毛玻璃
- **Material Design 3** - 色彩与动效
- **Glassmorphism.com** - 毛玻璃效果
- **Dribbble/Behance** - 现代UI趋势

---

**设计系统由 frontend-v2 团队精心打造** 🎨✨

**版本**: v2.0.0  
**更新日期**: 2025-09-30  
**维护者**: AI助手 & 开发团队


