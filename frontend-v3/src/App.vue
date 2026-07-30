<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-notification-provider>
      <n-message-provider>
        <div v-if="auth.isLoggedIn" :class="['app-shell', { 'is-collapsed': effectiveCollapsed }]">
          <aside class="app-sidebar" aria-label="主导航" :aria-expanded="!effectiveCollapsed">
            <div class="window-dots" aria-hidden="true" />

            <div class="brand-row">
              <button class="brand-button" type="button" :aria-label="effectiveCollapsed ? '展开侧栏' : '折叠侧栏'" @click="collapsed = !collapsed">
                <span class="brand-mark">O</span>
                <span class="brand-copy">
                  <strong>Ops Workbench</strong>
                  <small>智能运维工作台</small>
                </span>
              </button>
              <n-button class="collapse-button" quaternary circle :aria-label="effectiveCollapsed ? '展开侧栏' : '折叠侧栏'" @click="collapsed = !collapsed">
                <template #icon>
                  <n-icon><component :is="effectiveCollapsed ? ChevronForwardOutline : ChevronBackOutline" /></n-icon>
                </template>
              </n-button>
            </div>

            <button class="new-chat-button" type="button" :disabled="chatNavigationLocked" @click="openNewChat">
              <span class="new-chat-copy">新建排障对话</span>
              <n-icon aria-hidden="true"><AddOutline /></n-icon>
            </button>

            <nav class="nav-group">
              <button
                v-for="item in menuItems"
                :key="item.key"
                :class="['nav-item', { active: isActive(item.key) }]"
                type="button"
                :aria-current="isActive(item.key) ? 'page' : undefined"
                :title="item.label"
                :disabled="chatNavigationLocked && !isActive(item.key)"
                @click="onMenuSelect(item.key)"
              >
                <n-icon :size="18"><component :is="item.icon" /></n-icon>
                <span>{{ item.label }}</span>
              </button>
            </nav>

            <section class="recent-context" aria-label="最近上下文">
              <div class="nav-title">最近上下文</div>
              <div class="thread-list">
                <button
                  v-for="session in recentSessions"
                  :key="session.id"
                  type="button"
                  class="thread-item"
                  :title="session.title"
                  :disabled="chatNavigationLocked"
                  @click="openRecentSession(session.id)"
                >
                  <span class="thread-title">{{ session.title }}</span>
                  <small>{{ formatCompactTime(session.updated_at) }}</small>
                </button>
                <div v-if="!recentSessions.length" class="thread-empty">暂无最近会话</div>
              </div>
            </section>

            <div class="account-card">
              <div class="avatar">{{ userInitial }}</div>
              <div class="account-copy">
                <strong>{{ auth.username || 'user' }}</strong>
                <span>{{ auth.role }}</span>
              </div>
              <n-button quaternary circle aria-label="退出登录" title="退出登录" @click="logout">
                <template #icon>
                  <n-icon><LogOutOutline /></n-icon>
                </template>
              </n-button>
            </div>
          </aside>

          <section class="app-main">
            <header class="app-topbar">
              <div class="crumbs">
                <strong>Ops Workbench Demo</strong>
                <span>/</span>
                <strong>ops-workbench</strong>
                <span>/</span>
                <span>{{ routeSectionTitle }}</span>
              </div>
              <div class="workspace-strip" aria-label="当前工作区态势">
                <span :class="['workspace-chip', routeAccessTone]">
                  <small>Access</small>
                  <strong>{{ routeAccessLabel }}</strong>
                </span>
                <span class="workspace-chip">
                  <small>Modules</small>
                  <strong>{{ menuItems.length }}</strong>
                </span>
                <span class="workspace-chip">
                  <small>Context</small>
                  <strong>{{ recentSessionCount }}</strong>
                </span>
              </div>
              <div class="top-actions">
                <n-tag size="small" round :type="auth.isAdmin ? 'error' : auth.isOperator ? 'warning' : 'info'">
                  {{ auth.username }} · {{ auth.role }}
                </n-tag>
                <n-button secondary size="small" @click="logout">退出</n-button>
              </div>
            </header>
            <main :class="['app-content', { 'app-content-full': route.meta.fullBleed }]">
              <router-view />
            </main>
          </section>
        </div>
        <router-view v-else />
      </n-message-provider>
    </n-notification-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NConfigProvider, NIcon, NMessageProvider, NNotificationProvider, NTag } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import {
  AddOutline,
  ChevronBackOutline,
  ChevronForwardOutline,
  ChatbubblesOutline,
  ConstructOutline,
  DocumentTextOutline,
  GitNetworkOutline,
  LogOutOutline,
  SettingsOutline,
  ShieldOutline,
  SpeedometerOutline,
  TimeOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useChatStore } from '@/stores/chat'

const auth = useAuthStore()
const sessionStore = useSessionStore()
const chatStore = useChatStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const isNarrow = ref(false)
const effectiveCollapsed = computed(() => isNarrow.value || collapsed.value)

const appFontFamily = 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif'
const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: appFontFamily,
    primaryColor: '#5b5bd6',
    primaryColorHover: '#4f46e5',
    primaryColorPressed: '#4338ca',
    primaryColorSuppl: '#5b5bd6',
    bodyColor: '#f8fafc',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    tableColor: '#ffffff',
    borderColor: '#dbe1ea',
    textColorBase: '#111827',
    textColor1: '#111827',
    textColor2: '#374151',
    textColor3: '#6b7280',
    fontSize: '14px',
    borderRadius: '8px',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusSmall: '8px',
    heightMedium: '40px',
    heightSmall: '36px',
    fontWeight: '570',
  },
  DataTable: {
    thColor: '#f8fafc',
    tdColor: '#ffffff',
    tdColorHover: '#f3f4f6',
    borderColor: '#e5e7eb',
    thTextColor: '#6b7280',
    tdTextColor: '#374151',
  },
  Input: {
    color: '#ffffff',
    colorFocus: '#ffffff',
    border: '1px solid #dbe1ea',
    borderHover: '1px solid #cbd5e1',
    borderFocus: '1px solid #5b5bd6',
    boxShadowFocus: '0 0 0 3px rgba(91, 91, 214, 0.16)',
    borderRadius: '8px',
  },
  Select: {
    peers: {
      InternalSelection: {
        color: '#ffffff',
        colorActive: '#ffffff',
        border: '1px solid #dbe1ea',
        borderHover: '1px solid #cbd5e1',
        borderActive: '1px solid #5b5bd6',
        boxShadowActive: '0 0 0 3px rgba(91, 91, 214, 0.16)',
        borderRadius: '8px',
      },
    },
  },
}

const recentSessions = computed(() => sessionStore.sessions.slice(0, 5))
const recentSessionCount = computed(() => recentSessions.value.length)
const chatNavigationLocked = computed(() => route.name === 'Chat' && chatStore.streaming)

const menuItems = computed<Array<{ label: string; key: string; icon: Component }>>(() => {
  const items = [
    { label: 'Tracing', key: 'Dashboard', icon: SpeedometerOutline },
    { label: 'Chat', key: 'Chat', icon: ChatbubblesOutline },
    { label: 'Tools', key: 'MCPConfig', icon: ConstructOutline },
    { label: 'Graph', key: 'KnowledgeGraph', icon: GitNetworkOutline },
    { label: 'Models', key: 'LLMConfig', icon: SettingsOutline },
  ]
  if (auth.isOperator) {
    items.push({ label: 'Schedules', key: 'Scheduler', icon: TimeOutline })
  }
  if (auth.isAdmin) {
    items.push({ label: 'Access', key: 'AccessControl', icon: ShieldOutline })
    items.push({ label: 'Audit logs', key: 'AuditLogs', icon: DocumentTextOutline })
  }
  return items
})

const userInitial = computed(() => (auth.username || 'U').slice(0, 1).toUpperCase())
const routeSectionTitle = computed(() => {
  const titles: Record<string, string> = {
    Dashboard: 'Traces',
    Chat: 'Chat',
    MCPConfig: 'Tools',
    KnowledgeGraph: 'Graph',
    LLMConfig: 'Models',
    Scheduler: 'Schedules',
    AccessControl: 'Access',
    AuditLogs: 'Audit logs',
  }
  return titles[String(route.name || '')] || String(route.meta.title || 'Workspace')
})
const routeAccessLabel = computed(() => {
  const permission = String(route.meta.permission || '')
  if (permission === 'admin') return 'Admin'
  if (permission === 'operator') return 'Operator'
  return 'Open'
})
const routeAccessTone = computed(() => {
  const permission = String(route.meta.permission || '')
  if (permission === 'admin') return 'danger'
  if (permission === 'operator') return 'warning'
  return 'success'
})

function isActive(key: string) {
  return route.name === key
}

function onMenuSelect(key: string) {
  if (chatNavigationLocked.value && !isActive(key)) return
  router.push({ name: key })
}

function openNewChat() {
  if (chatNavigationLocked.value) return
  router.push({ name: 'Chat', query: { new: '1' } })
}

function openRecentSession(sessionId: string) {
  if (chatNavigationLocked.value) return
  router.push({ name: 'Chat', query: { session: sessionId } })
}

function formatCompactTime(value?: string) {
  if (!value) return '未更新'
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function logout() {
  auth.logout()
  router.push({ name: 'Login' })
}

function syncResponsiveChrome() {
  isNarrow.value = window.innerWidth <= 980
  if (isNarrow.value) {
    collapsed.value = true
  }
}

onMounted(() => {
  syncResponsiveChrome()
  window.addEventListener('resize', syncResponsiveChrome)
})

watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) sessionStore.fetchSessions()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncResponsiveChrome)
})
</script>

<style>
.app-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  width: 100vw;
  height: 100dvh;
  min-height: 0;
  max-height: 100dvh;
  overflow: hidden;
  border: 0;
  background: var(--dr-bg);
  color: var(--dr-text);
  transition: grid-template-columns 180ms ease;
}

.app-shell.is-collapsed {
  grid-template-columns: 72px minmax(0, 1fr);
}

.app-sidebar {
  position: relative;
  isolation: isolate;
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 14px;
  padding: 16px 12px;
  overflow: hidden;
  border-right: 1px solid var(--dr-sidebar-border);
  background: var(--dr-sidebar);
  box-shadow: none;
  transition: padding 180ms ease;
}

.app-sidebar::before {
  display: none;
}

.app-sidebar::after {
  content: "";
  display: none;
}

.app-sidebar > * {
  position: relative;
  z-index: 1;
}

.window-dots {
  display: none;
}

.window-dots::before {
  display: none;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 36px;
}

.brand-button {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 0;
  background: transparent;
  color: var(--dr-sidebar-text);
  cursor: pointer;
  text-align: left;
}

.brand-mark {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #f1f5f9;
  color: var(--dr-text);
  font-size: var(--dr-text-sm);
  font-weight: 680;
  box-shadow: none;
}

.brand-copy {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.brand-copy strong {
  color: var(--dr-sidebar-text);
  font-size: var(--dr-text-lg);
  font-weight: 610;
  line-height: 1.15;
  text-shadow: none;
}

.brand-copy small,
.account-copy span {
  color: var(--dr-sidebar-muted);
  font-size: var(--dr-text-sm);
}

.crumbs {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}

.collapse-button {
  flex: 0 0 auto;
  min-width: 36px;
}

.new-chat-button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 44px;
  padding: 0 12px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--dr-sidebar-text);
  box-shadow: none;
  cursor: pointer;
  font-weight: 560;
  overflow: hidden;
}

.new-chat-button::before {
  display: none;
}

.new-chat-button:hover,
.nav-item:hover,
.thread-item:hover {
  background: #f3f4f6;
  color: var(--dr-sidebar-text);
}

.new-chat-button:hover {
  border-color: transparent;
  box-shadow: none;
}

.new-chat-button:hover::before {
  opacity: 1;
}

.new-chat-button:disabled,
.nav-item:disabled,
.thread-item:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.nav-group,
.thread-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item,
.thread-item {
  min-width: 0;
  border: 0;
  border-radius: var(--dr-radius);
  background: transparent;
  color: var(--dr-sidebar-muted);
  cursor: pointer;
  text-align: left;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 0 9px;
  font-size: var(--dr-text-md);
  font-weight: 480;
  transition: background-color 160ms ease, box-shadow 160ms ease, color 160ms ease;
}

.nav-item.active {
  background: #f1f5f9;
  color: var(--dr-sidebar-text);
  font-weight: 620;
  box-shadow: none;
}

.nav-item.active::before {
  display: none;
}

.nav-item.active::after {
  display: none;
}

.nav-item.active .n-icon {
  color: var(--dr-text);
  filter: none;
}

.recent-context {
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.nav-title {
  margin: 14px 8px 6px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
  font-weight: 590;
  text-transform: uppercase;
}

.thread-item {
  display: grid;
  gap: 2px;
  min-height: 44px;
  padding: 7px 9px;
  overflow: hidden;
  font-size: var(--dr-text-sm);
}

.thread-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-item small,
.thread-empty {
  overflow: hidden;
  color: var(--dr-sidebar-muted);
  font-size: var(--dr-text-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-empty {
  padding: 8px 9px;
}

.account-card {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) 32px;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 8px 0 0;
  border-top: 1px solid var(--dr-border-soft);
}

.avatar {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background: #f1f5f9;
  color: var(--dr-sidebar-text);
  font-size: var(--dr-text-xs);
  font-weight: 650;
}

.account-copy {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.account-copy strong {
  overflow: hidden;
  color: var(--dr-sidebar-text);
  font-size: var(--dr-text-sm);
  font-weight: 610;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-main {
  position: relative;
  isolation: isolate;
  display: flex;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  flex-direction: column;
  background: var(--dr-bg);
}

.app-main::before {
  display: none;
}

.app-main::after {
  display: none;
}

.app-topbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex: 0 0 58px;
  min-height: 58px;
  padding: 0 24px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: #ffffff;
  backdrop-filter: none;
}

.crumbs {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}

.crumbs strong {
  overflow: hidden;
  color: var(--dr-text);
  font-weight: 610;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-strip {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex: 1 1 auto;
}

.workspace-chip {
  min-width: 0;
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 9px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #f8fafc;
  color: var(--dr-text-soft);
  white-space: nowrap;
}

.workspace-chip small {
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 700;
}

.workspace-chip strong {
  overflow: hidden;
  color: var(--dr-text);
  font-size: 12px;
  font-weight: 680;
  text-overflow: ellipsis;
}

.workspace-chip.success {
  border-color: #b8e3d1;
  background: #f0fdf4;
}

.workspace-chip.warning {
  border-color: #f3d89b;
  background: #fffbeb;
}

.workspace-chip.danger {
  border-color: #f2b8b5;
  background: #fff5f5;
}

.top-actions {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 8px;
}

.top-actions .n-tag {
  border-color: #dbe1ea !important;
  background: #f1f5f9 !important;
  color: #374151 !important;
}

.app-content {
  position: relative;
  z-index: 1;
  min-height: 0;
  flex: 1 1 auto;
  overflow: auto;
  padding: 24px;
  background: transparent;
}

.app-content-full {
  height: 100%;
  padding: 0;
  overflow: hidden;
}

.is-collapsed .brand-copy,
.is-collapsed .new-chat-copy,
.is-collapsed .nav-title,
.is-collapsed .nav-item span,
.is-collapsed .recent-context,
.is-collapsed .account-copy {
  display: none;
}

.is-collapsed .app-sidebar {
  padding: 12px 8px;
}

.is-collapsed .brand-row,
.is-collapsed .brand-button,
.is-collapsed .new-chat-button,
.is-collapsed .nav-item {
  justify-content: center;
}

.is-collapsed .brand-row {
  flex-direction: column;
  gap: 8px;
}

.is-collapsed .new-chat-button,
.is-collapsed .nav-item {
  padding: 0;
}

.is-collapsed .account-card {
  grid-template-columns: 1fr;
  justify-items: center;
}

@media (max-width: 980px) {
  .app-topbar {
    padding: 0 12px;
  }

  .workspace-strip {
    justify-content: flex-end;
  }

  .workspace-chip small {
    display: none;
  }

  .workspace-chip:nth-child(n + 3) {
    display: none;
  }

  .workspace-strip {
    display: none;
  }

  .top-actions .n-tag {
    display: none;
  }

  .app-content {
    padding: 18px;
  }

  .app-content-full {
    padding: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-shell,
  .app-sidebar {
    transition: none;
  }
}
</style>
