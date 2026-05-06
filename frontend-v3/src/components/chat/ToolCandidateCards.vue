<template>
  <div v-if="hasCandidates" class="candidate-panel">
    <div class="candidate-header">
      <span>候选工具</span>
      <n-tag v-if="payload.query" size="tiny" round>{{ payload.query }}</n-tag>
      <n-tag v-if="payload.total !== undefined" size="tiny" round>{{ payload.total }} 个</n-tag>
    </div>

    <div class="layer-list">
      <section v-for="layer in displayLayers" :key="layer.name" class="candidate-layer">
        <div v-if="showLayerHeaders" class="layer-header">
          <div class="layer-title-row">
            <span class="layer-title">{{ layer.title }}</span>
            <span class="layer-count">{{ layer.total }} 个</span>
          </div>
          <div v-if="layer.description" class="layer-desc">{{ layer.description }}</div>
        </div>

        <div v-for="group in layer.categoryGroups" :key="`${layer.name}-${group.category}`" class="category-section">
          <div v-if="showGroupHeader(layer, group)" class="category-header">
            <span>{{ group.title || group.category }}</span>
            <span>{{ group.total }} 个</span>
          </div>

          <div class="candidate-list">
            <div v-for="tool in group.results" :key="`${layer.name}-${group.category}-${tool.name}`" class="candidate-card">
              <div class="candidate-top">
                <div class="candidate-title">{{ tool.title || tool.name }}</div>
                <div class="candidate-tags">
                  <n-tag size="tiny" :type="dangerTagType(tool.dangerLevel)">{{ dangerLabel(tool.dangerLevel) }}</n-tag>
                  <n-tag size="tiny" :type="policyTagType(tool.executionPolicy)">{{ policyLabel(tool.executionPolicy) }}</n-tag>
                </div>
              </div>
              <div class="candidate-name">{{ tool.name }}</div>
              <div v-if="tool.description" class="candidate-desc">{{ tool.description }}</div>
              <div v-if="tool.available === false && tool.unavailableReason" class="candidate-unavailable">
                {{ tool.unavailableReason }}
              </div>
              <div class="candidate-meta">
                <span>{{ tool.category || 'uncategorized' }}</span>
                <span>{{ tool.server || 'unknown' }}</span>
                <span v-if="tool.score !== undefined">score {{ tool.score }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
  <div v-else-if="payload.reason" class="empty-result">{{ payload.reason }}</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'
import type {
  ToolCandidateCategoryGroup,
  ToolCandidateRelevanceLayer,
  ToolDangerLevel,
  ToolExecutionPolicy,
  ToolSearchResponse,
} from '@/types'

const props = defineProps<{ payload: ToolSearchResponse }>()

const candidates = computed(() => props.payload.results || [])
const displayLayers = computed<ToolCandidateRelevanceLayer[]>(() => {
  const layers = props.payload.relevanceLayers?.filter((layer) => layer.total > 0)
  if (layers?.length) return layers

  const groups = props.payload.categoryGroups?.filter((group) => group.total > 0)
  if (groups?.length) {
    return [fallbackLayer('候选工具', groups)]
  }

  if (candidates.value.length) {
    return [
      fallbackLayer('候选工具', [
        {
          category: 'all',
          title: '全部',
          total: candidates.value.length,
          results: candidates.value,
        },
      ]),
    ]
  }

  return []
})
const hasCandidates = computed(() => displayLayers.value.some((layer) => layer.total > 0))
const showLayerHeaders = computed(() => Boolean(props.payload.relevanceLayers?.length) || displayLayers.value.length > 1)

function fallbackLayer(title: string, groups: ToolCandidateCategoryGroup[]): ToolCandidateRelevanceLayer {
  return {
    name: 'direct',
    title,
    total: groups.reduce((sum, group) => sum + group.total, 0),
    categoryGroups: groups,
    results: groups.flatMap((group) => group.results),
  }
}

function showGroupHeader(layer: ToolCandidateRelevanceLayer, group: ToolCandidateCategoryGroup) {
  return layer.categoryGroups.length > 1 || group.category !== 'all'
}

function dangerLabel(level?: ToolDangerLevel) {
  if (level === 'write') return '写入'
  if (level === 'dangerous') return '高危'
  return '只读'
}

function dangerTagType(level?: ToolDangerLevel) {
  if (level === 'dangerous') return 'error'
  if (level === 'write') return 'warning'
  return 'info'
}

function policyLabel(policy?: ToolExecutionPolicy) {
  if (policy === 'unavailable') return '不可用'
  if (policy === 'catalog_only') return '仅目录'
  if (policy === 'external_mcp') return '外部 MCP'
  return '可执行'
}

function policyTagType(policy?: ToolExecutionPolicy) {
  if (policy === 'unavailable') return 'error'
  if (policy === 'catalog_only') return 'default'
  if (policy === 'external_mcp') return 'warning'
  return 'success'
}
</script>

<style scoped>
.candidate-panel {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #383838;
}
.candidate-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c9c9c9;
  font-size: 12px;
  margin-bottom: 8px;
}
.layer-list {
  display: grid;
  gap: 12px;
}
.candidate-layer {
  display: grid;
  gap: 8px;
}
.layer-header {
  display: grid;
  gap: 2px;
}
.layer-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.layer-title {
  color: #f0f0f0;
  font-size: 13px;
  font-weight: 600;
}
.layer-count,
.layer-desc,
.category-header {
  color: #999;
  font-size: 12px;
}
.category-section {
  display: grid;
  gap: 6px;
}
.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.candidate-list {
  display: grid;
  gap: 8px;
}
.candidate-card {
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  padding: 8px;
  background: #222;
}
.candidate-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.candidate-title {
  font-weight: 600;
  line-height: 1.4;
  color: #f0f0f0;
}
.candidate-tags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.candidate-name {
  margin-top: 2px;
  color: #a0a0a0;
  font-size: 12px;
  word-break: break-all;
}
.candidate-desc {
  margin-top: 6px;
  color: #d0d0d0;
  line-height: 1.5;
  font-size: 13px;
}
.candidate-unavailable {
  margin-top: 6px;
  color: #ffb4ab;
  line-height: 1.5;
  font-size: 12px;
}
.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  color: #909090;
  font-size: 12px;
}
.empty-result {
  margin-top: 8px;
  color: #999;
  font-size: 12px;
}
</style>
