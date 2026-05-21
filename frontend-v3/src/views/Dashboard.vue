<template>
  <div class="ops-page" :style="themeStyle">
    <header class="ops-topbar">
      <div class="title-block">
        <img class="title-icon" :src="iconSrc(iconPack.bot)" alt="">
        <div>
          <div class="eyebrow">Ding Robot</div>
          <h1>ChatOps 运维控制台</h1>
          <p>用工具链、知识图谱和集群证据组织每一次排障。</p>
        </div>
      </div>
      <div class="topbar-actions">
        <div class="status-pill strong">
          <span :class="['status-dot', cluster.available ? 'green' : 'amber']" />
          <span>{{ cluster.name }}</span>
        </div>
        <button class="icon-button" :disabled="refreshing" title="刷新状态" aria-label="刷新 Dashboard 状态" @click="refresh">
          <img :src="iconSrc(iconPack.timeline)" alt="">
        </button>
      </div>
    </header>

    <section class="command-strip" aria-label="运行状态摘要">
      <div class="command-metric">
        <span>Namespace</span>
        <strong>{{ cluster.namespace }}</strong>
        <small>{{ clusterModeText }}</small>
      </div>
      <div class="command-metric">
        <span>MCP Tools</span>
        <strong>{{ tools.available }}/{{ tools.total }}</strong>
        <small>{{ tools.unavailable }} unavailable</small>
      </div>
      <div class="command-metric">
        <span>Knowledge Graph</span>
        <strong>{{ graphNodeCount }}</strong>
        <small>{{ coveragePercent }}% metrics coverage</small>
      </div>
      <div class="command-metric">
        <span>Automation</span>
        <strong>{{ schedulerJobs }}</strong>
        <small>{{ schedulerState }}</small>
      </div>
      <div class="command-metric">
        <span>LLM</span>
        <strong>{{ llmState }}</strong>
        <small>structured fallback ready</small>
      </div>
    </section>

    <div class="ops-grid">
      <aside class="insights-column">
        <section class="panel overview-panel">
          <div class="panel-heading">
            <div>
              <span class="panel-kicker">Signals</span>
              <h2>运行信号</h2>
            </div>
            <n-spin v-if="refreshing" size="small" />
          </div>

          <div class="insight-list">
            <article v-for="item in insightCards" :key="item.id" :class="['insight-card', item.tone]">
              <div class="generated-icon">
                <img :src="iconSrc(item.icon)" :alt="item.label">
              </div>
              <div>
                <span>{{ item.label }}</span>
                <strong>{{ item.title }}</strong>
                <small>{{ item.detail }}</small>
              </div>
            </article>
          </div>
        </section>

        <section class="panel compact-panel">
          <div class="panel-heading tight">
            <div>
              <span class="panel-kicker">Coverage</span>
              <h2>工具覆盖</h2>
            </div>
          </div>
          <div class="matrix-grid">
            <div class="matrix-item">
              <span>全部工具</span>
              <strong>{{ tools.total }}</strong>
            </div>
            <div class="matrix-item">
              <span>Kubernetes</span>
              <strong>{{ tools.kubernetes }}</strong>
            </div>
            <div class="matrix-item">
              <span>不可用</span>
              <strong>{{ tools.unavailable }}</strong>
            </div>
            <div class="matrix-item">
              <span>任务</span>
              <strong>{{ schedulerJobs }}</strong>
            </div>
          </div>
        </section>
      </aside>

      <main class="chat-column">
        <section class="ask-panel">
          <div class="ask-head">
            <div>
              <span class="panel-kicker">Command Center</span>
              <h2>输入目标，Bot 组织证据链</h2>
            </div>
            <span :class="['agent-state', agentTone]">{{ agentState }}</span>
          </div>

          <div class="prompt-box">
            <img class="prompt-icon" :src="iconSrc(iconPack.bot)" alt="">
            <input
              v-model="promptDraft"
              type="text"
              aria-label="ChatOps 指令"
              placeholder="例如：查看 default namespace 当前状态"
              @keydown.enter="goToRoute('Chat')"
            >
            <button @click="goToRoute('Chat')">
              <img :src="iconSrc(iconPack.timeline)" alt="">
              执行
            </button>
          </div>

          <div class="suggestions">
            <button v-for="item in suggestions" :key="item" @click="promptDraft = item">{{ item }}</button>
          </div>
        </section>

        <section class="conversation-panel">
          <div class="conversation-head">
            <div>
              <span class="panel-kicker">Run Preview</span>
              <h2>一次标准排障的执行预览</h2>
            </div>
            <span>{{ lastUpdatedText }}</span>
          </div>

          <div class="message user-message">
            <div class="avatar">U</div>
            <div class="bubble">查看 {{ cluster.namespace }} namespace 当前状态</div>
          </div>

          <div class="message bot-message">
            <div class="avatar bot">
              <img :src="iconSrc(iconPack.bot)" alt="">
            </div>
            <div class="bot-card">
              <div class="bot-summary">
                <div>
                  <span class="panel-kicker">Bot Answer</span>
                  <h3>已准备好按证据链排查当前集群</h3>
                </div>
                <span class="result-badge">ready</span>
              </div>
              <p>
                系统会先读取资源状态，再关联事件与图谱上下文；LLM 不可用时仍保留结构化证据。
              </p>

              <div class="tool-chip-row">
                <span v-for="tool in previewTools" :key="tool" class="tool-chip">{{ tool }}</span>
              </div>

              <div class="result-grid">
                <div>
                  <span>集群</span>
                  <strong>{{ cluster.name }}</strong>
                </div>
                <div>
                  <span>可用工具</span>
                  <strong>{{ tools.available }}</strong>
                </div>
                <div>
                  <span>图谱节点</span>
                  <strong>{{ graphNodeCount }}</strong>
                </div>
              </div>

              <div class="action-row">
                <button @click="goToRoute('Chat')">继续排查</button>
                <button @click="goToRoute('KnowledgeGraph')">查看图谱</button>
                <button @click="goToRoute('MCPConfig')">MCP 工具</button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <aside class="context-column">
        <section class="panel investigation-panel">
          <div class="panel-heading">
            <div>
              <span class="panel-kicker">Context</span>
              <h2>排障上下文</h2>
            </div>
            <span class="mini-time">{{ lastUpdatedText }}</span>
          </div>

          <div class="resource-map">
            <div v-for="(node, index) in resourceNodes" :key="node.kind" class="resource-step">
              <div :class="['resource-node', node.tone]">
                <img :src="iconSrc(node.icon)" :alt="node.kind">
                <div>
                  <span>{{ node.kind }}</span>
                  <strong>{{ node.count }}</strong>
                </div>
              </div>
              <div v-if="index < resourceNodes.length - 1" class="resource-line" />
            </div>
          </div>
        </section>

        <section class="panel timeline-panel">
          <div class="panel-heading tight">
            <div>
              <span class="panel-kicker">Workflow</span>
              <h2>执行链路</h2>
            </div>
          </div>

          <div class="timeline">
            <div v-for="item in timelineItems" :key="item.id" class="timeline-item">
              <span :class="['timeline-dot', item.tone]" />
              <img :src="iconSrc(item.icon)" :alt="item.title">
              <div>
                <strong>{{ item.title }}</strong>
                <span>{{ item.detail }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="panel next-actions-panel">
          <div class="panel-heading tight">
            <div>
              <span class="panel-kicker">Actions</span>
              <h2>下一步动作</h2>
            </div>
          </div>
          <div class="next-actions">
            <button v-for="action in nextActions" :key="action.id" @click="goToRoute(action.route)">
              <img :src="iconSrc(action.icon)" :alt="action.title">
              {{ action.title }}
            </button>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NSpin, useMessage } from 'naive-ui'
import botCoreIcon from '@/assets/generated/bot-core.svg'
import executionFlowIcon from '@/assets/generated/execution-flow.svg'
import knowledgeMapIcon from '@/assets/generated/knowledge-map.svg'
import kubernetesClusterIcon from '@/assets/generated/kubernetes-cluster.svg'
import mcpToolchainIcon from '@/assets/generated/mcp-toolchain.svg'
import { systemApi } from '@/api/client'
import type {
  DashboardAction,
  DashboardCluster,
  DashboardIconPack,
  DashboardInsight,
  DashboardResourceNode,
  DashboardSummary,
  DashboardTheme,
  DashboardTimelineItem,
  DashboardTools,
} from '@/types'

const router = useRouter()
const message = useMessage()

const generatedIcons: Record<string, string> = {
  'bot-core': botCoreIcon,
  'execution-flow': executionFlowIcon,
  'knowledge-map': knowledgeMapIcon,
  'kubernetes-cluster': kubernetesClusterIcon,
  'mcp-toolchain': mcpToolchainIcon,
}

const defaultTheme: DashboardTheme = {
  background: '#070a0f',
  shell: '#0d1420',
  surface: '#111827',
  surface_alt: '#172235',
  surface_light: '#f8fafc',
  border: '#2a3648',
  text: '#f8fafc',
  muted: '#9aa8bd',
  primary: '#22c55e',
  accent: '#38bdf8',
  warning: '#f59e0b',
  danger: '#ef4444',
}

const fallbackIconPack: DashboardIconPack = {
  bot: 'bot-core',
  kubernetes: 'kubernetes-cluster',
  mcp: 'mcp-toolchain',
  graph: 'knowledge-map',
  timeline: 'execution-flow',
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

const suggestions = ['查看异常 Pod', '汇总最近事件', '检查 Service 暴露']
const previewTools = ['k8s-get-pods', 'k8s-get-events', 'k8s-get-services', 'toolsearch']
const dashboard = ref<DashboardSummary | null>(null)
const refreshing = ref(false)
const lastUpdated = ref<Date | null>(null)
const promptDraft = ref('查看 default namespace 当前状态')

const theme = computed(() => dashboard.value?.theme || defaultTheme)
const iconPack = computed(() => dashboard.value?.icon_pack || fallbackIconPack)
const cluster = computed(() => dashboard.value?.cluster || fallbackCluster)
const tools = computed(() => dashboard.value?.tools || fallbackTools)
const insightCards = computed<DashboardInsight[]>(() => dashboard.value?.insights || [])
const resourceNodes = computed<DashboardResourceNode[]>(() => dashboard.value?.resource_map || [])
const timelineItems = computed<DashboardTimelineItem[]>(() => dashboard.value?.execution_timeline || [])
const nextActions = computed<DashboardAction[]>(() => dashboard.value?.next_actions || [])
const schedulerJobs = computed(() => dashboard.value?.scheduler.jobs ?? 0)
const schedulerState = computed(() => {
  const scheduler = dashboard.value?.scheduler
  if (!scheduler?.enabled) return 'scheduler disabled'
  return scheduler.running ? 'scheduler running' : 'scheduler stopped'
})
const graphNodeCount = computed(() => dashboard.value?.knowledge_graph.summary.nodes ?? 0)
const coveragePercent = computed(() => Math.round((dashboard.value?.knowledge_graph.coverage.coverage ?? 0) * 100))
const llmState = computed(() => {
  const llm = dashboard.value?.llm
  if (!llm?.configured) return '未配置'
  return llm.enabled ? '已启用' : '已暂停'
})
const clusterModeText = computed(() => (cluster.value.available ? cluster.value.mode : cluster.value.unavailable_reason || 'not connected'))
const agentTone = computed(() => (cluster.value.available && tools.value.available > 0 ? 'green' : 'amber'))
const agentState = computed(() => (cluster.value.available && tools.value.available > 0 ? 'Agent online' : 'Agent degraded'))
const lastUpdatedText = computed(() => {
  if (!lastUpdated.value) return '尚未刷新'
  return lastUpdated.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})
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

function iconSrc(name: string) {
  return generatedIcons[name] || botCoreIcon
}

async function refresh() {
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

function goToRoute(routeName: string) {
  router.push({ name: routeName })
}

onMounted(refresh)
</script>

<style scoped>
.ops-page {
  min-height: calc(100dvh - 48px);
  overflow: auto;
  padding: 20px;
  box-sizing: border-box;
  background: var(--ops-bg);
  color: var(--ops-text);
  font-size: 14px;
  line-height: 1.5;
  --ops-row: #0a111d;
  --ops-row-hover: #101a2a;
  --ops-text-secondary: color-mix(in srgb, var(--ops-muted) 86%, white 14%);
  --tone-green: var(--ops-primary);
  --tone-green-bg: rgba(34, 197, 94, 0.12);
  --tone-blue: var(--ops-accent);
  --tone-blue-bg: rgba(56, 189, 248, 0.12);
  --tone-amber: var(--ops-warning);
  --tone-amber-bg: rgba(245, 158, 11, 0.13);
  --tone-slate: #94a3b8;
  --tone-slate-bg: rgba(148, 163, 184, 0.12);
}

.ops-page *,
.ops-page *::before,
.ops-page *::after {
  box-sizing: border-box;
}

.ops-page button,
.ops-page input {
  font: inherit;
}

.ops-page button:focus-visible,
.ops-page input:focus-visible {
  outline: 2px solid var(--ops-accent);
  outline-offset: 2px;
}

.ops-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 14px;
}

.title-block {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.title-icon {
  width: 46px;
  height: 46px;
  flex: 0 0 auto;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-shell);
}

.eyebrow,
.panel-kicker {
  display: block;
  color: var(--ops-text-secondary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.ops-topbar h1,
.panel-heading h2,
.ask-head h2,
.conversation-head h2,
.bot-summary h3 {
  margin: 0;
  color: var(--ops-text);
  letter-spacing: 0;
}

.ops-topbar h1 {
  margin-top: 2px;
  font-size: 24px;
  line-height: 1.2;
}

.title-block p {
  max-width: 620px;
  margin: 6px 0 0;
  color: var(--ops-muted);
  line-height: 1.55;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-pill,
.icon-button {
  min-height: 40px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-surface);
  color: var(--ops-muted);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  font-size: 12px;
  white-space: nowrap;
}

.status-pill.strong {
  color: var(--ops-text);
  font-weight: 700;
}

.status-pill strong {
  color: var(--ops-text);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}

.status-dot.green {
  background: var(--ops-primary);
  box-shadow: 0 0 0 3px var(--tone-green-bg);
}

.status-dot.amber {
  background: var(--ops-warning);
  box-shadow: 0 0 0 3px var(--tone-amber-bg);
}

.icon-button {
  width: 40px;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
  transition: border-color 160ms ease, background-color 160ms ease;
}

.icon-button:hover:not(:disabled) {
  border-color: var(--ops-accent);
  background: var(--ops-surface-alt);
}

.icon-button img {
  width: 22px;
  height: 22px;
}

.icon-button:disabled {
  opacity: 0.55;
  cursor: wait;
}

.command-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
  padding: 10px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-shell);
}

.command-metric {
  min-width: 0;
  min-height: 76px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--ops-border) 82%, white 18%);
  border-left: 3px solid var(--ops-accent);
  border-radius: 8px;
  background: var(--ops-surface);
}

.command-metric:nth-child(2),
.command-metric:nth-child(4) {
  border-left-color: var(--ops-primary);
}

.command-metric:nth-child(5) {
  border-left-color: var(--ops-warning);
}

.command-metric span,
.command-metric small {
  display: block;
  overflow: hidden;
  color: var(--ops-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.command-metric span {
  font-size: 12px;
  font-weight: 700;
}

.command-metric strong {
  display: block;
  overflow: hidden;
  margin-top: 4px;
  color: var(--ops-text);
  font-size: 20px;
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.command-metric small {
  margin-top: 5px;
  font-size: 12px;
}

.ops-grid {
  display: grid;
  grid-template-columns: minmax(270px, 0.86fr) minmax(520px, 1.5fr) minmax(310px, 1fr);
  gap: 16px;
  align-items: start;
}

.panel,
.ask-panel,
.conversation-panel {
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-shell);
}

.panel {
  padding: 14px;
}

.panel + .panel,
.ask-panel + .conversation-panel {
  margin-top: 16px;
}

.panel-heading,
.ask-head,
.conversation-head,
.bot-summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.panel-heading h2,
.ask-head h2,
.conversation-head h2 {
  margin-top: 4px;
  font-size: 16px;
  line-height: 1.3;
}

.panel-heading.tight h2 {
  font-size: 15px;
}

.insight-list {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.insight-card {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 10px;
  min-height: 74px;
  padding: 10px;
  border: 1px solid color-mix(in srgb, var(--ops-border) 78%, white 22%);
  border-left-width: 3px;
  border-radius: 8px;
  background: var(--ops-surface);
}

.insight-card span,
.matrix-item span,
.result-grid span,
.resource-node span,
.timeline-item span,
.mini-time,
.conversation-head > span {
  color: var(--ops-muted);
  font-size: 12px;
}

.insight-card strong {
  display: block;
  margin-top: 3px;
  color: var(--ops-text);
  font-size: 14px;
  line-height: 1.35;
}

.insight-card small {
  display: block;
  margin-top: 5px;
  color: var(--ops-muted);
  font-size: 12px;
  line-height: 1.45;
}

.generated-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--ops-border) 70%, white 30%);
  border-radius: 8px;
  background: var(--ops-row);
}

.generated-icon img,
.resource-node img,
.timeline-item img,
.next-actions img,
.prompt-box button img,
.avatar.bot img {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.insight-card.green,
.resource-node.green {
  border-left-color: var(--ops-primary);
}

.insight-card.amber,
.resource-node.amber {
  border-left-color: var(--ops-warning);
}

.insight-card.blue,
.resource-node.blue {
  border-left-color: var(--ops-accent);
}

.insight-card.slate,
.resource-node.slate {
  border-left-color: #7890ad;
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.matrix-item {
  min-height: 76px;
  padding: 11px;
  border: 1px solid color-mix(in srgb, var(--ops-border) 78%, white 22%);
  border-radius: 8px;
  background: var(--ops-surface);
}

.matrix-item strong {
  display: block;
  margin-top: 6px;
  color: var(--ops-text);
  font-size: 24px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.ask-panel {
  padding: 16px;
  background: var(--ops-surface);
}

.agent-state {
  min-height: 28px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.agent-state.green {
  background: var(--tone-green-bg);
  color: #86efac;
}

.agent-state.amber {
  background: var(--tone-amber-bg);
  color: #fde68a;
}

.prompt-box {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-height: 60px;
  margin-top: 16px;
  padding: 8px 8px 8px 12px;
  border: 1px solid color-mix(in srgb, var(--ops-accent) 54%, var(--ops-border) 46%);
  border-radius: 8px;
  background: var(--ops-row);
}

.prompt-icon {
  width: 32px;
  height: 32px;
}

.prompt-box input {
  min-width: 0;
  min-height: 44px;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--ops-text);
  font: inherit;
}

.prompt-box input::placeholder {
  color: color-mix(in srgb, var(--ops-muted) 84%, white 16%);
}

.prompt-box button,
.action-row button,
.suggestions button,
.next-actions button {
  border: 1px solid transparent;
  border-radius: 8px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease;
}

.prompt-box button {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 14px;
  background: var(--ops-primary);
  color: #03110a;
}

.prompt-box button:hover,
.action-row button:first-child:hover {
  background: #4ade80;
}

.prompt-box button img {
  width: 22px;
  height: 22px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.suggestions button {
  min-height: 38px;
  padding: 7px 11px;
  border-color: var(--ops-border);
  background: var(--ops-shell);
  color: var(--ops-text);
  font-size: 12px;
}

.suggestions button:hover,
.next-actions button:hover,
.action-row button:not(:first-child):hover {
  border-color: var(--ops-accent);
  background: var(--ops-surface-alt);
}

.conversation-panel {
  padding: 16px;
}

.conversation-head {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--ops-border);
}

.message {
  display: flex;
  gap: 10px;
}

.message + .message {
  margin-top: 14px;
}

.avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-surface);
  color: var(--ops-text);
  font-size: 12px;
  font-weight: 800;
}

.avatar.bot {
  background: transparent;
  border: 0;
}

.avatar.bot img {
  width: 36px;
  height: 36px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
}

.bubble {
  max-width: 76%;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--ops-accent) 42%, var(--ops-border) 58%);
  border-radius: 8px;
  background: var(--tone-blue-bg);
  color: var(--ops-text);
}

.bot-card {
  flex: 1;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--ops-border) 80%, white 20%);
  border-radius: 8px;
  background: var(--ops-row);
}

.bot-summary h3 {
  margin-top: 3px;
  font-size: 16px;
  line-height: 1.35;
}

.result-badge {
  min-height: 28px;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--tone-green-bg);
  color: #86efac;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.bot-card p {
  margin: 12px 0 0;
  color: var(--ops-muted);
  line-height: 1.65;
}

.tool-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.tool-chip {
  padding: 5px 8px;
  border: 1px solid color-mix(in srgb, var(--ops-accent) 42%, var(--ops-border) 58%);
  border-radius: 8px;
  background: var(--tone-blue-bg);
  color: #bfdbfe;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.result-grid > div {
  padding: 11px;
  border: 1px solid color-mix(in srgb, var(--ops-border) 78%, white 22%);
  border-radius: 8px;
  background: var(--ops-surface);
}

.result-grid strong {
  display: block;
  margin-top: 5px;
  color: var(--ops-text);
  font-variant-numeric: tabular-nums;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.action-row button {
  min-height: 40px;
  padding: 8px 11px;
  border-color: var(--ops-border);
  background: var(--ops-surface);
  color: var(--ops-text);
  font-size: 12px;
}

.action-row button:first-child {
  border-color: var(--ops-primary);
  background: var(--ops-primary);
  color: #03110a;
}

.resource-map {
  margin-top: 16px;
}

.resource-step {
  display: grid;
  grid-template-columns: 1fr;
}

.resource-node {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 56px;
  padding: 10px;
  border: 1px solid color-mix(in srgb, var(--ops-border) 78%, white 22%);
  border-left-width: 3px;
  border-radius: 8px;
  background: var(--ops-surface);
}

.resource-node strong {
  display: block;
  margin-top: 3px;
  color: var(--ops-text);
  font-variant-numeric: tabular-nums;
}

.resource-line {
  width: 2px;
  height: 14px;
  margin-left: 24px;
  background: var(--ops-border);
}

.timeline {
  position: relative;
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 10px 30px minmax(0, 1fr);
  gap: 9px;
  align-items: start;
  min-width: 0;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  margin-top: 10px;
  border-radius: 999px;
  background: #94a3b8;
}

.timeline-dot.green {
  background: var(--ops-primary);
}

.timeline-dot.amber {
  background: var(--ops-warning);
}

.timeline-dot.blue {
  background: var(--ops-accent);
}

.timeline-dot.slate {
  background: #7890ad;
}

.timeline-item img {
  width: 26px;
  height: 26px;
  border-radius: 8px;
}

.timeline-item strong {
  display: block;
  color: var(--ops-text);
  font-size: 13px;
  line-height: 1.35;
}

.timeline-item span {
  display: block;
  margin-top: 3px;
  line-height: 1.4;
}

.next-actions {
  display: grid;
  gap: 9px;
  margin-top: 14px;
}

.next-actions button {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 9px;
  justify-content: flex-start;
  padding: 0 11px;
  border-color: var(--ops-border);
  background: var(--ops-surface);
  color: var(--ops-text);
}

.next-actions img {
  width: 26px;
  height: 26px;
  border-radius: 8px;
}

@media (max-width: 1280px) {
  .command-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .ops-grid {
    grid-template-columns: minmax(250px, 0.9fr) minmax(440px, 1.4fr);
  }

  .context-column {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }

  .context-column .panel {
    margin-top: 0;
  }
}

@media (max-width: 900px) {
  .ops-page {
    padding: 14px;
  }

  .ops-topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .topbar-actions {
    justify-content: flex-start;
  }

  .command-strip,
  .ops-grid,
  .context-column,
  .result-grid {
    grid-template-columns: 1fr;
  }

  .prompt-box {
    grid-template-columns: 32px minmax(0, 1fr);
  }

  .prompt-box button {
    grid-column: 1 / -1;
    width: 100%;
  }

  .bubble {
    max-width: none;
  }
}
</style>
