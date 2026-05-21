<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-notification-provider>
      <n-message-provider>
        <n-layout v-if="auth.isLoggedIn" class="app-shell" has-sider>
          <n-layout-sider class="app-sider" bordered :width="208" :collapsed-width="64" collapse-mode="width" :collapsed="effectiveCollapsed" show-trigger @collapse="collapsed = true" @expand="collapsed = false">
            <div class="sider-header">
              <img class="brand-mark" :src="botCoreIcon" alt="">
              <span v-if="!effectiveCollapsed" class="brand-text">运维机器人</span>
            </div>
            <n-menu :options="menuOptions" :collapsed="effectiveCollapsed" :value="route.name as string" @update:value="onMenuSelect" />
          </n-layout-sider>
          <n-layout>
            <n-layout-header class="app-header" bordered>
              <div class="route-title">
                <span>{{ route.meta.title }}</span>
                <small>ChatOps Console</small>
              </div>
              <n-space align="center">
                <n-tag size="small" :type="auth.isAdmin ? 'error' : auth.isOperator ? 'warning' : 'info'">{{ auth.username }} ({{ auth.role }})</n-tag>
                <n-button text @click="auth.logout(); router.push({ name: 'Login' })">退出</n-button>
              </n-space>
            </n-layout-header>
            <n-layout-content :class="['app-content', { 'app-content-full': route.meta.fullBleed }]">
              <router-view />
            </n-layout-content>
          </n-layout>
        </n-layout>
        <router-view v-else />
      </n-message-provider>
    </n-notification-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, h, computed, onBeforeUnmount, onMounted } from 'vue'
import type { Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { darkTheme, NConfigProvider, NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NButton, NSpace, NTag, NNotificationProvider, NMessageProvider, NIcon } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import {
  ChatbubblesOutline,
  ConstructOutline,
  GitNetworkOutline,
  SettingsOutline,
  ShieldOutline,
  SpeedometerOutline,
  TimeOutline,
} from '@vicons/ionicons5'
import botCoreIcon from '@/assets/generated/bot-core.svg'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const isNarrow = ref(false)
const effectiveCollapsed = computed(() => isNarrow.value || collapsed.value)
const appFontFamily = 'Inter, "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: appFontFamily,
    primaryColor: '#22c55e',
    primaryColorHover: '#4ade80',
    primaryColorPressed: '#16a34a',
    primaryColorSuppl: '#38bdf8',
    bodyColor: '#070a0f',
    cardColor: '#0d1420',
    modalColor: '#0d1420',
    popoverColor: '#0d1420',
    borderColor: '#2a3648',
    textColorBase: '#f8fafc',
  },
}

function renderIcon(icon: Component) {
  return () => h(NIcon, { size: 18 }, { default: () => h(icon) })
}

const menuOptions = computed(() => {
  const items = [
    { label: '运维概览', key: 'Dashboard', icon: renderIcon(SpeedometerOutline) },
    { label: '智能对话', key: 'Chat', icon: renderIcon(ChatbubblesOutline) },
    { label: 'MCP 工具', key: 'MCPConfig', icon: renderIcon(ConstructOutline) },
    { label: '知识图谱', key: 'KnowledgeGraph', icon: renderIcon(GitNetworkOutline) },
    { label: 'LLM 配置', key: 'LLMConfig', icon: renderIcon(SettingsOutline) },
  ]
  if (auth.isOperator) {
    items.push({ label: '定时任务', key: 'Scheduler', icon: renderIcon(TimeOutline) })
  }
  if (auth.isAdmin) {
    items.push({ label: '权限管理', key: 'AccessControl', icon: renderIcon(ShieldOutline) })
  }
  return items
})

function onMenuSelect(key: string) {
  router.push({ name: key })
}

function syncResponsiveChrome() {
  isNarrow.value = window.innerWidth <= 900
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
body,
#app {
  margin: 0;
  font-family: Inter, "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #070a0f;
}

.app-shell {
  height: 100vh;
  background: #070a0f;
}

.app-sider {
  background: #0d1420 !important;
}

.sider-header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 12px;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid var(--n-border-color);
}
.brand-mark {
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border: 1px solid #2a3648;
  border-radius: 8px;
  object-fit: cover;
  background: #111827;
}
.brand-text {
  min-width: 0;
  color: #f1f5f9;
  white-space: nowrap;
}
.app-header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #0d1420 !important;
}
.route-title {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
  color: #f8fafc;
  font-weight: 700;
  line-height: 1.15;
}
.route-title small {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
}
.app-content {
  padding: 16px;
  overflow: auto;
  height: calc(100vh - 52px);
  background: #070a0f;
}
.app-content-full {
  padding: 0;
  overflow: hidden;
}

@media (max-width: 900px) {
  .app-header {
    gap: 8px;
    padding: 0 10px;
  }

  .route-title {
    font-size: 13px;
  }

  .route-title small {
    display: none;
  }

  .app-content {
    padding: 10px;
  }

  .app-content-full {
    padding: 0;
  }
}
</style>
