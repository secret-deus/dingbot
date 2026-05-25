<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-notification-provider>
      <n-message-provider>
        <div v-if="auth.isLoggedIn" :class="['app-shell', { 'is-collapsed': effectiveCollapsed }]">
          <aside class="app-sidebar" aria-label="主导航" :aria-expanded="!effectiveCollapsed">
            <div class="window-dots" aria-hidden="true" />

            <div class="brand-row">
              <button class="brand-button" type="button" :aria-label="effectiveCollapsed ? '展开侧栏' : '折叠侧栏'" @click="collapsed = !collapsed">
                <span class="brand-mark">D</span>
                <span class="brand-copy">
                  <strong>Ding Robot</strong>
                  <small>ChatOps Console</small>
                </span>
              </button>
              <n-button class="collapse-button" quaternary circle :aria-label="effectiveCollapsed ? '展开侧栏' : '折叠侧栏'" @click="collapsed = !collapsed">
                <template #icon>
                  <n-icon><component :is="effectiveCollapsed ? ChevronForwardOutline : ChevronBackOutline" /></n-icon>
                </template>
              </n-button>
            </div>

            <button class="new-chat-button" type="button" @click="router.push({ name: 'Chat' })">
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
                @click="onMenuSelect(item.key)"
              >
                <n-icon :size="18"><component :is="item.icon" /></n-icon>
                <span>{{ item.label }}</span>
              </button>
            </nav>

            <section class="recent-context" aria-label="最近上下文">
              <div class="nav-title">最近上下文</div>
              <div class="thread-list">
                <button v-for="thread in recentThreads" :key="thread" type="button" class="thread-item" @click="router.push({ name: 'Chat' })">
                  {{ thread }}
                </button>
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
                <span>{{ route.meta.permission === 'admin' ? '管理' : '工作区' }}</span>
                <span>/</span>
                <strong>{{ route.meta.title }}</strong>
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
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
  GitNetworkOutline,
  LogOutOutline,
  SettingsOutline,
  ShieldOutline,
  SpeedometerOutline,
  TimeOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const isNarrow = ref(false)
const effectiveCollapsed = computed(() => isNarrow.value || collapsed.value)

const appFontFamily = '"Tiempos Text", "Ivar Text", "Georgia", "Times New Roman", "Songti SC", "STSong", "SimSun", serif'
const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: appFontFamily,
    primaryColor: '#c96442',
    primaryColorHover: '#d46d49',
    primaryColorPressed: '#9f432d',
    primaryColorSuppl: '#c96442',
    bodyColor: '#f7f5ef',
    cardColor: '#fffdf7',
    modalColor: '#fffdf7',
    popoverColor: '#fffdf7',
    tableColor: '#fffdf7',
    borderColor: '#ded8cd',
    textColorBase: '#191814',
    textColor1: '#191814',
    textColor2: '#4f4a43',
    textColor3: '#7b756a',
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
    thColor: '#fbf8f1',
    tdColor: '#fffdf7',
    tdColorHover: '#fbf6ee',
    borderColor: '#e9e3d8',
    thTextColor: '#7b756a',
    tdTextColor: '#4f4a43',
  },
  Input: {
    color: '#fffdf8',
    colorFocus: '#fffdf8',
    border: '1px solid #ded8cd',
    borderHover: '1px solid #cbbdaa',
    borderFocus: '1px solid #b7674c',
    boxShadowFocus: '0 0 0 3px rgba(201, 100, 66, 0.14)',
    borderRadius: '8px',
  },
  Select: {
    peers: {
      InternalSelection: {
        color: '#fffdf8',
        colorActive: '#fffdf8',
        border: '1px solid #ded8cd',
        borderHover: '1px solid #cbbdaa',
        borderActive: '1px solid #b7674c',
        boxShadowActive: '0 0 0 3px rgba(201, 100, 66, 0.14)',
        borderRadius: '8px',
      },
    },
  },
}

const recentThreads = [
  'default namespace 服务端点巡检',
  'ToolSearch 目录恢复验证',
  'ECS CPU 监控数据读取',
  'DingTalk 调度通知检查',
  'K8s endpoints 异常排查',
]

const menuItems = computed<Array<{ label: string; key: string; icon: Component }>>(() => {
  const items = [
    { label: '运维概览', key: 'Dashboard', icon: SpeedometerOutline },
    { label: '智能对话', key: 'Chat', icon: ChatbubblesOutline },
    { label: 'MCP 工具', key: 'MCPConfig', icon: ConstructOutline },
    { label: '知识图谱', key: 'KnowledgeGraph', icon: GitNetworkOutline },
    { label: 'LLM 配置', key: 'LLMConfig', icon: SettingsOutline },
  ]
  if (auth.isOperator) {
    items.push({ label: '定时任务', key: 'Scheduler', icon: TimeOutline })
  }
  if (auth.isAdmin) {
    items.push({ label: '权限管理', key: 'AccessControl', icon: ShieldOutline })
  }
  return items
})

const userInitial = computed(() => (auth.username || 'U').slice(0, 1).toUpperCase())

function isActive(key: string) {
  if (key === 'AccessControl') return route.name === 'AccessControl' || route.name === 'AuditLogs'
  return route.name === key
}

function onMenuSelect(key: string) {
  router.push({ name: key })
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

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncResponsiveChrome)
})
</script>

<style>
.app-shell {
  display: grid;
  grid-template-columns: 272px minmax(0, 1fr);
  width: 100vw;
  height: 100dvh;
  min-height: 0;
  max-height: 100dvh;
  overflow: hidden;
  border: 1px solid rgba(25, 24, 20, 0.08);
  background: var(--dr-surface);
  color: var(--dr-text);
  transition: grid-template-columns 180ms ease;
}

.app-shell.is-collapsed {
  grid-template-columns: 72px minmax(0, 1fr);
}

.app-sidebar {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 12px;
  padding: 14px 12px;
  border-right: 1px solid var(--dr-border);
  background: var(--dr-sidebar);
  transition: padding 180ms ease;
}

.window-dots {
  width: 44px;
  height: 12px;
  margin: 0 0 2px 4px;
  display: flex;
  gap: 6px;
  opacity: 0.8;
}

.window-dots::before {
  width: 36px;
  height: 8px;
  border-radius: 999px;
  background: #d7cab9;
  content: "";
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
  color: var(--dr-text);
  cursor: pointer;
  text-align: left;
}

.brand-mark {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid #d4cbbd;
  border-radius: var(--dr-radius);
  background: #fffdf8;
  color: var(--dr-accent-deep);
  font-size: var(--dr-text-sm);
  font-weight: 680;
}

.brand-copy {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.brand-copy strong {
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 620;
  line-height: 1.15;
}

.brand-copy small,
.crumbs,
.account-copy span {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}

.collapse-button {
  flex: 0 0 auto;
  min-width: 36px;
}

.new-chat-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid #d9d1c4;
  border-radius: var(--dr-radius);
  background: #fffdf7;
  color: var(--dr-text);
  box-shadow: 0 1px 1px rgba(25, 24, 20, 0.04);
  cursor: pointer;
  font-weight: 570;
}

.new-chat-button:hover,
.nav-item:hover,
.thread-item:hover {
  background: var(--dr-surface-hover);
  color: var(--dr-text);
}

.new-chat-button:hover {
  border-color: #cabba7;
  box-shadow: 0 8px 20px rgba(25, 24, 20, 0.06);
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
  color: var(--dr-text-soft);
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
}

.nav-item.active {
  background: #faf1ea;
  color: var(--dr-text);
  font-weight: 610;
  box-shadow: inset 0 0 0 1px rgba(25, 24, 20, 0.05), 0 1px 0 rgba(255, 255, 255, 0.68);
}

.nav-item.active::before {
  position: absolute;
  left: -4px;
  width: 3px;
  height: 18px;
  border-radius: 999px;
  background: var(--dr-accent);
  content: "";
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
  min-height: 34px;
  padding: 7px 9px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--dr-text-sm);
}

.account-card {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) 32px;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 8px 0 0;
  border-top: 1px solid #ded5c7;
}

.avatar {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background: #d8d0c3;
  color: var(--dr-text);
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
  color: var(--dr-text-soft);
  font-size: var(--dr-text-sm);
  font-weight: 610;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-main {
  display: flex;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  flex-direction: column;
  background: var(--dr-bg);
}

.app-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex: 0 0 56px;
  min-height: 56px;
  padding: 0 22px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: rgba(250, 247, 241, 0.86);
  backdrop-filter: blur(12px);
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

.top-actions {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 8px;
}

.app-content {
  min-height: 0;
  flex: 1 1 auto;
  overflow: auto;
  padding: 28px;
  background: var(--dr-bg);
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
