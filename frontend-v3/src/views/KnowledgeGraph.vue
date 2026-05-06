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
          <n-switch v-model:value="allNamespaces" size="small" />
        </label>
        <n-input v-model:value="namespace" class="namespace-input" placeholder="namespace" :disabled="allNamespaces" />
        <n-button :loading="loading" @click="loadGraph(false)">刷新</n-button>
        <n-button type="primary" :loading="syncing" @click="syncGraph">同步图谱</n-button>
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

    <div class="kg-layout">
      <section class="graph-panel">
        <div class="panel-head">
          <div>
            <div class="panel-title">拓扑关系</div>
            <div class="panel-subtitle">{{ graph?.updated_at ? `更新时间 ${formatTime(graph.updated_at)}` : '尚未同步' }}</div>
          </div>
          <div class="legend">
            <span v-for="kind in visibleKinds" :key="kind">
              <i :style="{ background: kindColor(kind) }" />
              {{ kindLabel(kind) }}
            </span>
          </div>
        </div>

        <div class="graph-canvas">
          <n-spin v-if="loading || syncing" />
          <n-empty v-else-if="!graph?.nodes.length" description="暂无图谱数据，点击同步图谱" />
          <svg
            v-else
            class="graph-svg"
            :viewBox="`0 0 ${layout.width} ${layout.height}`"
            role="img"
            aria-label="K8s knowledge graph"
          >
            <defs>
              <marker id="kg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
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
import { NAlert, NButton, NDataTable, NEmpty, NInput, NSpin, NSwitch, NTag, useMessage } from 'naive-ui'
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
  ingress: '#7c3aed',
  service: '#0891b2',
  deployment: '#2563eb',
  replicaset: '#4f46e5',
  pod: '#059669',
  node: '#d97706',
}

const selectedNode = computed(() => graph.value?.nodes.find((node) => node.id === selectedNodeId.value) || null)
const coverageText = computed(() => {
  const coverage = graph.value?.coverage.coverage ?? 0
  return `${Math.round(coverage * 100)}%`
})
const visibleKinds = computed(() => {
  const kinds = new Set((graph.value?.nodes || []).map((node) => node.kind))
  return kindOrder.filter((kind) => kinds.has(kind))
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
  await loadGraph(true)
})
</script>

<style scoped>
.kg-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.kg-header,
.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  font-size: 18px;
  font-weight: 650;
  line-height: 1.4;
}
.page-subtitle,
.panel-subtitle {
  margin-top: 2px;
  color: #8f9299;
  font-size: 13px;
}
.kg-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.all-ns-toggle {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #d3d8e3;
  font-size: 13px;
  white-space: nowrap;
}
.namespace-input {
  width: 180px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.stat-block {
  min-height: 68px;
  border: 1px solid #343434;
  border-radius: 8px;
  background: #202020;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}
.stat-label {
  color: #9ca3af;
  font-size: 12px;
}
.stat-block strong {
  color: #f8fafc;
  font-size: 22px;
  line-height: 1.2;
  overflow-wrap: anywhere;
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
  border: 1px solid #303036;
  border-radius: 8px;
  background: #17171a;
}
.graph-panel,
.table-panel {
  padding: 14px;
}
.detail-panel {
  padding: 14px;
}
.panel-title {
  color: #f3f4f6;
  font-size: 15px;
  font-weight: 650;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px 12px;
  max-width: 460px;
  color: #b7bbc4;
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
.graph-canvas {
  height: min(62vh, 640px);
  min-height: 460px;
  margin-top: 12px;
  display: grid;
  place-items: center;
  overflow: auto;
  border: 1px solid #24262d;
  border-radius: 8px;
  background:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    #101114;
  background-size: 28px 28px;
}
.graph-svg {
  width: 100%;
  min-width: 760px;
  height: 100%;
}
.graph-edge {
  fill: none;
  stroke: #64748b;
  stroke-width: 1.5;
  opacity: 0.72;
}
.graph-node {
  cursor: pointer;
  outline: none;
}
.graph-node rect {
  stroke: rgba(255, 255, 255, 0.18);
  stroke-width: 1;
}
.graph-node:hover rect,
.graph-node.selected rect {
  stroke: #e2e8f0;
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
  color: #f8fafc;
  font-size: 18px;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.detail-tags {
  display: flex;
  gap: 8px;
  margin: 10px 0 16px;
}
.detail-section {
  display: grid;
  gap: 6px;
  margin-top: 14px;
}
.detail-section span {
  color: #a6adbb;
  font-size: 12px;
}
.detail-section pre {
  max-height: 180px;
  margin: 0;
  overflow: auto;
  border: 1px solid #303036;
  border-radius: 8px;
  background: #101114;
  color: #dbe2ee;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  padding: 10px;
}
.table-panel {
  display: grid;
  gap: 12px;
}
:deep(.selected-row td) {
  background: rgba(50, 91, 141, 0.22) !important;
}
@media (max-width: 1100px) {
  .kg-header,
  .panel-head {
    display: block;
  }
  .kg-actions {
    margin-top: 12px;
  }
  .stats-grid,
  .kg-layout {
    grid-template-columns: 1fr;
  }
  .detail-panel {
    min-height: 260px;
  }
}
</style>
