<template>
  <div class="access-page dr-page">
    <header class="dr-page-header">
      <div>
        <h1>权限管理</h1>
        <p>管理当前角色边界、工具权限策略和审计事件。未接入真实后端的用户写入能力保持只读展示。</p>
      </div>
      <div class="dr-toolbar">
        <n-button secondary :loading="auditLoading" @click="fetchAudit">刷新审计</n-button>
        <n-button type="primary" disabled>新增用户</n-button>
      </div>
    </header>

    <section class="dr-stats-grid">
      <article class="dr-stat-card">
        <span>用户角色</span>
        <strong>{{ roleUsers.length }}</strong>
        <small>admin / operator / viewer</small>
      </article>
      <article class="dr-stat-card">
        <span>角色策略</span>
        <strong>{{ rolePolicies.length }}</strong>
        <small>当前前端只读展示</small>
      </article>
      <article class="dr-stat-card">
        <span>审计事件</span>
        <strong>{{ auditLogs.length }}</strong>
        <small>最近 {{ auditLimit }} 条</small>
      </article>
      <article class="dr-stat-card">
        <span>危险动作</span>
        <strong>确认</strong>
        <small>写入与高危工具走确认门</small>
      </article>
    </section>

    <div class="dr-two-column access-workspace">
      <section class="dr-panel">
        <div class="dr-panel-head">
          <div>
            <h2 class="dr-panel-title">用户和角色</h2>
            <span class="dr-panel-subtitle">展示当前系统约定角色，不模拟不存在的保存接口。</span>
          </div>
          <n-button secondary disabled>筛选</n-button>
        </div>
        <div class="search-row">
          <n-input v-model:value="userSearch" clearable placeholder="搜索用户名或角色" />
        </div>
        <div class="role-list">
          <article v-for="user in filteredUsers" :key="user.username" class="role-row">
            <div class="user-cell">
              <span class="avatar">{{ user.username.slice(0, 1).toUpperCase() }}</span>
              <span>
                <strong>{{ user.username }}</strong>
                <small>{{ user.description }}</small>
              </span>
            </div>
            <span :class="['dr-badge', user.role]">{{ user.role }}</span>
            <span>{{ user.scope }}</span>
            <span class="dr-muted">{{ user.lastActive }}</span>
          </article>
        </div>
      </section>

      <aside class="detail-stack">
        <section class="dr-panel">
          <div class="dr-panel-head">
            <div>
              <h2 class="dr-panel-title">角色策略</h2>
              <span class="dr-panel-subtitle">策略来自当前权限约定，后续接入真实管理 API 后再开放编辑。</span>
            </div>
          </div>
          <div class="policy-form">
            <label class="field">
              <span>选择角色</span>
              <n-select v-model:value="selectedRole" :options="roleOptions" />
            </label>
            <label class="field">
              <span>工具权限</span>
              <n-input :value="selectedPolicy.toolPrefix" readonly />
            </label>
            <p>{{ selectedPolicy.description }}</p>
            <n-button type="primary" disabled>保存策略</n-button>
          </div>
        </section>

        <section class="dr-panel">
          <div class="dr-panel-head">
            <div>
              <h2 class="dr-panel-title">最近审计</h2>
              <span class="dr-panel-subtitle">真实读取 `/config/audit`。</span>
            </div>
          </div>
          <div class="audit-list">
            <article v-for="log in recentAuditLogs" :key="log.id" class="audit-item">
              <span class="audit-dot" />
              <div>
                <strong>{{ log.actor }} · {{ log.action }}</strong>
                <small>{{ log.resource }} / {{ log.result }} / {{ formatTime(log.created_at) }}</small>
              </div>
            </article>
            <div v-if="!recentAuditLogs.length" class="dr-empty">暂无审计事件</div>
          </div>
        </section>
      </aside>
    </div>

    <section class="dr-panel dr-table-panel">
      <div class="dr-panel-head">
        <div>
          <h2 class="dr-panel-title">审计日志</h2>
          <span class="dr-panel-subtitle">保留真实数据表格，方便筛查操作人、资源与结果。</span>
        </div>
      </div>
      <div class="audit-filter-bar">
        <label class="field compact">
          <span>操作人</span>
          <n-input
            v-model:value="auditFilters.actor"
            clearable
            placeholder="admin / scheduler"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>操作</span>
          <n-input
            v-model:value="auditFilters.action"
            clearable
            placeholder="api.get / tool"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>资源</span>
          <n-input
            v-model:value="auditFilters.resource"
            clearable
            placeholder="/chat / aliyun"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>资源 ID</span>
          <n-input
            v-model:value="auditFilters.resource_id"
            clearable
            placeholder="实例 / 会话 / 任务"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>结果</span>
          <n-select
            v-model:value="auditFilters.result"
            clearable
            placeholder="全部"
            :options="resultOptions"
          />
        </label>
        <div class="filter-actions">
          <n-button type="primary" :loading="auditLoading" @click="applyAuditFilters">应用</n-button>
          <n-button secondary :disabled="auditLoading" @click="clearAuditFilters">清空</n-button>
        </div>
      </div>
      <n-data-table :columns="auditColumns" :data="auditLogs" :loading="auditLoading" size="small" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { NButton, NDataTable, NInput, NSelect, NTag } from 'naive-ui'
import { systemApi } from '@/api/client'
import type { AuditLog } from '@/types'

const auditLimit = 50
const auditLogs = ref<AuditLog[]>([])
const auditLoading = ref(false)
const userSearch = ref('')
const selectedRole = ref<'admin' | 'operator' | 'viewer'>('operator')
const auditFilters = ref({
  actor: '',
  action: '',
  resource: '',
  resource_id: '',
  result: null as string | null,
})

const roleUsers = [
  { username: 'admin', role: 'admin', description: '本地默认管理员', scope: '全部工具、配置、审计', lastActive: '当前会话' },
  { username: 'ops', role: 'operator', description: '值班工程师', scope: 'K8s / ECS 工具与定时任务', lastActive: '示例角色' },
  { username: 'viewer', role: 'viewer', description: '观察者账号', scope: 'Dashboard、会话与只读上下文', lastActive: '示例角色' },
]

const rolePolicies = [
  { role: 'admin', toolPrefix: 'all tools', description: '管理员拥有配置、审计、工具执行和高危确认权限。' },
  { role: 'operator', toolPrefix: 'k8s-, ecs-describe-, toolsearch', description: '值班角色可执行常规巡检与调度动作，高危写入仍需要确认。' },
  { role: 'viewer', toolPrefix: 'dashboard, sessions, read-only', description: '观察者只查看聚合状态、历史会话和只读上下文。' },
] as const

const roleOptions = rolePolicies.map((item) => ({ label: item.role, value: item.role }))
const resultOptions = [
  { label: 'success', value: 'success' },
  { label: 'failure', value: 'failure' },
]
const selectedPolicy = computed(() => rolePolicies.find((item) => item.role === selectedRole.value) || rolePolicies[1])
const filteredUsers = computed(() => {
  const query = userSearch.value.trim().toLowerCase()
  if (!query) return roleUsers
  return roleUsers.filter((user) => [user.username, user.role, user.scope].some((value) => value.toLowerCase().includes(query)))
})
const recentAuditLogs = computed(() => auditLogs.value.slice(0, 4))

const auditColumns = [
  { title: '时间', key: 'created_at', width: 170, render: (row: AuditLog) => formatTime(row.created_at) },
  { title: '操作人', key: 'actor', width: 120 },
  { title: '操作', key: 'action', width: 170 },
  { title: '资源', key: 'resource' },
  { title: '资源 ID', key: 'resource_id', width: 140, render: (row: AuditLog) => row.resource_id || '-' },
  {
    title: '结果',
    key: 'result',
    width: 100,
    render: (row: AuditLog) => h(NTag, { size: 'small', type: row.result === 'success' ? 'success' : 'warning' }, { default: () => row.result }),
  },
  { title: 'IP', key: 'ip', width: 140 },
]

async function fetchAudit() {
  auditLoading.value = true
  try {
    auditLogs.value = await systemApi.auditLogs(auditQueryParams())
  } finally {
    auditLoading.value = false
  }
}

function auditQueryParams() {
  const params: {
    actor?: string
    action?: string
    resource?: string
    resource_id?: string
    result?: string
    limit: number
  } = { limit: auditLimit }
  const fields = auditFilters.value
  if (fields.actor.trim()) params.actor = fields.actor.trim()
  if (fields.action.trim()) params.action = fields.action.trim()
  if (fields.resource.trim()) params.resource = fields.resource.trim()
  if (fields.resource_id.trim()) params.resource_id = fields.resource_id.trim()
  if (fields.result) params.result = fields.result
  return params
}

function applyAuditFilters() {
  fetchAudit()
}

function clearAuditFilters() {
  auditFilters.value = {
    actor: '',
    action: '',
    resource: '',
    resource_id: '',
    result: null,
  }
  fetchAudit()
}

function formatTime(value: string) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchAudit)
</script>

<style scoped>
.access-workspace {
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.8fr);
}

.search-row {
  padding: 12px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: var(--dr-bg-page);
}

.role-list {
  display: grid;
}

.role-row {
  display: grid;
  grid-template-columns: minmax(220px, 1.2fr) 110px minmax(180px, 1fr) 120px;
  align-items: center;
  gap: 12px;
  min-height: 72px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  color: var(--dr-text-soft);
  font-size: var(--dr-text-sm);
}

.role-row:last-child {
  border-bottom: 0;
}

.role-row:hover {
  background: #fbf6ee;
}

.user-cell {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
  color: var(--dr-text);
}

.user-cell strong {
  display: block;
  font-size: var(--dr-text-md);
  font-weight: 590;
}

.user-cell small {
  display: block;
  margin-top: 2px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
}

.detail-stack,
.policy-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.policy-form {
  padding: 16px;
}

.field {
  display: grid;
  gap: 6px;
  color: var(--dr-text-soft);
  font-size: var(--dr-text-sm);
  font-weight: 590;
}

.field.compact {
  min-width: 0;
}

.policy-form p {
  margin: 0;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  line-height: 1.58;
}

.audit-list {
  display: flex;
  flex-direction: column;
  min-height: 150px;
  padding: 6px 0;
}

.audit-filter-bar {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr)) auto;
  gap: 12px;
  padding: 14px 16px;
  border-top: 1px solid var(--dr-border-soft);
  border-bottom: 1px solid var(--dr-border-soft);
  background: var(--dr-bg-page);
}

.filter-actions {
  display: flex;
  align-items: end;
  gap: 8px;
  padding-bottom: 1px;
}

.audit-item {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 10px;
  padding: 10px 16px;
}

.audit-dot {
  width: 7px;
  height: 7px;
  margin-top: 7px;
  border-radius: 50%;
  background: var(--dr-accent);
  box-shadow: 0 0 0 4px rgba(201, 100, 66, 0.1);
}

.audit-item strong {
  display: block;
  color: var(--dr-text);
  font-size: var(--dr-text-sm);
  font-weight: 610;
}

.audit-item small {
  display: block;
  margin-top: 2px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
}

@media (max-width: 980px) {
  .role-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .audit-filter-bar {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    align-items: stretch;
  }
}
</style>
