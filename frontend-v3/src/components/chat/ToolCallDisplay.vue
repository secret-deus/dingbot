<template>
  <div class="tool-calls">
    <div v-for="call in calls" :key="call.id" class="tool-call">
      <n-tag size="small" type="info">🔧 {{ call.function.name }}</n-tag>
      <details>
        <summary style="cursor: pointer; font-size: 12px; color: #888; margin-top: 4px">参数</summary>
        <pre class="args">{{ formatArgs(call.function.arguments) }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NTag } from 'naive-ui'
import type { ToolCall } from '@/types'

defineProps<{ calls: ToolCall[] }>()

function formatArgs(argsStr: string): string {
  try {
    return JSON.stringify(JSON.parse(argsStr), null, 2)
  } catch {
    return argsStr
  }
}
</script>

<style scoped>
.tool-calls { margin-top: 8px; }
.tool-call { margin-bottom: 4px; }
.args { background: #1a1a1a; padding: 6px; border-radius: 4px; font-size: 12px; overflow-x: auto; margin-top: 2px; }
</style>
