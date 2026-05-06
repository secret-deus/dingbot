<template>
  <div :class="['message-row', message.role]">
    <div v-if="message.role !== 'user'" class="avatar">{{ avatarText }}</div>
    <div class="message-body">
      <template v-if="message.role === 'user'">
        <div v-if="message.content" class="content" v-html="renderedContent" />
      </template>
      <template v-else>
        <ToolCallDisplay v-if="message.tool_calls?.length" :calls="message.tool_calls" :results="message.tool_results || []" />
        <div v-if="message.content" class="content assistant-content" v-html="renderedContent" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import 'highlight.js/styles/github-dark.css'
import ToolCallDisplay from './ToolCallDisplay.vue'
import type { Message } from '@/types'

const props = defineProps<{ message: Message }>()

const roleAvatars: Record<string, string> = {
  assistant: 'AI',
  system: 'SYS',
  tool: 'TL',
}

const avatarText = computed(() => roleAvatars[props.message.role] || props.message.role.slice(0, 2).toUpperCase())

const renderedContent = computed(() => {
  const raw = props.message.content || ''
  try { return marked.parse(raw) as string } catch { return raw }
})
</script>

<style scoped>
.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.message-row.user {
  justify-content: flex-end;
}
.avatar {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #263244;
  color: #eef2ff;
  font-size: 11px;
  font-weight: 700;
}
.message-body {
  min-width: 0;
  max-width: 76%;
}
.message-row.user .message-body {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  background: #263244;
}
.message-row.assistant .message-body,
.message-row.system .message-body,
.message-row.tool .message-body {
  padding-top: 2px;
}
.message-row.tool .message-body {
  width: 100%;
  max-width: 100%;
}
.content {
  line-height: 1.6;
  word-break: break-word;
  color: #ececef;
}
.assistant-content {
  margin-top: 10px;
}
.content :deep(p:first-child) {
  margin-top: 0;
}
.content :deep(p:last-child) {
  margin-bottom: 0;
}
.content :deep(pre) {
  background: #18181b;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}
.content :deep(code) {
  font-size: 13px;
}
@media (max-width: 820px) {
  .message-body,
  .message-row.user .message-body {
    max-width: 88%;
  }
}
</style>
