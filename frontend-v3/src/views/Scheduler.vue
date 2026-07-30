<template>
  <div class="scheduler-page" :inert="taskBusy" :aria-busy="taskBusy">
    <div class="page-header">
      <div>
        <div class="page-title">定时任务管理</div>
        <div class="page-subtitle">任务调度、执行记录与钉钉通知</div>
      </div>
      <n-button size="small" type="primary" :disabled="taskBusy" @click="showCreate = true">新建任务</n-button>
    </div>

    <section class="scheduler-summary" aria-label="定时任务状态">
      <article class="summary-tile">
        <span>Tasks</span>
        <strong>{{ tasks.length }}</strong>
        <small>registered schedules</small>
      </article>
      <article class="summary-tile">
        <span>Active</span>
        <strong>{{ activeTaskCount }}</strong>
        <small>ready to run</small>
      </article>
      <article class="summary-tile">
        <span>Paused</span>
        <strong>{{ pausedTaskCount }}</strong>
        <small>manual resume required</small>
      </article>
      <article class="summary-tile">
        <span>DingTalk</span>
        <strong>{{ notifyTaskCount }}</strong>
        <small>notification enabled</small>
      </article>
    </section>

    <section class="scheduler-focus" aria-label="调度器运行概览">
      <article :class="['focus-card', readinessTone]">
        <span class="focus-kicker">Run readiness</span>
        <strong>{{ readinessTitle }}</strong>
        <small>{{ readinessDetail }}</small>
      </article>
      <article class="focus-card">
        <span class="focus-kicker">Next operator action</span>
        <strong>{{ nextActionTitle }}</strong>
        <small>{{ nextActionDetail }}</small>
      </article>
      <article class="focus-card">
        <span class="focus-kicker">Latest result</span>
        <strong>{{ latestResultTitle }}</strong>
        <small>{{ latestResultDetail }}</small>
      </article>
    </section>

    <section class="task-panel">
      <div class="panel-head">
        <div>
          <div class="panel-title">Schedules</div>
          <div class="panel-subtitle">Cron tasks and latest execution result.</div>
        </div>
      </div>
      <div v-if="tasks.length" class="task-card-grid" aria-label="任务运行卡片">
        <article v-for="task in tasks" :key="task.id" class="task-card">
          <div>
            <span :class="['task-state-dot', task.status]" aria-hidden="true" />
            <strong>{{ task.name }}</strong>
            <n-tag size="small" :type="statusColors[task.status] || 'default'">{{ task.status }}</n-tag>
          </div>
          <p>{{ task.prompt || '未填写任务 Prompt' }}</p>
          <dl>
            <div>
              <dt>Cron</dt>
              <dd>{{ task.cron_expr }}</dd>
            </div>
            <div>
              <dt>Notify</dt>
              <dd>{{ task.notify_dingtalk ? 'DingTalk on' : 'off' }}</dd>
            </div>
            <div>
              <dt>Last run</dt>
              <dd>{{ formatRunAt(task.last_run_at) }}</dd>
            </div>
          </dl>
          <small>{{ task.last_result || '暂无执行结果' }}</small>
        </article>
      </div>
      <n-data-table :columns="columns" :data="tasks" :loading="loading" size="small" />
    </section>

    <n-modal
      v-model:show="showCreate"
      title="新建定时任务"
      preset="dialog"
      positive-text="创建"
      negative-text="取消"
      :positive-button-props="createPositiveButtonProps"
      @positive-click="createTask"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item label="任务名" :validation-status="fieldStatus(form.name)" :feedback="fieldFeedback(form.name, '请输入任务名')">
          <n-input v-model:value="form.name" placeholder="default namespace 巡检" :disabled="taskBusy" :input-props="{ name: 'task-name' }" />
        </n-form-item>
        <n-form-item label="Cron" :validation-status="fieldStatus(form.cron_expr)" :feedback="fieldFeedback(form.cron_expr, '请输入 Cron 表达式')">
          <n-input v-model:value="form.cron_expr" placeholder="0 */30 * * * *" :disabled="taskBusy" :input-props="{ name: 'cron-expr' }" />
        </n-form-item>
        <n-form-item label="Prompt" :validation-status="fieldStatus(form.prompt)" :feedback="fieldFeedback(form.prompt, '请输入任务 Prompt')">
          <n-input v-model:value="form.prompt" type="textarea" :rows="3" placeholder="描述巡检目标、范围和输出要求" :disabled="taskBusy" :input-props="{ name: 'task-prompt' }" />
        </n-form-item>
        <n-form-item label="通知钉钉"><n-switch v-model:value="form.notify_dingtalk" :disabled="taskBusy" /></n-form-item>
      </n-form>
    </n-modal>

    <n-modal v-model:show="showExecutions" preset="card" title="执行记录" style="width: min(900px, 92vw)">
      <n-data-table :columns="executionColumns" :data="executions" :loading="executionLoading" size="small" />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, h } from 'vue'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NTag, NPopconfirm, useMessage } from 'naive-ui'
import { schedulerApi } from '@/api/client'
import type { ScheduledTask, TaskExecution } from '@/types'

const message = useMessage()
const loading = ref(false)
const tasks = ref<ScheduledTask[]>([])
const showCreate = ref(false)
const showExecutions = ref(false)
const executionLoading = ref(false)
const createLoading = ref(false)
const taskActionLoading = ref(false)
const executions = ref<TaskExecution[]>([])
const form = ref({ name: '', cron_expr: '', prompt: '', notify_dingtalk: false })
const canCreateTask = computed(() => Boolean(form.value.name.trim() && form.value.cron_expr.trim() && form.value.prompt.trim()))
const taskBusy = computed(() => loading.value || createLoading.value || taskActionLoading.value)
const createPositiveButtonProps = computed(() => ({ disabled: !canCreateTask.value || taskBusy.value, loading: createLoading.value }))
const activeTaskCount = computed(() => tasks.value.filter((task) => task.status === 'active').length)
const pausedTaskCount = computed(() => tasks.value.filter((task) => task.status === 'paused').length)
const notifyTaskCount = computed(() => tasks.value.filter((task) => task.notify_dingtalk).length)
const latestTask = computed(() =>
  [...tasks.value]
    .filter((task) => task.last_run_at)
    .sort((a, b) => String(b.last_run_at).localeCompare(String(a.last_run_at)))[0],
)
const readinessTone = computed(() => {
  if (!tasks.value.length) return 'muted'
  if (activeTaskCount.value > 0) return 'ready'
  return 'paused'
})
const readinessTitle = computed(() => {
  if (!tasks.value.length) return 'No schedules yet'
  if (activeTaskCount.value > 0) return `${activeTaskCount.value} active schedule${activeTaskCount.value > 1 ? 's' : ''}`
  return 'All schedules paused'
})
const readinessDetail = computed(() => {
  if (!tasks.value.length) return 'Create a schedule to start recurring ChatOps checks.'
  if (activeTaskCount.value > 0) return `${pausedTaskCount.value} paused, ${notifyTaskCount.value} with DingTalk notification.`
  return 'Resume a schedule when the prompt and notification target are ready.'
})
const nextActionTitle = computed(() => {
  if (!tasks.value.length) return 'Create first schedule'
  if (pausedTaskCount.value > 0) return 'Review paused schedules'
  return 'Inspect latest execution'
})
const nextActionDetail = computed(() => {
  if (!tasks.value.length) return 'Use 新建任务 to define cron, prompt, and DingTalk notification.'
  if (pausedTaskCount.value > 0) return `${pausedTaskCount.value} schedule${pausedTaskCount.value > 1 ? 's' : ''} need manual resume before automatic runs.`
  return 'Open 执行记录 to confirm the most recent output and failures.'
})
const latestResultTitle = computed(() => latestTask.value?.name || 'No run history')
const latestResultDetail = computed(() => {
  if (!latestTask.value) return 'Run a task manually or wait for the next cron execution.'
  return latestTask.value.last_result || `Last run at ${formatRunAt(latestTask.value.last_run_at)}.`
})

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
    h(NPopconfirm, {
      positiveText: '运行',
      negativeText: '取消',
      positiveButtonProps: { type: 'primary', size: 'tiny', disabled: taskBusy.value },
      negativeButtonProps: { size: 'tiny' },
      onPositiveClick: () => runTask(row),
    }, {
      trigger: () => h(NButton, { size: 'tiny', type: 'primary', disabled: taskBusy.value }, { default: () => '运行' }),
      default: () => `运行任务「${row.name || row.id}」？`,
    }),
    h(NButton, { size: 'tiny', style: 'margin-left: 8px', onClick: () => showHistory(row) }, { default: () => '记录' }),
    h(NPopconfirm, {
      positiveText: row.status === 'active' ? '暂停' : '启用',
      negativeText: '取消',
      positiveButtonProps: { type: row.status === 'active' ? 'warning' : 'primary', size: 'tiny', disabled: taskBusy.value },
      negativeButtonProps: { size: 'tiny' },
      onPositiveClick: () => toggleStatus(row),
    }, {
      trigger: () => h(NButton, { size: 'tiny', style: 'margin-left: 8px', disabled: taskBusy.value }, { default: () => row.status === 'active' ? '暂停' : '启用' }),
      default: () => `${row.status === 'active' ? '暂停' : '启用'}任务「${row.name || row.id}」？`,
    }),
    h(NPopconfirm, {
      positiveText: '删除',
      negativeText: '取消',
      positiveButtonProps: { type: 'error', size: 'tiny', disabled: taskBusy.value },
      negativeButtonProps: { size: 'tiny' },
      onPositiveClick: () => deleteTask(row.id),
    }, {
      trigger: () => h(NButton, { size: 'tiny', type: 'error', style: 'margin-left: 8px', disabled: taskBusy.value }, { default: () => '删除' }),
      default: () => `删除任务「${row.name || row.id}」？`,
    }),
  ]},
]

const executionColumns = [
  { title: '开始时间', key: 'started_at', width: 170 },
  { title: '结束时间', key: 'finished_at', width: 170 },
  { title: '状态', key: 'status', width: 90, render: (row: TaskExecution) => h(NTag, { size: 'small', type: row.status === 'success' ? 'success' : row.status === 'failed' ? 'error' : 'warning' }, { default: () => row.status }) },
  { title: '结果', key: 'result', ellipsis: { tooltip: true } },
  { title: '错误', key: 'error', ellipsis: { tooltip: true } },
]

function formatRunAt(value?: string) {
  if (!value) return 'never'
  return value.replace('T', ' ').slice(0, 19)
}

async function fetchTasks() {
  if (loading.value) return

  loading.value = true
  try { tasks.value = await schedulerApi.list() }
  finally { loading.value = false }
}

async function createTask() {
  if (taskBusy.value) return false

  if (!canCreateTask.value) {
    message.warning('请填写任务名、Cron 和 Prompt')
    return false
  }

  createLoading.value = true
  try {
    await schedulerApi.create({
      name: form.value.name.trim(),
      cron_expr: form.value.cron_expr.trim(),
      prompt: form.value.prompt.trim(),
      notify_dingtalk: form.value.notify_dingtalk,
    })
    message.success('任务已创建')
    showCreate.value = false
    form.value = { name: '', cron_expr: '', prompt: '', notify_dingtalk: false }
    await fetchTasks()
  } catch (error) {
    message.error(errorMessage(error, '创建失败'))
    return false
  } finally {
    createLoading.value = false
  }
}

async function toggleStatus(task: ScheduledTask) {
  if (taskBusy.value) return

  taskActionLoading.value = true
  const newStatus = task.status === 'active' ? 'paused' : 'active'
  try {
    await schedulerApi.update(task.id, { status: newStatus })
    await fetchTasks()
  } finally {
    taskActionLoading.value = false
  }
}

async function runTask(task: ScheduledTask) {
  if (taskBusy.value) return

  taskActionLoading.value = true
  try {
    const res = await schedulerApi.run(task.id)
    if (res.status === 'success') {
      message.success('任务执行成功')
    } else {
      message.error(res.error || '任务执行失败')
    }
    await fetchTasks()
    await showHistory(task)
  } finally {
    taskActionLoading.value = false
  }
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
  if (taskBusy.value) return

  taskActionLoading.value = true
  try {
    await schedulerApi.delete(id)
    await fetchTasks()
  } finally {
    taskActionLoading.value = false
  }
}

function fieldStatus(value: string) {
  return value.trim() ? undefined : 'error'
}

function fieldFeedback(value: string, fallback: string) {
  return value.trim() ? undefined : fallback
}

function errorMessage(error: unknown, fallback: string) {
  const maybe = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = maybe.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => typeof item?.msg === 'string' ? item.msg : String(item)).join('；')
  }
  return typeof detail === 'string' ? detail : maybe.message || fallback
}

onMounted(fetchTasks)
</script>

<style scoped>
.scheduler-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  color: var(--dr-text);
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 2px;
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

.scheduler-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.summary-tile {
  min-width: 0;
  min-height: 72px;
  padding: 11px 12px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #ffffff;
}

.summary-tile span {
  display: block;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  font-weight: 590;
}

.summary-tile strong {
  display: block;
  margin-top: 6px;
  color: var(--dr-text);
  font-size: 18px;
  font-weight: 620;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.summary-tile small {
  display: block;
  margin-top: 7px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}

.scheduler-focus {
  display: grid;
  grid-template-columns: 1.05fr 1fr 1.3fr;
  gap: 10px;
}

.focus-card {
  min-width: 0;
  min-height: 96px;
  padding: 13px 14px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #ffffff;
}

.focus-card.ready {
  border-color: #b8e3d1;
  background: #f0fdf4;
}

.focus-card.paused {
  border-color: #f3d89b;
  background: #fffbeb;
}

.focus-card.muted {
  background: #f8fafc;
}

.focus-kicker {
  display: block;
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 750;
  text-transform: uppercase;
}

.focus-card strong {
  display: block;
  margin-top: 8px;
  overflow: hidden;
  color: var(--dr-text);
  font-size: 17px;
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.focus-card small {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.task-panel {
  overflow: hidden;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface-lift);
  box-shadow: none;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  min-height: 56px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: #fbfcfe;
}

.panel-title {
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 610;
}

.panel-subtitle {
  margin-top: 3px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}

.task-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 10px;
  padding: 2px 0 16px;
}

.task-card {
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #ffffff;
}

.task-card > div:first-child {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-card strong {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  color: var(--dr-text);
  font-size: 14px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-state-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: #94a3b8;
}

.task-state-dot.active {
  background: #059669;
}

.task-state-dot.paused {
  background: #d97706;
}

.task-card p {
  display: -webkit-box;
  min-height: 38px;
  margin: 12px 0 0;
  overflow: hidden;
  color: var(--dr-text);
  font-size: 13px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.task-card dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 12px 0 0;
}

.task-card dt {
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 650;
}

.task-card dd {
  min-width: 0;
  margin: 4px 0 0;
  overflow: hidden;
  color: var(--dr-text);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-card > small {
  display: -webkit-box;
  margin-top: 12px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.task-panel :deep(.n-data-table) {
  border: 0;
}

@media (max-width: 980px) {
  .scheduler-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .scheduler-focus {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-header {
    display: block;
  }

  .page-header .n-button {
    margin-top: 12px;
  }

  .scheduler-summary {
    grid-template-columns: 1fr;
  }

  .task-card dl {
    grid-template-columns: 1fr;
  }
}
</style>
