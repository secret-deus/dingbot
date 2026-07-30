<template>
  <main class="trace-detail" aria-label="Runtime detail">
    <section class="detail-heading">
      <div>
        <div class="detail-name">
          <span :class="['span-icon', selectedStep ? selectedStep.tone : 'list-icon']" aria-hidden="true">
            <n-icon v-if="!selectedStep"><DocumentTextOutline /></n-icon>
            <span v-else>{{ selectedStep.icon }}</span>
          </span>
          <h2>{{ selectedStep?.title || 'runtime' }}</h2>
          <button class="copy-id" type="button" @click="$emit('copy', 'Snapshot ID', traceId)">ID</button>
        </div>
        <p>{{ timestamp }}</p>
      </div>
    </section>

    <section class="trace-chips" aria-label="Runtime metadata">
      <button
        v-for="chip in chips"
        :key="chip.label"
        :class="['chip', { dark: chip.dark }]"
        type="button"
        @click="$emit('copy', chip.label, chip.value)"
      >
        {{ chip.label }}: {{ chip.value }}
      </button>
    </section>

    <nav class="trace-tabs" aria-label="Runtime sections">
      <button :class="{ active: activeTab === 'preview' }" type="button" @click="$emit('update:activeTab', 'preview')">
        Preview
      </button>
      <button :class="{ active: activeTab === 'scores' }" type="button" @click="$emit('update:activeTab', 'scores')">
        Scores
      </button>
      <div class="format-toggle" role="group" aria-label="Trace output format">
        <button :class="{ active: format === 'formatted' }" type="button" @click="$emit('update:format', 'formatted')">
          Formatted
        </button>
        <button :class="{ active: format === 'json' }" type="button" @click="$emit('update:format', 'json')">
          JSON
        </button>
      </div>
    </nav>

    <template v-if="activeTab === 'preview'">
      <section class="io-block">
        <div class="io-head">
          <h3>Input</h3>
          <button type="button" @click="$emit('copy', 'Input', inputText)">View as markdown <n-icon><CopyOutline /></n-icon></button>
        </div>
        <pre class="input-box">{{ renderedInput }}</pre>
      </section>

      <section class="io-block">
        <div class="io-head">
          <h3>Output</h3>
          <button type="button" @click="$emit('copy', 'Output', outputText)">View as markdown <n-icon><CopyOutline /></n-icon></button>
        </div>
        <pre class="output-box">{{ renderedOutput }}</pre>
      </section>

      <section class="io-block metadata-block">
        <div class="io-head">
          <h3>Metadata</h3>
          <button type="button" aria-label="复制 metadata" @click="$emit('copy', 'Metadata', metadataText)">
            <n-icon><CopyOutline /></n-icon>
          </button>
        </div>
        <pre class="metadata-box">{{ metadataText }}</pre>
      </section>
    </template>

    <section v-else class="score-grid" aria-label="Trace scores">
      <article v-for="score in scores" :key="score.label" :class="['score-card', score.tone]">
        <span>{{ score.label }}</span>
        <strong>{{ score.value }}</strong>
        <small>{{ score.detail }}</small>
      </article>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NIcon } from 'naive-ui'
import { CopyOutline, DocumentTextOutline } from '@vicons/ionicons5'
import type { TraceChip, TraceFormat, TraceScore, TraceStep, TraceTab } from '@/types/trace'

const props = defineProps<{
  traceId: string
  timestamp: string
  selectedStep?: TraceStep
  chips: TraceChip[]
  activeTab: TraceTab
  format: TraceFormat
  inputText: string
  outputText: string
  metadataText: string
  scores: TraceScore[]
}>()

defineEmits<{
  'update:activeTab': [value: TraceTab]
  'update:format': [value: TraceFormat]
  copy: [label: string, value: string]
}>()

const renderedInput = computed(() => (props.format === 'json' ? JSON.stringify({ input: props.inputText }, null, 2) : `"${props.inputText}"`))
const renderedOutput = computed(() => (props.format === 'json' ? JSON.stringify({ output: props.outputText }, null, 2) : `"${props.outputText}"`))
</script>
