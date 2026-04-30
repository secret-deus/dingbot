<template>
  <div class="ops-page">
    <header class="ops-topbar">
      <div class="title-block">
        <div class="title-copy">
          <div class="title-kicker">DINGOPS COPILOT</div>
          <h1>云原生运维指挥台</h1>
        </div>
        <div class="env-switch" aria-label="环境">
          <button
            v-for="env in overview.environments"
            :key="env"
            type="button"
            :class="{ selected: env === overview.environment }"
          >
            {{ env }}
          </button>
        </div>
      </div>

      <div class="top-actions">
        <span class="status-pill">
          <span :class="['dot', healthClass]" />
          {{ overview.mode }}
        </span>
        <span :class="['status-pill', dataSourceClass]">{{ sourceLabel }}</span>
        <el-button class="refresh-btn" :loading="loading" @click="loadOverview">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </header>

    <div v-if="lastError" class="fallback-banner">
      后端标准接口暂不可用，当前展示本地 fallback 数据。原因：{{ lastError }}
    </div>

    <main class="ops-grid">
      <section id="command-section" class="ops-panel command-panel">
        <div class="panel-header">
          <div>
            <h2>Command Center</h2>
            <p>自然语言诊断入口，保留证据轨迹与风险确认状态。</p>
          </div>
          <button type="button" class="ghost-btn" @click="openChat">打开完整对话</button>
        </div>

        <div class="command-body">
          <div class="chat-stream">
            <div
              v-for="message in overview.messages"
              :key="message.id"
              :class="['message', message.role]"
            >
              <div class="meta">
                <span>{{ message.actor }}</span>
                <span>{{ message.time }}</span>
              </div>
              <div class="bubble">
                <div v-if="message.role === 'assistant'" class="answer-head">
                  <span>{{ message.title }}</span>
                  <span class="confidence">{{ message.confidence }}</span>
                </div>
                <p>{{ message.content }}</p>
                <div v-if="message.findings?.length" class="finding-grid">
                  <div v-for="finding in message.findings" :key="finding.label" class="finding">
                    <b>{{ finding.value }}</b>
                    <span>{{ finding.label }}</span>
                  </div>
                </div>
              </div>
            </div>

            <form class="composer" @submit.prevent="submitCommand">
              <input
                v-model="commandDraft"
                type="text"
                autocomplete="off"
                placeholder="输入诊断命令，例如：排查 prod 支付服务 5xx 飙升"
              >
              <button type="submit">发送</button>
            </form>
          </div>

          <aside id="audit-section" class="tool-trace">
            <div class="section-label">Tool Trace</div>
            <div v-for="trace in overview.toolTraces" :key="trace.id" class="trace-item">
              <div class="trace-top">
                <strong>{{ trace.name }}</strong>
                <span :class="['tag', trace.state]">{{ trace.stateText }}</span>
              </div>
              <p>{{ trace.description }}</p>
              <code>{{ trace.evidence }}</code>
            </div>
          </aside>
        </div>
      </section>

      <aside class="context-stack">
        <section id="topology-section" class="ops-panel">
          <div class="panel-header compact">
            <div>
              <h2>Live Context</h2>
              <p>{{ overview.contextNote }}</p>
            </div>
          </div>
          <div class="metrics-grid">
            <article
              v-for="metric in overview.metrics"
              :key="metric.label"
              :class="['metric-card', metric.tone]"
            >
              <span>{{ metric.label }}</span>
              <strong>{{ metric.value }}</strong>
              <p>{{ metric.detail }}</p>
            </article>
          </div>
          <div class="runtime-strip">
            <div class="runtime-head">
              <span>Local MCP Runtime</span>
              <strong>{{ overview.mcpRuntime.transport }}</strong>
            </div>
            <div class="runtime-stats">
              <div>
                <b>{{ overview.mcpRuntime.status }}</b>
                <span>status</span>
              </div>
              <div>
                <b>{{ overview.mcpRuntime.toolCount }}</b>
                <span>tools</span>
              </div>
              <div>
                <b>{{ overview.mcpRuntime.remoteConnections }}</b>
                <span>remote</span>
              </div>
            </div>
            <div class="provider-grid">
              <div
                v-for="provider in overview.mcpRuntime.providers"
                :key="provider.id"
                class="provider-pill"
              >
                <span>{{ provider.id }}</span>
                <strong>{{ provider.toolCount }}</strong>
              </div>
            </div>
          </div>
        </section>

        <section class="ops-panel">
          <div class="panel-header compact">
            <div>
              <h2>Topology</h2>
              <p>工作负载、节点、实例和告警的关联。</p>
            </div>
          </div>
          <div class="topology-map">
            <span
              v-for="edge in overview.topology.edges"
              :key="edge.id"
              class="edge"
              :style="edgeStyle(edge)"
            />
            <div
              v-for="node in overview.topology.nodes"
              :key="node.id"
              :class="['topology-node', node.tone]"
              :style="{ left: `${node.x}%`, top: `${node.y}%` }"
            >
              {{ node.name }}
              <span>{{ node.meta }}</span>
            </div>
          </div>
        </section>

        <section class="ops-panel">
          <div class="panel-header compact">
            <div>
              <h2>Risk Radar</h2>
              <p>高危动作、缺失信号与待确认项。</p>
            </div>
          </div>
          <div class="risk-list">
            <div v-for="risk in overview.risks" :key="risk.id" class="risk-row">
              <span :class="['severity', risk.level]" />
              <div>
                <strong>{{ risk.title }}</strong>
                <p>{{ risk.description }}</p>
              </div>
              <span class="risk-state">{{ risk.state }}</span>
            </div>
          </div>
        </section>
      </aside>

      <section id="incident-section" class="ops-panel timeline-panel">
        <div class="timeline-column">
          <div class="panel-header compact">
            <div>
              <h2>Incident Timeline</h2>
              <p>告警、钉钉协同与手动取证的顺序。</p>
            </div>
          </div>
          <div class="timeline-list">
            <div v-for="item in overview.timeline" :key="item.id" class="timeline-item">
              <span>{{ item.time }}</span>
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="timeline-column">
          <div class="panel-header compact">
            <div>
              <h2>Automation Queue</h2>
              <p>只读、需确认、已审计的自动化动作。</p>
            </div>
          </div>
          <div class="queue-list">
            <div v-for="task in overview.automationQueue" :key="task.id" class="queue-item">
              <div>
                <strong>{{ task.name }}</strong>
                <p>{{ task.target }}</p>
              </div>
              <span :class="['tag', task.state]">{{ task.stateText }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { api } from '@/api/client'

const router = useRouter()
const loading = ref(false)
const lastError = ref('')
const dataSource = ref('fallback')
const commandDraft = ref('')
const overview = ref(createFallbackOverview())

const sourceLabel = computed(() => (dataSource.value === 'live' ? '实时接口' : '本地 fallback'))
const dataSourceClass = computed(() => (dataSource.value === 'live' ? 'live' : 'fallback'))
const healthClass = computed(() => {
  const level = overview.value.healthLevel
  if (level === 'critical') return 'critical'
  if (level === 'warning') return 'warning'
  return 'healthy'
})

const loadOverview = async () => {
  loading.value = true
  try {
    const { data, meta } = await api.ops.getOverview()
    overview.value = normalizeOverview(data, meta)
    dataSource.value = 'live'
    lastError.value = ''
  } catch (error) {
    const fallback = createFallbackOverview()
    overview.value = normalizeOverview(fallback, {
      generatedAt: new Date().toISOString(),
      source: 'local-fallback'
    })
    dataSource.value = 'fallback'
    lastError.value = error?.message || '请求失败'
  } finally {
    loading.value = false
  }
}

const openChat = () => {
  router.push('/chat')
}

const submitCommand = () => {
  const message = commandDraft.value.trim()
  if (!message) return
  router.push({ path: '/chat', query: { q: message } })
  ElMessage.info('已切换到完整对话页继续执行')
}

const edgeStyle = (edge) => ({
  left: `${edge.left}%`,
  top: `${edge.top}%`,
  width: `${edge.width}%`,
  transform: `rotate(${edge.rotate}deg)`
})

const normalizeOverview = (data, meta = {}) => {
  const fallback = createFallbackOverview()
  const source = data || {}

  return {
    summary: source.summary || fallback.summary,
    environment: source.environment || source.currentEnvironment || fallback.environment,
    environments: source.environments || fallback.environments,
    mode: source.mode || fallback.mode,
    healthLevel: source.healthLevel || source.health_level || fallback.healthLevel,
    contextNote: source.contextNote || source.context_note || fallback.contextNote,
    metrics: normalizeList(source.metrics, fallback.metrics),
    messages: normalizeList(source.messages || source.commandMessages, fallback.messages),
    toolTraces: normalizeList(source.toolTraces || source.tool_traces, fallback.toolTraces),
    mcpRuntime: normalizeMcpRuntime(source.mcpRuntime || source.mcp_runtime, fallback.mcpRuntime),
    topology: {
      nodes: normalizeList(source.topology?.nodes, fallback.topology.nodes),
      edges: normalizeList(source.topology?.edges, fallback.topology.edges)
    },
    risks: normalizeList(source.risks, fallback.risks),
    timeline: normalizeList(source.timeline || source.incidentTimeline, fallback.timeline),
    automationQueue: normalizeList(
      source.automationQueue || source.automation_queue,
      fallback.automationQueue
    ),
    meta
  }
}

const normalizeList = (value, fallback) => (Array.isArray(value) && value.length > 0 ? value : fallback)

const normalizeMcpRuntime = (value, fallback) => {
  const source = value || {}
  return {
    enabled: source.enabled ?? fallback.enabled,
    transport: source.transport || fallback.transport,
    status: source.status || fallback.status,
    toolCount: source.tool_count ?? source.toolCount ?? fallback.toolCount,
    remoteConnections: source.remote_connections ?? source.remoteConnections ?? fallback.remoteConnections,
    providers: normalizeList(
      (source.providers || []).map((provider) => ({
        id: provider.id,
        transport: provider.transport || source.transport || 'local',
        toolCount: provider.tool_count ?? provider.toolCount ?? 0,
        enabled: provider.enabled ?? true
      })),
      fallback.providers
    )
  }
}

function createFallbackOverview() {
  return {
    summary: 'prod-cn-hz 环境存在支付链路延迟升高，当前处于只读取证模式。',
    environment: 'prod-cn-hz',
    environments: ['prod-cn-hz', 'prod-cn-bj', 'staging'],
    mode: '只读取证 / 审计开启',
    healthLevel: 'warning',
    contextNote: '最近 15 分钟的告警、资源与工具覆盖摘要。',
    mcpRuntime: {
      enabled: true,
      transport: 'local',
      status: 'connected',
      toolCount: 21,
      remoteConnections: 0,
      providers: [
        { id: 'builtin-k8s', transport: 'local', toolCount: 18, enabled: true },
        { id: 'builtin-ecs', transport: 'local', toolCount: 3, enabled: true }
      ]
    },
    metrics: [
      { label: '活跃事故', value: '3', detail: '1 个 P1，2 个 P2', tone: 'danger' },
      { label: '工具覆盖', value: '86%', detail: 'K8s/ECS/日志已接入', tone: 'good' },
      { label: '信号缺口', value: '4', detail: '2 个服务缺少应用指标', tone: 'warning' },
      { label: '待确认动作', value: '2', detail: '扩容与重启需人工确认', tone: 'neutral' }
    ],
    messages: [
      {
        id: 'm1',
        role: 'user',
        actor: 'SRE',
        time: '10:42',
        content: '排查 prod 支付服务 5xx 飙升，先不要执行写操作。'
      },
      {
        id: 'm2',
        role: 'assistant',
        actor: 'DingOps Copilot',
        time: '10:43',
        title: '初步 RCA',
        confidence: '82%',
        content: '5xx 高峰与 checkout-api 发布后 6 分钟重合，两个 Pod CPU throttling 明显，ECS ingress 节点连接数接近阈值。',
        findings: [
          { label: '异常 Pod', value: '2' },
          { label: '关联告警', value: '7' },
          { label: '建议动作', value: '3' }
        ]
      }
    ],
    toolTraces: [
      {
        id: 't1',
        name: 'local_mcp_runtime',
        state: 'green',
        stateText: '完成',
        description: '主进程内加载 K8s/ECS provider，不依赖远程 SSE 服务。',
        evidence: 'transport=local; providers=2; remote_connections=0'
      },
      {
        id: 't2',
        name: 'ecs_monitor_data',
        state: 'amber',
        stateText: '缺采样',
        description: 'ingress 节点近 5 分钟存在两个采样点缺失。',
        evidence: 'cn-hangzhou.i-bp*** NetworkIn 92% threshold'
      },
      {
        id: 't3',
        name: 'dingtalk_audit',
        state: 'green',
        stateText: '已记录',
        description: '当前会话处于只读模式，未触发变更动作。',
        evidence: 'audit_id=AUD-20260429-1043 readonly=true'
      }
    ],
    topology: {
      nodes: [
        { id: 'n1', name: 'DingTalk', meta: 'incident channel', tone: 'green', x: 8, y: 18 },
        { id: 'n2', name: 'Copilot API', meta: 'v2 envelope', tone: 'blue', x: 38, y: 35 },
        { id: 'n3', name: 'Local MCP', meta: '21 tools', tone: 'green', x: 66, y: 16 },
        { id: 'n4', name: 'K8s / ECS', meta: 'in-process', tone: 'green', x: 62, y: 62 }
      ],
      edges: [
        { id: 'e1', left: 24, top: 30, width: 21, rotate: 15 },
        { id: 'e2', left: 52, top: 36, width: 20, rotate: -20 },
        { id: 'e3', left: 51, top: 52, width: 18, rotate: 28 }
      ]
    },
    risks: [
      { id: 'r1', level: 'critical', title: '支付服务重启', description: '会影响 2 个活跃订单队列', state: '需确认' },
      { id: 'r2', level: 'warning', title: '指标覆盖缺口', description: 'checkout-worker 缺少应用层指标', state: '待补齐' },
      { id: 'r3', level: 'normal', title: '审计链路', description: '当前只读取证已写入审计轨迹', state: '正常' }
    ],
    timeline: [
      { id: 'i1', time: '10:31', title: 'P1 告警触发', description: '支付链路 5xx 超过 3 分钟阈值。' },
      { id: 'i2', time: '10:36', title: '发布事件关联', description: 'checkout-api 镜像从 1.42.7 升级到 1.43.0。' },
      { id: 'i3', time: '10:43', title: '只读取证完成', description: 'Pod、ECS、告警和钉钉上下文已聚合。' }
    ],
    automationQueue: [
      { id: 'a1', name: '生成事故摘要', target: '发送到钉钉 incident 群', state: 'green', stateText: '可执行' },
      { id: 'a2', name: '扩容 checkout-api', target: 'replicas 6 -> 9', state: 'amber', stateText: '需确认' },
      { id: 'a3', name: '回滚镜像版本', target: '1.43.0 -> 1.42.7', state: 'red', stateText: '高危' }
    ]
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.ops-page {
  --ops-panel: var(--ops-surface);
  --ops-panel-2: var(--ops-surface-raised);
  --ops-line: var(--ops-border);
  --ops-line-soft: var(--ops-border);
  --ops-faint: var(--ops-muted-2);
  --ops-cyan: var(--ops-accent);
  --ops-green: var(--ops-success);
  --ops-amber: var(--ops-warning);
  --ops-red: var(--ops-danger);
  min-height: 100%;
  padding: 0;
  background: var(--ops-bg);
  color: var(--ops-text);
  letter-spacing: 0;
}

.ops-topbar {
  min-height: 72px;
  display: grid;
  grid-template-columns: minmax(360px, 1fr) auto;
  gap: 20px;
  align-items: center;
  padding: 14px 22px;
  border-bottom: 1px solid var(--ops-line);
  background: color-mix(in srgb, var(--ops-bg-elevated) 94%, transparent);
}

.title-block {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.title-copy {
  min-width: 0;
}

.title-kicker,
.section-label {
  color: var(--ops-muted);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.title-block h1,
.panel-header h2 {
  margin: 2px 0 0;
  line-height: 1.2;
  font-weight: 780;
}

.title-block h1 {
  font-size: 22px;
}

.panel-header p,
.metric-card p,
.risk-row p,
.timeline-item p,
.queue-item p,
.trace-item p {
  margin: 4px 0 0;
  color: var(--ops-muted);
  font-size: 12px;
  line-height: 1.5;
}

.top-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.env-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  border: 1px solid var(--ops-line);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

.env-switch button,
.ghost-btn,
.composer button {
  border: 0;
  border-radius: 7px;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.env-switch button {
  min-height: 32px;
  padding: 0 10px;
  color: var(--ops-muted);
  background: transparent;
  font-size: 12px;
}

.env-switch button.selected {
  color: var(--ops-text);
  background: var(--ops-accent-soft);
  box-shadow: inset 0 0 0 1px var(--ops-accent-border);
}

.status-pill {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  gap: 8px;
  padding: 0 11px;
  border: 1px solid var(--ops-line);
  border-radius: 8px;
  background: var(--ops-surface-raised);
  color: var(--ops-muted);
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.status-pill.live {
  color: var(--ops-green);
  border-color: color-mix(in srgb, var(--ops-success) 26%, transparent);
}

.status-pill.fallback {
  color: var(--ops-amber);
  border-color: color-mix(in srgb, var(--ops-warning) 30%, transparent);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ops-green);
}

.dot.warning {
  background: var(--ops-amber);
}

.dot.critical {
  background: var(--ops-red);
}

.refresh-btn {
  --el-button-bg-color: var(--ops-surface-raised);
  --el-button-border-color: var(--ops-line);
  --el-button-text-color: var(--ops-text);
  --el-button-hover-bg-color: var(--ops-surface-hover);
  --el-button-hover-border-color: var(--ops-accent-border);
  --el-button-hover-text-color: var(--ops-text);
  border-radius: 8px;
  font-weight: 800;
}

.fallback-banner {
  margin: 14px 22px 0;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--ops-warning) 30%, transparent);
  border-radius: 8px;
  background: var(--ops-warning-soft);
  color: var(--ops-warning);
  font-size: 12px;
  font-weight: 700;
}

.ops-grid {
  display: grid;
  grid-template-columns: minmax(440px, 1.35fr) minmax(330px, 0.86fr);
  grid-template-areas:
    "command context"
    "timeline context";
  gap: 18px;
  padding: 18px 22px 24px;
  align-items: start;
}

.ops-panel {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--ops-line);
  border-radius: 8px;
  background: var(--ops-panel);
  box-shadow: 0 22px 64px rgba(0, 0, 0, 0.28);
}

.command-panel {
  grid-area: command;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--ops-line-soft);
}

.panel-header.compact {
  padding-bottom: 12px;
}

.panel-header h2 {
  font-size: 15px;
}

.ghost-btn {
  min-height: 34px;
  padding: 0 12px;
  color: var(--ops-text);
  background: var(--ops-surface-raised);
  border: 1px solid var(--ops-line);
  white-space: nowrap;
}

.command-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 290px;
  min-height: 620px;
}

.chat-stream {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border-right: 1px solid var(--ops-line-soft);
}

.message {
  display: grid;
  gap: 8px;
  max-width: 94%;
}

.message.user {
  align-self: flex-end;
}

.meta {
  display: flex;
  gap: 8px;
  color: var(--ops-faint);
  font-size: 11px;
  font-weight: 800;
}

.bubble {
  padding: 13px 14px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-surface-raised);
  font-size: 13px;
  line-height: 1.6;
}

.message.user .bubble {
  background: var(--ops-surface-selected);
  border-color: var(--ops-accent-border);
}

.bubble p {
  margin: 0;
}

.answer-head {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 8px;
  color: var(--ops-green);
  font-weight: 800;
}

.confidence {
  margin-left: auto;
  padding: 4px 8px;
  border: 1px solid color-mix(in srgb, var(--ops-success) 26%, transparent);
  border-radius: 999px;
  color: var(--ops-text);
  background: var(--ops-success-soft);
  font-size: 11px;
}

.finding-grid,
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.finding-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 12px;
  gap: 8px;
}

.finding,
.metric-card {
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-bg-elevated);
}

.finding b,
.metric-card strong {
  display: block;
  margin-bottom: 3px;
  font-size: 18px;
  line-height: 1.1;
}

.finding span,
.metric-card span {
  color: var(--ops-muted);
  font-size: 11px;
  font-weight: 800;
}

.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  margin-top: auto;
}

.composer input {
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--ops-accent-border);
  border-radius: 8px;
  outline: none;
  background: var(--ops-bg-elevated);
  color: var(--ops-text);
}

.composer button {
  min-width: 84px;
  color: var(--ops-accent-text);
  background: var(--ops-cyan);
}

.tool-trace {
  display: grid;
  align-content: start;
  gap: 12px;
  padding: 16px;
  background: var(--ops-bg-elevated);
}

.trace-item {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

.trace-top,
.queue-item,
.risk-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.trace-top {
  font-size: 12px;
}

.trace-item code {
  display: block;
  padding: 9px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 6px;
  overflow-wrap: anywhere;
  background: var(--ops-bg-elevated);
  color: var(--ops-text-soft);
  font-size: 11px;
  line-height: 1.55;
}

.tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid var(--ops-line);
  border-radius: 999px;
  color: var(--ops-muted);
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.tag.green {
  color: var(--ops-green);
  border-color: color-mix(in srgb, var(--ops-success) 28%, transparent);
  background: var(--ops-success-soft);
}

.tag.amber {
  color: var(--ops-amber);
  border-color: color-mix(in srgb, var(--ops-warning) 30%, transparent);
  background: var(--ops-warning-soft);
}

.tag.red {
  color: var(--ops-red);
  border-color: color-mix(in srgb, var(--ops-danger) 30%, transparent);
  background: var(--ops-danger-soft);
}

.context-stack {
  grid-area: context;
  display: grid;
  gap: 18px;
}

.metrics-grid {
  padding: 0 16px 16px;
}

.runtime-strip {
  display: grid;
  gap: 12px;
  margin: 0 16px 16px;
  padding: 13px;
  border: 1px solid color-mix(in srgb, var(--ops-success) 24%, transparent);
  border-radius: 8px;
  background: var(--ops-surface);
}

.runtime-head,
.runtime-stats,
.provider-grid,
.provider-pill {
  display: flex;
  align-items: center;
}

.runtime-head {
  justify-content: space-between;
  gap: 10px;
}

.runtime-head span,
.runtime-stats span,
.provider-pill span {
  min-width: 0;
  color: var(--ops-muted);
  font-size: 11px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.runtime-head strong {
  color: var(--ops-green);
  font-size: 12px;
  text-transform: uppercase;
}

.runtime-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.runtime-stats div {
  min-width: 0;
  padding: 9px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-bg-elevated);
}

.runtime-stats b {
  display: block;
  color: var(--ops-text);
  font-size: 13px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.provider-grid {
  flex-wrap: wrap;
  gap: 8px;
}

.provider-pill {
  min-height: 30px;
  gap: 8px;
  padding: 0 9px;
  border: 1px solid var(--ops-accent-border);
  border-radius: 999px;
  background: var(--ops-accent-soft);
}

.provider-pill strong {
  color: var(--ops-cyan);
  font-size: 12px;
}

.metric-card.good strong {
  color: var(--ops-green);
}

.metric-card.warning strong {
  color: var(--ops-amber);
}

.metric-card.danger strong {
  color: var(--ops-red);
}

.topology-map {
  height: 260px;
  margin: 0 16px 16px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-bg-elevated);
}

.topology-node {
  position: absolute;
  min-width: 96px;
  padding: 9px 10px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-surface-raised);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
  font-size: 12px;
  font-weight: 800;
}

.topology-node span {
  display: block;
  margin-top: 3px;
  color: var(--ops-muted);
  font-size: 10px;
}

.topology-node.blue {
  border-color: var(--ops-accent-border);
}

.topology-node.green {
  border-color: color-mix(in srgb, var(--ops-success) 42%, transparent);
}

.topology-node.amber {
  border-color: color-mix(in srgb, var(--ops-warning) 46%, transparent);
}

.topology-node.red {
  border-color: color-mix(in srgb, var(--ops-danger) 52%, transparent);
}

.edge {
  position: absolute;
  height: 1px;
  background: var(--ops-accent-border);
  transform-origin: left center;
}

.risk-list {
  display: grid;
  gap: 0;
  padding: 0 16px 16px;
}

.risk-row {
  padding: 10px 0;
  border-top: 1px solid var(--ops-line-soft);
}

.risk-row strong,
.timeline-item strong,
.queue-item strong {
  font-size: 12px;
}

.severity {
  flex: 0 0 auto;
  width: 8px;
  height: 28px;
  border-radius: 4px;
  background: var(--ops-green);
}

.severity.warning {
  background: var(--ops-amber);
}

.severity.critical {
  background: var(--ops-red);
}

.risk-state {
  flex: 0 0 auto;
  color: var(--ops-muted);
  font-size: 11px;
  font-weight: 800;
}

.timeline-panel {
  grid-area: timeline;
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.timeline-column + .timeline-column {
  border-left: 1px solid var(--ops-line-soft);
}

.timeline-list,
.queue-list {
  display: grid;
  gap: 10px;
  padding: 0 18px 18px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 50px minmax(0, 1fr);
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--ops-line-soft);
}

.timeline-item > span {
  color: var(--ops-cyan);
  font-size: 12px;
  font-weight: 800;
}

.queue-item {
  padding: 12px;
  border: 1px solid var(--ops-line-soft);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

@media (max-width: 1180px) {
  .ops-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "command"
      "context"
      "timeline";
  }

  .context-stack {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .ops-topbar {
    grid-template-columns: 1fr;
  }

  .title-block {
    align-items: flex-start;
    flex-direction: column;
  }

  .top-actions {
    justify-content: flex-start;
  }

  .command-body,
  .timeline-panel,
  .context-stack {
    grid-template-columns: 1fr;
  }

  .chat-stream {
    border-right: 0;
    border-bottom: 1px solid var(--ops-line-soft);
  }

  .timeline-column + .timeline-column {
    border-left: 0;
    border-top: 1px solid var(--ops-line-soft);
  }
}

@media (max-width: 620px) {
  .ops-topbar,
  .ops-grid {
    padding-left: 12px;
    padding-right: 12px;
  }

  .ops-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .env-switch {
    width: 100%;
    overflow-x: auto;
  }

  .finding-grid,
  .metrics-grid,
  .composer {
    grid-template-columns: 1fr;
  }

  .message {
    max-width: 100%;
  }
}
</style>
