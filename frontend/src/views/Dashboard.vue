<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="page-title">系统仪表板</h1>
      <div class="actions">
        <el-button type="primary" @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
        </el-button>
        <el-button type="success" @click="onRunInspection" :loading="inspectionLoading">
          一键巡检
        </el-button>
      </div>
    </div>

    <!-- 状态卡片网格 -->
    <div class="grid grid-4 mb-20">
      <!-- 系统状态 -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">系统状态</h3>
          <span :class="['status-indicator', systemStatus.healthy ? 'online' : 'offline']">
            {{ systemStatus.healthy ? '运行中' : '异常' }}
          </span>
        </div>
        <div class="status-details">
          <div class="status-item">
            <span class="label">MCP客户端:</span>
            <span :class="['value', systemStatus.mcp_client ? 'success' : 'error']">
              {{ systemStatus.mcp_client ? '已连接' : '未连接' }}
            </span>
          </div>
          <div class="status-item">
            <span class="label">LLM处理器:</span>
            <span :class="['value', systemStatus.llm_processor ? 'success' : 'error']">
              {{ systemStatus.llm_processor ? '已就绪' : '未就绪' }}
            </span>
          </div>
          <div class="status-item">
            <span class="label">钉钉机器人:</span>
            <span :class="['value', systemStatus.dingtalk_bot ? 'success' : 'error']">
              {{ systemStatus.dingtalk_bot ? '已配置' : '未配置' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 工具统计 -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">可用工具</h3>
          <span class="badge">{{ toolsCount }}</span>
        </div>
        <div class="metric-value">
          <span class="number">{{ toolsCount }}</span>
          <span class="unit">个工具</span>
        </div>
        <div class="metric-trend">
          <span class="trend-text">MCP工具集成正常</span>
        </div>
      </div>

      <!-- API版本 -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">API版本</h3>
          <span class="badge info">v2.0</span>
        </div>
        <div class="version-info">
          <div class="version-item">
            <span class="label">当前版本:</span>
            <span class="value">{{ apiVersion }}</span>
          </div>
          <div class="version-item">
            <span class="label">兼容性:</span>
            <span class="value">{{ compatibility }}</span>
          </div>
        </div>
      </div>

      <!-- 最后更新时间 -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">最后更新</h3>
        </div>
        <div class="time-info">
          <div class="time-value">{{ formatTime(lastUpdateTime) }}</div>
          <div class="time-relative">{{ timeAgo(lastUpdateTime) }}</div>
        </div>
      </div>
    </div>

    <!-- 详细信息面板 -->
    <div class="grid grid-2">
      <!-- 工具列表 -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">工具列表</h3>
          <el-button size="small" @click="loadTools">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="tools-list" v-if="tools.length > 0">
          <div 
            v-for="tool in tools" 
            :key="tool.name" 
            class="tool-item"
          >
            <div class="tool-info">
              <div class="tool-name">{{ tool.name }}</div>
              <div class="tool-description">{{ tool.description }}</div>
            </div>
            <div class="tool-meta">
              <span class="tool-category">{{ tool.category || 'general' }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-state-text">暂无可用工具</div>
        </div>
      </div>

      <!-- 系统日志 -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">系统日志</h3>
          <el-button size="small" @click="clearLogs">清空</el-button>
        </div>
        <div class="logs-container">
          <div 
            v-for="(log, index) in systemLogs" 
            :key="index"
            :class="['log-item', log.level]"
          >
            <span class="log-time">{{ formatLogTime(log.time) }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 巡检结果对话框 -->
    <el-dialog v-model="inspectionDialogVisible" title="巡检结果" width="800px">
      <div v-html="inspectionMarkdown"></div>
      <template #footer>
        <el-button type="primary" @click="inspectionDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import { renderMarkdown } from '@/utils/markdown'

// 响应式数据
const loading = ref(false)
const systemStatus = ref({
  healthy: false,
  mcp_client: false,
  llm_processor: false,
  dingtalk_bot: false,
  tools_count: 0
})
const tools = ref([])
const toolsCount = ref(0)
const apiVersion = ref('2.0')
const compatibility = ref('v1')
const lastUpdateTime = ref(new Date())
const systemLogs = ref([
  { time: new Date(), level: 'info', message: '系统启动完成' },
  { time: new Date(), level: 'success', message: 'MCP客户端连接成功' },
  { time: new Date(), level: 'info', message: 'LLM处理器初始化完成' }
])

let refreshTimer = null

// 巡检数据
const inspectionLoading = ref(false)
const inspectionDialogVisible = ref(false)
const inspectionMarkdown = ref('')

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadSystemStatus(),
      loadTools(),
      loadApiInfo()
    ])
    lastUpdateTime.value = new Date()
    addLog('info', '数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    addLog('error', '数据刷新失败')
  } finally {
    loading.value = false
  }
}

const onRunInspection = async () => {
  inspectionLoading.value = true
  try {
    const res = await api.inspection.run({
      scope: { includeNamespaces: ['default', 'kube-system'], maxDepth: 2 },
      options: { sendToDingTalk: true, includeAnomalies: true }
    })
    const data = res.data
    inspectionMarkdown.value = renderMarkdown(data.analysisMarkdown)
    inspectionDialogVisible.value = true
    addLog('success', '巡检完成')
  } catch (e) {
    addLog('error', `巡检失败: ${e?.message || e}`)
  } finally {
    inspectionLoading.value = false
  }
}

const loadSystemStatus = async () => {
  try {
    const response = await api.system.getV2Health()
    const data = response.data
    console.log('健康检查响应数据:', data)
    console.log('钉钉机器人状态:', data.components.dingtalk_bot)
    systemStatus.value = {
      healthy: data.healthy,
      mcp_client: data.components.mcp_client,
      llm_processor: data.components.llm_processor,
      dingtalk_bot: data.components.dingtalk_bot,
      tools_count: data.components.tools_available
    }
    console.log('更新后的systemStatus:', systemStatus.value)
    // 统一设置工具数量，避免多处设置造成冲突
    toolsCount.value = data.components.tools_available || 0
    console.log('工具数量已更新:', toolsCount.value)
  } catch (error) {
    console.error('获取系统状态失败:', error)
    // 失败时设置默认值
    toolsCount.value = 0
    systemStatus.value = {
      healthy: false,
      mcp_client: false,
      llm_processor: false,
      dingtalk_bot: false,
      tools_count: 0
    }
  }
}

const loadTools = async () => {
  try {
    const response = await api.system.getTools()
    tools.value = response.data.tools || []
    // 不再在这里设置toolsCount，避免与健康检查接口冲突
    // toolsCount由loadSystemStatus统一管理
  } catch (error) {
    console.error('获取工具列表失败:', error)
    tools.value = []
  }
}

const loadApiInfo = async () => {
  try {
    const response = await api.system.getV2Status()
    const data = response.data
    apiVersion.value = data.version
    compatibility.value = data.compatible_with
  } catch (error) {
    console.error('获取API信息失败:', error)
  }
}

const addLog = (level, message) => {
  systemLogs.value.unshift({
    time: new Date(),
    level,
    message
  })
  // 保持最多50条日志
  if (systemLogs.value.length > 50) {
    systemLogs.value = systemLogs.value.slice(0, 50)
  }
}

const clearLogs = () => {
  systemLogs.value = []
  ElMessage.success('日志已清空')
}

const formatTime = (time) => {
  return time.toLocaleString('zh-CN')
}

const formatLogTime = (time) => {
  return time.toLocaleTimeString('zh-CN')
}

const timeAgo = (time) => {
  const now = new Date()
  const diff = now - time
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

// 生命周期
onMounted(() => {
  refreshData()
  // 每30秒自动刷新
  refreshTimer = setInterval(refreshData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard {
  height: 100%;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.actions { display: flex; gap: 12px; }

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.status-details {
  margin-top: 16px;
}

.status-item,
.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.status-item:last-child,
.version-item:last-child {
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

.metric-trend {
  text-align: center;
}

.trend-text {
  font-size: 12px;
  color: var(--success-color);
}

.time-info {
  text-align: center;
  margin-top: 16px;
}

.time-value {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.time-relative {
  font-size: 12px;
  color: var(--text-secondary);
}

.tools-list {
  max-height: 300px;
  overflow-y: auto;
}

.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-extra-light);
}

.tool-item:last-child {
  border-bottom: none;
}

.tool-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.tool-description {
  font-size: 12px;
  color: var(--text-secondary);
}

.tool-category {
  font-size: 11px;
  padding: 2px 6px;
  background-color: var(--background-base);
  color: var(--text-secondary);
  border-radius: 4px;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
}

.log-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
  font-size: 12px;
  border-bottom: 1px solid var(--border-extra-light);
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--text-secondary);
  margin-right: 8px;
  min-width: 80px;
}

.log-level {
  margin-right: 8px;
  min-width: 50px;
  font-weight: 500;
}

.log-item.info .log-level {
  color: var(--info-color);
}

.log-item.success .log-level {
  color: var(--success-color);
}

.log-item.error .log-level {
  color: var(--danger-color);
}

.log-message {
  color: var(--text-primary);
  flex: 1;
}
</style> 