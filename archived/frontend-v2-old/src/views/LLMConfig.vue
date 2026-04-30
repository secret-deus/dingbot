<template>
  <div class="llm-config-page">
    <header class="llm-hero">
      <div>
        <p class="eyebrow">MODEL CONTROL</p>
        <h1>LLM 设置</h1>
        <span>运行时模型、Provider、参数和安全策略集中查看。</span>
      </div>
      <div class="hero-actions">
        <el-button :loading="loading" @click="loadConfig">刷新</el-button>
        <el-button type="success" @click="openEditor()">编辑配置</el-button>
        <el-button type="primary" :loading="reloading" @click="reloadConfig">重新加载配置</el-button>
      </div>
    </header>

    <section class="metric-grid">
      <article v-for="item in metrics" :key="item.label" :class="['panel-card metric-card', item.tone]">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.detail }}</p>
      </article>
    </section>

    <section class="llm-layout">
      <div class="panel-card runtime-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">RUNTIME</p>
            <h2>当前生效配置</h2>
          </div>
          <el-tag :type="configSynced ? 'success' : 'warning'" effect="dark">
            {{ configSynced ? '已同步' : '需重载' }}
          </el-tag>
        </div>

        <div v-if="loading" class="skeleton-wrap">
          <el-skeleton :rows="6" animated />
        </div>
        <div v-else class="runtime-grid">
          <div v-for="item in runtimeRows" :key="item.label" class="runtime-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </div>

      <aside class="panel-card policy-panel">
        <p class="eyebrow">GUARDRAILS</p>
        <h2>策略开关</h2>
        <div class="policy-list">
          <div v-for="item in policyRows" :key="item.label" class="policy-item">
            <span :class="['status-dot', item.enabled ? 'green' : 'amber']" />
            <div>
              <strong>{{ item.label }}</strong>
              <p>{{ item.detail }}</p>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <section class="panel-card providers-panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">PROVIDERS</p>
          <h2>模型供应商</h2>
        </div>
        <span class="provider-count">{{ providers.length }} providers</span>
      </div>

      <div v-if="providers.length" class="provider-grid">
        <article
          v-for="provider in providers"
          :key="provider.id"
          :class="['provider-card', { active: provider.id === savedConfig.default_provider }]"
        >
          <div class="provider-top">
            <div>
              <strong>{{ provider.name || provider.id }}</strong>
              <code>{{ provider.id }}</code>
            </div>
            <div class="provider-actions">
              <el-tag :type="provider.enabled ? 'success' : 'info'" effect="dark">
                {{ provider.enabled ? '启用' : '禁用' }}
              </el-tag>
              <button type="button" class="edit-link" @click="openEditor(provider.id)">编辑</button>
            </div>
          </div>
          <div class="provider-meta">
            <span>模型</span>
            <strong>{{ provider.model || '-' }}</strong>
          </div>
          <div class="provider-meta">
            <span>Base URL</span>
            <strong>{{ displayBaseUrl(provider.base_url) }}</strong>
          </div>
          <div class="cap-list">
            <span :class="{ on: provider.supports_streaming }">stream</span>
            <span :class="{ on: provider.supports_functions }">tools</span>
            <span :class="{ on: provider.supports_vision }">vision</span>
          </div>
        </article>
      </div>

      <el-empty v-else description="暂无 LLM Provider 配置" />
    </section>

    <section class="panel-card raw-panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">CONFIG SNAPSHOT</p>
          <h2>脱敏配置快照</h2>
        </div>
        <span class="hint">只读展示，避免覆盖真实密钥</span>
      </div>
      <pre>{{ configPreview }}</pre>
    </section>

    <el-drawer
      v-model="editorVisible"
      title="编辑 LLM 配置"
      size="520px"
      class="llm-editor-drawer"
      destroy-on-close
    >
      <el-form label-position="top" class="llm-editor-form">
        <el-form-item label="启用 LLM">
          <el-switch v-model="editForm.enabled" />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="Provider ID">
            <el-input v-model="editForm.providerId" disabled />
          </el-form-item>
          <el-form-item label="显示名称">
            <el-input v-model="editForm.name" placeholder="OpenAI" />
          </el-form-item>
        </div>

        <el-form-item label="模型">
          <el-input v-model="editForm.model" placeholder="gpt-4.1-mini" />
        </el-form-item>

        <el-form-item label="Base URL">
          <el-input v-model="editForm.baseUrl" placeholder="https://api.openai.com/v1" />
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="editForm.apiKey"
            type="password"
            show-password
            placeholder="留空则保留当前密钥"
            autocomplete="new-password"
          />
          <p class="form-help">保存时留空不会覆盖现有密钥；只有填写新 Key 才会替换。</p>
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="Temperature">
            <el-input-number v-model="editForm.temperature" :min="0" :max="2" :step="0.1" controls-position="right" />
          </el-form-item>
          <el-form-item label="Max Tokens">
            <el-input-number v-model="editForm.maxTokens" :min="1" :max="32000" controls-position="right" />
          </el-form-item>
        </div>

        <div class="form-grid">
          <el-form-item label="Timeout 秒">
            <el-input-number v-model="editForm.timeout" :min="1" :max="300" controls-position="right" />
          </el-form-item>
          <el-form-item label="最大重试">
            <el-input-number v-model="editForm.maxRetries" :min="0" :max="10" controls-position="right" />
          </el-form-item>
        </div>

        <el-form-item label="流式输出">
          <el-switch v-model="editForm.stream" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="editorVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveConfig">保存并应用</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api/client'

const loading = ref(false)
const reloading = ref(false)
const saving = ref(false)
const editorVisible = ref(false)
const savedConfig = ref({})
const runtimeConfig = ref({})
const configSynced = ref(false)
const editingProviderId = ref('')
const editForm = ref({
  enabled: true,
  providerId: '',
  name: '',
  model: '',
  baseUrl: '',
  apiKey: '',
  temperature: 0.7,
  maxTokens: 2000,
  timeout: 30,
  maxRetries: 3,
  stream: false
})

const providers = computed(() => savedConfig.value.providers || [])
const defaultProvider = computed(() => providers.value.find((item) => item.id === savedConfig.value.default_provider))

const metrics = computed(() => [
  {
    label: '运行状态',
    value: savedConfig.value.enabled === false ? 'OFF' : 'ON',
    detail: runtimeConfig.value ? 'LLM processor runtime' : '运行时信息未返回',
    tone: savedConfig.value.enabled === false ? 'warning' : 'good'
  },
  {
    label: '默认模型',
    value: runtimeConfig.value?.model || defaultProvider.value?.model || '-',
    detail: runtimeConfig.value?.provider || savedConfig.value.default_provider || '未指定 provider',
    tone: 'neutral'
  },
  {
    label: 'Provider',
    value: providers.value.length,
    detail: `${providers.value.filter((item) => item.enabled).length} 个启用`,
    tone: providers.value.length ? 'good' : 'warning'
  },
  {
    label: '配置同步',
    value: configSynced.value ? 'SYNC' : 'CHECK',
    detail: configSynced.value ? '保存配置与运行时一致' : '建议重新加载后确认',
    tone: configSynced.value ? 'good' : 'warning'
  }
])

const runtimeRows = computed(() => [
  { label: 'Provider', value: runtimeConfig.value?.provider || savedConfig.value.default_provider || '-' },
  { label: 'Model', value: runtimeConfig.value?.model || defaultProvider.value?.model || '-' },
  { label: 'Temperature', value: runtimeConfig.value?.temperature ?? savedConfig.value.global_defaults?.temperature ?? '-' },
  { label: 'Max Tokens', value: runtimeConfig.value?.max_tokens ?? savedConfig.value.global_defaults?.max_tokens ?? '-' },
  { label: 'Timeout', value: `${runtimeConfig.value?.timeout ?? savedConfig.value.global_defaults?.timeout ?? '-'}s` },
  { label: 'API Key', value: (runtimeConfig.value?.api_key || defaultProvider.value?.api_key) ? '已脱敏' : '未配置' }
])

const policyRows = computed(() => [
  {
    label: '敏感数据脱敏',
    enabled: savedConfig.value.security?.mask_sensitive_data !== false,
    detail: savedConfig.value.security?.mask_sensitive_data === false ? '响应可能包含敏感字段' : 'API key 与密钥字段会脱敏展示'
  },
  {
    label: '请求日志',
    enabled: savedConfig.value.logging?.enable_request_logging !== false,
    detail: savedConfig.value.logging?.enable_response_logging ? '请求与响应日志开启' : '仅记录请求侧信息'
  },
  {
    label: '缓存',
    enabled: savedConfig.value.cache?.enabled === true,
    detail: savedConfig.value.cache?.enabled ? `TTL ${savedConfig.value.cache.ttl || 0}s` : '当前未启用缓存'
  },
  {
    label: '监控',
    enabled: savedConfig.value.monitoring?.enabled !== false,
    detail: savedConfig.value.monitoring?.collect_metrics === false ? '指标采集关闭' : '采集调用耗时和错误率'
  }
])

const configPreview = computed(() => JSON.stringify(maskSecrets(savedConfig.value || {}), null, 2))

const normalizeRuntimeResponse = (payload) => {
  const body = payload?.data || payload || {}
  return body.data || body
}

const normalizeSavedConfig = (config) => {
  const source = config || {}
  if (Array.isArray(source.providers)) {
    return source
  }

  if (source.provider || source.model || source.base_url) {
    const providerId = source.provider || 'default'
    return {
      version: 'runtime',
      name: 'LLM配置',
      description: '由兼容接口返回的运行时配置',
      enabled: source.enabled !== false,
      default_provider: providerId,
      providers: [
        {
          id: providerId,
          name: providerId.toUpperCase(),
          enabled: source.enabled !== false,
          model: source.model,
          base_url: source.base_url,
          api_key: source.api_key ? '***' : '',
          temperature: source.temperature,
          max_tokens: source.max_tokens,
          timeout: source.timeout,
          max_retries: source.max_retries,
          stream: source.stream,
          supports_streaming: source.stream !== false,
          supports_functions: true,
          supports_vision: false
        }
      ],
      global_defaults: {
        temperature: source.temperature,
        max_tokens: source.max_tokens,
        timeout: source.timeout,
        max_retries: source.max_retries,
        stream: source.stream
      },
      security: {
        mask_sensitive_data: true
      },
      logging: {
        enable_request_logging: true,
        enable_response_logging: false
      },
      cache: {
        enabled: false
      },
      monitoring: {
        enabled: true,
        collect_metrics: true
      }
    }
  }

  return source
}

const maskSecrets = (value) => {
  if (Array.isArray(value)) {
    return value.map(maskSecrets)
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        /api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password/i.test(key) ? '***' : maskSecrets(item)
      ])
    )
  }
  return value
}

const cloneConfig = () => JSON.parse(JSON.stringify(savedConfig.value || {}))

const openEditor = (providerId = savedConfig.value.default_provider) => {
  const provider = providers.value.find((item) => item.id === providerId) || providers.value[0] || {}
  editingProviderId.value = provider.id || providerId || 'openai'
  editForm.value = {
    enabled: savedConfig.value.enabled !== false,
    providerId: editingProviderId.value,
    name: provider.name || editingProviderId.value.toUpperCase(),
    model: provider.model || runtimeConfig.value?.model || '',
    baseUrl: provider.base_url === '***' ? '' : provider.base_url || '',
    apiKey: '',
    temperature: Number(provider.temperature ?? savedConfig.value.global_defaults?.temperature ?? 0.7),
    maxTokens: Number(provider.max_tokens ?? savedConfig.value.global_defaults?.max_tokens ?? 2000),
    timeout: Number(provider.timeout ?? savedConfig.value.global_defaults?.timeout ?? 30),
    maxRetries: Number(provider.max_retries ?? savedConfig.value.global_defaults?.max_retries ?? 3),
    stream: Boolean(provider.stream ?? savedConfig.value.global_defaults?.stream ?? false)
  }
  editorVisible.value = true
}

const saveConfig = async () => {
  const nextConfig = cloneConfig()
  const providerIndex = (nextConfig.providers || []).findIndex((item) => item.id === editingProviderId.value)
  if (providerIndex < 0) {
    ElMessage.error('未找到可编辑的 Provider')
    return
  }

  const currentProvider = nextConfig.providers[providerIndex]
  nextConfig.enabled = editForm.value.enabled
  nextConfig.default_provider = editForm.value.providerId
  nextConfig.global_defaults = {
    ...(nextConfig.global_defaults || {}),
    temperature: editForm.value.temperature,
    max_tokens: editForm.value.maxTokens,
    timeout: editForm.value.timeout,
    max_retries: editForm.value.maxRetries,
    stream: editForm.value.stream
  }
  nextConfig.providers[providerIndex] = {
    ...currentProvider,
    id: editForm.value.providerId,
    name: editForm.value.name || editForm.value.providerId.toUpperCase(),
    enabled: editForm.value.enabled,
    model: editForm.value.model,
    base_url: editForm.value.baseUrl || currentProvider.base_url || null,
    api_key: editForm.value.apiKey || currentProvider.api_key || '***',
    temperature: editForm.value.temperature,
    max_tokens: editForm.value.maxTokens,
    timeout: editForm.value.timeout,
    max_retries: editForm.value.maxRetries,
    stream: editForm.value.stream
  }

  saving.value = true
  try {
    await api.config.updateLLMConfig(nextConfig)
    ElMessage.success('LLM 配置已保存并应用')
    editorVisible.value = false
    await loadConfig()
  } finally {
    saving.value = false
  }
}

const loadConfig = async () => {
  loading.value = true
  try {
    const [currentResponse, runtimeResponse] = await Promise.all([
      api.config.getLLMConfig(),
      api.config.getLLMRuntimeConfig()
    ])
    const current = normalizeRuntimeResponse(currentResponse)
    const runtime = normalizeRuntimeResponse(runtimeResponse)
    savedConfig.value = normalizeSavedConfig(current.config || current.saved_config || current || {})
    runtimeConfig.value = runtime.runtime_config || {}
    configSynced.value = Boolean(runtime.config_synced)
  } finally {
    loading.value = false
  }
}

const reloadConfig = async () => {
  reloading.value = true
  try {
    await api.config.reloadLLMConfig()
    ElMessage.success('LLM 配置已重新加载')
    await loadConfig()
  } finally {
    reloading.value = false
  }
}

const displayBaseUrl = (value) => {
  if (!value) return '默认端点'
  if (value === '***') return '已脱敏，保存时保留原值'
  return value
}

onMounted(loadConfig)
</script>

<style scoped>
.llm-config-page {
  --line: var(--ops-border);
  --panel: var(--ops-surface);
  --panel-strong: var(--ops-surface-raised);
  --text: var(--ops-text);
  --muted: var(--ops-muted);
  --green: var(--ops-success);
  --amber: var(--ops-warning);
  --cyan: var(--ops-accent);
  min-height: 100%;
  padding: 28px;
  color: var(--text);
  background: var(--ops-bg);
}

.llm-hero,
.metric-grid,
.llm-layout,
.section-head,
.provider-top,
.provider-meta,
.policy-item,
.hero-actions {
  display: flex;
}

.llm-hero {
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  margin-bottom: 18px;
}

.llm-hero h1,
.section-head h2,
.policy-panel h2 {
  margin: 0;
  color: var(--text);
}

.llm-hero h1 {
  font-size: 32px;
}

.llm-hero span,
.metric-card p,
.policy-item p,
.hint,
.provider-count {
  color: var(--muted);
}

.hero-actions {
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.panel-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: none;
  backdrop-filter: none;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.metric-card {
  flex-direction: column;
  padding: 16px;
}

.metric-card span {
  color: var(--muted);
  font-size: 12px;
}

.metric-card strong {
  margin: 8px 0 2px;
  color: var(--text);
  font-size: 28px;
}

.metric-card.good strong,
.status-dot.green {
  color: var(--green);
}

.metric-card.warning strong,
.status-dot.amber {
  color: var(--amber);
}

.llm-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(300px, 0.9fr);
  gap: 18px;
  margin-bottom: 18px;
}

.runtime-panel,
.policy-panel,
.providers-panel,
.raw-panel {
  padding: 18px;
}

.section-head {
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.runtime-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.runtime-item {
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

.runtime-item span,
.provider-meta span {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
}

.runtime-item strong,
.provider-meta strong {
  display: block;
  overflow-wrap: anywhere;
  color: var(--text);
}

.policy-list {
  display: grid;
  gap: 14px;
}

.policy-item {
  gap: 12px;
  align-items: flex-start;
}

.status-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  margin-top: 5px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 18px currentColor;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.provider-card {
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

.provider-card.active {
  border-color: var(--ops-accent-border);
  box-shadow: inset 0 0 0 1px var(--ops-accent-border);
}

.provider-top {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.provider-actions {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  gap: 8px;
}

.edit-link {
  padding: 0;
  border: 0;
  color: var(--cyan);
  background: transparent;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.provider-top code {
  display: block;
  margin-top: 4px;
  color: var(--cyan);
  font-size: 12px;
}

.provider-meta {
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--ops-border);
}

.provider-meta strong {
  text-align: right;
}

.cap-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.cap-list span {
  padding: 5px 8px;
  border: 1px solid var(--ops-border);
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
}

.cap-list span.on {
  border-color: color-mix(in srgb, var(--ops-success) 40%, transparent);
  color: var(--green);
  background: var(--ops-success-soft);
}

.raw-panel {
  margin-top: 18px;
}

.raw-panel pre {
  max-height: 360px;
  overflow: auto;
  margin: 0;
  padding: 14px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--panel-strong);
  color: var(--ops-text-soft);
  font-size: 12px;
  line-height: 1.6;
}

.skeleton-wrap {
  padding: 10px 0;
}

.llm-editor-form {
  padding-right: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-help {
  margin: 6px 0 0;
  color: var(--ops-muted);
  font-size: 12px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:global(.llm-editor-drawer) {
  background: var(--ops-surface);
  color: var(--ops-text);
}

:global(.llm-editor-drawer .el-drawer__header) {
  color: var(--ops-text);
  border-bottom: 1px solid var(--ops-border);
}

:global(.llm-editor-drawer .el-form-item__label) {
  color: var(--ops-text-soft);
}

@media (max-width: 1180px) {
  .metric-grid,
  .provider-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .runtime-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .llm-config-page {
    padding: 18px;
  }

  .llm-hero,
  .llm-layout {
    grid-template-columns: 1fr;
  }

  .llm-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .provider-grid,
  .form-grid,
  .runtime-grid {
    grid-template-columns: 1fr;
  }
}
</style>
