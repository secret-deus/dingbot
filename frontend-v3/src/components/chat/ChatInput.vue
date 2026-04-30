<template>
  <div style="display: flex; gap: 8px; padding-top: 8px; border-top: 1px solid #333">
    <n-input
      v-model:value="text"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 4 }"
      placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
      :disabled="disabled"
      @keydown="onKeydown"
    />
    <n-button type="primary" :disabled="disabled || !text.trim()" @click="send">发送</n-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NButton } from 'naive-ui'

defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{ send: [content: string] }>()

const text = ref('')

function send() {
  const val = text.value.trim()
  if (!val) return
  emit('send', val)
  text.value = ''
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>
