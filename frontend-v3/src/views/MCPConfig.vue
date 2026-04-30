<template>
  <n-card title="MCP 工具管理" size="small">
    <template #header-extra>
      <n-button size="small" @click="mcpStore.fetchTools()">刷新</n-button>
    </template>
    <n-spin v-if="mcpStore.loading" />
    <n-data-table v-else :columns="columns" :data="mcpStore.tools" :pagination="{ pageSize: 20 }" size="small" />
  </n-card>
</template>

<script setup lang="ts">
import { onMounted, h } from 'vue'
import { NCard, NButton, NSpin, NDataTable, NTag } from 'naive-ui'
import { useMcpStore } from '@/stores/mcp'

const mcpStore = useMcpStore()

const columns = [
  { title: '工具名', key: 'name', width: 200 },
  { title: '描述', key: 'description' },
  { title: '来源', key: 'server', width: 120, render: (row: any) => h(NTag, { size: 'small', type: row.server === 'builtin' ? 'info' : 'success' }, { default: () => row.server }) },
]

onMounted(() => mcpStore.fetchTools())
</script>
