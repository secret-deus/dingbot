<template>
  <n-card title="权限管理" size="small">
    <n-tabs v-model:value="activeTab">
      <n-tab-pane name="users" tab="用户管理">
        <p style="color: #999">用户管理功能开发中，当前可通过 API 管理。</p>
      </n-tab-pane>
      <n-tab-pane name="audit" tab="审计日志">
        <n-data-table :columns="auditColumns" :data="auditLogs" :loading="auditLoading" size="small" />
      </n-tab-pane>
    </n-tabs>
  </n-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NCard, NTabs, NTabPane, NDataTable } from 'naive-ui'
import { systemApi } from '@/api/client'
import type { AuditLog } from '@/types'

const auditLogs = ref<AuditLog[]>([])
const auditLoading = ref(false)
const route = useRoute()
const activeTab = ref(route.name === 'AuditLogs' || route.query.tab === 'audit' ? 'audit' : 'users')

const auditColumns = [
  { title: '时间', key: 'created_at', width: 170 },
  { title: '操作人', key: 'actor', width: 100 },
  { title: '操作', key: 'action', width: 140 },
  { title: '资源', key: 'resource' },
  { title: '结果', key: 'result', width: 80 },
  { title: 'IP', key: 'ip', width: 130 },
]

async function fetchAudit() {
  auditLoading.value = true
  try { auditLogs.value = await systemApi.auditLogs({ limit: 50 }) }
  finally { auditLoading.value = false }
}

onMounted(fetchAudit)
</script>
