<template>
  <div class="trace-page" :style="themeStyle">
    <TraceHeader
      :title="traceTitle"
      :refreshing="refreshing"
      @refresh="refresh"
    />

    <div class="trace-workbench">
      <TraceTimeline
        v-model:query="searchQuery"
        v-model:timeline-visible="timelineVisible"
        :steps="filteredTraceSteps"
        :selected-id="selectedSpanId"
        :main-duration="scopeSummary"
        :total-cost="toolSummary"
        :runtime-status="runtimeStatus"
        @select="selectedSpanId = $event"
      />

      <TraceDetail
        v-model:active-tab="activeTab"
        v-model:format="format"
        :trace-id="traceId"
        :timestamp="formattedTimestamp"
        :selected-step="selectedStep"
        :chips="traceChips"
        :input-text="inputText"
        :output-text="selectedOutputText"
        :metadata-text="metadataText"
        :scores="traceScores"
        @copy="copyValue"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import { systemApi } from '@/api/client'
import TraceDetail from '@/components/dashboard/TraceDetail.vue'
import TraceHeader from '@/components/dashboard/TraceHeader.vue'
import TraceTimeline from '@/components/dashboard/TraceTimeline.vue'
import type { DashboardCluster, DashboardSummary, DashboardTheme, DashboardTools } from '@/types'
import type { TraceChip, TraceFormat, TraceScore, TraceStep, TraceTab } from '@/types/trace'
import '@/styles/trace-workbench.css'

const auth = useAuthStore()
const message = useMessage()

const defaultTheme: DashboardTheme = {
  background: '#f8fafc',
  shell: '#ffffff',
  surface: '#ffffff',
  surface_alt: '#eef2f7',
  surface_light: '#ffffff',
  border: '#dbe1ea',
  text: '#111827',
  muted: '#6b7280',
  primary: '#5b5bd6',
  accent: '#5b5bd6',
  warning: '#8f6b18',
  danger: '#b42318',
}

const fallbackCluster: DashboardCluster = {
  name: 'Kubernetes 未连接',
  namespace: 'default',
  available: false,
  configured: false,
  mode: 'kubeconfig',
  unavailable_reason: '',
}

const fallbackTools: DashboardTools = {
  total: 0,
  available: 0,
  unavailable: 0,
  kubernetes: 0,
}

const dashboard = ref<DashboardSummary | null>(null)
const refreshing = ref(false)
const lastUpdated = ref<Date | null>(null)
const searchQuery = ref('')
const timelineVisible = ref(true)
const selectedSpanId = ref('root')
const activeTab = ref<TraceTab>('preview')
const format = ref<TraceFormat>('formatted')
const theme = computed(() => dashboard.value?.theme || defaultTheme)
const cluster = computed(() => dashboard.value?.cluster || fallbackCluster)
const tools = computed(() => dashboard.value?.tools || fallbackTools)
const schedulerJobs = computed(() => dashboard.value?.scheduler.jobs ?? 0)
const schedulerState = computed(() => {
  const scheduler = dashboard.value?.scheduler
  if (!scheduler?.enabled) return 'scheduler disabled'
  return scheduler.running ? 'scheduler running' : 'scheduler stopped'
})
const graphNodeCount = computed(() => dashboard.value?.knowledge_graph.summary.nodes ?? 0)
const llmState = computed(() => {
  const llm = dashboard.value?.llm
  if (!llm?.configured) return '未配置'
  return llm.enabled ? '已启用' : '已暂停'
})
const clusterModeText = computed(() => (cluster.value.available ? cluster.value.mode : cluster.value.unavailable_reason || 'not connected'))
const runtimeStatus = computed(() => (cluster.value.available ? 'Ready' : 'Degraded'))
const scopeSummary = computed(() => cluster.value.namespace || 'default')
const toolSummary = computed(() => `${tools.value.available}/${tools.value.total} tools`)
const userId = computed(() => (auth.username ? `u-${auth.username}` : 'unknown'))
const traceId = computed(() => {
  const seed = `${cluster.value.name}-${cluster.value.namespace}`.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return `runtime-${seed || 'ding-robot'}`
})
const traceTitle = computed(() => `Runtime: ${cluster.value.name} / ${cluster.value.namespace}`)
const inputText = computed(() => `读取 ${cluster.value.namespace} namespace 的 Dashboard 聚合状态`)
const outputText = computed(() => {
  if (!cluster.value.available) {
    return `当前 ${cluster.value.namespace} namespace 暂无可用集群连接。请先检查 kubeconfig 与 MCP 配置，系统仍保留结构化证据和配置状态。`
  }
  return `已读取 ${cluster.value.name} / ${cluster.value.namespace} 的运行上下文。当前可用工具 ${tools.value.available}/${tools.value.total}，知识图谱包含 ${graphNodeCount.value} 个节点，定时任务 ${schedulerJobs.value} 个，LLM 状态为 ${llmState.value}。`
})
const selectedOutputText = computed(() => {
  if (!selectedStep.value) return outputText.value
  return `${selectedStep.value.title}: ${selectedStep.value.detail}`
})

const formattedTimestamp = computed(() => {
  const date = lastUpdated.value || new Date()
  const pad = (value: number, size = 2) => String(value).padStart(size, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}`
})

const traceSteps = computed<TraceStep[]>(() => [
  {
    id: 'cluster',
    title: 'cluster connectivity',
    meta: clusterModeText.value,
    status: cluster.value.available ? 'Ready' : 'Blocked',
    metric: cluster.value.available ? cluster.value.mode : 'not connected',
    detail: cluster.value.available
      ? `${cluster.value.name} 已连接，当前 namespace 为 ${cluster.value.namespace}。`
      : `集群未连接：${clusterModeText.value}。`,
    icon: '↔',
    tone: 'blue',
  },
  {
    id: 'tools',
    title: 'tool catalog',
    meta: `${tools.value.available}/${tools.value.total} available`,
    status: tools.value.available ? 'Ready' : 'Waiting',
    metric: `${tools.value.unavailable} unavailable`,
    detail: `工具目录共 ${tools.value.total} 个工具，其中 ${tools.value.available} 个可用、${tools.value.unavailable} 个不可用。`,
    icon: '↔',
    tone: 'blue',
  },
  {
    id: 'knowledge-graph',
    title: 'knowledge graph',
    meta: `${graphNodeCount.value} nodes`,
    status: graphNodeCount.value ? 'Ready' : 'Empty',
    metric: `${graphNodeCount.value} nodes`,
    detail: `知识图谱当前包含 ${graphNodeCount.value} 个节点。`,
    icon: '↔',
    tone: 'blue',
  },
  {
    id: 'scheduler',
    title: 'scheduler',
    meta: schedulerState.value,
    status: dashboard.value?.scheduler.running ? 'Running' : 'Stopped',
    metric: `${schedulerJobs.value} jobs`,
    detail: `调度器状态为 ${schedulerState.value}，当前记录 ${schedulerJobs.value} 个任务。`,
    icon: '↔',
    tone: 'blue',
  },
  {
    id: 'llm',
    title: 'llm runtime',
    meta: llmState.value,
    status: dashboard.value?.llm.enabled ? 'Enabled' : 'Disabled',
    metric: dashboard.value?.llm.configured ? 'configured' : 'not configured',
    detail: `LLM 当前状态为 ${llmState.value}。`,
    icon: '✣',
    tone: 'pink',
  },
])
const filteredTraceSteps = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return traceSteps.value
  return traceSteps.value.filter((step) => `${step.id} ${step.title} ${step.meta} ${step.detail}`.toLowerCase().includes(query))
})
const selectedStep = computed(() => traceSteps.value.find((step) => step.id === selectedSpanId.value))
const traceChips = computed<TraceChip[]>(() => [
  { label: 'User ID', value: userId.value, dark: true },
  { label: 'Namespace', value: cluster.value.namespace, dark: true },
  { label: 'Cluster', value: cluster.value.name },
  { label: 'Connection', value: clusterModeText.value },
  { label: 'Tools', value: toolSummary.value },
  { label: 'Graph nodes', value: String(graphNodeCount.value) },
])
const traceScores = computed<TraceScore[]>(() => [
  { label: 'Tool readiness', value: `${tools.value.available}/${tools.value.total}`, detail: `${tools.value.unavailable} unavailable tools`, tone: tools.value.unavailable ? 'amber' : 'green' },
  { label: 'Graph context', value: String(graphNodeCount.value), detail: 'nodes linked to this answer', tone: 'blue' },
  { label: 'Runtime', value: cluster.value.available ? 'Ready' : 'Degraded', detail: clusterModeText.value, tone: cluster.value.available ? 'green' : 'amber' },
])
const metadata = computed(() => ({
  cluster: cluster.value.name,
  namespace: cluster.value.namespace,
  tools: `${tools.value.available}/${tools.value.total}`,
  knowledge_graph_nodes: graphNodeCount.value,
  scheduler: schedulerState.value,
  llm: llmState.value,
  selected_span: selectedSpanId.value,
}))
const metadataText = computed(() => JSON.stringify(metadata.value, null, 2))
const themeStyle = computed(() => ({
  '--ops-bg': theme.value.background,
  '--ops-shell': theme.value.shell,
  '--ops-surface': theme.value.surface,
  '--ops-surface-alt': theme.value.surface_alt,
  '--ops-border': theme.value.border,
  '--ops-text': theme.value.text,
  '--ops-muted': theme.value.muted,
  '--ops-primary': theme.value.primary,
  '--ops-accent': theme.value.accent,
  '--ops-warning': theme.value.warning,
  '--ops-danger': theme.value.danger,
}))

async function refresh() {
  if (refreshing.value) return

  refreshing.value = true
  try {
    dashboard.value = await systemApi.dashboard()
    lastUpdated.value = new Date()
  } catch {
    message.error('获取 Dashboard 聚合数据失败')
  } finally {
    refreshing.value = false
  }
}

async function copyValue(label: string, value: string) {
  try {
    await navigator.clipboard.writeText(value)
    message.success(`${label} 已复制`)
  } catch {
    message.warning('当前浏览器不允许写入剪贴板')
  }
}

onMounted(refresh)
</script>
