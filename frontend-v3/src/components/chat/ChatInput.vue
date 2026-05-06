<template>
  <div class="composer">
    <n-input
      v-model:value="text"
      class="composer-input"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 5 }"
      placeholder="输入消息，Enter 发送"
      :input-props="{ id: 'chat-message-input', name: 'message', autocomplete: 'off', 'aria-label': '消息内容' }"
      :disabled="disabled"
      @keydown="onKeydown"
    />
    <n-button class="send-button" type="primary" circle :disabled="disabled || !text.trim()" @click="send">
      <template #icon>
        <n-icon><SendOutline /></n-icon>
      </template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NButton, NIcon } from 'naive-ui'
import { SendOutline } from '@vicons/ionicons5'

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

<style scoped>
.composer {
  width: min(100%, 880px);
  min-height: 58px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 42px;
  align-items: end;
  gap: 10px;
  padding: 10px 10px 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: #1b1b1f;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
}
.composer-input :deep(.n-input-wrapper) {
  padding-left: 0;
  padding-right: 0;
}
.composer-input :deep(.n-input__border),
.composer-input :deep(.n-input__state-border) {
  display: none;
}
.composer-input :deep(textarea) {
  line-height: 1.55;
}
.send-button {
  width: 36px;
  height: 36px;
  align-self: end;
}
</style>
