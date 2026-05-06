<template>
  <n-grid :cols="4" :x-gap="12" :y-gap="12">
    <n-gi>
      <n-card title="集群状态" size="small">
        <n-spin v-if="loading" />
        <template v-else>
          <n-descriptions label-placement="left" :column="1" size="small">
            <n-descriptions-item label="Nodes">{{ health.mcp_servers ? Object.keys(health.mcp_servers).length : 0 }}</n-descriptions-item>
            <n-descriptions-item label="LLM">
              <n-tag :type="health.llm_enabled ? 'success' : 'error'" size="small">{{ health.llm_enabled ? '已启用' : '未启用' }}</n-tag>
            </n-descriptions-item>
          </n-descriptions>
        </template>
      </n-card>
    </n-gi>
    <n-gi>
      <n-card title="MCP 工具" size="small">
        <n-spin v-if="mcpLoading" />
        <template v-else>
          <div style="font-size: 28px; font-weight: 600; text-align: center">{{ tools.length }}</div>
          <div style="text-align: center; color: #999; font-size: 12px">已注册工具数</div>
        </template>
      </n-card>
    </n-gi>
    <n-gi>
      <n-card title="定时任务" size="small">
        <div style="font-size: 28px; font-weight: 600; text-align: center">{{ taskCount }}</div>
        <div style="text-align: center; color: #999; font-size: 12px">活跃任务</div>
      </n-card>
    </n-gi>
    <n-gi>
      <n-card title="快捷操作" size="small">
        <n-space vertical>
          <n-button block @click="$router.push('/chat')">开始对话</n-button>
          <n-button block @click="$router.push('/llm-config')">LLM 配置</n-button>
          <n-button block @click="refresh">刷新状态</n-button>
        </n-space>
      </n-card>
    </n-gi>
    <n-gi :span="4">
      <n-card title="MCP 服务器状态" size="small">
        <n-data-table :columns="serverColumns" :data="serverData" size="small" />
      </n-card>
    </n-gi>
  </n-grid>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NGrid, NGi, NCard, NDescriptions, NDescriptionsItem, NTag, NButton, NSpace, NSpin, NDataTable, useMessage } from 'naive-ui'
import { systemApi, schedulerApi } from '@/api/client'
import { useMcpStore } from '@/stores/mcp'
import type { HealthStatus, MCPTool } from '@/types'

const message = useMessage()
const mcpStore = useMcpStore()
const loading = ref(true)
const mcpLoading = ref(true)
const health = ref<HealthStatus>({ status: '', version: '', llm_enabled: false, mcp_servers: {} })
const tools = ref<MCPTool[]>([])
const taskCount = ref(0)

const serverColumns = [
  { title: '服务器', key: 'name' },
  { title: '状态', key: 'connected', render: (row: any) => row.connected ? '✅ 已连接' : '❌ 未连接' },
  { title: '工具数', key: 'tools' },
]
const serverData = ref<{ name: string; connected: boolean; tools: number }[]>([])

async function refresh() {
  loading.value = true
  try {
    health.value = await systemApi.health()
    serverData.value = Object.entries(health.value.mcp_servers || {}).map(([name, info]) => ({
      name, connected: info.connected, tools: info.tools,
    }))
  } catch { message.error('获取状态失败') }
  finally { loading.value = false }

  mcpLoading.value = true
  try {
    await mcpStore.fetchTools()
    tools.value = mcpStore.tools
  } finally { mcpLoading.value = false }

  try {
    const tasks = await schedulerApi.list()
    taskCount.value = tasks.filter((t: any) => t.status === 'active').length
  } catch { /* ignore */ }
}

onMounted(refresh)
</script>
