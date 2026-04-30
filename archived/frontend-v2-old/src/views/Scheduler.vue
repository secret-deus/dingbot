<template>
  <div class="scheduler-page scheduler-cockpit">
    <section class="scheduler-command-strip">
      <div class="command-copy">
        <p class="eyebrow">AUTOMATION CONTROL</p>
        <h1>任务调度</h1>
        <span>编排巡检、资源分析和健康监控任务，保持执行链路可追踪、可暂停、可回放。</span>
      </div>

      <div class="command-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建任务</el-button>
        <el-button :icon="Refresh" :loading="loading" @click="refreshData">刷新</el-button>
      </div>
    </section>

    <section class="metric-strip">
      <div class="metric-tile accent">
        <span>Tasks</span>
        <strong>{{ stats.total_tasks || 0 }}</strong>
        <em>已登记任务</em>
      </div>
      <div class="metric-tile">
        <span>Enabled</span>
        <strong>{{ stats.enabled_tasks || 0 }}</strong>
        <em>处于启用状态</em>
      </div>
      <div class="metric-tile warning">
        <span>Running</span>
        <strong>{{ stats.running_tasks || 0 }}</strong>
        <em>正在执行</em>
      </div>
      <div class="metric-tile success">
        <span>Success</span>
        <strong>{{ formatPercent(stats.success_rate) }}</strong>
        <em>最近执行成功率</em>
      </div>
    </section>

    <section class="scheduler-shell">
      <aside class="scheduler-rail">
        <div class="rail-card">
          <p class="eyebrow">VIEW</p>
          <div class="segmented-nav">
            <button :class="{ active: activeTab === 'tasks' }" @click="switchTab('tasks')">
              任务矩阵
            </button>
            <button :class="{ active: activeTab === 'executions' }" @click="switchTab('executions')">
              执行流水
            </button>
            <button :class="{ active: activeTab === 'monitor' }" @click="switchTab('monitor')">
              运行态
            </button>
          </div>
        </div>

        <div class="rail-card">
          <p class="eyebrow">SCHEDULER</p>
          <div class="status-stack">
            <div class="status-line">
              <span>调度器</span>
              <strong :class="schedulerStatus.scheduler?.running ? 'ok' : 'bad'">
                {{ schedulerStatus.scheduler?.running ? '运行中' : '已停止' }}
              </strong>
            </div>
            <div class="status-line">
              <span>任务管理器</span>
              <strong :class="schedulerStatus.task_manager?.initialized ? 'ok' : 'bad'">
                {{ schedulerStatus.task_manager?.initialized ? '已初始化' : '未初始化' }}
              </strong>
            </div>
            <div class="status-line">
              <span>执行器</span>
              <strong :class="schedulerStatus.task_executor?.initialized ? 'ok' : 'bad'">
                {{ schedulerStatus.task_executor?.initialized ? '已初始化' : '未初始化' }}
              </strong>
            </div>
          </div>
        </div>

        <div class="rail-card">
          <p class="eyebrow">RUNNING</p>
          <strong class="rail-number">{{ Object.keys(runningTasks).length }}</strong>
          <span class="rail-hint">当前运行任务</span>
        </div>
      </aside>

      <main class="scheduler-stage">
        <section v-if="activeTab === 'tasks'" class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">TASK MATRIX</p>
              <h2>任务矩阵</h2>
              <span>按任务类型和启用状态筛选，快速执行或查看历史。</span>
            </div>
            <div class="stage-filters">
              <el-select v-model="filters.task_type" placeholder="任务类型" clearable @change="loadTasks">
                <el-option label="全部类型" value="" />
                <el-option label="集群巡检" value="cluster_check" />
                <el-option label="资源分析" value="resource_analysis" />
                <el-option label="健康监控" value="health_monitor" />
                <el-option label="自定义任务" value="custom" />
              </el-select>
              <el-select v-model="filters.enabled_only" placeholder="状态筛选" clearable @change="loadTasks">
                <el-option label="全部状态" :value="false" />
                <el-option label="仅启用" :value="true" />
              </el-select>
              <el-button @click="resetFilters">重置</el-button>
            </div>
          </div>

          <div v-loading="loading" class="task-board">
            <div v-if="tasks.length === 0" class="empty-cockpit">
              <strong>暂无调度任务</strong>
              <span>可以先创建一个集群巡检或资源分析任务。</span>
              <el-button type="primary" :icon="Plus" @click="showCreateDialog">创建任务</el-button>
            </div>

            <article v-for="task in tasks" v-else :key="task.id" class="task-card">
              <div class="task-select">
                <el-checkbox :model-value="isTaskSelected(task)" @change="toggleTaskSelection(task, $event)" />
              </div>
              <div class="task-main">
                <div class="task-title-row">
                  <div>
                    <h3>{{ task.name }}</h3>
                    <p>{{ task.description || '未填写任务说明' }}</p>
                  </div>
                  <div class="task-badges">
                    <el-tag :type="getTaskTypeColor(task.task_type)">
                      {{ formatTaskType(task.task_type) }}
                    </el-tag>
                    <span class="state-pill" :class="{ on: task.enabled }">
                      {{ task.enabled ? 'Enabled' : 'Paused' }}
                    </span>
                  </div>
                </div>

                <div class="task-meta-grid">
                  <div>
                    <span>计划</span>
                    <el-tooltip :content="formatCronExpression(task.cron_expression)" placement="top">
                      <code>{{ task.cron_expression }}</code>
                    </el-tooltip>
                  </div>
                  <div>
                    <span>下次执行</span>
                    <strong>{{ task.next_run_time ? formatDateTime(task.next_run_time) : '-' }}</strong>
                  </div>
                  <div>
                    <span>最后执行</span>
                    <strong>{{ task.last_run_time ? formatDateTime(task.last_run_time) : '从未执行' }}</strong>
                  </div>
                </div>
              </div>

              <div class="task-controls">
                <el-switch v-model="task.enabled" :loading="task.updating" @change="toggleTask(task)" />
                <div class="task-buttons">
                  <el-button size="small" type="primary" plain :loading="task.running" @click="runTask(task)">执行</el-button>
                  <el-button size="small" @click="editTask(task)">编辑</el-button>
                  <el-button size="small" @click="viewExecutions(task)">历史</el-button>
                  <el-button size="small" type="danger" plain @click="deleteTask(task)">删除</el-button>
                </div>
              </div>
            </article>
          </div>

          <div class="stage-footer">
            <div v-if="selectedTasks.length > 0" class="batch-bar">
              <span>已选择 {{ selectedTasks.length }} 个任务</span>
              <el-button size="small" @click="batchEnable">批量启用</el-button>
              <el-button size="small" @click="batchDisable">批量禁用</el-button>
              <el-button size="small" @click="batchRun">批量执行</el-button>
              <el-button size="small" type="danger" plain @click="batchDelete">批量删除</el-button>
            </div>
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </section>

        <section v-else-if="activeTab === 'executions'" class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">EXECUTION STREAM</p>
              <h2>执行流水</h2>
              <span>选择任务后查看执行状态、耗时、重试和详情。</span>
            </div>
            <div class="stage-filters">
              <el-select v-model="executionFilters.task_id" placeholder="选择任务" clearable @change="loadExecutions">
                <el-option label="全部任务" value="" />
                <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
              </el-select>
              <el-button :loading="executionsLoading" @click="loadExecutions">刷新流水</el-button>
            </div>
          </div>

          <div v-loading="executionsLoading" class="execution-stream">
            <div v-if="executions.length === 0" class="empty-cockpit">
              <strong>暂无执行记录</strong>
              <span>从任务矩阵选择一个任务，或执行一次任务后查看流水。</span>
            </div>
            <article v-for="execution in executions" v-else :key="execution.id || execution.started_at" class="execution-row">
              <div class="execution-status" :class="execution.status">
                {{ formatExecutionStatus(execution.status) }}
              </div>
              <div class="execution-main">
                <h3>{{ execution.task_name }}</h3>
                <div class="execution-meta">
                  <span>开始 {{ formatDateTime(execution.started_at) }}</span>
                  <span>完成 {{ execution.completed_at ? formatDateTime(execution.completed_at) : '-' }}</span>
                  <span>耗时 {{ execution.duration_seconds ? formatDuration(execution.duration_seconds) : '-' }}</span>
                  <span>重试 {{ execution.retry_count || 0 }}</span>
                </div>
              </div>
              <el-button size="small" @click="viewExecutionDetail(execution)">详情</el-button>
            </article>
          </div>

          <div class="stage-footer">
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
        </section>

        <section v-else class="stage-panel">
          <div class="stage-head">
            <div>
              <p class="eyebrow">RUNTIME MONITOR</p>
              <h2>调度运行态</h2>
              <span>观察调度器、任务管理器、执行器和正在运行的任务。</span>
            </div>
            <el-button :loading="statusLoading" @click="loadSchedulerStatus">刷新状态</el-button>
          </div>

          <div class="runtime-grid">
            <div class="runtime-card">
              <p class="eyebrow">CORE SERVICES</p>
              <div class="runtime-line">
                <span>Scheduler</span>
                <strong :class="schedulerStatus.scheduler?.running ? 'ok' : 'bad'">
                  {{ schedulerStatus.scheduler?.running ? 'Running' : 'Stopped' }}
                </strong>
              </div>
              <div class="runtime-line">
                <span>Task Manager</span>
                <strong :class="schedulerStatus.task_manager?.initialized ? 'ok' : 'bad'">
                  {{ schedulerStatus.task_manager?.initialized ? 'Ready' : 'Not Ready' }}
                </strong>
              </div>
              <div class="runtime-line">
                <span>Executor</span>
                <strong :class="schedulerStatus.task_executor?.initialized ? 'ok' : 'bad'">
                  {{ schedulerStatus.task_executor?.initialized ? 'Ready' : 'Not Ready' }}
                </strong>
              </div>
            </div>

            <div class="runtime-card">
              <p class="eyebrow">RUNNING TASKS</p>
              <div v-if="Object.keys(runningTasks).length === 0" class="empty-inline">暂无运行中的任务</div>
              <div v-for="(task, taskId) in runningTasks" v-else :key="taskId" class="running-row">
                <div>
                  <strong>{{ task.name || taskId }}</strong>
                  <span>开始 {{ formatDateTime(task.start_time) }}</span>
                </div>
                <span class="state-pill on">Running</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </section>

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

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'executions') {
    loadExecutions()
  }
  if (tab === 'monitor') {
    loadSchedulerStatus()
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

const isTaskSelected = (task) => selectedTasks.value.some((item) => item.id === task.id)

const toggleTaskSelection = (task, checked) => {
  if (checked) {
    if (!isTaskSelected(task)) {
      selectedTasks.value = [...selectedTasks.value, task]
    }
    return
  }
  selectedTasks.value = selectedTasks.value.filter((item) => item.id !== task.id)
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
  min-height: 100%;
  overflow-y: auto;
  color: #e5f3ff;
}

.scheduler-cockpit {
  padding: 24px;
  background: #090a08;
}

.scheduler-command-strip {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 22px 24px;
  border: 1px solid rgba(214, 168, 79, 0.2);
  background: #12140f;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.28);
  border-radius: 10px;
  margin-bottom: 18px;
}

.command-copy h1,
.stage-head h2 {
  margin: 0;
  color: #f8fbff;
  letter-spacing: 0;
}

.command-copy h1 {
  font-size: 30px;
  line-height: 1.15;
}

.command-copy span,
.stage-head span,
.metric-tile em,
.rail-hint,
.empty-cockpit span {
  color: #8ea5b8;
  font-style: normal;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #d6a84f;
}

.command-actions,
.stage-filters,
.task-buttons,
.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.metric-tile,
.rail-card,
.stage-panel,
.runtime-card {
  border: 1px solid rgba(148, 148, 132, 0.16);
  background: #12140f;
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
}

.metric-tile {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.metric-tile span,
.task-meta-grid span,
.status-line span,
.runtime-line span,
.execution-meta,
.running-row span {
  color: #8aa0b2;
  font-size: 12px;
}

.metric-tile strong {
  color: #d6a84f;
  font-size: 30px;
  line-height: 1;
}

.metric-tile.warning strong {
  color: #fbbf24;
}

.metric-tile.success strong {
  color: #8bff9b;
}

.scheduler-shell {
  display: grid;
  grid-template-columns: 270px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.scheduler-rail {
  display: grid;
  gap: 12px;
  position: sticky;
  top: 16px;
}

.rail-card {
  padding: 16px;
}

.segmented-nav {
  display: grid;
  gap: 8px;
}

.segmented-nav button,
.quick-action-button {
  width: 100%;
  border: 1px solid rgba(214, 168, 79, 0.18);
  background: #151712;
  color: #b9c8d8;
  border-radius: 8px;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
}

.segmented-nav button.active {
  color: #031016;
  background: #d6a84f;
  border-color: transparent;
  font-weight: 700;
}

.status-stack {
  display: grid;
  gap: 10px;
}

.status-line,
.runtime-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.ok {
  color: #8bff9b;
}

.bad {
  color: #fb7185;
}

.rail-number {
  display: block;
  color: #d6a84f;
  font-size: 34px;
  line-height: 1;
}

.scheduler-stage {
  min-width: 0;
}

.stage-panel {
  padding: 18px;
  min-height: 560px;
}

.stage-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(148, 148, 132, 0.14);
  margin-bottom: 16px;
}

.stage-head h2 {
  font-size: 22px;
}

.stage-filters {
  justify-content: flex-end;
}

.stage-filters :deep(.el-select) {
  width: 150px;
}

.task-board,
.execution-stream {
  display: grid;
  gap: 12px;
}

.task-card,
.execution-row,
.running-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px;
  border: 1px solid rgba(148, 148, 132, 0.14);
  background: #151712;
  border-radius: 9px;
}

.task-select {
  align-self: start;
  padding-top: 4px;
}

.task-title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.task-title-row h3,
.execution-main h3,
.running-row strong {
  margin: 0 0 4px;
  color: #eef7ff;
  font-size: 15px;
}

.task-title-row p {
  margin: 0;
  color: #8aa0b2;
  font-size: 13px;
}

.task-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.state-pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  color: #9fb2c5;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 148, 132, 0.18);
  font-size: 12px;
  font-weight: 700;
}

.state-pill.on {
  color: #052414;
  background: #8bff9b;
  border-color: transparent;
}

.task-meta-grid {
  display: grid;
  grid-template-columns: 180px repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.task-meta-grid > div {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.task-meta-grid code,
.task-meta-grid strong {
  color: #d9edf7;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-controls {
  display: grid;
  justify-items: end;
  gap: 12px;
  min-width: 260px;
}

.stage-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.batch-bar {
  padding: 8px 10px;
  border: 1px solid rgba(214, 168, 79, 0.2);
  background: rgba(214, 168, 79, 0.08);
  border-radius: 8px;
  color: #c7d8e6;
}

.execution-row {
  grid-template-columns: 118px minmax(0, 1fr) auto;
}

.execution-status {
  border-radius: 8px;
  min-height: 42px;
  display: grid;
  place-items: center;
  background: rgba(214, 168, 79, 0.13);
  color: #e0b45a;
  font-size: 12px;
  font-weight: 800;
}

.execution-status.success,
.execution-status.completed {
  background: rgba(34, 197, 94, 0.14);
  color: #8bff9b;
}

.execution-status.failed,
.execution-status.error {
  background: rgba(244, 63, 94, 0.16);
  color: #fb7185;
}

.execution-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.runtime-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.runtime-card {
  padding: 18px;
  display: grid;
  gap: 14px;
}

.running-row {
  grid-template-columns: minmax(0, 1fr) auto;
  margin-top: 10px;
}

.running-row > div {
  display: grid;
  gap: 4px;
}

.empty-cockpit,
.empty-inline {
  min-height: 220px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  text-align: center;
  color: #c7d8e6;
}

.empty-inline {
  min-height: 120px;
  color: #8aa0b2;
}

.execution-detail {
  margin-top: 16px;
}

.scheduler-cockpit :deep(.el-button) {
  border-radius: 8px;
}

.scheduler-cockpit :deep(.el-input__wrapper),
.scheduler-cockpit :deep(.el-select__wrapper),
.scheduler-cockpit :deep(.el-pagination button),
.scheduler-cockpit :deep(.el-pager li) {
  background: rgba(15, 23, 42, 0.82);
  border-color: rgba(148, 148, 132, 0.18);
  box-shadow: 0 0 0 1px rgba(148, 148, 132, 0.16) inset;
  color: #d9edf7;
}

.scheduler-cockpit :deep(.el-input__inner),
.scheduler-cockpit :deep(.el-select__placeholder),
.scheduler-cockpit :deep(.el-pagination__total),
.scheduler-cockpit :deep(.el-pagination__sizes),
.scheduler-cockpit :deep(.el-pagination__goto),
.scheduler-cockpit :deep(.el-pagination__classifier) {
  color: #b9c8d8;
}

@media (max-width: 1180px) {
  .metric-strip,
  .runtime-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .scheduler-shell {
    grid-template-columns: 1fr;
  }

  .scheduler-rail {
    position: static;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .scheduler-cockpit {
    padding: 14px;
  }

  .scheduler-command-strip,
  .stage-head,
  .task-title-row,
  .stage-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .metric-strip,
  .scheduler-rail,
  .runtime-grid,
  .task-meta-grid {
    grid-template-columns: 1fr;
  }

  .task-card,
  .execution-row {
    grid-template-columns: 1fr;
  }

  .task-controls {
    justify-items: start;
    min-width: 0;
  }
}
</style>
