<template>
  <n-card title="定时任务管理" size="small">
    <template #header-extra>
      <n-button size="small" type="primary" @click="showCreate = true">新建任务</n-button>
    </template>
    <n-data-table :columns="columns" :data="tasks" :loading="loading" size="small" />
    <n-modal v-model:show="showCreate" title="新建定时任务" preset="dialog" positive-text="创建" negative-text="取消" @positive-click="createTask">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="任务名"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="Cron"><n-input v-model:value="form.cron_expr" placeholder="0 */30 * * * *" /></n-form-item>
        <n-form-item label="Prompt"><n-input v-model:value="form.prompt" type="textarea" :rows="3" /></n-form-item>
        <n-form-item label="通知钉钉"><n-switch v-model:value="form.notify_dingtalk" /></n-form-item>
      </n-form>
    </n-modal>
  </n-card>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NCard, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NTag, useMessage } from 'naive-ui'
import { schedulerApi } from '@/api/client'
import type { ScheduledTask } from '@/types'

const message = useMessage()
const loading = ref(false)
const tasks = ref<ScheduledTask[]>([])
const showCreate = ref(false)
const form = ref({ name: '', cron_expr: '', prompt: '', notify_dingtalk: false })

type TagType = 'default' | 'info' | 'success' | 'warning' | 'error' | 'primary'
const statusColors: Record<string, TagType> = { active: 'success', paused: 'warning', disabled: 'default' }

const columns = [
  { title: '名称', key: 'name', width: 160 },
  { title: 'Cron', key: 'cron_expr', width: 140 },
  { title: '状态', key: 'status', width: 80, render: (row: any) => h(NTag, { size: 'small', type: statusColors[row.status] || 'default' }, { default: () => row.status }) },
  { title: '上次运行', key: 'last_run_at', width: 160 },
  { title: '操作', key: 'actions', width: 140, render: (row: any) => [
    h(NButton, { size: 'tiny', onClick: () => toggleStatus(row) }, { default: () => row.status === 'active' ? '暂停' : '启用' }),
    h(NButton, { size: 'tiny', type: 'error', style: 'margin-left: 8px', onClick: () => deleteTask(row.id) }, { default: () => '删除' }),
  ]},
]

async function fetchTasks() {
  loading.value = true
  try { tasks.value = await schedulerApi.list() }
  finally { loading.value = false }
}

async function createTask() {
  try {
    await schedulerApi.create(form.value)
    message.success('任务已创建')
    showCreate.value = false
    form.value = { name: '', cron_expr: '', prompt: '', notify_dingtalk: false }
    await fetchTasks()
  } catch { message.error('创建失败') }
}

async function toggleStatus(task: ScheduledTask) {
  const newStatus = task.status === 'active' ? 'paused' : 'active'
  await schedulerApi.update(task.id, { status: newStatus })
  await fetchTasks()
}

async function deleteTask(id: string) {
  await schedulerApi.delete(id)
  await fetchTasks()
}

onMounted(fetchTasks)
</script>
