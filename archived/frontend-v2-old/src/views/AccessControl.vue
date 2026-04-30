<template>
  <div class="access-control-page ops-management-page">
    <header class="page-header ops-page-hero">
      <div>
        <p class="eyebrow">IDENTITY & ACCESS</p>
        <h1>访问控制</h1>
        <span>本地用户、角色权限和会话身份统一管理。</span>
      </div>
      <el-button type="primary" :loading="loading" @click="loadData">刷新</el-button>
    </header>

    <section class="metrics-grid">
      <div class="metric-card">
        <span>用户</span>
        <strong>{{ users.length }}</strong>
      </div>
      <div class="metric-card">
        <span>启用</span>
        <strong>{{ enabledUsers }}</strong>
      </div>
      <div class="metric-card">
        <span>角色</span>
        <strong>{{ roles.length }}</strong>
      </div>
      <div class="metric-card">
        <span>权限</span>
        <strong>{{ permissionCount }}</strong>
      </div>
    </section>

    <section class="iam-layout">
      <el-card class="panel-card">
        <template #header>
          <div class="panel-title">角色矩阵</div>
        </template>
        <div class="role-stack">
          <article v-for="role in roles" :key="role.id" class="role-card">
            <div class="role-topline">
              <strong>{{ role.name }}</strong>
              <el-tag>{{ role.id }}</el-tag>
            </div>
            <p>{{ role.description }}</p>
            <div class="permission-cloud">
              <el-tag
                v-for="permission in role.permissions"
                :key="permission"
                effect="plain"
              >
                {{ permission }}
              </el-tag>
            </div>
          </article>
        </div>
      </el-card>

      <el-card v-if="canWriteUsers" class="panel-card">
        <template #header>
          <div class="panel-title">新增用户</div>
        </template>
        <el-form class="create-form" label-position="top" @submit.prevent="createUser">
          <el-form-item label="用户名">
            <el-input v-model="createForm.username" placeholder="ops-user" />
          </el-form-item>
          <el-form-item label="显示名称">
            <el-input v-model="createForm.display_name" placeholder="运维同学" />
          </el-form-item>
          <el-form-item label="初始密码">
            <el-input v-model="createForm.password" type="password" show-password />
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="createForm.roles" multiple placeholder="选择角色">
              <el-option
                v-for="role in roles"
                :key="role.id"
                :label="role.name"
                :value="role.id"
              />
            </el-select>
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="createUser">创建用户</el-button>
        </el-form>
      </el-card>
    </section>

    <el-card class="panel-card user-table-card">
      <template #header>
        <div class="panel-title">用户清单</div>
      </template>
      <el-table :data="users" v-loading="loading">
        <el-table-column label="用户" min-width="180">
          <template #default="{ row }">
            <div class="user-cell">
              <strong>{{ row.display_name }}</strong>
              <span>{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="180">
          <template #default="{ row }">
            <div class="tag-row">
              <el-tag v-for="role in row.roles" :key="role">{{ role }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="220">
          <template #default="{ row }">
            <span class="muted">{{ summarizePermissions(row.permissions) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="最近登录" min-width="180">
          <template #default="{ row }">
            <span class="muted">{{ formatDate(row.last_login_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="canWriteUsers" label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="selectUser(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.id === authStore.user?.id || row.id === 'usr_admin' || !row.enabled"
              @click="disableUser(row)"
            >
              停用
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="canWriteUsers && selectedUser" class="panel-card editor-card">
      <template #header>
        <div class="panel-title">编辑 {{ selectedUser.username }}</div>
      </template>
      <el-form class="create-form" label-position="top" @submit.prevent="saveUser">
        <el-form-item label="显示名称">
          <el-input v-model="editForm.display_name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.roles" multiple>
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="重置密码">
          <el-input v-model="editForm.password" type="password" show-password placeholder="留空则不修改" />
        </el-form-item>
        <div class="form-actions">
          <el-button @click="selectedUser = null">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const users = ref([])
const roles = ref([])
const permissions = ref({})
const selectedUser = ref(null)

const createForm = reactive({
  username: '',
  display_name: '',
  password: '',
  roles: ['viewer']
})

const editForm = reactive({
  display_name: '',
  password: '',
  roles: []
})

const enabledUsers = computed(() => users.value.filter((user) => user.enabled).length)
const permissionCount = computed(() => Object.keys(permissions.value).length)
const canWriteUsers = computed(() => authStore.hasPermission('users:write'))

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await api.users.list()
    users.value = data.users || []
    roles.value = data.roles || []
    permissions.value = data.permissions || {}
  } finally {
    loading.value = false
  }
}

const resetCreateForm = () => {
  createForm.username = ''
  createForm.display_name = ''
  createForm.password = ''
  createForm.roles = ['viewer']
}

const createUser = async () => {
  if (!canWriteUsers.value) {
    ElMessage.warning('当前账号没有用户写入权限')
    return
  }
  if (!createForm.username || !createForm.display_name || !createForm.password) {
    ElMessage.warning('请补全用户信息')
    return
  }
  saving.value = true
  try {
    await api.users.create({
      username: createForm.username,
      display_name: createForm.display_name,
      password: createForm.password,
      roles: createForm.roles,
      enabled: true
    })
    ElMessage.success('用户已创建')
    resetCreateForm()
    await loadData()
  } finally {
    saving.value = false
  }
}

const selectUser = (user) => {
  if (!canWriteUsers.value) return
  selectedUser.value = user
  editForm.display_name = user.display_name
  editForm.password = ''
  editForm.roles = [...user.roles]
}

const saveUser = async () => {
  if (!selectedUser.value) return
  if (!canWriteUsers.value) {
    ElMessage.warning('当前账号没有用户写入权限')
    return
  }
  saving.value = true
  try {
    const payload = {
      display_name: editForm.display_name,
      roles: editForm.roles
    }
    if (editForm.password) {
      payload.password = editForm.password
    }
    await api.users.update(selectedUser.value.id, payload)
    ElMessage.success('用户已更新')
    selectedUser.value = null
    await loadData()
  } finally {
    saving.value = false
  }
}

const disableUser = async (user) => {
  if (!canWriteUsers.value) {
    ElMessage.warning('当前账号没有用户写入权限')
    return
  }
  await ElMessageBox.confirm(`确定停用用户 ${user.username} 吗？`, '停用确认', {
    confirmButtonText: '停用',
    cancelButtonText: '取消',
    type: 'warning'
  })
  await api.users.disable(user.id)
  ElMessage.success('用户已停用')
  await loadData()
}

const summarizePermissions = (items = []) => {
  if (items.includes('*')) return '全部权限'
  if (!items.length) return '无权限'
  return items.slice(0, 4).join(' / ') + (items.length > 4 ? ` +${items.length - 4}` : '')
}

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

onMounted(loadData)
</script>

<style scoped>
.iam-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 18px;
  margin-top: 18px;
}

.role-stack {
  display: grid;
  gap: 12px;
}

.role-card {
  padding: 16px;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

.role-topline,
.form-actions,
.tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-topline {
  justify-content: space-between;
}

.role-card p,
.muted,
.user-cell span {
  color: var(--ops-muted);
}

.role-topline strong,
.user-cell strong {
  color: var(--ops-text);
}

.role-card p {
  margin: 8px 0 12px;
}

.permission-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.create-form {
  display: grid;
  gap: 2px;
}

.user-table-card,
.editor-card {
  margin-top: 18px;
}

.user-cell {
  display: grid;
  gap: 4px;
}

@media (max-width: 980px) {
  .iam-layout {
    grid-template-columns: 1fr;
  }
}
</style>
