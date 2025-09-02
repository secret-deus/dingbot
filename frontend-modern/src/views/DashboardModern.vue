<template>
  <div class="modern-dashboard">
    <div class="dashboard-header">
      <h1 class="page-title">系统仪表板</h1>
      <div class="actions">
        <el-button type="primary" @click="refreshData" :loading="loading" class="modern-btn">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="success" @click="onRunInspection" :loading="inspectionLoading" class="modern-btn">
          一键巡检
        </el-button>
      </div>
    </div>

    <!-- 状态卡片网格 -->
    <div class="stats-grid">
      <!-- 系统状态 -->
      <div class="stat-card">
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
      <div class="stat-card">
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
      <div class="stat-card">
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
      <div class="stat-card">
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
    <div class="content-grid">
      <!-- 工具列表 -->
      <div class="content-card">
        <div class="card-header">
          <h3 class="card-title">工具列表</h3>
          <div class="header-actions">
            <el-button size="small" @click="loadTools" :loading="loadingTools" class="modern-btn-small">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button size="small" type="primary" @click="refreshTools" :loading="refreshingTools" class="modern-btn-small">
              <el-icon><RefreshRight /></el-icon>
              重新加载
            </el-button>
          </div>
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
      <div class="content-card">
        <div class="card-header">
          <h3 class="card-title">系统日志</h3>
          <el-button size="small" @click="clearLogs" class="modern-btn-small">清空</el-button>
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
import { Refresh, RefreshRight } from '@element-plus/icons-vue'
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
const loadingTools = ref(false)
const refreshingTools = ref(false)
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
  loadingTools.value = true
  try {
    const response = await api.system.getTools()
    tools.value = response.data.tools || []
    toolsCount.value = response.data.total_count || tools.value.length
    addLog('info', `工具列表已更新，共 ${tools.value.length} 个工具`)
  } catch (error) {
    console.error('获取工具列表失败:', error)
    tools.value = []
    toolsCount.value = 0
    addLog('error', '获取工具列表失败')
  } finally {
    loadingTools.value = false
  }
}

const refreshTools = async () => {
  refreshingTools.value = true
  try {
    const response = await api.system.refreshTools()
    if (response.data.success) {
      tools.value = response.data.tools || []
      toolsCount.value = response.data.tools_count || 0
      ElMessage.success(response.data.message)
      addLog('success', `工具列表已重新加载，共 ${toolsCount.value} 个工具`)
      
      // 同时更新系统状态
      await loadSystemStatus()
    } else {
      ElMessage.error(response.data.error || '刷新工具列表失败')
      addLog('error', response.data.error || '刷新工具列表失败')
    }
  } catch (error) {
    console.error('刷新工具列表失败:', error)
    ElMessage.error('刷新工具列表失败')
    addLog('error', '刷新工具列表失败')
  } finally {
    refreshingTools.value = false
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
/* 现代化仪表板样式 */
.modern-dashboard {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-secondary);
  font-family: var(--font-sans);
  padding: var(--space-6);
}

/* 头部 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-8);
}

.page-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.actions {
  display: flex;
  gap: var(--space-3);
}

/* 现代化按钮 */
.modern-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--duration-200) var(--ease-out);
}

.modern-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.modern-btn-small {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  transition: all var(--duration-200) var(--ease-out);
}

.modern-btn-small:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  transition: all var(--duration-200) var(--ease-out);
  box-shadow: var(--shadow-sm);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-secondary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.status-indicator {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.status-indicator.online {
  background: var(--success-100);
  color: var(--success-700);
}

.status-indicator.offline {
  background: var(--error-100);
  color: var(--error-700);
}

.badge {
  background: var(--primary-100);
  color: var(--primary-700);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.badge.info {
  background: var(--info-100);
  color: var(--info-700);
}

/* 状态详情 */
.status-details {
  margin-top: var(--space-4);
}

.status-item,
.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: background-color var(--duration-200) var(--ease-out);
}

.status-item:hover,
.version-item:hover {
  background: var(--neutral-50);
}

.status-item:last-child,
.version-item:last-child {
  margin-bottom: 0;
}

.label {
  color: var(--text-secondary);
}

.value.success {
  color: var(--success-600);
  font-weight: var(--font-medium);
}

.value.error {
  color: var(--error-600);
  font-weight: var(--font-medium);
}

.value {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

/* 指标值 */
.metric-value {
  margin: var(--space-4) 0;
  text-align: center;
}

.number {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--primary-600);
}

.unit {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-left: var(--space-2);
}

.metric-trend {
  text-align: center;
}

.trend-text {
  font-size: var(--text-xs);
  color: var(--success-600);
  font-weight: var(--font-medium);
}

/* 时间信息 */
.time-info {
  text-align: center;
  margin-top: var(--space-4);
}

.time-value {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.time-relative {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

/* 内容网格 */
.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--space-6);
}

.content-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-200) var(--ease-out);
}

.content-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-secondary);
}

.content-card .card-header {
  padding: var(--space-6) var(--space-6) var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--border-primary);
}

.header-actions {
  display: flex;
  gap: var(--space-2);
}

/* 工具列表 */
.tools-list {
  max-height: 300px;
  overflow-y: auto;
  padding: var(--space-6);
}

.tool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  transition: background-color var(--duration-200) var(--ease-out);
  margin-bottom: var(--space-2);
}

.tool-item:hover {
  background: var(--neutral-50);
}

.tool-item:last-child {
  margin-bottom: 0;
}

.tool-name {
  font-weight: var(--font-medium);
  color: var(--text-primary);
  margin-bottom: var(--space-1);
  font-size: var(--text-sm);
}

.tool-description {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.tool-category {
  font-size: var(--text-xs);
  padding: var(--space-1) var(--space-2);
  background: var(--neutral-100);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  font-weight: var(--font-medium);
}

/* 空状态 */
.empty-state {
  padding: var(--space-8);
  text-align: center;
}

.empty-state-text {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

/* 日志容器 */
.logs-container {
  max-height: 300px;
  overflow-y: auto;
  font-family: var(--font-mono);
  padding: var(--space-6);
}

.log-item {
  display: flex;
  align-items: center;
  padding: var(--space-2) 0;
  font-size: var(--text-xs);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-1);
  padding-left: var(--space-2);
  padding-right: var(--space-2);
  transition: background-color var(--duration-200) var(--ease-out);
}

.log-item:hover {
  background: var(--neutral-50);
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-time {
  color: var(--text-tertiary);
  margin-right: var(--space-2);
  min-width: 80px;
}

.log-level {
  margin-right: var(--space-2);
  min-width: 50px;
  font-weight: var(--font-medium);
}

.log-item.info .log-level {
  color: var(--info-600);
}

.log-item.success .log-level {
  color: var(--success-600);
}

.log-item.error .log-level {
  color: var(--error-600);
}

.log-message {
  color: var(--text-primary);
  flex: 1;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .modern-dashboard {
    padding: var(--space-4);
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: stretch;
  }
  
  .actions {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
  
  .content-grid {
    gap: var(--space-4);
  }
  
  .page-title {
    font-size: var(--text-2xl);
    text-align: center;
  }
}

@media (max-width: 480px) {
  .tool-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
  
  .log-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-1);
  }
  
  .log-time,
  .log-level {
    min-width: auto;
  }
}
</style>