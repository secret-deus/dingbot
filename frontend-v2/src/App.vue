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
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-header>

        <!-- 主体内容 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" />
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
import { computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  User,
  ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 计算属性
const allRailItems = [
  { code: 'CMD', title: '指挥台', route: '/dashboard', permission: 'ops:read' },
  { code: 'AI', title: '智能对话', route: '/chat', permission: 'chat:read' },
  { code: 'MAP', title: '拓扑', route: '/dashboard', targetId: 'topology-section', permission: 'ops:read' },
  { code: 'INC', title: '事故', route: '/dashboard', targetId: 'incident-section', permission: 'ops:read' },
  { code: 'RUN', title: '自动化', route: '/scheduler', permission: 'scheduler:read' },
  { code: 'AUD', title: '审计', route: '/dashboard', targetId: 'audit-section', permission: 'ops:read' },
  { code: 'CFG', title: '配置', route: '/mcp-config', permission: 'mcp:read' },
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
  background: #080c14;
}

.layout-container {
  height: 100vh;
}

/* === 左侧 rail - 对齐原型 === */
.ops-rail {
  height: 100vh;
  padding: 16px 12px;
  border-right: 1px solid #24324a;
  background: #09101d;
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
  border: 1px solid rgba(56, 189, 248, 0.32);
  background: #0f1e31;
  color: #38bdf8;
  font-size: 14px;
  font-weight: 800;
  box-shadow: inset 0 0 18px rgba(56, 189, 248, 0.12);
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
  color: #8fa0b8;
  cursor: pointer;
  position: relative;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.rail-nav button:hover,
.rail-nav button.active {
  color: #e6edf7;
  background: #121f34;
  border-color: rgba(56, 189, 248, 0.26);
}

.rail-nav button.active::before {
  content: "";
  width: 3px;
  height: 24px;
  background: #38bdf8;
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
  border: 1px solid rgba(52, 211, 153, 0.2);
  background: rgba(52, 211, 153, 0.08);
  color: #34d399;
  font-size: 12px;
  font-weight: 800;
}

/* === 顶部导航栏 - 极简设计 === */
.header {
  background: rgba(9, 15, 26, 0.94);
  border-bottom: 1px solid #24324a;
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
  border-bottom: 1px solid #24324a;
  background: rgba(9, 15, 26, 0.97);
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
  background: #0d1728;
  color: #8fa0b8;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.mobile-nav button:hover,
.mobile-nav button.active {
  color: #e6edf7;
  background: #121f34;
  border-color: rgba(56, 189, 248, 0.26);
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
  color: #e6edf7;
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
  border: 1px solid #24324a;
  background: #0d1728;
}

.user-dropdown:hover {
  background: #132238;
  border-color: rgba(56, 189, 248, 0.34);
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
  color: #e6edf7;
  font-size: 14px;
  font-weight: 700;
}

.dropdown-icon {
  color: #8fa0b8;
  font-size: 12px;
  transition: transform 0.2s ease;
}

.user-dropdown:hover .dropdown-icon {
  transform: translateY(2px);
}

/* === 主内容区 - 极简设计 === */
.main-content {
  background:
    linear-gradient(180deg, rgba(20, 29, 46, 0.92) 0%, #080c14 280px),
    #080c14;
  padding: 22px;
  overflow-y: auto;
  color: #e6edf7;
}

.ops-route-shell .main-content {
  padding: 0;
  background: #080c14;
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
  color: #e6edf7;
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
  border: 1px solid #25324a;
  border-radius: 8px;
  background: rgba(17, 26, 43, 0.96) !important;
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
  color: #e6edf7 !important;
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
  border: 1px solid #25324a !important;
  border-radius: 8px !important;
  background: rgba(17, 26, 43, 0.96) !important;
  box-shadow: none !important;
  color: #e6edf7 !important;
}

.main-content :deep(.el-card__header),
.main-content :deep(.card-header) {
  background: #111b2d !important;
  border-bottom-color: rgba(148, 163, 184, 0.18) !important;
}

.main-content :deep(.el-tabs__nav-wrap::after) {
  background-color: #25324a;
}

.main-content :deep(.el-tabs__item) {
  color: #8fa0b8;
  font-weight: 800;
}

.main-content :deep(.el-tabs__item.is-active),
.main-content :deep(.el-tabs__item:hover) {
  color: #38bdf8;
}

.main-content :deep(.el-tabs__active-bar) {
  background-color: #38bdf8;
}

.main-content :deep(.el-table),
.main-content :deep(.el-table__expanded-cell) {
  --el-table-border-color: rgba(148, 163, 184, 0.18);
  --el-table-header-bg-color: #0d1728;
  --el-table-tr-bg-color: #101a2b;
  --el-table-row-hover-bg-color: #132238;
  border: 1px solid #25324a !important;
  background: #0b1424 !important;
  color: #e6edf7 !important;
  box-shadow: none !important;
}

.main-content :deep(.el-table th.el-table__cell) {
  background: #0d1728 !important;
  border-color: #25324a !important;
  color: #8fa0b8 !important;
}

.main-content :deep(.el-table tr),
.main-content :deep(.el-table td.el-table__cell) {
  background: #101a2b !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
  color: #d7e0ee !important;
}

.main-content :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #132238 !important;
}

.main-content :deep(.el-table__inner-wrapper::before),
.main-content :deep(.el-table__border-left-patch) {
  background: #25324a !important;
}

.main-content :deep(.el-input__wrapper),
.main-content :deep(.el-select__wrapper),
.main-content :deep(.el-textarea__inner),
.main-content :deep(.el-input-number__decrease),
.main-content :deep(.el-input-number__increase) {
  border: 1px solid #25324a !important;
  background: #08111f !important;
  box-shadow: none !important;
  color: #e6edf7 !important;
}

.main-content :deep(.el-input__inner),
.main-content :deep(.el-select__placeholder),
.main-content :deep(.el-textarea__inner) {
  color: #e6edf7 !important;
}

.main-content :deep(.search-input .el-input__inner),
.main-content :deep(.message-input .el-textarea__inner) {
  border-color: #25324a !important;
  background: #08111f !important;
  color: #e6edf7 !important;
}

.main-content :deep(.el-input__inner::placeholder),
.main-content :deep(.el-textarea__inner::placeholder) {
  color: #607089 !important;
}

.main-content :deep(.el-button) {
  border-radius: 8px;
  font-weight: 800;
}

.main-content :deep(.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning):not(.el-button--danger)) {
  border-color: #25324a;
  background: #0d1728;
  color: #d7e0ee;
}

.main-content :deep(.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning):not(.el-button--danger):hover) {
  border-color: rgba(56, 189, 248, 0.34);
  background: #132238;
  color: #e6edf7;
}

.main-content :deep(.el-button--primary) {
  border-color: rgba(56, 189, 248, 0.44);
  background: #132238;
  color: #7dd3fc;
}

.main-content :deep(.el-tag) {
  border-radius: 999px;
  font-weight: 800;
  background: rgba(56, 189, 248, 0.07) !important;
  border-color: rgba(56, 189, 248, 0.22) !important;
  color: #7dd3fc !important;
}

.main-content :deep(.el-tag.el-tag--success) {
  background: rgba(52, 211, 153, 0.08) !important;
  border-color: rgba(52, 211, 153, 0.22) !important;
  color: #34d399 !important;
}

.main-content :deep(.el-tag.el-tag--danger) {
  background: rgba(251, 113, 133, 0.08) !important;
  border-color: rgba(251, 113, 133, 0.22) !important;
  color: #fb7185 !important;
}

.main-content :deep(.eyebrow) {
  margin: 0 0 6px;
  color: #8fa0b8 !important;
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
  color: #8fa0b8;
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
  color: #8fa0b8 !important;
  font-weight: 800;
}

.main-content :deep(.metric-card strong) {
  display: block;
  margin-top: 16px;
  color: #34d399;
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
  color: #8fa0b8 !important;
}

.main-content :deep(.metric-value .number),
.main-content :deep(.stat-value),
.main-content :deep(.value.success) {
  color: #34d399 !important;
}

.main-content :deep(.value.error) {
  color: #fb7185 !important;
}

.main-content :deep(code),
.main-content :deep(pre),
.main-content :deep(.cron-expression),
.main-content :deep(.error-details) {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: #080f1c !important;
  color: #b9c6d9 !important;
}

.main-content :deep(.chat-body) {
  min-height: 0;
  border: 1px solid #25324a;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(17, 26, 43, 0.96);
}

.main-content :deep(.history-sidebar),
.main-content :deep(.stream-chat) {
  background: #0d1626 !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
}

.main-content :deep(.chat-input-container) {
  border-top: 1px solid rgba(148, 163, 184, 0.18) !important;
  background: #0d1626 !important;
}

.main-content :deep(.input-card) {
  border: 1px solid rgba(56, 189, 248, 0.28) !important;
  border-radius: 8px !important;
  background: #101a2b !important;
  box-shadow: none !important;
}

.main-content :deep(.input-card:hover),
.main-content :deep(.input-card:focus-within) {
  border-color: rgba(56, 189, 248, 0.44) !important;
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
  background: #111b2d !important;
  box-shadow: none !important;
  color: #e6edf7 !important;
}

.main-content :deep(.user-message-card) {
  border: 1px solid rgba(56, 189, 248, 0.28) !important;
  background: #15324a !important;
  color: #e6edf7 !important;
  box-shadow: none !important;
}

.main-content :deep(.question-chip) {
  border-color: rgba(56, 189, 248, 0.24) !important;
  background: rgba(56, 189, 248, 0.07) !important;
  color: #d7e0ee !important;
}

.main-content :deep(.mcp-toggle) {
  border: 1px solid rgba(56, 189, 248, 0.22) !important;
  background: rgba(56, 189, 248, 0.07) !important;
}

.main-content :deep(.filters-panel) {
  border-color: rgba(148, 163, 184, 0.18) !important;
  background: #101a2b !important;
}

.main-content :deep(.user-content),
.main-content :deep(.assistant-content),
.main-content :deep(.welcome-content h3),
.main-content :deep(.welcome-content p),
.main-content :deep(.example-questions h4),
.main-content :deep(.session-title),
.main-content :deep(.card-author),
.main-content :deep(.tool-name) {
  color: #e6edf7 !important;
}

:global(.ops-user-menu.el-popper),
:global(.el-select__popper.el-popper) {
  border: 1px solid #25324a !important;
  background: #101a2b !important;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.32) !important;
}

:global(.ops-user-menu .el-dropdown-menu),
:global(.el-select-dropdown) {
  background: #101a2b !important;
}

:global(.ops-user-menu .el-dropdown-menu__item),
:global(.el-select-dropdown__item) {
  color: #d7e0ee !important;
}

:global(.ops-user-menu .el-dropdown-menu__item:hover),
:global(.el-select-dropdown__item.hover),
:global(.el-select-dropdown__item:hover) {
  background: #132238 !important;
  color: #e6edf7 !important;
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
