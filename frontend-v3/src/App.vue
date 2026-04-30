<template>
  <n-config-provider :theme="darkTheme">
    <n-notification-provider>
      <n-message-provider>
        <n-layout v-if="auth.isLoggedIn" has-sider style="height: 100vh">
          <n-layout-sider bordered :width="200" :collapsed-width="64" collapse-mode="width" :collapsed="collapsed" show-trigger @collapse="collapsed = true" @expand="collapsed = false">
            <div class="sider-header">
              <span v-if="!collapsed">运维机器人</span>
              <span v-else>🤖</span>
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
            <n-layout-content style="padding: 16px; overflow: auto; height: calc(100vh - 48px)">
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
import { useRoute, useRouter } from 'vue-router'
import { darkTheme, NConfigProvider, NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NButton, NSpace, NTag, NNotificationProvider, NMessageProvider } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const menuOptions = computed(() => {
  const items = [
    { label: '运维概览', key: 'Dashboard', icon: () => h('span', '📊') },
    { label: '智能对话', key: 'Chat', icon: () => h('span', '💬') },
    { label: 'MCP 工具', key: 'MCPConfig', icon: () => h('span', '🔧') },
  ]
  if (auth.isOperator) {
    items.push({ label: '定时任务', key: 'Scheduler', icon: () => h('span', '⏰') })
  }
  if (auth.isAdmin) {
    items.push({ label: '权限管理', key: 'AccessControl', icon: () => h('span', '🛡️') })
  }
  return items
})

function onMenuSelect(key: string) {
  router.push({ name: key })
}
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.sider-header { height: 48px; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 600; border-bottom: 1px solid var(--n-border-color); }
</style>
