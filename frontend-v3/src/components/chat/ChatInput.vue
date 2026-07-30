<template>
  <div class="composer">
    <n-input
      ref="inputRef"
      v-model:value="text"
      class="composer-input"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 5 }"
      placeholder="输入消息，Enter 发送"
      :input-props="inputProps"
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
import { onBeforeUnmount, ref } from 'vue'
import { NInput, NButton, NIcon } from 'naive-ui'
import { SendOutline, StopCircleOutline } from '@vicons/ionicons5'

defineProps<{ disabled?: boolean; streaming?: boolean }>()
const emit = defineEmits<{ send: [content: string]; stop: [] }>()

const inputRef = ref<InstanceType<typeof NInput> | null>(null)
const text = defineModel<string>({ default: '' })
const isComposing = ref(false)
let compositionEndTimer: number | undefined

const inputProps = {
  id: 'chat-message-input',
  name: 'message',
  autocomplete: 'off',
  'aria-label': '消息内容',
  onCompositionstart: handleCompositionStart,
  onCompositionend: handleCompositionEnd
}

function send() {
  const val = text.value.trim()
  if (!val) return
  emit('send', val)
  text.value = ''
}

function handleCompositionStart() {
  if (compositionEndTimer) {
    window.clearTimeout(compositionEndTimer)
    compositionEndTimer = undefined
  }
  isComposing.value = true
}

function handleCompositionEnd() {
  compositionEndTimer = window.setTimeout(() => {
    isComposing.value = false
    compositionEndTimer = undefined
  }, 30)
}

function onKeydown(e: KeyboardEvent) {
  if (isComposing.value || e.isComposing || e.keyCode === 229) return

  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

onBeforeUnmount(() => {
  if (compositionEndTimer) window.clearTimeout(compositionEndTimer)
})

defineExpose({
  focus: () => inputRef.value?.focus(),
})
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
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}
.composer-input {
  min-height: 44px;
  padding: 0 12px;
  border-radius: 7px;
  background: #f8fafc;
}
.composer-input :deep(.n-input-wrapper) {
  padding-left: 0;
  padding-right: 0;
}
.composer-input :deep(.n-input) {
  background: transparent;
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
  border-radius: 7px;
}
.stop-button {
  --n-color: var(--dr-red);
  --n-color-hover: #9f1f16;
  --n-color-pressed: #842018;
  --n-color-focus: var(--dr-red);
}
</style>
