<template>
  <div class="scheduler-page">
    <div class="page-header">
      <div>
        <div class="page-title">定时任务管理</div>
        <div class="page-subtitle">任务调度、执行记录与钉钉通知</div>
      </div>
      <n-button size="small" type="primary" @click="showCreate = true">新建任务</n-button>
    </div>

    <n-data-table :columns="columns" :data="tasks" :loading="loading" size="small" />

    <n-modal v-model:show="showCreate" title="新建定时任务" preset="dialog" positive-text="创建" negative-text="取消" @positive-click="createTask">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="任务名"><n-input v-model:value="form.name" :input-props="{ name: 'task-name' }" /></n-form-item>
        <n-form-item label="Cron"><n-input v-model:value="form.cron_expr" placeholder="0 */30 * * * *" :input-props="{ name: 'cron-expr' }" /></n-form-item>
        <n-form-item label="Prompt"><n-input v-model:value="form.prompt" type="textarea" :rows="3" :input-props="{ name: 'task-prompt' }" /></n-form-item>
        <n-form-item label="通知钉钉"><n-switch v-model:value="form.notify_dingtalk" /></n-form-item>
      </n-form>
    </n-modal>

    <n-modal v-model:show="showExecutions" preset="card" title="执行记录" style="width: min(900px, 92vw)">
      <n-data-table :columns="executionColumns" :data="executions" :loading="executionLoading" size="small" />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NTag, useMessage } from 'naive-ui'
import { schedulerApi } from '@/api/client'
import type { ScheduledTask, TaskExecution } from '@/types'

const message = useMessage()
const loading = ref(false)
const tasks = ref<ScheduledTask[]>([])
const showCreate = ref(false)
const showExecutions = ref(false)
const executionLoading = ref(false)
const executions = ref<TaskExecution[]>([])
const form = ref({ name: '', cron_expr: '', prompt: '', notify_dingtalk: false })

type TagType = 'default' | 'info' | 'success' | 'warning' | 'error' | 'primary'
const statusColors: Record<string, TagType> = { active: 'success', paused: 'warning', disabled: 'default' }

const columns = [
  { title: '名称', key: 'name', width: 160 },
  { title: 'Cron', key: 'cron_expr', width: 140 },
  { title: '状态', key: 'status', width: 80, render: (row: any) => h(NTag, { size: 'small', type: statusColors[row.status] || 'default' }, { default: () => row.status }) },
  { title: '通知', key: 'notify_dingtalk', width: 80, render: (row: ScheduledTask) => h(NTag, { size: 'small', type: row.notify_dingtalk ? 'success' : 'default' }, { default: () => row.notify_dingtalk ? '钉钉' : '关闭' }) },
  { title: '上次运行', key: 'last_run_at', width: 160 },
  { title: '最近结果', key: 'last_result', ellipsis: { tooltip: true } },
  { title: '操作', key: 'actions', width: 240, render: (row: ScheduledTask) => [
    h(NButton, { size: 'tiny', type: 'primary', onClick: () => runTask(row) }, { default: () => '运行' }),
    h(NButton, { size: 'tiny', style: 'margin-left: 8px', onClick: () => showHistory(row) }, { default: () => '记录' }),
    h(NButton, { size: 'tiny', style: 'margin-left: 8px', onClick: () => toggleStatus(row) }, { default: () => row.status === 'active' ? '暂停' : '启用' }),
    h(NButton, { size: 'tiny', type: 'error', style: 'margin-left: 8px', onClick: () => deleteTask(row.id) }, { default: () => '删除' }),
  ]},
]

const executionColumns = [
  { title: '开始时间', key: 'started_at', width: 170 },
  { title: '结束时间', key: 'finished_at', width: 170 },
  { title: '状态', key: 'status', width: 90, render: (row: TaskExecution) => h(NTag, { size: 'small', type: row.status === 'success' ? 'success' : row.status === 'failed' ? 'error' : 'warning' }, { default: () => row.status }) },
  { title: '结果', key: 'result', ellipsis: { tooltip: true } },
  { title: '错误', key: 'error', ellipsis: { tooltip: true } },
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

async function runTask(task: ScheduledTask) {
  const res = await schedulerApi.run(task.id)
  if (res.status === 'success') {
    message.success('任务执行成功')
  } else {
    message.error(res.error || '任务执行失败')
  }
  await fetchTasks()
  await showHistory(task)
}

async function showHistory(task: ScheduledTask) {
  showExecutions.value = true
  executionLoading.value = true
  try {
    executions.value = await schedulerApi.executions(task.id)
  } finally {
    executionLoading.value = false
  }
}

async function deleteTask(id: string) {
  await schedulerApi.delete(id)
  await fetchTasks()
}

onMounted(fetchTasks)
</script>

<style scoped>
.scheduler-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--dr-text);
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  color: var(--dr-text);
  font-size: var(--dr-text-2xl);
  font-weight: 620;
  line-height: 1.12;
}
.page-subtitle {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-md);
  margin-top: 7px;
}

.scheduler-page :deep(.n-data-table) {
  overflow: hidden;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface-lift);
  box-shadow: var(--dr-shadow);
}
</style>
