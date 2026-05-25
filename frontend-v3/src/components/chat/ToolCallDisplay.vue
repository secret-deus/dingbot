<template>
  <div class="tool-calls">
    <div v-for="call in calls" :key="call.id" class="tool-call">
      <n-tag size="small" type="info">{{ call.function.name }}</n-tag>
      <details>
        <summary class="args-summary">参数</summary>
        <pre class="args">{{ formatArgs(call.function.arguments) }}</pre>
      </details>
      <ToolCandidateCards v-if="toolSearchPayload(call.id)" :payload="toolSearchPayload(call.id)!" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'
import ToolCandidateCards from './ToolCandidateCards.vue'
import type { ToolCall, ToolResult, ToolSearchResponse } from '@/types'

const props = defineProps<{ calls: ToolCall[]; results?: ToolResult[] }>()

const resultsByCallId = computed(() => {
  const map = new Map<string, ToolResult>()
  for (const result of props.results || []) {
    map.set(result.tool_call_id, result)
  }
  return map
})

function formatArgs(argsStr: string): string {
  try {
    return JSON.stringify(JSON.parse(argsStr), null, 2)
  } catch {
    return argsStr
  }
}

function toolSearchPayload(callId: string): ToolSearchResponse | null {
  const toolResult = resultsByCallId.value.get(callId)
  if (!toolResult || toolResult.tool_name !== 'toolsearch') {
    return null
  }

  const payload = unwrapToolPayload(toolResult.result)
  if (payload && typeof payload === 'object' && ('results' in payload || 'reason' in payload)) {
    return payload as ToolSearchResponse
  }
  return null
}

function unwrapToolPayload(value: unknown): unknown {
  if (value && typeof value === 'object' && 'result' in value) {
    return unwrapToolPayload((value as { result: unknown }).result)
  }
  if (typeof value === 'string') {
    try {
      return JSON.parse(value)
    } catch {
      return value
    }
  }
  return value
}
</script>

<style scoped>
.tool-calls {
  margin-top: 8px;
}

.tool-call {
  margin-bottom: 8px;
}

.args-summary {
  margin-top: 6px;
  color: var(--dr-text-muted);
  cursor: pointer;
  font-size: var(--dr-text-xs);
}

.args {
  margin-top: 4px;
  padding: 8px;
  overflow-x: auto;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #fbf8f1;
  color: var(--dr-text-soft);
  font-size: var(--dr-text-xs);
}
</style>
