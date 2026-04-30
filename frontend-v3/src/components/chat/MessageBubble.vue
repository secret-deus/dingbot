<template>
  <div :class="['message-bubble', message.role]">
    <div class="role-tag">{{ roleLabel }}</div>
    <div class="content" v-html="renderedContent" />
    <ToolCallDisplay v-if="message.tool_calls?.length" :calls="message.tool_calls" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import 'highlight.js/styles/github-dark.css'
import ToolCallDisplay from './ToolCallDisplay.vue'
import type { Message } from '@/types'

const props = defineProps<{ message: Message }>()

const roleLabels: Record<string, string> = {
  user: '👤 用户',
  assistant: '🤖 助手',
  system: '⚙️ 系统',
  tool: '🔧 工具',
}

const roleLabel = computed(() => roleLabels[props.message.role] || props.message.role)

const renderedContent = computed(() => {
  const raw = props.message.content || ''
  try { return marked.parse(raw) as string } catch { return raw }
})
</script>

<style scoped>
.message-bubble {
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  max-width: 85%;
}
.message-bubble.user {
  background: #2d4a7a;
  margin-left: auto;
}
.message-bubble.assistant {
  background: #2a2a2a;
  border: 1px solid #333;
}
.message-bubble.tool {
  background: #1a2a1a;
  border: 1px solid #2a3a2a;
}
.role-tag {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}
.content {
  line-height: 1.6;
  word-break: break-word;
}
.content :deep(pre) {
  background: #1a1a1a;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
}
.content :deep(code) {
  font-size: 13px;
}
</style>
