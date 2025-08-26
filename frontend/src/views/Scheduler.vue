<template>
  <div class="scheduler-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">任务调度管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog" :icon="Plus">
          新建任务
        </el-button>
        <el-button @click="refreshData" :loading="loading" :icon="Refresh">
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-4 mb-20">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">总任务数</h3>
          <span class="badge">{{ stats.total_tasks || 0 }}</span>
        </div>
        <div class="metric-value">
          <span class="number">{{ stats.total_tasks || 0 }}</span>
          <span class="unit">个任务</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">启用任务</h3>
          <span class="badge success">{{ stats.enabled_tasks || 0 }}</span>
        </div>
        <div class="metric-value">
          <span class="number">{{ stats.enabled_tasks || 0 }}</span>
          <span class="unit">个启用</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">运行中</h3>
          <span class="badge warning">{{ stats.running_tasks || 0 }}</span>
        </div>
        <div class="metric-value">
          <span class="number">{{ stats.running_tasks || 0 }}</span>
          <span class="unit">个运行</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">成功率</h3>
          <span class="badge info">{{ formatPercent(stats.success_rate) }}</span>
        </div>
        <div class="metric-value">
          <span class="number">{{ formatPercent(stats.success_rate) }}</span>
          <span class="unit">成功率</span>
        </div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="scheduler-tabs">
      <!-- 任务列表 -->
      <el-tab-pane label="任务列表" name="tasks">
        <div class="tab-content">
          <!-- 过滤器 -->
          <div class="filters mb-16">
            <el-row :gutter="16">
              <el-col :span="6">
                <el-select v-model="filters.task_type" placeholder="任务类型" clearable @change="loadTasks">
                  <el-option label="全部类型" value="" />
                  <el-option label="集群巡检" value="cluster_check" />
                  <el-option label="资源分析" value="resource_analysis" />
                  <el-option label="健康监控" value="health_monitor" />
                  <el-option label="自定义任务" value="custom" />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-select v-model="filters.enabled_only" placeholder="状态筛选" clearable @change="loadTasks">
                  <el-option label="全部状态" :value="false" />
                  <el-option label="仅启用" :value="true" />
                </el-select>
              </el-col>
              <el-col :span="12">
                <div class="filter-actions">
                  <el-button @click="resetFilters">重置筛选</el-button>
                  <el-button type="primary" @click="loadTasks">应用筛选</el-button>
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- 任务表格 -->
          <el-table 
            :data="tasks" 
            v-loading="loading"
            style="width: 100%"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="任务名称" min-width="200">
              <template #default="scope">
                <div class="task-name">
                  <span class="name">{{ scope.row.name }}</span>
                  <span class="description">{{ scope.row.description }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="task_type" label="类型" width="120">
              <template #default="scope">
                <el-tag :type="getTaskTypeColor(scope.row.task_type)">
                  {{ formatTaskType(scope.row.task_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cron_expression" label="执行计划" width="150">
              <template #default="scope">
                <el-tooltip :content="formatCronExpression(scope.row.cron_expression)" placement="top">
                  <code class="cron-expression">{{ scope.row.cron_expression }}</code>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="状态" width="80">
              <template #default="scope">
                <el-switch
                  v-model="scope.row.enabled"
                  @change="toggleTask(scope.row)"
                  :loading="scope.row.updating"
                />
              </template>
            </el-table-column>
            <el-table-column prop="next_run_time" label="下次执行" width="160">
              <template #default="scope">
                <span v-if="scope.row.next_run_time" class="next-run-time">
                  {{ formatDateTime(scope.row.next_run_time) }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="last_run_time" label="最后执行" width="160">
              <template #default="scope">
                <span v-if="scope.row.last_run_time" class="last-run-time">
                  {{ formatDateTime(scope.row.last_run_time) }}
                </span>
                <span v-else class="text-muted">从未执行</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button-group>
                  <el-button size="small" @click="runTask(scope.row)" :loading="scope.row.running">
                    执行
                  </el-button>
                  <el-button size="small" @click="editTask(scope.row)">
                    编辑
                  </el-button>
                  <el-button size="small" @click="viewExecutions(scope.row)">
                    历史
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteTask(scope.row)">
                    删除
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>

          <!-- 批量操作 -->
          <div v-if="selectedTasks.length > 0" class="batch-actions">
            <el-alert
              :title="`已选择 ${selectedTasks.length} 个任务`"
              type="info"
              :closable="false"
            >
              <template #default>
                <div class="batch-buttons">
                  <el-button size="small" @click="batchEnable">批量启用</el-button>
                  <el-button size="small" @click="batchDisable">批量禁用</el-button>
                  <el-button size="small" @click="batchRun">批量执行</el-button>
                  <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
                </div>
              </template>
            </el-alert>
          </div>
        </div>
      </el-tab-pane>

      <!-- 执行历史 -->
      <el-tab-pane label="执行历史" name="executions">
        <div class="tab-content">
          <div class="executions-header">
            <el-select v-model="executionFilters.task_id" placeholder="选择任务" clearable @change="loadExecutions">
              <el-option label="全部任务" value="" />
              <el-option 
                v-for="task in tasks" 
                :key="task.id" 
                :label="task.name" 
                :value="task.id" 
              />
            </el-select>
            <el-button @click="loadExecutions" :loading="executionsLoading">刷新历史</el-button>
          </div>

          <el-table :data="executions" v-loading="executionsLoading" style="width: 100%">
            <el-table-column prop="task_name" label="任务名称" width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getExecutionStatusColor(scope.row.status)">
                  {{ formatExecutionStatus(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" width="160">
              <template #default="scope">
                {{ formatDateTime(scope.row.started_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="completed_at" label="完成时间" width="160">
              <template #default="scope">
                <span v-if="scope.row.completed_at">
                  {{ formatDateTime(scope.row.completed_at) }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="duration_seconds" label="执行时长" width="120">
              <template #default="scope">
                <span v-if="scope.row.duration_seconds">
                  {{ formatDuration(scope.row.duration_seconds) }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="retry_count" label="重试次数" width="100" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" @click="viewExecutionDetail(scope.row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 执行历史分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="executionPagination.page"
              v-model:page-size="executionPagination.page_size"
              :page-sizes="[10, 20, 50]"
              :total="executionPagination.total"
              layout="total, sizes, prev, pager, next"
              @size-change="handleExecutionSizeChange"
              @current-change="handleExecutionCurrentChange"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 实时监控 -->
      <el-tab-pane label="实时监控" name="monitor">
        <div class="tab-content">
          <div class="monitor-header">
            <h3>调度器状态</h3>
            <el-button @click="loadSchedulerStatus" :loading="statusLoading">刷新状态</el-button>
          </div>

          <div class="grid grid-2">
            <div class="card">
              <div class="card-header">
                <h3 class="card-title">调度器信息</h3>
              </div>
              <div class="status-details">
                <div class="status-item">
                  <span class="label">运行状态:</span>
                  <span :class="['value', schedulerStatus.scheduler?.running ? 'success' : 'error']">
                    {{ schedulerStatus.scheduler?.running ? '运行中' : '已停止' }}
                  </span>
                </div>
                <div class="status-item">
                  <span class="label">任务管理器:</span>
                  <span :class="['value', schedulerStatus.task_manager?.initialized ? 'success' : 'error']">
                    {{ schedulerStatus.task_manager?.initialized ? '已初始化' : '未初始化' }}
                  </span>
                </div>
                <div class="status-item">
                  <span class="label">任务执行器:</span>
                  <span :class="['value', schedulerStatus.task_executor?.initialized ? 'success' : 'error']">
                    {{ schedulerStatus.task_executor?.initialized ? '已初始化' : '未初始化' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h3 class="card-title">运行中任务</h3>
                <span class="badge">{{ Object.keys(runningTasks).length }}</span>
              </div>
              <div class="running-tasks">
                <div v-if="Object.keys(runningTasks).length === 0" class="empty-state">
                  <div class="empty-state-text">暂无运行中的任务</div>
                </div>
                <div v-else>
                  <div 
                    v-for="(task, taskId) in runningTasks" 
                    :key="taskId"
                    class="running-task-item"
                  >
                    <div class="task-info">
                      <div class="task-name">{{ task.name || taskId }}</div>
                      <div class="task-start-time">开始时间: {{ formatDateTime(task.start_time) }}</div>
                    </div>
                    <div class="task-status">
                      <el-tag type="warning">运行中</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog
      v-model="taskDialogVisible"
      :title="isEditing ? '编辑任务' : '创建任务'"
      width="800px"
      @closed="resetTaskForm"
    >
      <TaskConfigForm
        v-if="taskDialogVisible"
        :task="currentTask"
        :is-editing="isEditing"
        @save="handleTaskSave"
        @cancel="taskDialogVisible = false"
      />
    </el-dialog>

    <!-- 执行历史详情对话框 -->
    <el-dialog
      v-model="executionDetailVisible"
      title="执行详情"
      width="600px"
    >
      <div v-if="currentExecution" class="execution-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ currentExecution.task_name }}</el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="getExecutionStatusColor(currentExecution.status)">
              {{ formatExecutionStatus(currentExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(currentExecution.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ currentExecution.completed_at ? formatDateTime(currentExecution.completed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时长">
            {{ currentExecution.duration_seconds ? formatDuration(currentExecution.duration_seconds) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="重试次数">{{ currentExecution.retry_count }}</el-descriptions-item>
          <el-descriptions-item label="是否重试">{{ currentExecution.is_retry ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="通知已发送">{{ currentExecution.notification_sent ? '是' : '否' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { api, schedulerAPI, schedulerApiUtils, SCHEDULER_CONSTANTS } from '@/api/client'
import TaskConfigForm from '@/components/TaskConfigForm.vue'

// 响应式数据
const loading = ref(false)
const statusLoading = ref(false)
const executionsLoading = ref(false)
const activeTab = ref('tasks')

// 统计数据
const stats = ref({
  total_tasks: 0,
  enabled_tasks: 0,
  running_tasks: 0,
  success_rate: 0
})

// 任务列表
const tasks = ref([])
const selectedTasks = ref([])
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 过滤器
const filters = reactive({
  task_type: '',
  enabled_only: false
})

// 执行历史
const executions = ref([])
const executionPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})
const executionFilters = reactive({
  task_id: ''
})

// 调度器状态
const schedulerStatus = ref({})
const runningTasks = ref({})

// 对话框状态
const taskDialogVisible = ref(false)
const executionDetailVisible = ref(false)
const isEditing = ref(false)
const currentTask = ref(null)
const currentExecution = ref(null)

// 定时器
let refreshTimer = null

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadStats(),
      loadTasks(),
      loadSchedulerStatus()
    ])
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await api.scheduler.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const loadTasks = async () => {
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filters
    }
    const response = await api.scheduler.getTasks(params)
    const data = response.data
    
    tasks.value = data.tasks.map(task => ({
      ...task,
      updating: false,
      running: false
    }))
    pagination.total = data.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  }
}

const loadExecutions = async () => {
  executionsLoading.value = true
  try {
    const params = {
      page: executionPagination.page,
      page_size: executionPagination.page_size
    }
    
    let response
    if (executionFilters.task_id) {
      response = await api.scheduler.getTaskExecutions(executionFilters.task_id, params)
    } else {
      // 这里需要一个获取所有执行历史的API，暂时使用空数组
      response = { data: { executions: [], total: 0 } }
    }
    
    const data = response.data
    executions.value = data.executions || []
    executionPagination.total = data.total || 0
  } catch (error) {
    console.error('获取执行历史失败:', error)
    ElMessage.error('获取执行历史失败')
  } finally {
    executionsLoading.value = false
  }
}

const loadSchedulerStatus = async () => {
  statusLoading.value = true
  try {
    const [statusResponse, runningResponse] = await Promise.all([
      api.scheduler.getStatus(),
      api.scheduler.getRunningTasks()
    ])
    
    schedulerStatus.value = statusResponse.data
    runningTasks.value = runningResponse.data.running_tasks || {}
  } catch (error) {
    console.error('获取调度器状态失败:', error)
  } finally {
    statusLoading.value = false
  }
}

// 任务操作
const showCreateDialog = () => {
  isEditing.value = false
  currentTask.value = null
  taskDialogVisible.value = true
}

const editTask = (task) => {
  isEditing.value = true
  currentTask.value = { ...task }
  taskDialogVisible.value = true
}

const toggleTask = async (task) => {
  task.updating = true
  try {
    await api.scheduler.updateTask(task.id, { enabled: task.enabled })
    ElMessage.success(`任务已${task.enabled ? '启用' : '禁用'}`)
    await loadStats() // 更新统计数据
  } catch (error) {
    task.enabled = !task.enabled // 回滚状态
    ElMessage.error(`操作失败: ${error.message}`)
  } finally {
    task.updating = false
  }
}

const runTask = async (task) => {
  task.running = true
  try {
    await api.scheduler.runTask(task.id)
    ElMessage.success('任务已开始执行')
    await loadStats() // 更新统计数据
  } catch (error) {
    ElMessage.error(`执行任务失败: ${error.message}`)
  } finally {
    task.running = false
  }
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.scheduler.deleteTask(task.id)
    ElMessage.success('任务删除成功')
    await loadTasks()
    await loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`删除任务失败: ${error.message}`)
    }
  }
}

const viewExecutions = (task) => {
  executionFilters.task_id = task.id
  activeTab.value = 'executions'
  loadExecutions()
}

const viewExecutionDetail = (execution) => {
  currentExecution.value = execution
  executionDetailVisible.value = true
}

// 批量操作
const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

const batchEnable = async () => {
  const taskIds = selectedTasks.value.map(task => task.id)
  try {
    await schedulerAPI.batchToggle(taskIds, true)
    ElMessage.success('批量启用成功')
    await loadTasks()
    await loadStats()
  } catch (error) {
    ElMessage.error('批量启用失败')
  }
}

const batchDisable = async () => {
  const taskIds = selectedTasks.value.map(task => task.id)
  try {
    await schedulerAPI.batchToggle(taskIds, false)
    ElMessage.success('批量禁用成功')
    await loadTasks()
    await loadStats()
  } catch (error) {
    ElMessage.error('批量禁用失败')
  }
}

const batchRun = async () => {
  const taskIds = selectedTasks.value.map(task => task.id)
  try {
    await schedulerAPI.batchRun(taskIds)
    ElMessage.success('批量执行已开始')
    await loadStats()
  } catch (error) {
    ElMessage.error('批量执行失败')
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个任务吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const taskIds = selectedTasks.value.map(task => task.id)
    await schedulerAPI.batchDelete(taskIds)
    ElMessage.success('批量删除成功')
    await loadTasks()
    await loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  loadTasks()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadTasks()
}

const handleExecutionSizeChange = (size) => {
  executionPagination.page_size = size
  executionPagination.page = 1
  loadExecutions()
}

const handleExecutionCurrentChange = (page) => {
  executionPagination.page = page
  loadExecutions()
}

// 过滤器
const resetFilters = () => {
  filters.task_type = ''
  filters.enabled_only = false
  loadTasks()
}

// 表单处理
const handleTaskSave = async (taskData) => {
  try {
    if (isEditing.value) {
      await api.scheduler.updateTask(currentTask.value.id, taskData)
      ElMessage.success('任务更新成功')
    } else {
      await api.scheduler.createTask(taskData)
      ElMessage.success('任务创建成功')
    }
    
    taskDialogVisible.value = false
    await loadTasks()
    await loadStats()
  } catch (error) {
    ElMessage.error(`保存任务失败: ${error.message}`)
  }
}

const resetTaskForm = () => {
  currentTask.value = null
  isEditing.value = false
}

// 格式化函数
const formatTaskType = (type) => {
  return schedulerApiUtils.formatters.formatTaskType(type)
}

const formatCronExpression = (expression) => {
  return schedulerApiUtils.formatters.formatCronExpression(expression)
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatDuration = (seconds) => {
  return schedulerApiUtils.formatters.formatDuration(seconds)
}

const formatPercent = (value) => {
  if (value === undefined || value === null) return '0%'
  return `${(value * 100).toFixed(1)}%`
}

const formatExecutionStatus = (status) => {
  return schedulerApiUtils.formatters.formatTaskStatus(status).text
}

// 颜色函数
const getTaskTypeColor = (type) => {
  const colorMap = {
    'cluster_check': 'primary',
    'resource_analysis': 'success',
    'health_monitor': 'warning',
    'custom': 'info'
  }
  return colorMap[type] || 'default'
}

const getExecutionStatusColor = (status) => {
  return schedulerApiUtils.formatters.formatTaskStatus(status).color
}

// 生命周期
onMounted(() => {
  refreshData()
  // 每30秒自动刷新
  refreshTimer = setInterval(() => {
    loadStats()
    loadSchedulerStatus()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.scheduler-page {
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.scheduler-tabs {
  margin-top: 16px;
}

.tab-content {
  padding: 16px 0;
}

.filters {
  background: var(--background-base);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-light);
}

.filter-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.task-name {
  display: flex;
  flex-direction: column;
}

.task-name .name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.task-name .description {
  font-size: 12px;
  color: var(--text-secondary);
}

.cron-expression {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  background: var(--background-base);
  padding: 2px 4px;
  border-radius: 4px;
}

.next-run-time,
.last-run-time {
  font-size: 12px;
}

.text-muted {
  color: var(--text-secondary);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.batch-actions {
  margin-top: 16px;
}

.batch-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.executions-header {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.status-details {
  margin-top: 16px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.label {
  color: var(--text-secondary);
}

.value.success {
  color: var(--success-color);
  font-weight: 500;
}

.value.error {
  color: var(--danger-color);
  font-weight: 500;
}

.running-tasks {
  max-height: 300px;
  overflow-y: auto;
}

.running-task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-extra-light);
}

.running-task-item:last-child {
  border-bottom: none;
}

.task-info .task-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.task-info .task-start-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.execution-detail {
  margin-top: 16px;
}

.metric-value {
  margin: 16px 0;
  text-align: center;
}

.number {
  font-size: 32px;
  font-weight: 600;
  color: var(--primary-color);
}

.unit {
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 8px;
}
</style>
