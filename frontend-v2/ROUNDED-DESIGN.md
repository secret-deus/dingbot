# 圆角设计系统

## 🎨 圆角规范

frontend-v2已全面采用圆角矩形设计，提升现代感和视觉舒适度。

---

## 📐 圆角尺寸标准

### 主要布局

| 元素 | 圆角大小 | 说明 |
|------|---------|------|
| 侧边栏 | 24px | 右侧圆角 |
| 顶部栏 | 24px | 下方圆角 |
| Logo容器 | 24px | 上方圆角 |
| 主内容区 | 24px | 左上圆角 |

### 组件级别

| 组件类型 | 圆角大小 | 示例 |
|---------|---------|------|
| **大型容器** | 24px | Card、Dialog、Table |
| **中型控件** | 16px | Button、Input、Select |
| **小型元素** | 12px | Tag、Menu Item、Dropdown Item |
| **微型装饰** | 8px | Breadcrumb、Code |
| **圆形元素** | 50% | Avatar、Switch、Radio |

---

## 🎯 具体应用

### 1. 按钮系统

```css
/* 标准按钮 */
.el-button { border-radius: 16px; }

/* 小按钮 */
.el-button--small { border-radius: 12px; }

/* 大按钮 */
.el-button--large { border-radius: 20px; }
```

**视觉效果**: 柔和、友好、易点击

### 2. 输入控件

```css
/* 输入框 */
.el-input__wrapper { border-radius: 16px; }

/* 文本域 */
.el-textarea__inner { border-radius: 16px; }

/* 选择框 */
.el-select .el-input__wrapper { border-radius: 16px; }
```

**视觉效果**: 统一、整洁

### 3. 卡片容器

```css
/* 卡片 */
.el-card { border-radius: 24px; }

/* 对话框 */
.el-dialog { border-radius: 24px; }

/* 表格 */
.el-table { border-radius: 24px; }
```

**视觉效果**: 大气、现代

### 4. 标签徽章

```css
/* 标签 */
.el-tag { border-radius: 16px; }

/* 徽章 */
.el-badge__content { border-radius: 20px; }

/* 消息提示 */
.el-message { border-radius: 20px; }
```

**视觉效果**: 轻盈、醒目

### 5. 菜单导航

```css
/* 菜单项 */
.el-menu-item { 
  border-radius: 12px; 
  margin: 4px 8px;
}

/* 下拉菜单 */
.el-dropdown-menu { border-radius: 16px; }

/* 下拉项 */
.el-dropdown-menu__item { 
  border-radius: 12px;
  margin: 4px 0;
}
```

**视觉效果**: 清晰、易用

---

## 🎨 圆角层级

### 超大圆角 (32px+)
- 仅用于特殊装饰
- 不建议常规使用

### 大圆角 (24px)
- 主要布局容器
- 卡片、对话框
- 表格容器

### 中圆角 (16-20px)
- 按钮、输入框
- 标签、徽章
- 选择框、下拉菜单

### 小圆角 (12px)
- 菜单项
- 列表项
- 小型标签
- 侧边栏Logo

### 微圆角 (8px)
- 面包屑
- 代码块
- 小型装饰

### 圆形 (50%)
- 头像
- 开关按钮
- 单选框
- 状态指示器

---

## 💡 设计原则

### 1. 统一性
- 同类元素使用相同圆角大小
- 维持视觉一致性
- 建立用户认知

### 2. 层次感
- 大元素用大圆角
- 小元素用小圆角
- 通过圆角体现重要性

### 3. 协调性
- 父子元素圆角协调
- 避免圆角冲突
- 保持整体和谐

### 4. 功能性
- 按钮需要明显可点击
- 输入框需要清晰边界
- 容器需要明确范围

---

## 🛠️ 自定义工具类

### 快速应用圆角

```html
<!-- 小圆角 -->
<div class="rounded-sm">8px圆角</div>

<!-- 标准圆角 -->
<div class="rounded">12px圆角</div>

<!-- 中等圆角 -->
<div class="rounded-md">16px圆角</div>

<!-- 大圆角 -->
<div class="rounded-lg">20px圆角</div>

<!-- 超大圆角 -->
<div class="rounded-xl">24px圆角</div>

<!-- 特大圆角 -->
<div class="rounded-2xl">32px圆角</div>

<!-- 完全圆形 -->
<div class="rounded-full">9999px圆角</div>
```

---

## 📊 圆角效果对比

### 应用前
```
┌─────────────┐
│ 方形按钮    │
└─────────────┘
```
- 生硬、机械
- 缺乏亲和力
- 视觉疲劳

### 应用后
```
╭─────────────╮
│ 圆角按钮    │
╰─────────────╯
```
- 柔和、友好
- 现代美观
- 视觉舒适

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **保持一致性**
   ```css
   /* 所有主按钮使用相同圆角 */
   .el-button--primary { border-radius: 16px; }
   ```

2. **考虑上下文**
   ```css
   /* 小空间使用小圆角 */
   .compact-area .el-button { border-radius: 12px; }
   ```

3. **适配内容**
   ```css
   /* 大容器使用大圆角 */
   .large-card { border-radius: 24px; }
   ```

### ❌ 避免做法

1. **圆角过大**
   ```css
   /* ❌ 不要这样 */
   .el-button { border-radius: 50px; }
   ```

2. **圆角不一致**
   ```css
   /* ❌ 避免混乱 */
   .button1 { border-radius: 5px; }
   .button2 { border-radius: 15px; }
   .button3 { border-radius: 25px; }
   ```

3. **忽略层级**
   ```css
   /* ❌ 父子圆角冲突 */
   .parent { border-radius: 8px; }
   .child { border-radius: 20px; }
   ```

---

## 🎨 视觉效果

### 圆角的优势

1. **视觉舒适**
   - 减少视觉疲劳
   - 柔和的边缘更友好
   - 符合自然视觉习惯

2. **现代感**
   - iOS、Android原生设计趋势
   - Material Design 3.0标准
   - 符合2020+设计潮流

3. **层次感**
   - 通过圆角大小区分重要性
   - 建立视觉层级
   - 引导用户注意力

4. **品牌感**
   - 统一的圆角系统
   - 强化品牌识别
   - 提升专业形象

---

## 📱 响应式适配

### 移动端优化

```css
@media (max-width: 768px) {
  /* 移动端略微减小圆角 */
  .el-card { border-radius: 20px; }
  .el-button { border-radius: 14px; }
  .el-input__wrapper { border-radius: 14px; }
}

@media (max-width: 480px) {
  /* 小屏幕进一步优化 */
  .el-card { border-radius: 16px; }
  .el-button { border-radius: 12px; }
}
```

---

## 🔧 技术实现

### 实现文件

- **主布局**: `src/App.vue` (侧边栏、顶栏、主内容区)
- **组件样式**: `src/assets/css/rounded-theme.css` (所有Element Plus组件)
- **加载入口**: `src/main.js` (自动加载圆角主题)

### 覆盖范围

✅ 所有Element Plus组件 (40+个)  
✅ 自定义Vue组件  
✅ 原生HTML元素 (img, pre, code)  
✅ 通用工具类  

---

## 🎉 总结

**圆角设计系统让整个应用**:
- 🎨 更加美观现代
- 😊 更加友好亲和
- 🎯 更加专业统一
- ✨ 更加舒适易用

**记住**: 好的圆角设计是**统一、协调、有层次**的！

---

**享受圆角矩形的视觉体验！** 🎨✨


