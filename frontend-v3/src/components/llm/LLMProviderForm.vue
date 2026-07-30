<template>
  <section class="llm-panel form-panel">
    <div class="panel-title-row">
      <div>
        <span class="panel-kicker">Configuration</span>
        <div class="panel-title">{{ creatingProvider ? '新增模型' : '编辑模型' }}</div>
        <div class="panel-subtitle">API Key 留空表示不修改本地密钥</div>
      </div>
      <n-popconfirm
        v-if="canSetDefault"
        positive-text="设为默认"
        negative-text="取消"
        :positive-button-props="{ type: 'primary', size: 'small', disabled }"
        :negative-button-props="{ size: 'small' }"
        @positive-click="$emit('setAsDefault')"
      >
        <template #trigger>
          <n-button size="small" secondary :disabled="disabled">设为默认</n-button>
        </template>
        将「{{ providerSaveLabel }}」设为默认模型？新对话会优先使用它。
      </n-popconfirm>
    </div>

    <n-empty v-if="!selectedProviderId && !creatingProvider" description="暂无模型配置" />
    <n-form v-else label-placement="top" :show-feedback="false">
      <div class="form-section">
        <div class="form-row three">
          <n-form-item label="配置 ID">
            <n-input v-model:value="form.id" :disabled="!creatingProvider || disabled" placeholder="openai" />
          </n-form-item>
          <n-form-item label="名称">
            <n-input v-model:value="form.name" :disabled="disabled" placeholder="OpenAI / DeepSeek / Qwen" />
          </n-form-item>
          <n-form-item label="启用">
            <div class="inline-switch">
              <n-switch v-model:value="form.enabled" :disabled="disabled" />
            </div>
          </n-form-item>
        </div>

        <n-form-item label="模型">
          <n-input v-model:value="form.model" :disabled="disabled" placeholder="gpt-4o-mini" />
        </n-form-item>
        <n-form-item label="Base URL">
          <n-input v-model:value="form.base_url" :disabled="disabled" placeholder="https://api.openai.com/v1" />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input
            v-model:value="form.api_key"
            type="password"
            show-password-on="click"
            placeholder="留空表示不修改现有本地密钥"
            :disabled="disabled"
            :input-props="{ autocomplete: 'new-password' }"
          />
        </n-form-item>
      </div>

      <div class="form-section compact">
        <div class="section-label">Generation defaults</div>
        <div class="form-row four">
          <n-form-item label="Temperature">
            <n-input-number v-model:value="form.temperature" :min="0" :max="2" :step="0.1" :disabled="disabled" />
          </n-form-item>
          <n-form-item label="Max Tokens">
            <n-input-number v-model:value="form.max_tokens" :min="256" :max="64000" :step="256" :disabled="disabled" />
          </n-form-item>
          <n-form-item label="Timeout">
            <n-input-number v-model:value="form.timeout" :min="10" :max="600" :step="10" :disabled="disabled" />
          </n-form-item>
          <n-form-item label="流式">
            <div class="inline-switch">
              <n-switch v-model:value="form.stream" :disabled="disabled" />
            </div>
          </n-form-item>
        </div>
      </div>

      <div class="actions">
        <n-popconfirm
          v-if="!creatingProvider && selectedProviderId"
          positive-text="删除"
          negative-text="取消"
          :positive-button-props="{ type: 'error', disabled }"
          @positive-click="$emit('delete')"
        >
          <template #trigger>
            <n-button tertiary type="error" :disabled="disabled">删除</n-button>
          </template>
          删除模型配置「{{ selectedProviderLabel || selectedProviderId }}」？删除后无法在对话页选择它。
        </n-popconfirm>
        <n-button :disabled="disabled" @click="$emit('reset')">重置</n-button>
        <n-popconfirm
          positive-text="保存"
          negative-text="取消"
          :positive-button-props="{ type: 'primary', size: 'small', disabled }"
          :negative-button-props="{ size: 'small' }"
          @positive-click="$emit('save')"
        >
          <template #trigger>
            <n-button :loading="saving" :disabled="disabled" type="primary">保存并生效</n-button>
          </template>
          保存模型配置「{{ providerSaveLabel }}」并立即影响模型调用？
        </n-popconfirm>
      </div>
    </n-form>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NEmpty, NForm, NFormItem, NInput, NInputNumber, NPopconfirm, NSwitch } from 'naive-ui'

export interface LLMProviderFormState {
  id: string
  name: string
  enabled: boolean
  model: string
  base_url: string
  api_key: string
  temperature: number
  max_tokens: number
  timeout: number
  stream: boolean
}

const props = defineProps<{
  form: LLMProviderFormState
  creatingProvider: boolean
  selectedProviderId: string
  selectedProviderLabel?: string
  defaultProviderId?: string
  saving: boolean
  readOnly: boolean
}>()

defineEmits<{
  setAsDefault: []
  delete: []
  reset: []
  save: []
}>()

const disabled = computed(() => props.saving || props.readOnly)
const canSetDefault = computed(() => !props.readOnly && props.selectedProviderId && props.selectedProviderId !== props.defaultProviderId)
const providerSaveLabel = computed(() => props.form.name.trim() || props.form.id.trim() || '未命名模型')
</script>
