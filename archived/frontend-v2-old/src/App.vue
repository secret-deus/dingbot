<template>
  <div id="app" class="app-container">
    <!-- 只有登录后才显示主布局 -->
    <div v-if="showMainLayout">
      <!-- 导航栏 -->
      <el-container class="layout-container ops-app-theme">
      <!-- 侧边栏 -->
      <el-aside width="76px" class="ops-rail" aria-label="Primary">
        <button class="rail-brand" type="button" title="DingOps Copilot" @click="navigateTo('/dashboard')">
          DO
        </button>

        <nav class="rail-nav" aria-label="Primary navigation">
          <button
            v-for="item in railItems"
            :key="item.code"
            type="button"
            :class="{ active: isRailActive(item) }"
            :title="item.title"
            @click="navigateTo(item)"
          >
            <span>{{ item.code }}</span>
          </button>
        </nav>

        <div class="rail-bottom">
          <div class="mini-status" :title="accessMode.title">{{ accessMode.code }}</div>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-container :class="{ 'ops-route-shell': isOpsRoute }">
        <!-- 头部 -->
        <el-header v-if="!isOpsRoute" class="header">
          <div class="header-left">
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item>{{ breadcrumbTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <el-dropdown popper-class="ops-user-menu" @command="handleUserCommand">
              <span class="user-dropdown">
                <el-avatar :size="32" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="username">{{ authStore.displayName }}</span>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                  <el-dropdown-item
                    v-for="theme in OPS_THEMES"
                    :key="theme.id"
                    :command="`theme:${theme.id}`"
                  >
                    {{ currentTheme === theme.id ? '✓ ' : '' }}主题：{{ theme.name }}
                  </el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-header class="mobile-topbar">
          <button class="mobile-brand" type="button" title="DingOps Copilot" @click="navigateTo('/dashboard')">
            DO
          </button>

          <nav class="mobile-nav" aria-label="Mobile navigation">
            <button
              v-for="item in railItems"
              :key="item.code"
              type="button"
              :class="{ active: isRailActive(item) }"
              :title="item.title"
              @click="navigateTo(item)"
            >
              {{ item.code }}
            </button>
          </nav>

          <el-dropdown class="mobile-account" popper-class="ops-user-menu" @command="handleUserCommand">
            <span class="user-dropdown">
              <el-avatar :size="28" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item
                  v-for="theme in OPS_THEMES"
                  :key="theme.id"
                  :command="`theme:${theme.id}`"
                >
                  {{ currentTheme === theme.id ? '✓ ' : '' }}主题：{{ theme.name }}
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-header>

        <!-- 主体内容 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" :key="route.fullPath" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
    </div>

    <!-- 隐藏侧边栏时的浮动按钮 -->
    <!-- 未登录时显示路由视图（登录页） -->
    <div v-else>
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  User,
  ArrowDown
} from '@element-plus/icons-vue'
import { OPS_THEMES, applyOpsTheme, getSavedOpsTheme, getThemeName } from '@/theme/opsThemes'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const currentTheme = ref(getSavedOpsTheme())

// 计算属性
const allRailItems = [
  { code: 'CMD', title: '指挥台', route: '/dashboard', permission: 'ops:read' },
  { code: 'AI', title: '智能对话', route: '/chat', permission: 'chat:read' },
  { code: 'RUN', title: '自动化', route: '/scheduler', permission: 'scheduler:read' },
  { code: 'CFG', title: '配置中心', route: '/mcp-config', permission: 'mcp:read' },
  { code: 'IAM', title: '访问控制', route: '/access-control', permission: 'users:read' },
  { code: 'LOG', title: '操作日志', route: '/audit-logs', permission: 'audit:read' }
]

const railItems = computed(() => allRailItems.filter((item) => authStore.hasPermission(item.permission)))

const accessMode = computed(() => {
  if (authStore.permissions.includes('*')) {
    return { code: 'ADM', title: '管理员模式' }
  }
  if (authStore.hasPermission('users:read')) {
    return { code: 'IAM', title: '访问控制模式' }
  }
  return { code: 'RO', title: '只读模式' }
})

const showMainLayout = computed(() => {
  return authStore.isAuthenticated && route.path !== '/login'
})

const breadcrumbTitle = computed(() => {
  const titles = {
    '/dashboard': '运维指挥台',
    '/chat': '智能对话',
    '/topology': '拓扑',
    '/incidents': '事故',
    '/audit': '审计',
    '/llm-config': 'LLM设置',
    '/mcp-config': 'MCP配置',
    '/scheduler': '定时任务',
    '/access-control': '访问控制',
    '/audit-logs': '操作日志'
  }
  return titles[route.path] || '钉钉K8s运维机器人'
})

const isOpsRoute = computed(() => route.path === '/dashboard')

// 方法
const scrollToTarget = (targetId) => {
  window.requestAnimationFrame(() => {
    document.getElementById(targetId)?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  })
}

const navigateTo = async (target) => {
  const path = typeof target === 'string' ? target : target.route
  const targetId = typeof target === 'string' ? '' : target.targetId
  if (route.path !== path) {
    await router.push(targetId ? { path, hash: `#${targetId}` } : path)
  } else if (targetId && route.hash !== `#${targetId}`) {
    await router.push({ path, hash: `#${targetId}` })
  } else if (!targetId && route.hash) {
    await router.push(path)
  }

  if (targetId) {
    scrollToTarget(targetId)
  } else if (path === '/dashboard') {
    scrollToTarget('command-section')
  }
}

const isRailActive = (item) => {
  if (item.targetId) {
    return route.path === item.route && route.hash === `#${item.targetId}`
  }
  if (item.route === '/dashboard') {
    return route.path === item.route && !route.hash
  }
  return route.path === item.route
}

const handleAuthExpired = () => {
  authStore.clearSession()
  if (route.path !== '/login') {
    router.replace({
      path: '/login',
      query: { redirect: route.fullPath }
    })
  }
}

const handleUserCommand = async (command) => {
  if (command?.startsWith('theme:')) {
    const themeId = command.split(':')[1]
    currentTheme.value = applyOpsTheme(themeId)
    ElMessage.success(`已切换主题：${getThemeName(currentTheme.value)}`)
    return
  }

  switch (command) {
    case 'profile':
      ElMessage.info('个人设置功能开发中...')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '退出确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )

        // 执行退出登录
        await authStore.logout()
        ElMessage.success('已退出登录')

        // 跳转到登录页
        router.push('/login')
      } catch {
        // 用户取消退出
      }
      break
  }
}

// 监听路由变化
watch(route, (newRoute) => {
  console.log('路由变化:', newRoute.path)
  nextTick(() => {
    if (!newRoute.hash) {
      document.querySelector('.main-content')?.scrollTo({ top: 0, left: 0 })
    }
  })
})

// 组件挂载时初始化认证状态
onMounted(() => {
  authStore.initAuth()
  window.addEventListener('auth:expired', handleAuthExpired)
})

onUnmounted(() => {
  window.removeEventListener('auth:expired', handleAuthExpired)
})
</script>

<style scoped>
/* === 极简黑白设计 === */
.app-container {
  height: 100vh;
  overflow: hidden;
  background: var(--ops-bg);
}

.layout-container {
  height: 100vh;
}

/* === 左侧 rail - 对齐原型 === */
.ops-rail {
  height: 100vh;
  padding: 16px 12px;
  border-right: 1px solid var(--ops-border);
  background: var(--ops-bg-elevated);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  flex: 0 0 76px;
}

.rail-brand,
.mobile-brand,
.rail-nav button,
.mobile-nav button,
.mini-status {
  border-radius: 8px;
  letter-spacing: 0;
}

.rail-brand,
.mobile-brand {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 1px solid var(--ops-accent-border);
  background: var(--ops-surface-selected);
  color: var(--ops-accent-strong);
  font-size: 14px;
  font-weight: 800;
  box-shadow: none;
  cursor: pointer;
}

.rail-nav {
  display: grid;
  gap: 8px;
  width: 100%;
}

.rail-nav button {
  width: 52px;
  height: 48px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ops-muted);
  cursor: pointer;
  position: relative;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.rail-nav button:hover,
.rail-nav button.active {
  color: var(--ops-text);
  background: var(--ops-surface-hover);
  border-color: var(--ops-accent-border);
}

.rail-nav button.active::before {
  content: "";
  width: 3px;
  height: 24px;
  background: var(--ops-accent);
  border-radius: 3px;
  position: absolute;
  left: -7px;
  top: 12px;
}

.rail-nav span {
  display: block;
  font-size: 13px;
  font-weight: 800;
  line-height: 1;
}

.rail-bottom {
  margin-top: auto;
  display: grid;
  gap: 10px;
}

.mini-status {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--ops-success) 24%, transparent);
  background: var(--ops-success-soft);
  color: var(--ops-success);
  font-size: 12px;
  font-weight: 800;
}

/* === 顶部导航栏 - 极简设计 === */
.header {
  background: color-mix(in srgb, var(--ops-bg-elevated) 96%, transparent);
  border-bottom: 1px solid var(--ops-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: none;
  position: relative;
  z-index: 99;
  height: 72px;
}

.mobile-topbar {
  display: none;
  align-items: center;
  gap: 10px;
  height: 64px;
  padding: 0 12px;
  border-bottom: 1px solid var(--ops-border);
  background: color-mix(in srgb, var(--ops-bg-elevated) 98%, transparent);
  position: relative;
  z-index: 100;
}

.mobile-brand,
.mobile-account {
  flex: 0 0 auto;
}

.mobile-nav {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 0 2px;
  scrollbar-width: none;
}

.mobile-nav::-webkit-scrollbar {
  display: none;
}

.mobile-nav button {
  flex: 0 0 auto;
  min-width: 42px;
  height: 36px;
  border: 1px solid transparent;
  background: var(--ops-surface-raised);
  color: var(--ops-muted);
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.mobile-nav button:hover,
.mobile-nav button.active {
  color: var(--ops-text);
  background: var(--ops-surface-hover);
  border-color: var(--ops-accent-border);
}

.mobile-topbar .user-dropdown {
  padding: 5px 8px;
}

.mobile-topbar .user-avatar {
  margin-right: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.breadcrumb {
  font-size: 14px;
  font-weight: 800;
  color: var(--ops-text);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--border-radius-base);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--ops-border);
  background: var(--ops-surface-raised);
}

.user-dropdown:hover {
  background: var(--ops-surface-hover);
  border-color: var(--ops-accent-border);
  transform: translateY(-1px);
  box-shadow: none;
}

.user-dropdown:active {
  transform: translateY(0);
}

.user-avatar {
  margin-right: 8px;
}

.username {
  margin-right: 8px;
  color: var(--ops-text);
  font-size: 14px;
  font-weight: 700;
}

.dropdown-icon {
  color: var(--ops-muted);
  font-size: 12px;
  transition: transform 0.2s ease;
}

.user-dropdown:hover .dropdown-icon {
  transform: translateY(2px);
}

/* === 主内容区 - 极简设计 === */
.main-content {
  background: var(--ops-bg);
  padding: 22px;
  overflow-y: auto;
  color: var(--ops-text);
}

.ops-route-shell .main-content {
  padding: 0;
  background: var(--ops-bg);
}

/* === Shared Ops dark surface for non-dashboard pages === */
.main-content :deep(.mcp-config-page),
.main-content :deep(.scheduler-page),
.main-content :deep(.chat-page),
.main-content :deep(.access-control-page),
.main-content :deep(.audit-log-page),
.main-content :deep(.ops-management-page) {
  min-height: 100%;
  background: transparent !important;
  color: var(--ops-text);
}

.main-content :deep(.mcp-config-page),
.main-content :deep(.scheduler-page),
.main-content :deep(.ops-management-page) {
  padding: 0;
}

.main-content :deep(.page-header),
.main-content :deep(.chat-header-card),
.main-content :deep(.ops-page-hero) {
  margin: 0 0 18px;
  padding: 16px 18px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: rgba(18, 20, 16, 0.96) !important;
  box-shadow: 0 22px 64px rgba(0, 0, 0, 0.24) !important;
}

.main-content :deep(.chat-header-card .el-card__body) {
  padding: 0;
}

.main-content :deep(.page-title),
.main-content :deep(.page-header h1),
.main-content :deep(.page-header h2),
.main-content :deep(.card-title),
.main-content :deep(.card-header),
.main-content :deep(.panel-title),
.main-content :deep(.monitor-header h3),
.main-content :deep(.config-preview h3),
.main-content :deep(.preview-section h4) {
  color: var(--ops-text) !important;
}

.main-content :deep(.page-title),
.main-content :deep(.page-header h1) {
  font-size: 22px;
  font-weight: 780;
}

.main-content :deep(.el-card),
.main-content :deep(.card),
.main-content :deep(.panel-card),
.main-content :deep(.metric-card),
.main-content :deep(.filters),
.main-content :deep(.config-preview),
.main-content :deep(.storage-overview),
.main-content :deep(.storage-actions),
.main-content :deep(.operation-result) {
  border: 1px solid var(--ops-border) !important;
  border-radius: 8px !important;
  background: rgba(18, 20, 16, 0.96) !important;
  box-shadow: none !important;
  color: var(--ops-text) !important;
}

.main-content :deep(.el-card__header),
.main-content :deep(.card-header) {
  background: var(--ops-surface-raised) !important;
  border-bottom-color: var(--ops-border) !important;
}

.main-content :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--ops-border);
}

.main-content :deep(.el-tabs__item) {
  color: var(--ops-muted);
  font-weight: 800;
}

.main-content :deep(.el-tabs__item.is-active),
.main-content :deep(.el-tabs__item:hover) {
  color: var(--ops-accent);
}

.main-content :deep(.el-tabs__active-bar) {
  background-color: var(--ops-accent);
}

.main-content :deep(.el-table),
.main-content :deep(.el-table__expanded-cell) {
  --el-table-border-color: var(--ops-border);
  --el-table-header-bg-color: var(--ops-surface-raised);
  --el-table-tr-bg-color: var(--ops-surface);
  --el-table-row-hover-bg-color: var(--ops-surface-hover);
  border: 1px solid var(--ops-border) !important;
  background: var(--ops-surface) !important;
  color: var(--ops-text) !important;
  box-shadow: none !important;
}

.main-content :deep(.el-table th.el-table__cell) {
  background: var(--ops-surface-raised) !important;
  border-color: var(--ops-border) !important;
  color: var(--ops-muted) !important;
}

.main-content :deep(.el-table tr),
.main-content :deep(.el-table td.el-table__cell) {
  background: var(--ops-surface) !important;
  border-color: var(--ops-border) !important;
  color: var(--ops-text-soft) !important;
}

.main-content :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: var(--ops-surface-hover) !important;
}

.main-content :deep(.el-table__inner-wrapper::before),
.main-content :deep(.el-table__border-left-patch) {
  background: var(--ops-border) !important;
}

.main-content :deep(.el-input__wrapper),
.main-content :deep(.el-select__wrapper),
.main-content :deep(.el-textarea__inner),
.main-content :deep(.el-input-number__decrease),
.main-content :deep(.el-input-number__increase) {
  border: 1px solid var(--ops-border) !important;
  background: var(--ops-bg-elevated) !important;
  box-shadow: none !important;
  color: var(--ops-text) !important;
}

.main-content :deep(.el-input__inner),
.main-content :deep(.el-select__placeholder),
.main-content :deep(.el-textarea__inner) {
  color: var(--ops-text) !important;
}

.main-content :deep(.search-input .el-input__inner),
.main-content :deep(.message-input .el-textarea__inner) {
  border-color: var(--ops-border) !important;
  background: var(--ops-bg-elevated) !important;
  color: var(--ops-text) !important;
}

.main-content :deep(.el-input__inner::placeholder),
.main-content :deep(.el-textarea__inner::placeholder) {
  color: var(--ops-muted-2) !important;
}

.main-content :deep(.el-button) {
  border-radius: 8px;
  font-weight: 800;
}

.main-content :deep(.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning):not(.el-button--danger)) {
  border-color: var(--ops-border);
  background: var(--ops-surface-raised);
  color: var(--ops-text-soft);
}

.main-content :deep(.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning):not(.el-button--danger):hover) {
  border-color: var(--ops-accent-border);
  background: var(--ops-surface-hover);
  color: var(--ops-text);
}

.main-content :deep(.el-button--primary) {
  border-color: var(--ops-accent-border);
  background: var(--ops-accent-soft);
  color: var(--ops-accent-strong);
}

.main-content :deep(.el-tag) {
  border-radius: 999px;
  font-weight: 800;
  background: rgba(214, 168, 79, 0.08) !important;
  border-color: rgba(214, 168, 79, 0.22) !important;
  color: #e0b45a !important;
}

.main-content :deep(.el-tag.el-tag--success) {
  background: rgba(143, 191, 135, 0.1) !important;
  border-color: rgba(143, 191, 135, 0.24) !important;
  color: #9fcf96 !important;
}

.main-content :deep(.el-tag.el-tag--danger) {
  background: rgba(251, 113, 133, 0.08) !important;
  border-color: rgba(251, 113, 133, 0.22) !important;
  color: #fb7185 !important;
}

.main-content :deep(.eyebrow) {
  margin: 0 0 6px;
  color: #9da08e !important;
  font-size: 12px;
  font-weight: 900;
}

.main-content :deep(.ops-page-hero) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.main-content :deep(.ops-page-hero span) {
  color: #9da08e;
}

.main-content :deep(.metrics-grid) {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.main-content :deep(.metric-card) {
  min-height: 112px;
  padding: 18px;
}

.main-content :deep(.metric-card span),
.main-content :deep(.el-form-item__label) {
  color: #9da08e !important;
  font-weight: 800;
}

.main-content :deep(.metric-card strong) {
  display: block;
  margin-top: 16px;
  color: #9fcf96;
  font-size: 34px;
  line-height: 1;
}

.main-content :deep(.el-empty__description p),
.main-content :deep(.text-muted),
.main-content :deep(.label),
.main-content :deep(.task-name .description),
.main-content :deep(.metric-value .unit),
.main-content :deep(.preview-item .label),
.main-content :deep(.more-tools),
.main-content :deep(.empty-message),
.main-content :deep(.setting-help),
.main-content :deep(.quota-info),
.main-content :deep(.result-details li) {
  color: #9da08e !important;
}

.main-content :deep(.metric-value .number),
.main-content :deep(.stat-value),
.main-content :deep(.value.success) {
  color: #9fcf96 !important;
}

.main-content :deep(.value.error) {
  color: #fb7185 !important;
}

.main-content :deep(code),
.main-content :deep(pre),
.main-content :deep(.cron-expression),
.main-content :deep(.error-details) {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: #0f110d !important;
  color: #d5d1c3 !important;
}

.main-content :deep(.chat-body) {
  min-height: 0;
  border: 1px solid #2a2d24;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(18, 20, 16, 0.96);
}

.main-content :deep(.history-sidebar),
.main-content :deep(.stream-chat) {
  background: #12140f !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
}

.main-content :deep(.chat-input-container) {
  border-top: 1px solid rgba(148, 163, 184, 0.18) !important;
  background: #12140f !important;
}

.main-content :deep(.input-card) {
  border: 1px solid rgba(214, 168, 79, 0.24) !important;
  border-radius: 8px !important;
  background: #171a14 !important;
  box-shadow: none !important;
}

.main-content :deep(.input-card:hover),
.main-content :deep(.input-card:focus-within) {
  border-color: rgba(214, 168, 79, 0.38) !important;
  transform: none !important;
  box-shadow: none !important;
}

.main-content :deep(.welcome-card),
.main-content :deep(.assistant-message-card),
.main-content :deep(.history-header-card),
.main-content :deep(.session-card),
.main-content :deep(.tool-call-card),
.main-content :deep(.system-message-card),
.main-content :deep(.stat-item) {
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  background: #171a14 !important;
  box-shadow: none !important;
  color: #f1efe7 !important;
}

.main-content :deep(.user-message-card) {
  border: 1px solid rgba(214, 168, 79, 0.22) !important;
  background: #242115 !important;
  color: #f1efe7 !important;
  box-shadow: none !important;
}

.main-content :deep(.question-chip) {
  border-color: rgba(214, 168, 79, 0.2) !important;
  background: rgba(214, 168, 79, 0.07) !important;
  color: #e6e2d8 !important;
}

.main-content :deep(.mcp-toggle) {
  border: 1px solid rgba(214, 168, 79, 0.22) !important;
  background: rgba(214, 168, 79, 0.07) !important;
}

.main-content :deep(.filters-panel) {
  border-color: rgba(148, 163, 184, 0.18) !important;
  background: #171a14 !important;
}

.main-content :deep(.user-content),
.main-content :deep(.assistant-content),
.main-content :deep(.welcome-content h3),
.main-content :deep(.welcome-content p),
.main-content :deep(.example-questions h4),
.main-content :deep(.session-title),
.main-content :deep(.card-author),
.main-content :deep(.tool-name) {
  color: #f1efe7 !important;
}

:global(.ops-user-menu.el-popper),
:global(.el-select__popper.el-popper) {
  border: 1px solid #2a2d24 !important;
  background: #171a14 !important;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.32) !important;
}

:global(.ops-user-menu .el-dropdown-menu),
:global(.el-select-dropdown) {
  background: #171a14 !important;
}

:global(.ops-user-menu .el-dropdown-menu__item),
:global(.el-select-dropdown__item) {
  color: #e6e2d8 !important;
}

:global(.ops-user-menu .el-dropdown-menu__item:hover),
:global(.el-select-dropdown__item.hover),
:global(.el-select-dropdown__item:hover) {
  background: #1e2119 !important;
  color: #f1efe7 !important;
}

/* === 路由过渡动画 - 丝滑 === */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* === 响应式优化 === */
@media (max-width: 820px) {
  .ops-rail {
    display: none;
  }

  .header {
    display: none;
  }

  .mobile-topbar {
    display: flex;
  }

  .main-content :deep(.metrics-grid) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }

  .main-content {
    padding: 16px;
  }

  .username {
    display: none;
  }
}

@media (max-width: 560px) {
  .main-content :deep(.metrics-grid) {
    grid-template-columns: 1fr;
  }

  .main-content :deep(.ops-page-hero) {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
