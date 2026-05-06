<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-notification-provider>
      <n-message-provider>
        <n-layout v-if="auth.isLoggedIn" has-sider style="height: 100vh">
          <n-layout-sider bordered :width="200" :collapsed-width="64" collapse-mode="width" :collapsed="collapsed" show-trigger @collapse="collapsed = true" @expand="collapsed = false">
            <div class="sider-header">
              <span class="brand-mark">DR</span>
              <span v-if="!collapsed" class="brand-text">运维机器人</span>
            </div>
            <n-menu :options="menuOptions" :collapsed="collapsed" :value="route.name as string" @update:value="onMenuSelect" />
          </n-layout-sider>
          <n-layout>
            <n-layout-header bordered style="height: 48px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px">
              <span>{{ route.meta.title }}</span>
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
import { ref, h, computed } from 'vue'
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
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const appFontFamily = 'Inter, "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: appFontFamily,
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
</script>

<style>
body,
#app {
  margin: 0;
  font-family: Inter, "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.sider-header {
  height: 48px;
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
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border: 1px solid rgba(113, 139, 182, 0.42);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(67, 89, 124, 0.95), rgba(28, 36, 52, 0.95));
  color: #f3f7ff;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
}
.brand-text {
  min-width: 0;
  color: #f1f5f9;
  white-space: nowrap;
}
.app-content {
  padding: 16px;
  overflow: auto;
  height: calc(100vh - 48px);
}
.app-content-full {
  padding: 0;
  overflow: hidden;
}
</style>
