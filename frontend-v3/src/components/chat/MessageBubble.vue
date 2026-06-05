<template>
  <div :class="['message-row', message.role]">
    <div v-if="message.role !== 'user'" class="avatar">{{ avatarText }}</div>
    <div class="message-body">
      <template v-if="message.role === 'user'">
        <div v-if="message.content" class="content" v-html="renderedContent" />
      </template>
      <template v-else>
        <AssistantRunCard :message="message" :streaming="streaming" @tool-confirmed="emit('tool-confirmed')" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import 'highlight.js/styles/github.css'
import AssistantRunCard from './AssistantRunCard.vue'
import type { Message } from '@/types'

const props = defineProps<{ message: Message; streaming?: boolean }>()
const emit = defineEmits<{ 'tool-confirmed': [] }>()

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
  border: 1px solid rgba(47, 111, 237, 0.24);
  border-radius: var(--dr-radius);
  background: var(--dr-accent-wash);
  color: var(--dr-accent-deep);
  font-size: 11px;
  font-weight: 700;
}
.message-body {
  min-width: 0;
  max-width: 76%;
}
.message-row.assistant .message-body,
.message-row.system .message-body,
.message-row.tool .message-body {
  flex: 1;
  width: 100%;
  max-width: 100%;
}
.message-row.user .message-body {
  max-width: 70%;
  padding: 10px 14px;
  border: 1px solid rgba(47, 111, 237, 0.3);
  border-radius: var(--dr-radius);
  background: #ffffff;
  box-shadow: 0 1px 1px rgba(23, 23, 23, 0.03), 0 12px 28px rgba(42, 47, 55, 0.07);
}
.message-row.assistant .message-body,
.message-row.system .message-body,
.message-row.tool .message-body {
  padding-top: 2px;
}
.content {
  line-height: 1.6;
  word-break: break-word;
  color: var(--dr-text-soft);
}
.message-row.user .content {
  color: var(--dr-text);
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
  background: #f7f8fa;
  border: 1px solid var(--dr-border-soft);
  padding: 12px;
  border-radius: var(--dr-radius);
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
