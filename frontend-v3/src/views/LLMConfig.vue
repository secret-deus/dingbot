<template>
  <div class="llm-page">
    <section class="llm-hero">
      <div class="llm-hero-copy">
        <span class="llm-kicker">Settings / LLM Providers</span>
        <h1>LLM 配置</h1>
        <p>集中管理对话运行时的模型、密钥和脱敏策略，保存后新发起的消息会立即使用最新配置。</p>
      </div>
      <div class="llm-hero-actions">
        <n-button secondary :loading="loading" :disabled="configBusy" @click="loadConfig()">刷新</n-button>
      </div>
    </section>

    <LLMStatusStrip
      :status-text="statusText"
      :active="Boolean(config?.active)"
      :active-provider-count="activeProviderCount"
      :provider-count="providers.length"
      :default-provider-name="defaultProviderName"
      :source="config?.source"
    />

    <section class="llm-readiness-strip" aria-label="LLM 配置态势">
      <article :class="['readiness-card', chatReadinessTone]">
        <span class="readiness-kicker">Chat readiness</span>
        <strong>{{ chatReadinessTitle }}</strong>
        <small>{{ chatReadinessDetail }}</small>
      </article>
      <article :class="['readiness-card', secretPostureTone]">
        <span class="readiness-kicker">Secret posture</span>
        <strong>{{ secretPostureTitle }}</strong>
        <small>{{ secretPostureDetail }}</small>
      </article>
      <article :class="['readiness-card', routingTone]">
        <span class="readiness-kicker">Default routing</span>
        <strong>{{ routingTitle }}</strong>
        <small>{{ routingDetail }}</small>
      </article>
    </section>

    <section v-if="llmAttentionItems.length" class="llm-attention-list" aria-label="LLM 配置关注项">
      <article v-for="item in llmAttentionItems" :key="item.title" class="attention-item">
        <span>{{ item.label }}</span>
        <strong>{{ item.title }}</strong>
        <small>{{ item.detail }}</small>
      </article>
    </section>

    <div v-if="!auth.isAdmin || hasPlaceholderKey || savedApplied" class="notice-stack">
      <n-alert v-if="!auth.isAdmin" type="info" class="llm-alert">
        当前账号为只读模式。只有管理员可以修改模型、密钥和 Runtime 设置。
      </n-alert>
      <n-alert v-if="hasPlaceholderKey" type="warning" class="llm-alert">
        有模型配置仍使用示例 API Key，占位值会按未配置处理。
      </n-alert>
      <n-alert v-if="savedApplied" type="success" class="llm-alert">
        配置已写入本地文件。后续新消息会立即使用最新模型配置，已经在进行中的流式请求不切换。
      </n-alert>
    </div>

    <div class="llm-workbench" :inert="configBusy" :aria-busy="configBusy">
      <LLMProviderList
        :providers="providers"
        :selected-provider-id="selectedProviderId"
        :default-provider-id="config?.default_provider"
        :active-provider-count="activeProviderCount"
        :read-only="!auth.isAdmin"
        :busy="configBusy"
        @create="createProvider"
        @select="selectProvider"
      />

      <LLMProviderForm
        :form="providerForm"
        :creating-provider="creatingProvider"
        :selected-provider-id="selectedProviderId"
        :selected-provider-label="selectedProviderLabel"
        :default-provider-id="config?.default_provider"
        :saving="configBusy"
        :read-only="!auth.isAdmin"
        @set-as-default="setAsDefault"
        @delete="deleteSelectedProvider"
        @reset="resetForm"
        @save="saveProvider"
      />

      <LLMRuntimePanel
        :active="Boolean(config?.active)"
        :default-provider-name="defaultProviderName"
        :config-path="config?.config_path"
        :global-form="globalForm"
        :saving="configBusy"
        :read-only="!auth.isAdmin"
        @save="saveGlobalConfig"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { NAlert, NButton, useMessage } from 'naive-ui'
import { systemApi } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import LLMProviderForm from '@/components/llm/LLMProviderForm.vue'
import type { LLMProviderFormState } from '@/components/llm/LLMProviderForm.vue'
import LLMProviderList from '@/components/llm/LLMProviderList.vue'
import LLMRuntimePanel from '@/components/llm/LLMRuntimePanel.vue'
import LLMStatusStrip from '@/components/llm/LLMStatusStrip.vue'
import type { LLMConfig, LLMProviderConfig } from '@/types'
import '@/styles/llm-workbench.css'

const message = useMessage()
const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const savedApplied = ref(false)
const creatingProvider = ref(false)
const selectedProviderId = ref('')
const config = ref<LLMConfig | null>(null)
const configBusy = computed(() => loading.value || saving.value)

const globalForm = reactive({
  enabled: false,
  masking_enabled: true,
})

const providerForm = reactive<LLMProviderFormState>({
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
const activeProviderCount = computed(() => providers.value.filter((provider) => provider.enabled && provider.api_key_configured && !provider.api_key_placeholder).length)
const hasPlaceholderKey = computed(() => providers.value.some((provider) => provider.api_key_placeholder))
const enabledProviderCount = computed(() => providers.value.filter((provider) => provider.enabled).length)
const maskedProviderCount = computed(() => providers.value.filter((provider) => provider.api_key_configured && !provider.api_key_placeholder).length)
const defaultProvider = computed(() => providers.value.find((item) => item.id === config.value?.default_provider) || null)
const selectedProvider = computed(() => providers.value.find((item) => item.id === selectedProviderId.value) || null)
const selectedProviderLabel = computed(() => {
  if (!selectedProvider.value) return providerForm.name || providerForm.id || selectedProviderId.value
  return selectedProvider.value.name && selectedProvider.value.name !== selectedProvider.value.id
    ? `${selectedProvider.value.name} (${selectedProvider.value.id})`
    : selectedProvider.value.id
})
const defaultProviderReady = computed(() => Boolean(defaultProvider.value?.enabled && defaultProvider.value?.api_key_configured && !defaultProvider.value?.api_key_placeholder))
const statusText = computed(() => {
  if (config.value?.active) return '运行中'
  if (activeProviderCount.value) return '已配置'
  return '未配置'
})
const defaultProviderName = computed(() => {
  const provider = providers.value.find((item) => item.id === config.value?.default_provider)
  return provider ? `${provider.name || provider.id} / ${provider.model || '-'}` : '-'
})
const chatReadinessTone = computed(() => {
  if (config.value?.active && defaultProviderReady.value) return 'ready'
  if (activeProviderCount.value) return 'watch'
  return 'blocked'
})
const chatReadinessTitle = computed(() => {
  if (config.value?.active && defaultProviderReady.value) return 'Ready for new chats'
  if (!config.value?.enabled) return 'Runtime disabled'
  if (!activeProviderCount.value) return 'No usable provider'
  return 'Needs default review'
})
const chatReadinessDetail = computed(() => {
  if (config.value?.active && defaultProviderReady.value) return `${defaultProviderName.value} will serve newly created conversations.`
  if (!config.value?.enabled) return 'Enable the runtime before model calls are routed from chat.'
  if (!activeProviderCount.value) return 'Add a provider with a real API key before enabling model calls.'
  return `${activeProviderCount.value} provider(s) are usable, but the default route is not fully ready.`
})
const secretPostureTone = computed(() => {
  if (hasPlaceholderKey.value || !config.value?.masking_enabled) return 'watch'
  if (maskedProviderCount.value) return 'ready'
  return 'blocked'
})
const secretPostureTitle = computed(() => {
  if (hasPlaceholderKey.value) return 'Placeholder key detected'
  if (!config.value?.masking_enabled) return 'Masking disabled'
  return `${maskedProviderCount.value} key(s) configured`
})
const secretPostureDetail = computed(() => {
  if (hasPlaceholderKey.value) return 'Example API keys are ignored and should be replaced before runtime use.'
  if (!config.value?.masking_enabled) return 'Sensitive fields will not be masked before requests are sent to providers.'
  return 'Stored keys remain local; leaving API Key blank keeps the existing secret unchanged.'
})
const routingTone = computed(() => {
  if (defaultProviderReady.value) return 'ready'
  if (defaultProvider.value) return 'watch'
  return 'blocked'
})
const routingTitle = computed(() => {
  if (defaultProviderReady.value) return defaultProviderName.value
  if (defaultProvider.value) return 'Default route not ready'
  return 'No default provider'
})
const routingDetail = computed(() => {
  if (defaultProviderReady.value) return `${defaultProvider.value?.timeout || 60}s timeout, ${defaultProvider.value?.stream === false ? 'non-streaming' : 'streaming'} responses.`
  if (defaultProvider.value) return 'The selected default provider is disabled, missing a key, or still uses a placeholder key.'
  return 'Set a default provider so new conversations have a deterministic model route.'
})
const llmAttentionItems = computed(() => {
  const items: Array<{ label: string; title: string; detail: string }> = []
  if (!config.value?.enabled) {
    items.push({ label: 'Runtime', title: 'LLM runtime is disabled', detail: 'New conversations will not call model providers until runtime is enabled.' })
  }
  if (!activeProviderCount.value) {
    items.push({ label: 'Providers', title: 'No usable provider', detail: `${enabledProviderCount.value}/${providers.value.length} enabled provider(s), but none has a usable API key.` })
  }
  if (defaultProvider.value && !defaultProviderReady.value) {
    items.push({ label: 'Routing', title: 'Default provider is not ready', detail: `${defaultProvider.value.name || defaultProvider.value.id} cannot be used as-is for new chats.` })
  }
  if (!defaultProvider.value && providers.value.length) {
    items.push({ label: 'Routing', title: 'Default provider missing', detail: 'Pick a default route before relying on model calls from chat.' })
  }
  if (hasPlaceholderKey.value) {
    items.push({ label: 'Secrets', title: 'Placeholder API key exists', detail: 'Example key values are treated as unconfigured.' })
  }
  if (!config.value?.masking_enabled) {
    items.push({ label: 'Masking', title: 'Sensitive data masking is off', detail: 'Turn masking on before sending operational context to external providers.' })
  }
  return items
})

function applyConfig(value: LLMConfig) {
  config.value = value
  globalForm.enabled = value.enabled
  globalForm.masking_enabled = value.masking_enabled

  const valueProviders = value.providers || []
  const preferredId = selectedProviderId.value || value.default_provider || value.selected_provider_id || valueProviders[0]?.id || ''
  const nextProvider = valueProviders.find((provider) => provider.id === preferredId) || valueProviders[0]
  if (nextProvider) selectProvider(nextProvider.id, true)
  else {
    selectedProviderId.value = ''
    creatingProvider.value = false
  }
}

async function loadConfig(force = false) {
  if (loading.value || (saving.value && !force)) return
  loading.value = true
  try {
    applyConfig(await systemApi.llmConfig())
  } catch {
    message.error('读取 LLM 配置失败')
  } finally {
    loading.value = false
  }
}

function selectProvider(providerId: string, force = false) {
  if (saving.value && !force) return
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
  if (!auth.isAdmin || configBusy.value) return
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
  if (!auth.isAdmin || configBusy.value) return
  if (creatingProvider.value) createProvider()
  else if (selectedProviderId.value) selectProvider(selectedProviderId.value)
}

async function saveGlobalConfig() {
  if (!auth.isAdmin || configBusy.value) return
  saving.value = true
  try {
    const result = await systemApi.updateLlmConfig({
      enabled: globalForm.enabled,
      masking_enabled: globalForm.masking_enabled,
      default_provider: config.value?.default_provider,
    })
    savedApplied.value = !result.restart_required
    message.success('全局配置已保存')
    await loadConfig(true)
  } catch {
    message.error('保存失败，请确认当前账号有管理员权限')
  } finally {
    saving.value = false
  }
}

async function saveProvider() {
  if (!auth.isAdmin || configBusy.value) return
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
    await loadConfig(true)
  } catch {
    message.error('保存失败，请确认当前账号有管理员权限')
  } finally {
    saving.value = false
  }
}

async function setAsDefault() {
  if (!auth.isAdmin || configBusy.value) return
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
    await loadConfig(true)
  } catch {
    message.error('设置默认模型失败')
  } finally {
    saving.value = false
  }
}

async function deleteSelectedProvider() {
  if (!auth.isAdmin || configBusy.value) return
  if (!selectedProviderId.value) return
  saving.value = true
  try {
    await systemApi.deleteLlmProvider(selectedProviderId.value)
    selectedProviderId.value = ''
    message.success('模型配置已删除')
    await loadConfig(true)
  } catch {
    message.error('删除失败')
  } finally {
    saving.value = false
  }
}

function normalizeId(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '')
}

onMounted(() => loadConfig())
</script>
