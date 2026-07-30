<template>
  <aside class="trace-sidebar" aria-label="Runtime signals">
    <div class="trace-search-row">
      <label class="trace-search">
        <n-icon aria-hidden="true"><SearchOutline /></n-icon>
        <input
          :value="query"
          type="search"
          placeholder="Search runtime signals"
          aria-label="Search runtime signals"
          @input="$emit('update:query', ($event.target as HTMLInputElement).value)"
        >
      </label>
      <button
        :class="['timeline-toggle', { active: timelineVisible }]"
        type="button"
        :aria-pressed="timelineVisible"
        @click="$emit('update:timelineVisible', !timelineVisible)"
      >
        <span class="toggle-track"><span class="toggle-knob" /></span>
        <strong>Signals</strong>
      </button>
    </div>

    <div class="trace-tree">
      <button
        :class="['trace-tree-node', 'root-node', { active: selectedId === 'root' }]"
        type="button"
        @click="$emit('select', 'root')"
      >
        <span class="span-icon list-icon" aria-hidden="true">
          <n-icon><DocumentTextOutline /></n-icon>
        </span>
        <span class="span-copy">
          <span class="span-title-row">
            <strong>runtime</strong>
            <em :class="['span-status', runtimeStatus.toLowerCase()]">{{ runtimeStatus }}</em>
          </span>
          <span class="span-metrics">
            <span>{{ mainDuration }}</span>
            <span>{{ totalCost }}</span>
          </span>
        </span>
        <span class="tree-action" aria-hidden="true">⌄</span>
      </button>

      <div v-if="timelineVisible" class="trace-children">
        <button
          v-for="step in steps"
          :key="step.id"
          :class="['trace-tree-node', 'child-node', { active: selectedId === step.id }]"
          type="button"
          :title="`${step.title} · ${step.meta}`"
          @click="$emit('select', step.id)"
        >
          <span :class="['span-icon', step.tone]" aria-hidden="true">{{ step.icon }}</span>
          <span class="span-copy">
            <span class="span-title-row">
              <strong>{{ step.title }}</strong>
              <em v-if="step.status" :class="['span-status', statusClass(step.status)]">{{ step.status }}</em>
            </span>
            <span class="span-metrics">
              <span v-if="step.duration">{{ step.duration }}</span>
              <span>{{ step.metric || step.meta }}</span>
            </span>
          </span>
          <span v-if="step.badge" class="debug-badge">{{ step.badge }}</span>
        </button>
      </div>

      <p v-if="timelineVisible && !steps.length" class="trace-empty">No spans match this search.</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import { DocumentTextOutline, SearchOutline } from '@vicons/ionicons5'
import type { TraceStep } from '@/types/trace'

defineProps<{
  steps: TraceStep[]
  selectedId: string
  query: string
  timelineVisible: boolean
  mainDuration: string
  totalCost: string
  runtimeStatus: string
}>()

defineEmits<{
  'update:query': [value: string]
  'update:timelineVisible': [value: boolean]
  select: [id: string]
}>()

function statusClass(status: string) {
  return status.toLowerCase().replace(/[^a-z0-9]+/g, '-')
}
</script>
