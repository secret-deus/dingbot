# 更新日志

## v2.1.0 (2025-09-30)

### 🎨 UI重大更新 - 全面圆角化

#### 新增特性
- ✨ 为所有UI元素添加统一的圆角效果
- 🎨 创建完整的圆角设计系统
- 📐 定义清晰的圆角尺寸标准

#### 圆角规范
- **大型容器** (24px): Card、Dialog、Table、侧边栏、顶栏
- **中型控件** (16px): Button、Input、Select、Alert
- **小型元素** (12px): Tag、Menu Item、Logo
- **圆形元素** (50%): Avatar、Switch、状态指示器

#### 更新的组件
- [x] 侧边栏 - 右侧24px圆角 + 12px外边距
- [x] 顶部栏 - 下方24px圆角 + 12px外边距
- [x] Logo容器 - 顶部24px圆角
- [x] Logo图片 - 12px圆角
- [x] 主内容区 - 左上24px圆角
- [x] 侧边栏切换按钮 - 12px圆角
- [x] 用户下拉菜单 - 20px圆角

#### Element Plus组件优化
- [x] Button - 16px/12px/20px (标准/小/大)
- [x] Input/Textarea - 16px圆角
- [x] Select - 16px圆角 + 下拉项12px圆角
- [x] Card - 24px圆角
- [x] Dialog - 24px圆角
- [x] Message - 20px圆角
- [x] Table - 24px圆角 (含表头表尾)
- [x] Tag - 16px/12px/20px (标准/小/大)
- [x] Dropdown - 16px圆角 + 菜单项12px圆角
- [x] Pagination - 12px圆角
- [x] Switch - 20px圆角
- [x] Avatar - 圆形/12px圆角
- [x] 其他30+个组件全部优化

#### 新增工具类
```css
.rounded-sm    /* 8px */
.rounded       /* 12px */
.rounded-md    /* 16px */
.rounded-lg    /* 20px */
.rounded-xl    /* 24px */
.rounded-2xl   /* 32px */
.rounded-full  /* 完全圆形 */
```

#### 文件变更
- **新增**: `src/assets/css/rounded-theme.css` (圆角主题)
- **更新**: `src/App.vue` (主布局圆角)
- **更新**: `src/main.js` (加载圆角主题)
- **新增**: `ROUNDED-DESIGN.md` (设计文档)
- **新增**: `CHANGELOG.md` (本文件)

#### 构建结果
- ✅ 构建成功 (7.14s)
- ✅ 所有功能正常
- ✅ CSS增加约 4KB (gzip后 ~0.7KB)

#### 视觉效果
- 🎨 整体视觉更加柔和友好
- ✨ 现代感显著提升
- 😊 用户体验更加舒适
- 🎯 品牌形象更加专业

---

## v2.0.0 (2025-09-30)

### 🎉 重大更新 - 前端完全重构

#### 新增特性
- ✨ 全新的frontend-v2目录
- 🎨 现代化毛玻璃UI设计
- 🌈 动态渐变背景动画
- ✨ 流畅的微交互动画
- 📱 响应式设计优化

#### 设计特色
- **Glassmorphism**: 毛玻璃效果
- **渐变背景**: 4色流动动画
- **动画系统**: Logo浮动、按钮上浮、页面滑动
- **配色方案**: 紫蓝粉红渐变

#### 功能保持
- ✅ 所有原有功能完全不变
- ✅ API端点完全兼容
- ✅ 路由配置保持一致
- ✅ 状态管理逻辑不变

#### 技术栈
- Vue.js 3.4+ (Composition API)
- Element Plus 2.4+
- Pinia 2.1+
- Vue Router 4.2+
- Vite 5.0+

#### 文件统计
- 源文件: 25个 (完整迁移)
- 组件: 7个Vue组件
- 视图: 5个页面
- 总大小: 554MB (含node_modules)

---

## 即将推出

### v2.2.0
- [ ] 深色模式切换
- [ ] 主题色自定义
- [ ] 更多动画效果

### v2.3.0
- [ ] PWA支持
- [ ] 离线缓存
- [ ] 性能优化

### v3.0.0
- [ ] 多主题系统
- [ ] 主题编辑器
- [ ] 国际化支持

---

**每个版本都在变得更好！** ✨
