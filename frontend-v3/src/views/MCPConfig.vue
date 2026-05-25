<template>
  <div class="mcp-page">
    <div class="page-header">
      <div>
        <div class="page-title">MCP 工具管理</div>
        <div class="page-subtitle">ToolSearch、K8s、ECS 与阿里云只读能力配置</div>
      </div>
      <n-button size="small" :loading="mcpStore.loading || mcpStore.healthLoading" @click="mcpStore.refresh()">刷新</n-button>
    </div>

    <div class="stats-grid">
      <div class="stat-block">
        <span class="stat-label">ToolSearch</span>
        <strong>{{ toolsearchStatus }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">目录工具</span>
        <strong>{{ mcpStore.toolsearchHealth?.catalog_total ?? 0 }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">可执行</span>
        <strong>{{ executionPolicyCount('executable') }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">仅目录</span>
        <strong>{{ executionPolicyCount('catalog_only') }}</strong>
      </div>
      <div class="stat-block">
        <span class="stat-label">阿里云工具</span>
        <strong>{{ availableAliyunTools }}/{{ aliyunTools.length }}</strong>
      </div>
    </div>

    <div v-if="mcpStore.toolsearchHealth?.catalog_categories?.length" class="category-row">
      <n-tag v-for="item in mcpStore.toolsearchHealth.catalog_categories" :key="item.name" size="small" round>
        {{ item.name }} {{ item.count }}
      </n-tag>
    </div>

    <div class="config-grid">
      <section class="config-panel">
        <div class="config-panel-head">
          <div>
            <div class="config-title">K8s MCP</div>
            <div class="config-subtitle">{{ mcpStore.mcpConfig?.config_path || '未读取配置路径' }}</div>
          </div>
          <n-tag size="small" :type="statusTagType(mcpStore.mcpConfig?.k8s.available, mcpStore.mcpConfig?.k8s.enabled)">
            {{ statusLabel(mcpStore.mcpConfig?.k8s.available, mcpStore.mcpConfig?.k8s.enabled) }}
          </n-tag>
        </div>
        <div class="form-grid">
          <label class="field-row inline-field">
            <span>启用</span>
            <n-switch v-model:value="form.k8s.enabled" size="small" :disabled="!auth.isAdmin" />
          </label>
          <label class="field-row inline-field">
            <span>集群内运行</span>
            <n-switch v-model:value="form.k8s.in_cluster" size="small" :disabled="!auth.isAdmin" />
          </label>
          <label class="field-row wide-field">
            <span>Kubeconfig 路径</span>
            <n-input
              v-model:value="form.k8s.kubeconfig_path"
              clearable
              placeholder="默认使用 ~/.kube/config"
              :disabled="form.k8s.in_cluster || !auth.isAdmin"
            />
          </label>
          <label class="field-row">
            <span>默认命名空间</span>
            <n-input v-model:value="form.k8s.namespace" placeholder="default" :disabled="!auth.isAdmin" />
          </label>
        </div>
        <n-alert v-if="mcpStore.mcpConfig?.k8s.unavailable_reason" type="warning" :bordered="false" class="status-alert">
          {{ mcpStore.mcpConfig.k8s.unavailable_reason }}
        </n-alert>
      </section>

      <section class="config-panel">
        <div class="config-panel-head">
          <div>
            <div class="config-title">ECS MCP</div>
            <div class="config-subtitle">阿里云 ECS 只读巡检工具</div>
          </div>
          <n-tag size="small" :type="statusTagType(mcpStore.mcpConfig?.ecs.available, mcpStore.mcpConfig?.ecs.enabled)">
            {{ statusLabel(mcpStore.mcpConfig?.ecs.available, mcpStore.mcpConfig?.ecs.enabled) }}
          </n-tag>
        </div>
        <div class="form-grid">
          <label class="field-row inline-field">
            <span>启用</span>
            <n-switch v-model:value="form.ecs.enabled" size="small" :disabled="!auth.isAdmin" />
          </label>
          <label class="field-row">
            <span>地域</span>
            <n-input v-model:value="form.ecs.region_id" placeholder="cn-hangzhou" :disabled="!auth.isAdmin" />
          </label>
          <label class="field-row">
            <span>AccessKey ID</span>
            <n-input
              v-model:value="form.ecs.access_key_id"
              clearable
              :placeholder="mcpStore.mcpConfig?.ecs.access_key_id_configured ? '已配置，留空保持不变' : 'AccessKey ID'"
              :input-props="{ autocomplete: 'off' }"
              :disabled="!auth.isAdmin"
            />
          </label>
          <label class="field-row">
            <span>AccessKey Secret</span>
            <n-input
              v-model:value="form.ecs.access_key_secret"
              type="password"
              show-password-on="click"
              clearable
              :placeholder="mcpStore.mcpConfig?.ecs.access_key_secret_configured ? '已配置，留空保持不变' : 'AccessKey Secret'"
              :input-props="{ autocomplete: 'new-password' }"
              :disabled="!auth.isAdmin"
            />
          </label>
        </div>
        <n-alert v-if="mcpStore.mcpConfig?.ecs.unavailable_reason" type="warning" :bordered="false" class="status-alert">
          {{ mcpStore.mcpConfig.ecs.unavailable_reason }}
        </n-alert>
      </section>

      <section class="config-panel aliyun-panel">
        <div class="config-panel-head">
          <div>
            <div class="config-title">阿里云只读 Adapter</div>
            <div class="config-subtitle">
              仅暴露白名单内的 ECS、CMS、SLS 和负载均衡查询工具
            </div>
          </div>
          <n-tag size="small" :type="statusTagType(mcpStore.mcpConfig?.aliyun.available, mcpStore.mcpConfig?.aliyun.enabled)">
            {{ statusLabel(mcpStore.mcpConfig?.aliyun.available, mcpStore.mcpConfig?.aliyun.enabled) }}
          </n-tag>
        </div>

        <div class="adapter-summary">
          <div>
            <span>默认地域</span>
            <strong>{{ mcpStore.mcpConfig?.aliyun.default_region_id || 'cn-hangzhou' }}</strong>
          </div>
          <div>
            <span>允许地域</span>
            <strong>{{ mcpStore.mcpConfig?.aliyun.allowed_regions?.length || 0 }}</strong>
          </div>
          <div>
            <span>SLS 映射</span>
            <strong>{{ mcpStore.mcpConfig?.aliyun.sls_mapping_count || 0 }}</strong>
          </div>
        </div>

        <div class="form-grid aliyun-form">
          <label class="field-row inline-field">
            <span>启用</span>
            <n-switch v-model:value="form.aliyun.enabled" size="small" :disabled="!auth.isAdmin" />
          </label>
          <label class="field-row">
            <span>默认地域</span>
            <n-input v-model:value="form.aliyun.default_region_id" placeholder="cn-hangzhou" :disabled="!auth.isAdmin" />
          </label>
          <label class="field-row">
            <span>AccessKey ID</span>
            <n-input
              v-model:value="form.aliyun.access_key_id"
              clearable
              :placeholder="mcpStore.mcpConfig?.aliyun.access_key_id_configured ? '已配置，留空保持不变' : 'AccessKey ID'"
              :input-props="{ autocomplete: 'off' }"
              :disabled="!auth.isAdmin"
            />
          </label>
          <label class="field-row">
            <span>AccessKey Secret</span>
            <n-input
              v-model:value="form.aliyun.access_key_secret"
              type="password"
              show-password-on="click"
              clearable
              :placeholder="mcpStore.mcpConfig?.aliyun.access_key_secret_configured ? '已配置，留空保持不变' : 'AccessKey Secret'"
              :input-props="{ autocomplete: 'new-password' }"
              :disabled="!auth.isAdmin"
            />
          </label>
          <label class="field-row wide-field">
            <span>允许地域</span>
            <n-input
              v-model:value="form.aliyun.allowed_regions"
              placeholder="cn-hangzhou, cn-shanghai"
              :disabled="!auth.isAdmin"
            />
          </label>
          <label class="field-row wide-field">
            <span>允许实例 ID</span>
            <n-input
              v-model:value="form.aliyun.allowed_instance_ids"
              placeholder="可选，逗号分隔；为空表示仅按地域和标签限制"
              :disabled="!auth.isAdmin"
            />
          </label>
          <label class="field-row wide-field json-field">
            <span>必需标签 JSON</span>
            <n-input
              v-model:value="form.aliyun.required_tags_json"
              type="textarea"
              :autosize="{ minRows: 4, maxRows: 8 }"
              placeholder='{"env":["prod"],"owner":["ops"]}'
              :disabled="!auth.isAdmin"
            />
          </label>
          <label class="field-row wide-field json-field">
            <span>SLS 映射 JSON</span>
            <n-input
              v-model:value="form.aliyun.sls_mappings_json"
              type="textarea"
              :autosize="{ minRows: 4, maxRows: 8 }"
              placeholder='[{"service":"k8s","env":"prod","region_id":"cn-hangzhou","project":"example","logstore":"app"}]'
              :disabled="!auth.isAdmin"
              @update:value="slsMappingsDirty = true"
            />
          </label>
        </div>
        <n-alert v-if="mcpStore.mcpConfig?.aliyun.unavailable_reason" type="warning" :bordered="false" class="status-alert">
          {{ mcpStore.mcpConfig.aliyun.unavailable_reason }}
        </n-alert>
        <p class="readonly-note">当前版本只允许查询，不向 LLM 暴露写入、删除、重启、扩缩容或公网变更能力。</p>
      </section>
    </div>

    <n-alert v-if="formError" type="error" :bordered="false">
      {{ formError }}
    </n-alert>

    <div class="config-actions">
      <n-button
        type="primary"
        :loading="mcpStore.configSaving"
        :disabled="mcpStore.configLoading || !auth.isAdmin"
        @click="saveBuiltinConfig"
      >
        保存 MCP 配置
      </n-button>
      <span v-if="mcpStore.mcpConfig" class="save-hint">
        {{ auth.isAdmin ? '保存后会立即刷新内置工具列表。' : '只有 admin 可以保存 MCP 配置。' }}
      </span>
    </div>

    <n-data-table
      :loading="mcpStore.loading"
      :columns="columns"
      :data="mcpStore.tools"
      :pagination="{ pageSize: 20 }"
      size="small"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue'
import { NAlert, NButton, NDataTable, NInput, NSwitch, NTag } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useMcpStore } from '@/stores/mcp'

const mcpStore = useMcpStore()
const auth = useAuthStore()
const formError = ref('')
const slsMappingsDirty = ref(false)
const form = reactive({
  k8s: {
    enabled: true,
    kubeconfig_path: '',
    namespace: 'default',
    in_cluster: false,
  },
  ecs: {
    enabled: false,
    access_key_id: '',
    access_key_secret: '',
    region_id: 'cn-hangzhou',
  },
  aliyun: {
    enabled: false,
    access_key_id: '',
    access_key_secret: '',
    default_region_id: 'cn-hangzhou',
    allowed_regions: 'cn-hangzhou',
    required_tags_json: '{}',
    allowed_instance_ids: '',
    sls_mappings_json: '[]',
  },
})

const toolsearchStatus = computed(() => {
  if (!mcpStore.toolsearchHealth) return '未连接'
  return mcpStore.toolsearchHealth.connected ? '已连接' : '未连接'
})

const aliyunTools = computed(() => mcpStore.tools.filter((tool) => tool.name.startsWith('aliyun-')))
const availableAliyunTools = computed(() => aliyunTools.value.filter((tool) => tool.available !== false).length)

const columns = [
  { title: '工具名', key: 'name', width: 200 },
  { title: '描述', key: 'description' },
  { title: '来源', key: 'server', width: 120, render: (row: any) => h(NTag, { size: 'small', type: row.server === 'builtin' ? 'info' : 'success' }, { default: () => row.server }) },
  { title: '状态', key: 'available', width: 110, render: (row: any) => h(NTag, { size: 'small', type: row.available === false ? 'error' : 'success' }, { default: () => row.available === false ? '不可用' : '可用' }) },
]

function executionPolicyCount(name: string) {
  return mcpStore.toolsearchHealth?.execution_policies?.find((item) => item.name === name)?.count ?? 0
}

function statusLabel(available?: boolean, enabled?: boolean) {
  if (enabled === false) return '未启用'
  return available ? '可用' : '不可用'
}

function statusTagType(available?: boolean, enabled?: boolean) {
  if (enabled === false) return 'default'
  return available ? 'success' : 'warning'
}

async function saveBuiltinConfig() {
  formError.value = ''

  let requiredTags: Record<string, string[]>
  let slsMappings: Array<Record<string, unknown>> | undefined

  try {
    requiredTags = parseRequiredTags(form.aliyun.required_tags_json)
    slsMappings = slsMappingsDirty.value ? parseSlsMappings(form.aliyun.sls_mappings_json) : undefined
  } catch (error) {
    formError.value = error instanceof Error ? error.message : '阿里云配置 JSON 格式不正确'
    return
  }

  const aliyunPayload: {
    enabled: boolean
    default_region_id: string
    allowed_regions: string[]
    required_tags: Record<string, string[]>
    allowed_instance_ids: string[]
    access_key_id: string
    access_key_secret: string
    sls?: { mappings: Array<Record<string, unknown>> }
  } = {
    enabled: form.aliyun.enabled,
    default_region_id: form.aliyun.default_region_id.trim() || 'cn-hangzhou',
    allowed_regions: splitComma(form.aliyun.allowed_regions),
    required_tags: requiredTags,
    allowed_instance_ids: splitComma(form.aliyun.allowed_instance_ids),
    access_key_id: form.aliyun.access_key_id.trim(),
    access_key_secret: form.aliyun.access_key_secret.trim(),
  }
  if (slsMappings) {
    aliyunPayload.sls = { mappings: slsMappings }
  }

  await mcpStore.saveConfig({
    k8s: {
      enabled: form.k8s.enabled,
      kubeconfig_path: form.k8s.in_cluster ? '' : form.k8s.kubeconfig_path.trim(),
      namespace: form.k8s.namespace.trim() || 'default',
      in_cluster: form.k8s.in_cluster,
    },
    ecs: {
      enabled: form.ecs.enabled,
      region_id: form.ecs.region_id.trim() || 'cn-hangzhou',
      access_key_id: form.ecs.access_key_id.trim(),
      access_key_secret: form.ecs.access_key_secret.trim(),
    },
    aliyun: aliyunPayload,
  })
  form.ecs.access_key_id = ''
  form.ecs.access_key_secret = ''
  form.aliyun.access_key_id = ''
  form.aliyun.access_key_secret = ''
  slsMappingsDirty.value = false
}

watch(() => mcpStore.mcpConfig, (config) => {
  if (!config) return
  form.k8s.enabled = config.k8s.enabled
  form.k8s.kubeconfig_path = config.k8s.kubeconfig_path || ''
  form.k8s.namespace = config.k8s.namespace || 'default'
  form.k8s.in_cluster = config.k8s.in_cluster
  form.ecs.enabled = config.ecs.enabled
  form.ecs.region_id = config.ecs.region_id || 'cn-hangzhou'
  form.ecs.access_key_id = ''
  form.ecs.access_key_secret = ''
  if (!config.aliyun) return
  form.aliyun.enabled = config.aliyun.enabled
  form.aliyun.default_region_id = config.aliyun.default_region_id || 'cn-hangzhou'
  form.aliyun.allowed_regions = config.aliyun.allowed_regions?.join(', ') || form.aliyun.default_region_id
  form.aliyun.required_tags_json = JSON.stringify(config.aliyun.required_tags || {}, null, 2)
  form.aliyun.allowed_instance_ids = config.aliyun.allowed_instance_ids?.join(', ') || ''
  form.aliyun.sls_mappings_json = '[]'
  form.aliyun.access_key_id = ''
  form.aliyun.access_key_secret = ''
  slsMappingsDirty.value = false
}, { immediate: true })

onMounted(() => mcpStore.refresh())

function splitComma(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseRequiredTags(value: string) {
  const parsed = JSON.parse(value.trim() || '{}')
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('必需标签 JSON 必须是对象，例如 {"env":["prod"]}')
  }
  const normalized: Record<string, string[]> = {}
  for (const [key, rawValues] of Object.entries(parsed)) {
    if (!Array.isArray(rawValues)) {
      throw new Error(`必需标签 ${key} 必须是字符串数组`)
    }
    normalized[key] = rawValues.map((item) => String(item).trim()).filter(Boolean)
  }
  return normalized
}

function parseSlsMappings(value: string) {
  const parsed = JSON.parse(value.trim() || '[]')
  if (!Array.isArray(parsed)) {
    throw new Error('SLS 映射 JSON 必须是数组')
  }
  return parsed.map((item) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      throw new Error('每条 SLS 映射必须是对象')
    }
    return item as Record<string, unknown>
  })
}
</script>

<style scoped>
.mcp-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--dr-text);
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  color: var(--dr-text);
  font-size: var(--dr-text-2xl);
  font-weight: 620;
  line-height: 1.12;
}
.page-subtitle {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-md);
  margin-top: 7px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.stat-block {
  min-height: 92px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface);
  padding: 15px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  box-shadow: 0 1px 0 rgba(25, 24, 20, 0.03);
}
.stat-label {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  font-weight: 570;
}
.stat-block strong {
  color: var(--dr-text);
  font-size: 22px;
  font-weight: 610;
  line-height: 1.2;
}
.category-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}
.config-panel {
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface-lift);
  padding: 16px;
  box-shadow: var(--dr-shadow);
}
.config-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.config-title {
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 610;
}
.config-subtitle {
  margin-top: 2px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  word-break: break-all;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--dr-text-soft);
  font-size: var(--dr-text-sm);
  font-weight: 590;
}
.inline-field {
  min-height: 44px;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  padding: 0 10px;
  background: #fffdf8;
}
.wide-field {
  grid-column: 1 / -1;
}
.aliyun-panel {
  grid-column: 1 / -1;
}
.adapter-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.adapter-summary > div {
  min-height: 58px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius-sm);
  background: #fffdf8;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
}
.adapter-summary span,
.readonly-note {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}
.adapter-summary strong {
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 610;
}
.aliyun-form {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.json-field :deep(.n-input__textarea-el) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: var(--dr-text-sm);
}
.readonly-note {
  margin: 10px 0 0;
}
.status-alert {
  margin-top: 10px;
}
.config-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.save-hint {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .config-grid,
  .form-grid,
  .adapter-summary {
    grid-template-columns: 1fr;
  }
  .config-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
