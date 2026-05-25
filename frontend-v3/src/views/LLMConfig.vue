<template>
  <div class="llm-page">
    <section class="llm-header">
      <div>
        <h1>LLM 配置</h1>
        <p>管理多个兼容 OpenAI 的模型配置。保存后写入本地运行文件，新发起的对话消息会立即使用最新配置。</p>
      </div>
      <n-space align="center">
        <n-tag :type="config?.active ? 'success' : activeProviderCount ? 'warning' : 'error'" round>
          {{ statusText }}
        </n-tag>
        <n-button :loading="loading" @click="loadConfig">刷新</n-button>
      </n-space>
    </section>

    <n-alert v-if="hasPlaceholderKey" type="warning" class="llm-alert">
      有模型配置仍使用示例 API Key，占位值会按未配置处理。
    </n-alert>
    <n-alert v-if="savedApplied" type="success" class="llm-alert">
      配置已写入本地文件。后续新消息会立即使用最新模型配置，已经在进行中的流式请求不切换。
    </n-alert>

    <div class="llm-grid">
      <section class="llm-panel status-panel">
        <div class="panel-title">运行状态</div>
        <n-descriptions :column="1" label-placement="left" size="small">
          <n-descriptions-item label="运行中">
            <n-tag :type="config?.active ? 'success' : 'default'" size="small">{{ config?.active ? '是' : '否' }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="可用配置">
            <n-tag :type="activeProviderCount ? 'success' : 'error'" size="small">{{ activeProviderCount }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="默认模型">{{ defaultProviderName }}</n-descriptions-item>
          <n-descriptions-item label="配置源">{{ config?.source || '-' }}</n-descriptions-item>
          <n-descriptions-item label="配置文件">
            <span class="path-text">{{ config?.config_path || '-' }}</span>
          </n-descriptions-item>
        </n-descriptions>

        <div class="global-switches">
          <div class="switch-row">
            <span>启用 LLM</span>
            <n-switch v-model:value="globalForm.enabled" />
          </div>
          <div class="switch-row">
            <span>数据脱敏</span>
            <n-switch v-model:value="globalForm.masking_enabled" />
          </div>
        </div>
        <n-button block secondary :loading="saving" @click="saveGlobalConfig">保存全局设置</n-button>
      </section>

      <section class="llm-panel providers-panel">
        <div class="panel-title-row">
          <div>
            <div class="panel-title">模型配置</div>
            <div class="panel-subtitle">{{ providers.length }} 个配置</div>
          </div>
          <n-button size="small" type="primary" @click="createProvider">新增</n-button>
        </div>

        <div class="provider-list">
          <button
            v-for="provider in providers"
            :key="provider.id"
            :class="['provider-item', { active: provider.id === selectedProviderId }]"
            type="button"
            @click="selectProvider(provider.id)"
          >
            <span class="provider-main">
              <span class="provider-name">{{ provider.name || provider.id }}</span>
              <span class="provider-model">{{ provider.model || '未填写模型' }}</span>
            </span>
            <span class="provider-tags">
              <n-tag v-if="provider.id === config?.default_provider" size="small" type="info">默认</n-tag>
              <n-tag :type="provider.enabled && provider.api_key_configured ? 'success' : 'default'" size="small">
                {{ provider.enabled && provider.api_key_configured ? '可用' : '不可用' }}
              </n-tag>
            </span>
          </button>
        </div>
      </section>

      <section class="llm-panel form-panel">
        <div class="panel-title-row">
          <div>
            <div class="panel-title">{{ creatingProvider ? '新增模型' : '编辑模型' }}</div>
            <div class="panel-subtitle">API Key 留空表示不修改本地密钥</div>
          </div>
          <n-button
            v-if="selectedProviderId && selectedProviderId !== config?.default_provider"
            size="small"
            secondary
            @click="setAsDefault"
          >
            设为默认
          </n-button>
        </div>

        <n-empty v-if="!selectedProviderId && !creatingProvider" description="暂无模型配置" />
        <n-form v-else label-placement="top" :show-feedback="false">
          <div class="form-row three">
            <n-form-item label="配置 ID">
              <n-input v-model:value="providerForm.id" :disabled="!creatingProvider" placeholder="openai" />
            </n-form-item>
            <n-form-item label="名称">
              <n-input v-model:value="providerForm.name" placeholder="OpenAI / DeepSeek / Qwen" />
            </n-form-item>
            <n-form-item label="启用">
              <n-switch v-model:value="providerForm.enabled" />
            </n-form-item>
          </div>

          <n-form-item label="模型">
            <n-input v-model:value="providerForm.model" placeholder="gpt-4o-mini" />
          </n-form-item>
          <n-form-item label="Base URL">
            <n-input v-model:value="providerForm.base_url" placeholder="https://api.openai.com/v1" />
          </n-form-item>
          <n-form-item label="API Key">
            <n-input
              v-model:value="providerForm.api_key"
              type="password"
              show-password-on="click"
              placeholder="留空表示不修改现有本地密钥"
              :input-props="{ autocomplete: 'new-password' }"
            />
          </n-form-item>

          <div class="form-row four">
            <n-form-item label="Temperature">
              <n-input-number v-model:value="providerForm.temperature" :min="0" :max="2" :step="0.1" />
            </n-form-item>
            <n-form-item label="Max Tokens">
              <n-input-number v-model:value="providerForm.max_tokens" :min="256" :max="64000" :step="256" />
            </n-form-item>
            <n-form-item label="Timeout">
              <n-input-number v-model:value="providerForm.timeout" :min="10" :max="600" :step="10" />
            </n-form-item>
            <n-form-item label="流式">
              <n-switch v-model:value="providerForm.stream" />
            </n-form-item>
          </div>

          <div class="actions">
            <n-popconfirm
              v-if="!creatingProvider && selectedProviderId"
              positive-text="删除"
              negative-text="取消"
              @positive-click="deleteSelectedProvider"
            >
              <template #trigger>
                <n-button tertiary type="error">删除</n-button>
              </template>
              删除后无法在对话页选择这个模型配置。
            </n-popconfirm>
            <n-button @click="resetForm">重置</n-button>
            <n-button :loading="saving" type="primary" @click="saveProvider">保存并立即生效</n-button>
          </div>
        </n-form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  NAlert,
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSpace,
  NSwitch,
  NTag,
  useMessage,
} from 'naive-ui'
import { systemApi } from '@/api/client'
import type { LLMConfig, LLMProviderConfig } from '@/types'

const message = useMessage()
const loading = ref(false)
const saving = ref(false)
const savedApplied = ref(false)
const creatingProvider = ref(false)
const selectedProviderId = ref('')
const config = ref<LLMConfig | null>(null)

const globalForm = reactive({
  enabled: false,
  masking_enabled: true,
})

const providerForm = reactive({
  id: '',
  name: '',
  enabled: true,
  model: '',
  base_url: '',
  api_key: '',
  temperature: 0.3,
  max_tokens: 2000,
  timeout: 60,
  stream: true,
})

const providers = computed(() => config.value?.providers || [])

const activeProviderCount = computed(() =>
  providers.value.filter((provider) => provider.enabled && provider.api_key_configured).length,
)

const hasPlaceholderKey = computed(() =>
  providers.value.some((provider) => provider.api_key_placeholder),
)

const statusText = computed(() => {
  if (config.value?.active) return '运行中'
  if (activeProviderCount.value) return '已配置'
  return '未配置'
})

const defaultProviderName = computed(() => {
  const provider = providers.value.find((item) => item.id === config.value?.default_provider)
  return provider ? `${provider.name || provider.id} / ${provider.model || '-'}` : '-'
})

function applyConfig(value: LLMConfig) {
  config.value = value
  globalForm.enabled = value.enabled
  globalForm.masking_enabled = value.masking_enabled

  const valueProviders = value.providers || []
  const preferredId = selectedProviderId.value || value.default_provider || value.selected_provider_id || valueProviders[0]?.id || ''
  const nextProvider = valueProviders.find((provider) => provider.id === preferredId) || valueProviders[0]
  if (nextProvider) selectProvider(nextProvider.id)
  else {
    selectedProviderId.value = ''
    creatingProvider.value = false
  }
}

async function loadConfig() {
  loading.value = true
  try {
    applyConfig(await systemApi.llmConfig())
  } catch {
    message.error('读取 LLM 配置失败')
  } finally {
    loading.value = false
  }
}

function selectProvider(providerId: string) {
  const provider = providers.value.find((item) => item.id === providerId)
  if (!provider) return
  creatingProvider.value = false
  selectedProviderId.value = provider.id
  fillProviderForm(provider)
}

function fillProviderForm(provider: LLMProviderConfig) {
  providerForm.id = provider.id
  providerForm.name = provider.name || provider.id
  providerForm.enabled = provider.enabled
  providerForm.model = provider.model || ''
  providerForm.base_url = provider.base_url || ''
  providerForm.api_key = ''
  providerForm.temperature = provider.temperature
  providerForm.max_tokens = provider.max_tokens
  providerForm.timeout = provider.timeout || 60
  providerForm.stream = provider.stream !== false
}

function createProvider() {
  creatingProvider.value = true
  selectedProviderId.value = ''
  providerForm.id = `provider-${Date.now().toString(36).slice(-5)}`
  providerForm.name = ''
  providerForm.enabled = true
  providerForm.model = ''
  providerForm.base_url = ''
  providerForm.api_key = ''
  providerForm.temperature = 0.3
  providerForm.max_tokens = 2000
  providerForm.timeout = 60
  providerForm.stream = true
}

function resetForm() {
  if (creatingProvider.value) createProvider()
  else if (selectedProviderId.value) selectProvider(selectedProviderId.value)
}

async function saveGlobalConfig() {
  saving.value = true
  try {
    const result = await systemApi.updateLlmConfig({
      enabled: globalForm.enabled,
      masking_enabled: globalForm.masking_enabled,
      default_provider: config.value?.default_provider,
    })
    savedApplied.value = !result.restart_required
    message.success('全局配置已保存')
    await loadConfig()
  } catch {
    message.error('保存失败，请确认当前账号有管理员权限')
  } finally {
    saving.value = false
  }
}

async function saveProvider() {
  const providerId = normalizeId(providerForm.id)
  if (!providerId || !providerForm.model.trim()) {
    message.warning('请填写配置 ID 和模型名称')
    return
  }

  saving.value = true
  try {
    const providerPayload: Partial<LLMProviderConfig> & { api_key?: string } = {
      id: providerId,
      name: providerForm.name.trim() || providerId,
      enabled: providerForm.enabled,
      model: providerForm.model.trim(),
      base_url: providerForm.base_url.trim() || undefined,
      temperature: providerForm.temperature,
      max_tokens: providerForm.max_tokens,
      timeout: providerForm.timeout,
      stream: providerForm.stream,
    }
    if (providerForm.api_key.trim()) providerPayload.api_key = providerForm.api_key.trim()
    const result = await systemApi.updateLlmConfig({
      enabled: globalForm.enabled,
      masking_enabled: globalForm.masking_enabled,
      default_provider: config.value?.default_provider || providerId,
      provider_id: providerId,
      provider: providerPayload,
    })
    savedApplied.value = !result.restart_required
    selectedProviderId.value = providerId
    creatingProvider.value = false
    message.success('模型配置已保存')
    await loadConfig()
  } catch {
    message.error('保存失败，请确认当前账号有管理员权限')
  } finally {
    saving.value = false
  }
}

async function setAsDefault() {
  if (!selectedProviderId.value) return
  saving.value = true
  try {
    await systemApi.updateLlmConfig({
      enabled: globalForm.enabled,
      masking_enabled: globalForm.masking_enabled,
      default_provider: selectedProviderId.value,
    })
    savedApplied.value = true
    message.success('默认模型已更新')
    await loadConfig()
  } catch {
    message.error('设置默认模型失败')
  } finally {
    saving.value = false
  }
}

async function deleteSelectedProvider() {
  if (!selectedProviderId.value) return
  saving.value = true
  try {
    await systemApi.deleteLlmProvider(selectedProviderId.value)
    selectedProviderId.value = ''
    message.success('模型配置已删除')
    await loadConfig()
  } catch {
    message.error('删除失败')
  } finally {
    saving.value = false
  }
}

function normalizeId(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '')
}

onMounted(loadConfig)
</script>

<style scoped>
.llm-page {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--dr-text);
}
.llm-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  padding: 8px 4px 0;
}
.llm-header h1 {
  margin: 0 0 6px;
  color: var(--dr-text);
  font-size: var(--dr-text-2xl);
  font-weight: 620;
  line-height: 1.12;
}
.llm-header p {
  max-width: 760px;
  margin: 0;
  color: var(--dr-text-muted);
  line-height: 1.6;
}
.llm-alert {
  border-radius: 8px;
}
.llm-grid {
  display: grid;
  grid-template-columns: 300px 360px minmax(0, 1fr);
  gap: 16px;
}
.llm-panel {
  min-width: 0;
  border: 1px solid var(--dr-border-soft);
  background: var(--dr-surface-lift);
  border-radius: var(--dr-radius);
  padding: 18px;
  box-shadow: var(--dr-shadow);
}
.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.panel-title {
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 610;
  margin-bottom: 16px;
}
.panel-title-row .panel-title {
  margin-bottom: 4px;
}
.panel-subtitle {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}
.path-text {
  color: var(--dr-text-muted);
  word-break: break-all;
}
.global-switches {
  display: grid;
  gap: 12px;
  margin: 20px 0 16px;
}
.switch-row {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  padding: 0 12px;
  background: #fffdf8;
  color: var(--dr-text-soft);
}
.provider-list {
  max-height: 520px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.provider-item {
  width: 100%;
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: var(--dr-radius);
  background: #fffdf8;
  color: var(--dr-text-soft);
  text-align: left;
  cursor: pointer;
}
.provider-item:hover {
  background: var(--dr-surface-hover);
}
.provider-item.active {
  background: #faf1ea;
  border-color: rgba(25, 24, 20, 0.06);
}
.provider-main {
  min-width: 0;
  display: grid;
  gap: 4px;
}
.provider-name,
.provider-model {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.provider-name {
  font-size: 13px;
  font-weight: 650;
  color: var(--dr-text);
}
.provider-model {
  color: var(--dr-text-muted);
  font-size: 12px;
}
.provider-tags {
  display: flex;
  flex-shrink: 0;
  gap: 6px;
}
.form-row {
  display: grid;
  gap: 14px;
}
.form-row.three {
  grid-template-columns: 1.1fr 1.4fr 80px;
}
.form-row.four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}
@media (max-width: 1180px) {
  .llm-grid {
    grid-template-columns: 1fr;
  }
  .provider-list {
    max-height: none;
  }
}
@media (max-width: 720px) {
  .llm-header {
    display: block;
  }
  .form-row.three,
  .form-row.four {
    grid-template-columns: 1fr;
  }
  .actions {
    justify-content: stretch;
    flex-wrap: wrap;
  }
}
</style>
