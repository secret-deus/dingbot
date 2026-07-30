<template>
  <div :class="['access-page', 'dr-page', { 'audit-route': isAuditRoute }]">
    <header class="dr-page-header">
      <div class="access-heading">
        <span class="access-kicker">{{ accessPageKicker }}</span>
        <h1>{{ accessPageTitle }}</h1>
        <p>{{ accessPageDescription }}</p>
      </div>
      <div class="dr-toolbar">
        <n-button secondary :loading="auditLoading" :disabled="auditLoading" @click="fetchAudit">刷新审计</n-button>
        <n-button v-if="!isAuditRoute" secondary @click="router.push({ name: 'AuditLogs' })">查看审计日志</n-button>
        <n-button v-else secondary @click="router.push({ name: 'AccessControl' })">返回权限管理</n-button>
        <n-button v-if="!isAuditRoute" type="primary" :disabled="userPanelBusy" @click="showCreateUser = true">新增用户</n-button>
      </div>
    </header>

    <section class="access-summary-strip" aria-label="权限状态概览">
      <article class="summary-item">
        <span>用户</span>
        <strong>{{ roleUsers.length }}</strong>
        <small>启用 {{ activeUserCount }} 个账号</small>
      </article>
      <article class="summary-item">
        <span>角色策略</span>
        <strong>{{ rolePolicies.length }}</strong>
        <small>admin / operator / viewer</small>
      </article>
      <article class="summary-item">
        <span>最近审计</span>
        <strong>{{ auditLogs.length }}</strong>
        <small>最近 {{ auditLimit }} 条</small>
      </article>
      <article class="summary-item">
        <span>异常结果</span>
        <strong>{{ failedAuditCount }}</strong>
        <small>失败或需要复核</small>
      </article>
      <article class="summary-item summary-rule">
        <span>危险动作</span>
        <strong>确认门</strong>
        <small>写入与高危工具必须二次确认</small>
      </article>
    </section>

    <section class="access-risk-strip" aria-label="权限风险态势">
      <article :class="['risk-card', riskTone]">
        <span class="risk-kicker">Access posture</span>
        <strong>{{ riskTitle }}</strong>
        <small>{{ riskDetail }}</small>
      </article>
      <article class="risk-card">
        <span class="risk-kicker">Audit coverage</span>
        <strong>{{ auditCoverageTitle }}</strong>
        <small>{{ auditCoverageDetail }}</small>
      </article>
      <article class="risk-card">
        <span class="risk-kicker">Policy boundary</span>
        <strong>{{ selectedPolicy.role }} role</strong>
        <small>{{ selectedPolicy.permissions.join(' / ') }}</small>
      </article>
    </section>

    <section v-if="isAuditRoute" class="audit-focus-strip" aria-label="审计筛查状态">
      <article class="audit-focus-card">
        <span>Filtered window</span>
        <strong>{{ auditWindowTitle }}</strong>
        <small>{{ auditWindowDetail }}</small>
      </article>
      <article :class="['audit-focus-card', failedAuditCount > 0 ? 'danger' : 'ready']">
        <span>Failure focus</span>
        <strong>{{ auditFailureTitle }}</strong>
        <small>{{ auditFailureDetail }}</small>
      </article>
      <article class="audit-focus-card">
        <span>Privileged actions</span>
        <strong>{{ highRiskAuditCount }}</strong>
        <small>{{ auditHighRiskDetail }}</small>
      </article>
    </section>

    <div class="dr-two-column access-workspace">
      <section class="dr-panel">
        <div class="dr-panel-head">
          <div>
            <h2 class="dr-panel-title">用户和角色</h2>
            <span class="dr-panel-subtitle">调整账号启停和角色归属，保存后立即生效。</span>
          </div>
          <n-button secondary :loading="usersLoading" :disabled="userPanelBusy" @click="fetchUsers">刷新用户</n-button>
        </div>
        <div class="search-row">
          <n-input v-model:value="userSearch" clearable placeholder="搜索用户名或角色" />
        </div>
        <div v-if="showCreateUser" class="create-user-form">
          <n-form :show-label="false">
            <div class="create-grid">
              <n-form-item>
                <n-input v-model:value="newUser.username" :disabled="userPanelBusy" placeholder="用户名" />
              </n-form-item>
              <n-form-item>
                <n-input v-model:value="newUser.display_name" :disabled="userPanelBusy" placeholder="显示名" />
              </n-form-item>
              <n-form-item>
                <n-input v-model:value="newUser.password" type="password" show-password-on="click" :disabled="userPanelBusy" placeholder="初始密码" />
              </n-form-item>
              <n-form-item>
                <n-select v-model:value="newUser.role" :options="roleOptions" :disabled="userPanelBusy" />
              </n-form-item>
              <div class="create-actions">
                <n-popconfirm
                  positive-text="创建"
                  negative-text="取消"
                  :positive-button-props="{ type: 'primary', size: 'small', disabled: userPanelBusy }"
                  :negative-button-props="{ size: 'small' }"
                  @positive-click="createUser"
                >
                  <template #trigger>
                    <n-button type="primary" :loading="createLoading" :disabled="userPanelBusy">创建</n-button>
                  </template>
                  创建用户「{{ newUser.username.trim() || '未命名用户' }}」并授予 {{ newUser.role }} 角色？
                </n-popconfirm>
                <n-button secondary :disabled="createLoading" @click="resetCreateForm">取消</n-button>
              </div>
            </div>
          </n-form>
        </div>
        <div class="role-list">
          <div class="role-row role-row-head" aria-hidden="true">
            <span>用户</span>
            <span>角色</span>
            <span>状态</span>
            <span>更新时间</span>
            <span>操作</span>
          </div>
          <article v-for="user in filteredUsers" :key="user.username" class="role-row">
            <div class="user-cell">
              <span class="avatar">{{ user.username.slice(0, 1).toUpperCase() }}</span>
              <span>
                <strong>{{ user.username }}</strong>
                <small>{{ user.display_name || '未设置显示名' }}</small>
              </span>
            </div>
            <n-select v-model:value="user.role" :options="roleOptions" size="small" :disabled="userPanelBusy" />
            <n-switch v-model:value="user.is_active" size="small" :disabled="userPanelBusy">
              <template #checked>启用</template>
              <template #unchecked>停用</template>
            </n-switch>
            <span class="dr-muted">{{ formatTime(user.updated_at) }}</span>
            <n-popconfirm
              positive-text="保存"
              negative-text="取消"
              :positive-button-props="{ type: 'warning', size: 'small', disabled: userPanelBusy }"
              :negative-button-props="{ size: 'small' }"
              @positive-click="saveUser(user)"
            >
              <template #trigger>
                <n-button size="small" :loading="savingUser === user.username" :disabled="userPanelBusy">保存</n-button>
              </template>
              保存用户「{{ user.username }}」的角色和状态？保存后立即生效。
            </n-popconfirm>
          </article>
          <div v-if="!filteredUsers.length" class="dr-empty compact-empty">没有匹配的用户</div>
        </div>
      </section>

      <aside class="detail-stack">
        <section class="dr-panel">
          <div class="dr-panel-head">
            <div>
              <h2 class="dr-panel-title">角色策略</h2>
              <span class="dr-panel-subtitle">按角色查看工具边界，策略编辑待接口开放。</span>
            </div>
          </div>
          <div class="policy-form">
            <label class="field">
              <span>选择角色</span>
              <n-select v-model:value="selectedRole" :options="roleOptions" />
            </label>
            <label class="field">
              <span>工具权限</span>
              <span class="permission-chip-list">
                <span v-for="permission in selectedPolicy.permissions" :key="permission" class="permission-chip">
                  {{ permission }}
                </span>
              </span>
            </label>
            <p>{{ selectedPolicy.description }}</p>
            <n-button secondary disabled>策略编辑待开放</n-button>
          </div>
        </section>

        <section class="dr-panel">
          <div class="dr-panel-head">
            <div>
              <h2 class="dr-panel-title">最近审计</h2>
              <span class="dr-panel-subtitle">最近访问、配置和工具调用记录。</span>
            </div>
          </div>
          <div class="audit-list">
            <article v-for="log in recentAuditLogs" :key="log.id" class="audit-item">
              <span class="audit-dot" :class="auditResultClass(log.result)" />
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
          <span class="dr-panel-subtitle">按操作人、动作、资源和结果筛选完整记录。</span>
        </div>
      </div>
      <div class="audit-filter-bar">
        <label class="field compact">
          <span>操作人</span>
          <n-input
            v-model:value="auditFilters.actor"
            clearable
            :disabled="auditLoading"
            placeholder="admin / scheduler"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>操作</span>
          <n-input
            v-model:value="auditFilters.action"
            clearable
            :disabled="auditLoading"
            placeholder="api.get / tool"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>资源</span>
          <n-input
            v-model:value="auditFilters.resource"
            clearable
            :disabled="auditLoading"
            placeholder="/chat / aliyun"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>资源 ID</span>
          <n-input
            v-model:value="auditFilters.resource_id"
            clearable
            :disabled="auditLoading"
            placeholder="实例 / 会话 / 任务"
            @keyup.enter="applyAuditFilters"
          />
        </label>
        <label class="field compact">
          <span>结果</span>
          <n-select
            v-model:value="auditFilters.result"
            clearable
            :disabled="auditLoading"
            placeholder="全部"
            :options="resultOptions"
          />
        </label>
        <div class="filter-actions">
          <n-button type="primary" :loading="auditLoading" :disabled="auditLoading" @click="applyAuditFilters">应用</n-button>
          <n-button secondary :disabled="auditLoading" @click="clearAuditFilters">清空</n-button>
        </div>
      </div>
      <n-data-table :columns="auditColumns" :data="auditLogs" :loading="auditLoading" size="small" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NDataTable, NForm, NFormItem, NInput, NPopconfirm, NSelect, NSwitch, NTag, useMessage } from 'naive-ui'
import { systemApi, userApi } from '@/api/client'
import type { AuditLog, User } from '@/types'

const auditLimit = 50
const message = useMessage()
const route = useRoute()
const router = useRouter()
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
  { role: 'admin', permissions: ['全部工具', '配置写入', '审计管理', '高危确认'], description: '管理员拥有配置、审计、工具执行和高危确认权限。' },
  { role: 'operator', permissions: ['k8s-*', 'ecs-describe-*', 'toolsearch', '调度执行'], description: '值班角色可执行常规巡检与调度动作，高危写入仍需要确认。' },
  { role: 'viewer', permissions: ['Dashboard', '历史会话', '只读上下文'], description: '观察者只查看聚合状态、历史会话和只读上下文。' },
] as const

const roleOptions = rolePolicies.map((item) => ({ label: item.role, value: item.role }))
const resultOptions = [
  { label: 'success', value: 'success' },
  { label: 'failure', value: 'failure' },
]
const isAuditRoute = computed(() => route.name === 'AuditLogs')
const accessPageKicker = computed(() => isAuditRoute.value ? 'Audit Trail' : 'Access Control')
const accessPageTitle = computed(() => isAuditRoute.value ? '审计日志' : '权限管理')
const accessPageDescription = computed(() =>
  isAuditRoute.value
    ? '筛选访问、配置和工具调用记录，快速定位失败、高危和需要复核的动作。'
    : '配置用户角色、工具访问范围和审计追踪，保障运维动作边界清晰。',
)
const selectedPolicy = computed(() => rolePolicies.find((item) => item.role === selectedRole.value) || rolePolicies[1])
const activeUserCount = computed(() => roleUsers.value.filter((user) => user.is_active).length)
const failedAuditCount = computed(() => auditLogs.value.filter((log) => log.result !== 'success').length)
const inactiveUserCount = computed(() => roleUsers.value.length - activeUserCount.value)
const adminUserCount = computed(() => roleUsers.value.filter((user) => user.role === 'admin' && user.is_active).length)
const highRiskAuditCount = computed(() => auditLogs.value.filter((log) => /tool|confirm|delete|patch|post/i.test(log.action)).length)
const userPanelBusy = computed(() => usersLoading.value || createLoading.value || Boolean(savingUser.value))
const riskTone = computed(() => {
  if (failedAuditCount.value > 0) return 'danger'
  if (adminUserCount.value > 1 || inactiveUserCount.value > 0) return 'watch'
  return 'ready'
})
const riskTitle = computed(() => {
  if (failedAuditCount.value > 0) return `${failedAuditCount.value} audit exception${failedAuditCount.value > 1 ? 's' : ''}`
  if (adminUserCount.value > 1) return `${adminUserCount.value} active admins`
  return 'Boundary is clear'
})
const riskDetail = computed(() => {
  if (failedAuditCount.value > 0) return 'Review failed or denied audit results before allowing more privileged operations.'
  if (inactiveUserCount.value > 0) return `${inactiveUserCount.value} inactive account${inactiveUserCount.value > 1 ? 's' : ''} retained for review.`
  return `${activeUserCount.value} active user${activeUserCount.value > 1 ? 's' : ''}; dangerous tools stay behind confirmation gates.`
})
const auditCoverageTitle = computed(() => `${auditLogs.value.length}/${auditLimit} events loaded`)
const auditCoverageDetail = computed(() => {
  if (!auditLogs.value.length) return 'No audit events loaded yet; refresh audit before changing roles.'
  return `${highRiskAuditCount.value} privileged or tool-related events in the current audit window.`
})
const activeAuditFilterCount = computed(() => {
  const fields = auditFilters.value
  return [fields.actor, fields.action, fields.resource, fields.resource_id, fields.result].filter(Boolean).length
})
const auditWindowTitle = computed(() => `${auditLogs.value.length}/${auditLimit} events`)
const auditWindowDetail = computed(() => {
  if (activeAuditFilterCount.value > 0) return `${activeAuditFilterCount.value} active filter${activeAuditFilterCount.value > 1 ? 's' : ''} applied to the audit query.`
  return 'Unfiltered audit window; apply actor, action, resource, or result filters to narrow evidence.'
})
const auditFailureTitle = computed(() => failedAuditCount.value > 0 ? `${failedAuditCount.value} exception${failedAuditCount.value > 1 ? 's' : ''}` : 'No failures')
const auditFailureDetail = computed(() => {
  if (!auditLogs.value.length) return 'Load audit events to confirm failure posture.'
  if (failedAuditCount.value > 0) return 'Review failed or denied events before granting additional access.'
  return 'Current audit window contains only successful events.'
})
const auditHighRiskDetail = computed(() => {
  if (!highRiskAuditCount.value) return 'No delete, patch, post, confirm, or tool actions in the current window.'
  return 'Tool, confirm, delete, patch, and post actions are highlighted for privileged review.'
})
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
    render: (row: AuditLog) => h(NTag, { size: 'small', type: row.result === 'success' ? 'success' : 'error' }, { default: () => row.result }),
  },
  { title: 'IP', key: 'ip', width: 140 },
]

async function fetchAudit() {
  if (auditLoading.value) return
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
  if (usersLoading.value) return
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
  if (userPanelBusy.value) return
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
  if (userPanelBusy.value) return
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

function auditResultClass(result: string) {
  return result === 'success' ? 'success' : 'danger'
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
.access-heading {
  min-width: 0;
}

.access-kicker {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  margin-bottom: 7px;
  padding: 0 8px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 999px;
  background: #ffffff;
  color: var(--dr-blue);
  font-size: var(--dr-text-xs);
  font-weight: 650;
}

.access-summary-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.summary-item {
  min-width: 0;
  min-height: 72px;
  padding: 11px 12px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #ffffff;
  box-shadow: none;
}

.summary-item span {
  display: block;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  font-weight: 590;
}

.summary-item strong {
  display: block;
  margin-top: 6px;
  color: var(--dr-text);
  font-size: 18px;
  font-weight: 620;
  line-height: 1.05;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.summary-item small {
  display: block;
  margin-top: 7px;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-sm);
  line-height: 1.35;
}

.summary-rule {
  border-color: var(--dr-border);
  background: #fbfcfe;
}

.summary-rule strong {
  color: var(--dr-text);
}

.access-risk-strip {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1.3fr;
  gap: 10px;
}

.audit-focus-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.audit-focus-card {
  min-width: 0;
  min-height: 92px;
  padding: 13px 14px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #ffffff;
}

.audit-focus-card.ready {
  border-color: #b8e3d1;
  background: #f0fdf4;
}

.audit-focus-card.danger {
  border-color: #f2b8b5;
  background: #fff5f5;
}

.audit-focus-card span {
  display: block;
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 750;
  text-transform: uppercase;
}

.audit-focus-card strong {
  display: block;
  margin-top: 8px;
  overflow: hidden;
  color: var(--dr-text);
  font-size: 17px;
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audit-focus-card small {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.risk-card {
  min-width: 0;
  min-height: 96px;
  padding: 13px 14px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #ffffff;
}

.risk-card.ready {
  border-color: #b8e3d1;
  background: #f0fdf4;
}

.risk-card.watch {
  border-color: #f3d89b;
  background: #fffbeb;
}

.risk-card.danger {
  border-color: #f2b8b5;
  background: #fff5f5;
}

.risk-kicker {
  display: block;
  color: var(--dr-text-muted);
  font-size: 11px;
  font-weight: 750;
  text-transform: uppercase;
}

.risk-card strong {
  display: block;
  margin-top: 8px;
  overflow: hidden;
  color: var(--dr-text);
  font-size: 17px;
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-card small {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.access-workspace {
  grid-template-columns: minmax(0, 1.55fr) minmax(300px, 0.72fr);
  gap: 14px;
}

.audit-route .audit-focus-strip {
  order: 3;
}

.audit-route .dr-table-panel {
  order: 4;
}

.audit-route .access-workspace {
  order: 5;
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

.role-row-head {
  min-height: 36px;
  padding-top: 8px;
  padding-bottom: 8px;
  background: #fbfcfe;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
  font-weight: 650;
}

.role-row:last-child {
  border-bottom: 0;
}

.role-row:hover:not(.role-row-head) {
  background: #f6f8fb;
}

.role-row-head:hover {
  background: #fbfcfe;
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

.user-cell .avatar {
  width: 28px;
  height: 28px;
  border: 1px solid var(--dr-border-soft);
  background: var(--dr-accent-wash);
  color: var(--dr-accent-deep);
  box-shadow: none;
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
  padding: 14px 16px 16px;
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

.permission-chip-list {
  display: flex;
  min-width: 0;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-chip {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 8px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 999px;
  background: var(--dr-bg-page);
  color: var(--dr-text-soft);
  font-size: var(--dr-text-xs);
  font-weight: 610;
}

.policy-form .n-button {
  align-self: flex-start;
}

.audit-list {
  display: flex;
  flex-direction: column;
  min-height: 122px;
  padding: 4px 0 8px;
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
  padding: 8px 16px;
}

.audit-dot {
  width: 7px;
  height: 7px;
  margin-top: 7px;
  border-radius: 50%;
  background: var(--dr-accent);
  box-shadow: 0 0 0 4px rgba(47, 111, 237, 0.1);
}

.audit-dot.success {
  background: var(--dr-green);
  box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.1);
}

.audit-dot.danger {
  background: var(--dr-red);
  box-shadow: 0 0 0 4px rgba(180, 35, 24, 0.1);
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
  line-height: 1.38;
  overflow-wrap: anywhere;
}

.compact-empty {
  min-height: 96px;
}

@media (max-width: 1240px) {
  .access-summary-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .access-summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .access-risk-strip {
    grid-template-columns: 1fr;
  }

  .audit-focus-strip {
    grid-template-columns: 1fr;
  }

  .role-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .role-row-head {
    display: none;
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

@media (max-width: 620px) {
  .access-summary-strip {
    grid-template-columns: 1fr;
  }
}
</style>
