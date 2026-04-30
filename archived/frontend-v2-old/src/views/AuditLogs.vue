<template>
  <div class="audit-log-page ops-management-page">
    <header class="page-header ops-page-hero">
      <div>
        <p class="eyebrow">OPERATION AUDIT</p>
        <h1>操作日志</h1>
        <span>登录、用户变更、接口访问和关键操作统一留痕。</span>
      </div>
      <el-button type="primary" :loading="loading" @click="loadLogs">刷新</el-button>
    </header>

    <el-card class="panel-card filter-card">
      <el-form class="filters-form" label-position="top">
        <el-form-item label="操作者">
          <el-input v-model="filters.actor" clearable placeholder="admin" />
        </el-form-item>
        <el-form-item label="动作">
          <el-input v-model="filters.action" clearable placeholder="auth.login / users" />
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="filters.result" clearable placeholder="全部">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failure" />
          </el-select>
        </el-form-item>
        <el-form-item label="条数">
          <el-select v-model="filters.limit">
            <el-option label="50" :value="50" />
            <el-option label="100" :value="100" />
            <el-option label="200" :value="200" />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-action">
          <el-button type="primary" :loading="loading" @click="loadLogs">应用筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card logs-card">
      <template #header>
        <div class="panel-title">最近 {{ logs.length }} 条事件</div>
      </template>
      <el-table :data="logs" v-loading="loading">
        <el-table-column label="时间" min-width="170">
          <template #default="{ row }">
            <span class="muted">{{ formatTime(row.timestamp) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="actor" label="操作者" min-width="120" />
        <el-table-column prop="action" label="动作" min-width="140" />
        <el-table-column prop="resource" label="资源" min-width="110" />
        <el-table-column label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.result === 'success' ? 'success' : 'danger'">
              {{ row.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="220" />
        <el-table-column label="详情" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="selectedLog = row">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="selectedLog" class="panel-card detail-card">
      <template #header>
        <div class="panel-title">事件详情</div>
      </template>
      <pre>{{ JSON.stringify(selectedLog, null, 2) }}</pre>
      <el-button @click="selectedLog = null">收起</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '@/api/client'

const loading = ref(false)
const logs = ref([])
const selectedLog = ref(null)
const filters = reactive({
  actor: '',
  action: '',
  result: '',
  limit: 100
})

const loadLogs = async () => {
  loading.value = true
  try {
    const { data } = await api.audit.logs({
      limit: filters.limit,
      actor: filters.actor || undefined,
      action: filters.action || undefined,
      result: filters.result || undefined
    })
    logs.value = data.items || []
  } finally {
    loading.value = false
  }
}

const formatTime = (value) => {
  if (!value) return '-'
  return new Date(value * 1000).toLocaleString()
}

onMounted(loadLogs)
</script>

<style scoped>
.filter-card,
.logs-card,
.detail-card {
  margin-top: 18px;
}

.filters-form {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  align-items: end;
}

.filter-action {
  margin-bottom: 18px;
}

.muted {
  color: #8fa0b8;
}

pre {
  max-height: 360px;
  overflow: auto;
  margin: 0 0 16px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 8px;
  background: #080f1c;
  color: #b9c6d9;
}

@media (max-width: 980px) {
  .filters-form {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 620px) {
  .filters-form {
    grid-template-columns: 1fr;
  }
}
</style>
