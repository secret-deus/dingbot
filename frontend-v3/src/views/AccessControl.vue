<template>
  <div class="access-page dr-page">
    <header class="dr-page-header">
      <div>
        <h1>权限管理</h1>
        <p>管理当前角色边界、用户状态、工具权限策略和审计事件。</p>
      </div>
      <div class="dr-toolbar">
        <n-button secondary :loading="auditLoading" @click="fetchAudit">刷新审计</n-button>
        <n-button type="primary" @click="showCreateUser = true">新增用户</n-button>
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
            <span class="dr-panel-subtitle">真实读取 `/auth/users`，支持新增、角色调整和账号启停。</span>
          </div>
          <n-button secondary :loading="usersLoading" @click="fetchUsers">刷新用户</n-button>
        </div>
        <div class="search-row">
          <n-input v-model:value="userSearch" clearable placeholder="搜索用户名或角色" />
        </div>
        <div v-if="showCreateUser" class="create-user-form">
          <n-form :show-label="false">
            <div class="create-grid">
              <n-form-item>
                <n-input v-model:value="newUser.username" placeholder="用户名" />
              </n-form-item>
              <n-form-item>
                <n-input v-model:value="newUser.display_name" placeholder="显示名" />
              </n-form-item>
              <n-form-item>
                <n-input v-model:value="newUser.password" type="password" show-password-on="click" placeholder="初始密码" />
              </n-form-item>
              <n-form-item>
                <n-select v-model:value="newUser.role" :options="roleOptions" />
              </n-form-item>
              <div class="create-actions">
                <n-button type="primary" :loading="createLoading" @click="createUser">创建</n-button>
                <n-button secondary :disabled="createLoading" @click="resetCreateForm">取消</n-button>
              </div>
            </div>
          </n-form>
        </div>
        <div class="role-list">
          <article v-for="user in filteredUsers" :key="user.username" class="role-row">
            <div class="user-cell">
              <span class="avatar">{{ user.username.slice(0, 1).toUpperCase() }}</span>
              <span>
                <strong>{{ user.username }}</strong>
                <small>{{ user.display_name || '未设置显示名' }}</small>
              </span>
            </div>
            <n-select v-model:value="user.role" :options="roleOptions" size="small" />
            <n-switch v-model:value="user.is_active" size="small">
              <template #checked>启用</template>
              <template #unchecked>停用</template>
            </n-switch>
            <span class="dr-muted">{{ formatTime(user.updated_at) }}</span>
            <n-button size="small" :loading="savingUser === user.username" @click="saveUser(user)">保存</n-button>
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
import { NButton, NDataTable, NForm, NFormItem, NInput, NSelect, NSwitch, NTag, useMessage } from 'naive-ui'
import { systemApi, userApi } from '@/api/client'
import type { AuditLog, User } from '@/types'

const auditLimit = 50
const message = useMessage()
const auditLogs = ref<AuditLog[]>([])
const auditLoading = ref(false)
const roleUsers = ref<User[]>([])
const usersLoading = ref(false)
const createLoading = ref(false)
const savingUser = ref('')
const showCreateUser = ref(false)
const userSearch = ref('')
const selectedRole = ref<'admin' | 'operator' | 'viewer'>('operator')
const newUser = ref({
  username: '',
  display_name: '',
  password: '',
  role: 'viewer' as User['role'],
})
const auditFilters = ref({
  actor: '',
  action: '',
  resource: '',
  resource_id: '',
  result: null as string | null,
})

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
  if (!query) return roleUsers.value
  return roleUsers.value.filter((user) =>
    [user.username, user.role, user.display_name].some((value) => value.toLowerCase().includes(query)),
  )
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
  } catch {
    message.error('读取审计日志失败')
  } finally {
    auditLoading.value = false
  }
}

async function fetchUsers() {
  usersLoading.value = true
  try {
    roleUsers.value = await userApi.list()
  } catch {
    message.error('读取用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

async function createUser() {
  if (!newUser.value.username.trim() || !newUser.value.password.trim()) {
    message.warning('请填写用户名和初始密码')
    return
  }
  createLoading.value = true
  try {
    await userApi.create({
      username: newUser.value.username.trim(),
      password: newUser.value.password,
      display_name: newUser.value.display_name.trim(),
      role: newUser.value.role,
    })
    message.success('用户已创建')
    resetCreateForm()
    await fetchUsers()
  } catch (error) {
    message.error(errorMessage(error, '创建用户失败'))
  } finally {
    createLoading.value = false
  }
}

async function saveUser(user: User) {
  savingUser.value = user.username
  try {
    const updated = await userApi.update(user.username, {
      display_name: user.display_name,
      role: user.role,
      is_active: user.is_active,
    })
    const index = roleUsers.value.findIndex((item) => item.username === user.username)
    if (index >= 0) roleUsers.value[index] = updated
    message.success('用户已保存')
  } catch (error) {
    message.error(errorMessage(error, '保存用户失败'))
    await fetchUsers()
  } finally {
    savingUser.value = ''
  }
}

function resetCreateForm() {
  showCreateUser.value = false
  newUser.value = {
    username: '',
    display_name: '',
    password: '',
    role: 'viewer',
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

function errorMessage(error: unknown, fallback: string) {
  const maybe = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = maybe.response?.data?.detail
  return typeof detail === 'string' ? detail : maybe.message || fallback
}

onMounted(() => {
  fetchUsers()
  fetchAudit()
})
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
  grid-template-columns: minmax(220px, 1.2fr) 140px 90px 110px 82px;
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

.create-user-form {
  padding: 14px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: var(--dr-bg-page);
}

.create-grid {
  display: grid;
  grid-template-columns: minmax(130px, 1fr) minmax(130px, 1fr) minmax(150px, 1fr) 120px auto;
  gap: 10px;
  align-items: start;
}

.create-actions {
  display: flex;
  gap: 8px;
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

  .create-grid {
    grid-template-columns: 1fr;
  }

  .audit-filter-bar {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    align-items: stretch;
  }
}
</style>
