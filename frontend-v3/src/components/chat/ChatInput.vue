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
    <n-button
      v-if="streaming"
      class="send-button stop-button"
      type="primary"
      circle
      aria-label="停止输出"
      title="停止输出"
      @click="emit('stop')"
    >
      <template #icon>
        <n-icon><StopCircleOutline /></n-icon>
      </template>
    </n-button>
    <n-button v-else class="send-button" type="primary" circle :disabled="disabled || !text.trim()" @click="send">
      <template #icon>
        <n-icon><SendOutline /></n-icon>
      </template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NButton, NIcon } from 'naive-ui'
import { SendOutline, StopCircleOutline } from '@vicons/ionicons5'

defineProps<{ disabled?: boolean; streaming?: boolean }>()
const emit = defineEmits<{ send: [content: string]; stop: [] }>()

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
  width: min(100%, 920px);
  min-height: 62px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 44px;
  align-items: end;
  gap: 10px;
  padding: 11px 11px 11px 16px;
  border: 1px solid rgba(47, 111, 237, 0.3);
  border-radius: var(--dr-radius);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 0 0 4px rgba(47, 111, 237, 0.06), var(--dr-shadow-lift);
  backdrop-filter: blur(14px);
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
  color: var(--dr-text);
}
.send-button {
  width: 42px;
  height: 42px;
  align-self: end;
}
.stop-button {
  --n-color: var(--dr-red);
  --n-color-hover: #9f1f16;
  --n-color-pressed: #842018;
  --n-color-focus: var(--dr-red);
}
</style>
