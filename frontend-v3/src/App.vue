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

const appFontFamily = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif'
const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: appFontFamily,
    primaryColor: '#2f6fed',
    primaryColorHover: '#1f63e8',
    primaryColorPressed: '#174fc3',
    primaryColorSuppl: '#2f6fed',
    bodyColor: '#f4f7fb',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    tableColor: '#ffffff',
    borderColor: '#d7dee8',
    textColorBase: '#171717',
    textColor1: '#171717',
    textColor2: '#3f4248',
    textColor3: '#70727a',
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
    tdColorHover: '#f6f8fb',
    borderColor: '#e2e8f0',
    thTextColor: '#70727a',
    tdTextColor: '#3f4248',
  },
  Input: {
    color: '#ffffff',
    colorFocus: '#ffffff',
    border: '1px solid #d7dee8',
    borderHover: '1px solid #bfc7d3',
    borderFocus: '1px solid #2f6fed',
    boxShadowFocus: '0 0 0 3px rgba(47, 111, 237, 0.18)',
    borderRadius: '8px',
  },
  Select: {
    peers: {
      InternalSelection: {
        color: '#ffffff',
        colorActive: '#ffffff',
        border: '1px solid #d7dee8',
        borderHover: '1px solid #bfc7d3',
        borderActive: '1px solid #2f6fed',
        boxShadowActive: '0 0 0 3px rgba(47, 111, 237, 0.18)',
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
  border-right: 1px solid rgba(155, 215, 255, 0.18);
  background:
    linear-gradient(180deg, #0a0d14 0%, #111621 52%, #0a0d14 100%),
    var(--dr-sidebar);
  box-shadow: inset -1px 0 0 rgba(125, 227, 193, 0.08);
  transition: padding 180ms ease;
}

.app-sidebar::before {
  position: absolute;
  inset: 0;
  z-index: -2;
  background:
    linear-gradient(115deg, rgba(155, 215, 255, 0.07) 0 1px, transparent 1px 58px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(0deg, rgba(255, 255, 255, 0.026) 1px, transparent 1px);
  background-size: 100% 100%, 28px 28px, 28px 28px;
  content: "";
  opacity: 0.78;
}

.app-sidebar::after {
  position: absolute;
  top: 72px;
  right: -42px;
  z-index: -1;
  width: 190px;
  height: 320px;
  background:
    linear-gradient(135deg, rgba(155, 215, 255, 0.12), rgba(111, 140, 255, 0.05) 46%, transparent 47%),
    linear-gradient(135deg, transparent 0 56%, rgba(125, 227, 193, 0.1) 56.4%, transparent 66%);
  clip-path: polygon(22% 0, 100% 0, 78% 100%, 0 100%);
  content: "";
}

.app-sidebar > * {
  position: relative;
  z-index: 1;
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
  background: linear-gradient(90deg, var(--dr-neon-blue) 0 8px, var(--dr-neon-cyan) 8px 18px, var(--dr-neon-mint) 18px 28px);
  box-shadow: 0 0 16px rgba(155, 215, 255, 0.16);
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
  border: 1px solid rgba(155, 215, 255, 0.28);
  border-radius: var(--dr-radius);
  background:
    linear-gradient(135deg, rgba(155, 215, 255, 0.16), rgba(125, 227, 193, 0.08)),
    #0f1420;
  color: #f7fbff;
  font-size: var(--dr-text-sm);
  font-weight: 680;
  box-shadow: 0 0 0 1px rgba(155, 215, 255, 0.06), 0 0 18px rgba(111, 140, 255, 0.12);
}

.brand-copy {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.brand-copy strong {
  color: var(--dr-sidebar-text);
  font-size: var(--dr-text-lg);
  font-weight: 620;
  line-height: 1.15;
  text-shadow: 0 0 18px rgba(155, 215, 255, 0.14);
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
  border: 1px solid rgba(155, 215, 255, 0.2);
  border-radius: var(--dr-radius);
  background:
    linear-gradient(135deg, rgba(155, 215, 255, 0.08), rgba(125, 227, 193, 0.04)),
    rgba(255, 255, 255, 0.06);
  color: var(--dr-sidebar-text);
  box-shadow: none;
  cursor: pointer;
  font-weight: 570;
  overflow: hidden;
}

.new-chat-button::before {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(155, 215, 255, 0.1), transparent);
  content: "";
  opacity: 0;
  transition: opacity 160ms ease;
}

.new-chat-button:hover,
.nav-item:hover,
.thread-item:hover {
  background: rgba(155, 215, 255, 0.07);
  color: var(--dr-sidebar-text);
}

.new-chat-button:hover {
  border-color: rgba(155, 215, 255, 0.34);
  box-shadow: 0 0 0 1px rgba(155, 215, 255, 0.06), 0 0 24px rgba(111, 140, 255, 0.12);
}

.new-chat-button:hover::before {
  opacity: 1;
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
  transition: background-color 160ms ease, box-shadow 160ms ease, color 160ms ease;
}

.nav-item.active {
  background:
    linear-gradient(90deg, rgba(155, 215, 255, 0.16), rgba(111, 140, 255, 0.08) 54%, rgba(125, 227, 193, 0.05)),
    rgba(255, 255, 255, 0.06);
  color: var(--dr-sidebar-text);
  font-weight: 610;
  clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%);
  box-shadow:
    inset 0 0 0 1px rgba(155, 215, 255, 0.2),
    0 0 24px rgba(111, 140, 255, 0.1);
}

.nav-item.active::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 9px;
  background: linear-gradient(135deg, rgba(155, 215, 255, 0.8), rgba(125, 227, 193, 0.18) 70%, transparent 71%);
  clip-path: polygon(0 0, 100% 0, 42% 100%, 0 100%);
  content: "";
  opacity: 0.84;
}

.nav-item.active::after {
  display: none;
}

.nav-item.active .n-icon {
  color: var(--dr-neon-cyan);
  filter: drop-shadow(0 0 8px rgba(155, 215, 255, 0.26));
}

.recent-context {
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.nav-title {
  margin: 14px 8px 6px;
  color: color-mix(in srgb, var(--dr-neon-cyan) 60%, var(--dr-sidebar-muted) 40%);
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
  border-top: 1px solid rgba(155, 215, 255, 0.14);
}

.avatar {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background:
    linear-gradient(135deg, rgba(155, 215, 255, 0.14), rgba(125, 227, 193, 0.08)),
    rgba(255, 255, 255, 0.1);
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
  background: linear-gradient(135deg, #f4f7fb 0%, #ffffff 58%, #eef4f8 100%);
}

.app-main::before {
  position: absolute;
  inset: 0;
  z-index: -2;
  background:
    linear-gradient(135deg, rgba(17, 17, 22, 0.16) 0 27%, transparent 27.2%),
    linear-gradient(135deg, rgba(47, 111, 237, 0.1) 0 38%, transparent 38.2%);
  content: "";
}

.app-main::after {
  position: absolute;
  inset: 0;
  z-index: -1;
  background:
    linear-gradient(135deg, transparent 0 31%, rgba(255, 255, 255, 0.78) 31.2% 100%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.02));
  content: "";
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
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
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
