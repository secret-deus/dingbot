<template>
  <div class="kg-page">
    <div class="kg-header">
      <div>
        <div class="page-title">K8s 知识图谱</div>
        <div class="page-subtitle">从 Kubernetes API 同步拓扑关系，展示 Ingress、Service、Workload、Pod 与 Node 的依赖链路</div>
      </div>
      <div class="kg-actions">
        <label class="all-ns-toggle">
          <span>全部命名空间</span>
          <n-switch v-model:value="allNamespaces" size="small" :disabled="graphBusy" />
        </label>
        <n-input v-model:value="namespace" class="namespace-input" placeholder="namespace" :disabled="allNamespaces || graphBusy" />
        <n-button :loading="loading" :disabled="graphBusy" @click="loadGraph(false)">刷新</n-button>
        <n-popconfirm
          positive-text="同步"
          negative-text="取消"
          :positive-button-props="syncPositiveButtonProps"
          :negative-button-props="{ size: 'small' }"
          @positive-click="syncGraph"
        >
          <template #trigger>
            <n-button type="primary" :loading="syncing" :disabled="graphBusy">同步图谱</n-button>
          </template>
          同步 Kubernetes 知识图谱（{{ syncScopeLabel }}）？此操作会重新拉取集群拓扑。
        </n-popconfirm>
      </div>
    </div>

    <n-alert v-if="error" type="error" :bordered="false">{{ error }}</n-alert>

    <div class="stats-grid">
      <div class="stat-block">
        <span class="stat-label">节点</span>
        <strong>{{ graph?.summary.nodes ?? 0 }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">关系</span>
        <strong>{{ graph?.summary.edges ?? 0 }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">命名空间</span>
        <strong>{{ graph?.all_namespaces ? '全部' : graph?.namespace || '-' }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">指标覆盖</span>
        <strong>{{ coverageText }}</strong>
      </div>
    </div>

    <section class="kg-insight-strip" aria-label="图谱态势">
      <article :class="['insight-card', freshnessTone]">
        <span class="insight-kicker">Graph freshness</span>
        <strong>{{ freshnessTitle }}</strong>
        <small>{{ freshnessDetail }}</small>
      </article>
      <article :class="['insight-card', metricCoverageTone]">
        <span class="insight-kicker">Metric coverage</span>
        <strong>{{ metricCoverageTitle }}</strong>
        <small>{{ metricCoverageDetail }}</small>
      </article>
      <article class="insight-card">
        <span class="insight-kicker">Topology focus</span>
        <strong>{{ topologyFocusTitle }}</strong>
        <small>{{ topologyFocusDetail }}</small>
      </article>
    </section>

    <section v-if="graphAttentionItems.length" class="attention-list" aria-label="图谱关注项">
      <article v-for="item in graphAttentionItems" :key="item.title" class="attention-item">
        <span>{{ item.label }}</span>
        <strong>{{ item.title }}</strong>
        <small>{{ item.detail }}</small>
      </article>
    </section>

    <div class="kg-layout">
      <section class="graph-panel">
        <div class="panel-head">
          <div>
            <div class="panel-title">拓扑关系</div>
            <div class="panel-subtitle">{{ graph?.updated_at ? `更新时间 ${formatTime(graph.updated_at)}` : '尚未同步' }}</div>
          </div>
          <div class="graph-tools">
            <div class="legend">
              <span v-for="kind in visibleKinds" :key="kind">
                <i :style="{ background: kindColor(kind) }" />
                {{ kindLabel(kind) }}
              </span>
            </div>
            <div class="zoom-controls" aria-label="拓扑图缩放">
              <button type="button" :disabled="graphZoom <= minGraphZoom" aria-label="缩小拓扑图" @click="zoomGraph(-0.15)">−</button>
              <button type="button" aria-label="重置拓扑图缩放" @click="resetGraphZoom">{{ graphZoomPercent }}</button>
              <button type="button" :disabled="graphZoom >= maxGraphZoom" aria-label="放大拓扑图" @click="zoomGraph(0.15)">＋</button>
            </div>
          </div>
        </div>

        <div class="graph-canvas" @wheel="onGraphWheel">
          <n-spin v-if="loading || syncing" />
          <n-empty v-else-if="!graph?.nodes.length" description="暂无图谱数据，点击同步图谱" />
          <div v-else class="graph-viewport">
            <svg
              class="graph-svg"
              :style="graphSvgStyle"
              :viewBox="`0 0 ${layout.width} ${layout.height}`"
              role="img"
              aria-label="K8s knowledge graph"
            >
              <defs>
                <marker id="kg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#7b8794" />
                </marker>
              </defs>
              <path
                v-for="edge in layout.edges"
                :key="edge.id"
                class="graph-edge"
                :d="edge.path"
                marker-end="url(#kg-arrow)"
              >
                <title>{{ edge.type }}</title>
              </path>
              <g
                v-for="item in layout.nodes"
                :key="item.node.id"
                :class="['graph-node', { selected: selectedNodeId === item.node.id }]"
                :transform="`translate(${item.x}, ${item.y})`"
                tabindex="0"
                @click="selectNode(item.node.id)"
                @keydown.enter="selectNode(item.node.id)"
              >
                <rect :fill="kindColor(item.node.kind)" rx="8" ry="8" width="136" height="58" />
                <text class="node-kind" x="12" y="20">{{ kindLabel(item.node.kind) }}</text>
                <text class="node-name" x="12" y="42">{{ trimName(item.node.name) }}</text>
                <title>{{ item.node.kind }} / {{ item.node.name }}</title>
              </g>
            </svg>
          </div>
        </div>
      </section>

      <aside class="detail-panel">
        <div class="panel-title">节点详情</div>
        <template v-if="selectedNode">
          <div class="detail-title">{{ selectedNode.name }}</div>
          <div class="detail-tags">
            <n-tag size="small" :color="{ color: kindColor(selectedNode.kind), textColor: '#fff', borderColor: kindColor(selectedNode.kind) }">
              {{ kindLabel(selectedNode.kind) }}
            </n-tag>
            <n-tag size="small">{{ selectedNode.namespace || 'cluster' }}</n-tag>
          </div>
          <div class="relation-summary" aria-label="节点关系概览">
            <div>
              <span>上游</span>
              <strong>{{ selectedIncomingEdges.length }}</strong>
            </div>
            <div>
              <span>下游</span>
              <strong>{{ selectedOutgoingEdges.length }}</strong>
            </div>
            <div>
              <span>指标</span>
              <strong>{{ selectedNodeHasMetrics ? '有' : '无' }}</strong>
            </div>
          </div>
          <div v-if="selectedRelationText" class="relation-line">{{ selectedRelationText }}</div>
          <div class="detail-section">
            <span>Labels</span>
            <pre>{{ formatObject(selectedNode.labels) }}</pre>
          </div>
          <div class="detail-section">
            <span>Attributes</span>
            <pre>{{ formatObject(selectedNode.attributes) }}</pre>
          </div>
          <div class="detail-section">
            <span>Metrics</span>
            <pre>{{ formatObject(selectedNode.metrics) }}</pre>
          </div>
        </template>
        <n-empty v-else description="选择图谱节点查看详情" />
      </aside>
    </div>

    <section class="table-panel">
      <div class="panel-title">节点列表</div>
      <n-data-table
        :columns="nodeColumns"
        :data="graph?.nodes || []"
        :pagination="{ pageSize: 8 }"
        size="small"
        :row-props="rowProps"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { NAlert, NButton, NDataTable, NEmpty, NInput, NPopconfirm, NSpin, NSwitch, NTag, useMessage } from 'naive-ui'
import { systemApi } from '@/api/client'
import type { K8sKnowledgeGraph, KnowledgeGraphEdge, KnowledgeGraphNode } from '@/types'

const message = useMessage()
const namespace = ref('default')
const allNamespaces = ref(true)
const graph = ref<K8sKnowledgeGraph | null>(null)
const loading = ref(false)
const syncing = ref(false)
const error = ref('')
const selectedNodeId = ref('')
const minGraphZoom = 0.6
const maxGraphZoom = 2.4
const graphZoom = ref(1)

const kindOrder = ['ingress', 'service', 'deployment', 'replicaset', 'pod', 'node']
const kindNames: Record<string, string> = {
  ingress: 'Ingress',
  service: 'Service',
  deployment: 'Deployment',
  replicaset: 'ReplicaSet',
  pod: 'Pod',
  node: 'Node',
}
const kindColors: Record<string, string> = {
  ingress: '#4d6786',
  service: '#315a85',
  deployment: '#0f766e',
  replicaset: '#53616f',
  pod: '#49766c',
  node: '#5b6f99',
}

const selectedNode = computed(() => graph.value?.nodes.find((node) => node.id === selectedNodeId.value) || null)
const coverageText = computed(() => {
  const coverage = graph.value?.coverage.coverage ?? 0
  return `${Math.round(coverage * 100)}%`
})
const syncScopeLabel = computed(() => allNamespaces.value ? '全部命名空间' : (namespace.value.trim() || 'default'))
const graphBusy = computed(() => loading.value || syncing.value)
const syncPositiveButtonProps = computed(() => ({
  type: 'primary' as const,
  size: 'small' as const,
  disabled: graphBusy.value,
  loading: syncing.value,
}))
const visibleKinds = computed(() => {
  const kinds = new Set((graph.value?.nodes || []).map((node) => node.kind))
  return kindOrder.filter((kind) => kinds.has(kind))
})
const graphZoomPercent = computed(() => `${Math.round(graphZoom.value * 100)}%`)
const graphSvgStyle = computed(() => ({
  width: `${Math.round(layout.value.width * graphZoom.value)}px`,
  height: `${Math.round(layout.value.height * graphZoom.value)}px`,
}))
const graphAgeDays = computed(() => {
  if (!graph.value?.updated_at) return null
  const updatedAt = new Date(graph.value.updated_at)
  if (Number.isNaN(updatedAt.getTime())) return null
  return Math.max(0, Math.floor((Date.now() - updatedAt.getTime()) / 86_400_000))
})
const freshnessTone = computed(() => {
  if (!graph.value?.nodes.length || graphAgeDays.value === null) return 'blocked'
  if (graphAgeDays.value > 7) return 'watch'
  return 'ready'
})
const freshnessTitle = computed(() => {
  if (!graph.value?.nodes.length) return 'No graph snapshot'
  if (graphAgeDays.value === null) return 'Unknown update time'
  if (graphAgeDays.value === 0) return 'Updated today'
  return `${graphAgeDays.value} days old`
})
const freshnessDetail = computed(() => {
  if (!graph.value?.nodes.length) return 'Sync the graph before using topology data for diagnostics.'
  if (!graph.value?.updated_at) return 'The current graph snapshot does not include an update timestamp.'
  return `Last synced at ${formatTime(graph.value.updated_at)}. Refresh before incident triage if this is stale.`
})
const metricCoverageTone = computed(() => {
  const coverage = graph.value?.coverage.coverage ?? 0
  if (!graph.value?.nodes.length) return 'blocked'
  if (coverage < 0.5) return 'watch'
  return 'ready'
})
const metricCoverageTitle = computed(() => `${graph.value?.coverage.nodes_with_metrics ?? 0}/${graph.value?.coverage.total_nodes ?? 0} nodes with metrics`)
const metricCoverageDetail = computed(() => {
  const coverage = graph.value?.coverage.coverage ?? 0
  return `${Math.round(coverage * 100)}% coverage; nodes without metrics still need topology-only interpretation.`
})
const topologyFocusTitle = computed(() => {
  const topKind = nodeTypeEntries.value[0]
  return topKind ? `${topKind.count} ${kindLabel(topKind.kind)} nodes` : 'No dominant resource'
})
const topologyFocusDetail = computed(() => {
  if (!graph.value?.nodes.length) return 'No topology resource is available in the current snapshot.'
  const edgeTypes = Object.entries(graph.value.summary.edge_types || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 2)
    .map(([type, count]) => `${count} ${type}`)
  return edgeTypes.length ? `Main relations: ${edgeTypes.join(', ')}.` : 'No relation edges are visible in the current snapshot.'
})
const nodeTypeEntries = computed(() => Object.entries(graph.value?.summary.node_types || {})
  .map(([kind, count]) => ({ kind, count }))
  .sort((a, b) => b.count - a.count))
const selectedIncomingEdges = computed(() => (graph.value?.edges || []).filter((edge) => edge.target === selectedNodeId.value))
const selectedOutgoingEdges = computed(() => (graph.value?.edges || []).filter((edge) => edge.source === selectedNodeId.value))
const selectedNodeHasMetrics = computed(() => Boolean(selectedNode.value && Object.keys(selectedNode.value.metrics || {}).length))
const selectedRelationText = computed(() => {
  if (!selectedNode.value) return ''
  const upstream = selectedIncomingEdges.value[0]?.source
  const downstream = selectedOutgoingEdges.value[0]?.target
  const upstreamNode = upstream ? graph.value?.nodes.find((node) => node.id === upstream) : null
  const downstreamNode = downstream ? graph.value?.nodes.find((node) => node.id === downstream) : null
  if (upstreamNode && downstreamNode) return `${kindLabel(upstreamNode.kind)} ${upstreamNode.name} -> ${kindLabel(selectedNode.value.kind)} -> ${kindLabel(downstreamNode.kind)} ${downstreamNode.name}`
  if (upstreamNode) return `Upstream: ${kindLabel(upstreamNode.kind)} ${upstreamNode.name}`
  if (downstreamNode) return `Downstream: ${kindLabel(downstreamNode.kind)} ${downstreamNode.name}`
  return 'No direct relation is visible for this node.'
})
const graphAttentionItems = computed(() => {
  const items: Array<{ label: string; title: string; detail: string }> = []
  if (!graph.value?.nodes.length) {
    items.push({ label: 'Graph', title: 'No topology snapshot', detail: 'Run sync before using the graph page for diagnostics.' })
    return items
  }
  if (graphAgeDays.value !== null && graphAgeDays.value > 7) {
    items.push({ label: 'Freshness', title: `${graphAgeDays.value} days since last sync`, detail: 'Topology can drift quickly after deployments or namespace changes.' })
  }
  if ((graph.value.coverage.coverage ?? 0) < 0.5) {
    items.push({ label: 'Metrics', title: 'Low metric coverage', detail: `${graph.value.coverage.nodes_with_metrics}/${graph.value.coverage.total_nodes} nodes include metrics.` })
  }
  const isolatedCount = graph.value.nodes.filter((node) =>
    !graph.value?.edges.some((edge) => edge.source === node.id || edge.target === node.id),
  ).length
  if (isolatedCount) {
    items.push({ label: 'Topology', title: `${isolatedCount} isolated nodes`, detail: 'These resources have no visible upstream or downstream relation in this snapshot.' })
  }
  return items
})

const layout = computed(() => {
  const nodes = graph.value?.nodes || []
  const edges = graph.value?.edges || []
  const kinds = [
    ...kindOrder.filter((kind) => nodes.some((node) => node.kind === kind)),
    ...Array.from(new Set(nodes.map((node) => node.kind))).filter((kind) => !kindOrder.includes(kind)),
  ]
  const columnGap = 180
  const rowGap = 92
  const left = 42
  const top = 64
  const nodeWidth = 136
  const nodeHeight = 58
  const byKind = new Map<string, KnowledgeGraphNode[]>()
  for (const kind of kinds) {
    byKind.set(kind, nodes.filter((node) => node.kind === kind).sort((a, b) => a.name.localeCompare(b.name)))
  }
  const maxRows = Math.max(1, ...Array.from(byKind.values()).map((items) => items.length))
  const width = Math.max(760, left * 2 + (Math.max(kinds.length, 1) - 1) * columnGap + nodeWidth)
  const height = Math.max(460, top * 2 + maxRows * rowGap)
  const positions = new Map<string, { x: number; y: number; node: KnowledgeGraphNode }>()
  kinds.forEach((kind, columnIndex) => {
    const items = byKind.get(kind) || []
    const columnHeight = (items.length - 1) * rowGap
    const startY = Math.max(top, (height - columnHeight - nodeHeight) / 2)
    items.forEach((node, rowIndex) => {
      positions.set(node.id, {
        x: left + columnIndex * columnGap,
        y: startY + rowIndex * rowGap,
        node,
      })
    })
  })
  const renderedEdges = edges.flatMap((edge: KnowledgeGraphEdge, index) => {
    const source = positions.get(edge.source)
    const target = positions.get(edge.target)
    if (!source || !target) return []
    const sx = source.x + nodeWidth
    const sy = source.y + nodeHeight / 2
    const tx = target.x
    const ty = target.y + nodeHeight / 2
    const bend = Math.max(42, Math.abs(tx - sx) / 2)
    return [{
      id: `${edge.source}-${edge.target}-${edge.type}-${index}`,
      type: edge.type,
      path: `M ${sx} ${sy} C ${sx + bend} ${sy}, ${tx - bend} ${ty}, ${tx} ${ty}`,
    }]
  })
  return {
    width,
    height,
    nodes: Array.from(positions.values()),
    edges: renderedEdges,
  }
})

const nodeColumns = [
  {
    title: '类型',
    key: 'kind',
    width: 130,
    render: (row: KnowledgeGraphNode) => h(
      NTag,
      { size: 'small', color: { color: kindColor(row.kind), textColor: '#fff', borderColor: kindColor(row.kind) } },
      { default: () => kindLabel(row.kind) },
    ),
  },
  { title: '名称', key: 'name' },
  { title: '命名空间', key: 'namespace', width: 180, render: (row: KnowledgeGraphNode) => row.namespace || 'cluster' },
]

function rowProps(row: KnowledgeGraphNode) {
  return {
    class: row.id === selectedNodeId.value ? 'selected-row' : '',
    onClick: () => selectNode(row.id),
  }
}

async function loadGraph(autoSync = false) {
  if (graphBusy.value) return
  loading.value = true
  error.value = ''
  try {
    graph.value = await systemApi.k8sKnowledgeGraph({
      namespace: namespace.value.trim() || undefined,
      all_namespaces: allNamespaces.value,
      auto_sync: autoSync,
    })
    ensureSelectedNode()
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

async function syncGraph() {
  if (graphBusy.value) return
  syncing.value = true
  error.value = ''
  try {
    const result = await systemApi.syncK8sKnowledgeGraph({
      namespace: namespace.value.trim() || undefined,
      all_namespaces: allNamespaces.value,
    })
    graph.value = result.graph
    ensureSelectedNode()
    message.success('知识图谱已同步')
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    syncing.value = false
  }
}

async function loadDefaultNamespace() {
  try {
    const config = await systemApi.mcpConfig()
    namespace.value = config.k8s.namespace || 'default'
  } catch {
    namespace.value = 'default'
  }
}

function ensureSelectedNode() {
  if (!graph.value?.nodes.length) {
    selectedNodeId.value = ''
    return
  }
  if (!graph.value.nodes.some((node) => node.id === selectedNodeId.value)) {
    selectedNodeId.value = graph.value.nodes[0].id
  }
}

function selectNode(id: string) {
  selectedNodeId.value = id
}

function clampZoom(value: number) {
  return Math.min(maxGraphZoom, Math.max(minGraphZoom, Number(value.toFixed(2))))
}

function zoomGraph(delta: number) {
  graphZoom.value = clampZoom(graphZoom.value + delta)
}

function resetGraphZoom() {
  graphZoom.value = 1
}

function onGraphWheel(event: WheelEvent) {
  if (!graph.value?.nodes.length) return
  if (!event.ctrlKey && !event.metaKey) return
  event.preventDefault()
  zoomGraph(event.deltaY > 0 ? -0.12 : 0.12)
}

function kindLabel(kind: string) {
  return kindNames[kind] || kind
}

function kindColor(kind: string) {
  return kindColors[kind] || '#64748b'
}

function trimName(value: string) {
  return value.length > 18 ? `${value.slice(0, 16)}...` : value
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function formatObject(value: unknown) {
  if (!value || (typeof value === 'object' && !Object.keys(value as Record<string, unknown>).length)) return '{}'
  return JSON.stringify(value, null, 2)
}

function errorMessage(err: unknown) {
  const maybe = err as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = maybe.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail) return JSON.stringify(detail)
  return maybe.message || '知识图谱请求失败'
}

onMounted(async () => {
  await loadDefaultNamespace()
  await loadGraph(false)
})
</script>

<style scoped>
.kg-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  color: var(--dr-text);
}
.kg-header,
.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  color: var(--dr-text);
  font-size: var(--dr-text-2xl);
  font-weight: 620;
  line-height: 1.12;
}
.page-subtitle,
.panel-subtitle {
  margin-top: 7px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-md);
}
.kg-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.all-ns-toggle {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--dr-text-soft);
  font-size: 13px;
  white-space: nowrap;
}
.namespace-input {
  width: 180px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.stat-block {
  min-height: 72px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #ffffff;
  padding: 11px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  box-shadow: none;
}
.stat-label {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  font-weight: 570;
}
.stat-block strong {
  color: var(--dr-text);
  font-size: 18px;
  font-weight: 610;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.kg-insight-strip {
  display: grid;
  grid-template-columns: 1fr 1fr 1.15fr;
  gap: 10px;
}
.insight-card {
  min-width: 0;
  min-height: 96px;
  padding: 13px 14px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #ffffff;
}
.insight-card.ready {
  border-color: #b8e3d1;
  background: #f0fdf4;
}
.insight-card.watch {
  border-color: #f3d89b;
  background: #fffbeb;
}
.insight-card.blocked {
  border-color: #f2b8b5;
  background: #fff5f5;
}
.insight-kicker {
  display: block;
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 750;
  text-transform: uppercase;
}
.insight-card strong {
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
.insight-card small {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.attention-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}
.attention-item {
  min-width: 0;
  min-height: 82px;
  padding: 12px 14px;
  border: 1px solid #f3d89b;
  border-radius: 8px;
  background: #fffbeb;
}
.attention-item span {
  display: inline-flex;
  min-height: 22px;
  align-items: center;
  padding: 0 7px;
  border-radius: 999px;
  background: #ffffff;
  color: #92400e;
  font-size: 11px;
  font-weight: 750;
}
.attention-item strong {
  display: block;
  margin-top: 8px;
  color: var(--dr-text);
  font-size: 14px;
  font-weight: 650;
}
.attention-item small {
  display: -webkit-box;
  margin-top: 5px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.kg-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 12px;
}
.graph-panel,
.detail-panel,
.table-panel {
  min-width: 0;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface-lift);
  box-shadow: none;
  overflow: hidden;
}
.graph-panel,
.table-panel {
  padding: 0;
}
.detail-panel {
  padding: 14px;
}
.graph-panel .panel-head {
  min-height: 56px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: #fbfcfe;
}
.table-panel > .panel-title {
  min-height: 48px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: #fbfcfe;
}
.panel-title {
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 610;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px 12px;
  max-width: 460px;
  color: var(--dr-text-soft);
  font-size: 12px;
}
.legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.legend i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}
.graph-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px 14px;
}
.zoom-controls {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px;
  border-radius: 7px;
  background: #f1f5f9;
}
.zoom-controls button {
  min-width: 34px;
  height: 30px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: var(--dr-text);
  cursor: pointer;
  font-weight: 650;
}
.zoom-controls button:hover {
  background: #ffffff;
}
.zoom-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}
.graph-canvas {
  height: min(62vh, 640px);
  min-height: 460px;
  margin: 14px;
  display: block;
  overflow: auto;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #ffffff;
}
.graph-viewport {
  min-width: 100%;
  min-height: 100%;
  display: grid;
  place-items: center;
  padding: 16px;
}
.graph-svg {
  display: block;
  flex: 0 0 auto;
  min-width: 760px;
}
.graph-edge {
  fill: none;
  stroke: #7b8794;
  stroke-width: 1.5;
  opacity: 0.68;
}
.graph-node {
  cursor: pointer;
  outline: none;
}
.graph-node rect {
  stroke: rgba(255, 255, 255, 0.82);
  stroke-width: 1;
}
.graph-node:hover rect,
.graph-node.selected rect {
  stroke: #111827;
  stroke-width: 2;
}
.node-kind {
  fill: rgba(255, 255, 255, 0.74);
  font-size: 11px;
  font-weight: 650;
  pointer-events: none;
}
.node-name {
  fill: #fff;
  font-size: 13px;
  font-weight: 750;
  pointer-events: none;
}
.detail-title {
  margin-top: 12px;
  color: var(--dr-text);
  font-size: 18px;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.detail-tags {
  display: flex;
  gap: 8px;
  margin: 10px 0 16px;
}
.relation-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.relation-summary > div {
  min-height: 58px;
  padding: 9px 10px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #fbfcfe;
}
.relation-summary span {
  display: block;
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 650;
}
.relation-summary strong {
  display: block;
  margin-top: 5px;
  color: var(--dr-text);
  font-size: 18px;
  font-weight: 680;
}
.relation-line {
  margin-bottom: 14px;
  padding: 9px 10px;
  border-left: 3px solid #94a3b8;
  background: #f8fafc;
  color: var(--dr-text-soft);
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.detail-section {
  display: grid;
  gap: 6px;
  margin-top: 14px;
}
.detail-section span {
  color: var(--dr-text-muted);
  font-size: 12px;
}
.detail-section pre {
  max-height: 180px;
  margin: 0;
  overflow: auto;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #fbfcfe;
  color: var(--dr-text-soft);
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  padding: 10px;
}
.table-panel {
  display: grid;
  gap: 0;
}
.table-panel :deep(.n-data-table) {
  border: 0;
}
:deep(.selected-row td) {
  background: var(--dr-accent-wash) !important;
}
@media (max-width: 1100px) {
  .kg-header,
  .panel-head {
    display: block;
  }
  .kg-actions {
    margin-top: 12px;
    flex-wrap: wrap;
    align-items: flex-start;
    width: 100%;
  }
  .all-ns-toggle {
    width: 100%;
  }
  .namespace-input {
    flex: 1 1 140px;
    min-width: 0;
    width: auto;
  }
  .stats-grid,
  .kg-insight-strip,
  .kg-layout {
    grid-template-columns: 1fr;
  }
  .detail-panel {
    min-height: 260px;
  }
}
</style>
