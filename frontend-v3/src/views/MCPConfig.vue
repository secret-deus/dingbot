<template>
  <div class="mcp-page">
    <div class="page-header">
      <div>
        <div class="page-title">MCP 工具管理</div>
        <div class="page-subtitle">ToolSearch、K8s 与 ECS 工具配置</div>
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
            <n-switch v-model:value="form.k8s.enabled" size="small" />
          </label>
          <label class="field-row inline-field">
            <span>集群内运行</span>
            <n-switch v-model:value="form.k8s.in_cluster" size="small" />
          </label>
          <label class="field-row wide-field">
            <span>Kubeconfig 路径</span>
            <n-input
              v-model:value="form.k8s.kubeconfig_path"
              clearable
              placeholder="默认使用 ~/.kube/config"
              :disabled="form.k8s.in_cluster"
            />
          </label>
          <label class="field-row">
            <span>默认命名空间</span>
            <n-input v-model:value="form.k8s.namespace" placeholder="default" />
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
            <n-switch v-model:value="form.ecs.enabled" size="small" />
          </label>
          <label class="field-row">
            <span>地域</span>
            <n-input v-model:value="form.ecs.region_id" placeholder="cn-hangzhou" />
          </label>
          <label class="field-row">
            <span>AccessKey ID</span>
            <n-input
              v-model:value="form.ecs.access_key_id"
              clearable
              :placeholder="mcpStore.mcpConfig?.ecs.access_key_id_configured ? '已配置，留空保持不变' : 'AccessKey ID'"
              :input-props="{ autocomplete: 'off' }"
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
            />
          </label>
        </div>
        <n-alert v-if="mcpStore.mcpConfig?.ecs.unavailable_reason" type="warning" :bordered="false" class="status-alert">
          {{ mcpStore.mcpConfig.ecs.unavailable_reason }}
        </n-alert>
      </section>
    </div>

    <div class="config-actions">
      <n-button
        type="primary"
        :loading="mcpStore.configSaving"
        :disabled="mcpStore.configLoading"
        @click="saveBuiltinConfig"
      >
        保存 MCP 配置
      </n-button>
      <span v-if="mcpStore.mcpConfig" class="save-hint">保存后会立即刷新内置工具列表。</span>
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
import { computed, h, onMounted, reactive, watch } from 'vue'
import { NAlert, NButton, NDataTable, NInput, NSwitch, NTag } from 'naive-ui'
import { useMcpStore } from '@/stores/mcp'

const mcpStore = useMcpStore()
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
})

const toolsearchStatus = computed(() => {
  if (!mcpStore.toolsearchHealth) return '未连接'
  return mcpStore.toolsearchHealth.connected ? '已连接' : '未连接'
})

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
  })
  form.ecs.access_key_id = ''
  form.ecs.access_key_secret = ''
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
}, { immediate: true })

onMounted(() => mcpStore.refresh())
</script>

<style scoped>
.mcp-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
}
.page-subtitle {
  color: #8f8f8f;
  font-size: 13px;
  margin-top: 2px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.stat-block {
  min-height: 72px;
  border: 1px solid #343434;
  border-radius: 8px;
  background: #202020;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}
.stat-label {
  color: #9a9a9a;
  font-size: 12px;
}
.stat-block strong {
  color: #f2f2f2;
  font-size: 22px;
  line-height: 1.2;
}
.category-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.config-panel {
  border: 1px solid #343434;
  border-radius: 8px;
  background: #202020;
  padding: 14px;
}
.config-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.config-title {
  color: #f2f2f2;
  font-size: 15px;
  font-weight: 600;
}
.config-subtitle {
  margin-top: 2px;
  color: #8f8f8f;
  font-size: 12px;
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
  color: #bdbdbd;
  font-size: 12px;
}
.inline-field {
  min-height: 34px;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #303030;
  border-radius: 8px;
  padding: 0 10px;
}
.wide-field {
  grid-column: 1 / -1;
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
  color: #8f8f8f;
  font-size: 12px;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .config-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
  .config-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
