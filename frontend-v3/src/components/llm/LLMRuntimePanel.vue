<template>
  <aside class="llm-panel runtime-panel">
    <div class="panel-title-row">
      <div>
        <span class="panel-kicker">Runtime</span>
        <div class="panel-title">运行控制</div>
        <div class="panel-subtitle">影响新会话，不打断正在进行的流式请求。</div>
      </div>
    </div>

    <div class="runtime-list">
      <div class="runtime-row">
        <span>LLM runtime</span>
        <strong>{{ active ? 'Active' : 'Inactive' }}</strong>
      </div>
      <div class="runtime-row">
        <span>Default provider</span>
        <strong>{{ defaultProviderName }}</strong>
      </div>
      <div class="runtime-row">
        <span>Config path</span>
        <strong class="path-text">{{ configPath || '-' }}</strong>
      </div>
    </div>

    <div class="global-switches">
      <label class="switch-row">
        <span>
          <strong>启用 LLM</strong>
          <small>允许新对话调用模型</small>
        </span>
        <n-switch v-model:value="globalForm.enabled" :disabled="disabled" />
      </label>
      <label class="switch-row">
        <span>
          <strong>数据脱敏</strong>
          <small>发送模型前处理敏感字段</small>
        </span>
        <n-switch v-model:value="globalForm.masking_enabled" :disabled="disabled" />
      </label>
    </div>

    <n-popconfirm
      positive-text="保存"
      negative-text="取消"
      :positive-button-props="{ type: 'primary', size: 'small', disabled }"
      :negative-button-props="{ size: 'small' }"
      @positive-click="$emit('save')"
    >
      <template #trigger>
        <n-button block secondary :loading="saving" :disabled="disabled">保存 Runtime 设置</n-button>
      </template>
      保存 Runtime 设置并影响新对话？新对话会使用更新后的启用和脱敏策略。
    </n-popconfirm>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NPopconfirm, NSwitch } from 'naive-ui'

const props = defineProps<{
  active: boolean
  defaultProviderName: string
  configPath?: string
  globalForm: {
    enabled: boolean
    masking_enabled: boolean
  }
  saving: boolean
  readOnly: boolean
}>()

defineEmits<{
  save: []
}>()

const disabled = computed(() => props.saving || props.readOnly)
</script>
