<template>
  <div class="dashboard-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">系统仪表板</h1>
        <p class="page-subtitle">实时监控K8s集群状态和运维数据</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="refreshAllData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="success" @click="runInspection" :loading="inspectionLoading">
          <el-icon><Search /></el-icon>
          一键巡检
        </el-button>
      </div>
    </div>

    <!-- 统计卡片容器 -->
    <div class="stats-cards-container">
      <!-- 系统健康状态卡片 -->
      <div class="stats-card health-card">
        <div class="card-header">
          <div class="card-icon health">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="card-info">
            <h3 class="card-title">系统健康</h3>
            <p class="card-subtitle">整体运行状态</p>
          </div>
        </div>
        <div class="card-body">
          <div class="health-status">
            <div :class="['status-indicator', systemHealth.status]">
              <span class="status-text">{{ systemHealth.text }}</span>
            </div>
            <div class="health-score">
              <span class="score-value">{{ systemHealth.score }}</span>
              <span class="score-unit">%</span>
            </div>
          </div>
          <div class="health-details">
            <div class="detail-item">
              <span class="label">MCP客户端</span>
              <span :class="['status', systemStatus.mcp_client ? 'online' : 'offline']">
                {{ systemStatus.mcp_client ? '已连接' : '未连接' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">LLM处理器</span>
              <span :class="['status', systemStatus.llm_processor ? 'online' : 'offline']">
                {{ systemStatus.llm_processor ? '就绪' : '未就绪' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">钉钉机器人</span>
              <span :class="['status', systemStatus.dingtalk_bot ? 'online' : 'offline']">
                {{ systemStatus.dingtalk_bot ? '已配置' : '未配置' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 可用工具统计 -->
      <div class="stats-card tools-card">
        <div class="card-header">
          <div class="card-icon tools">
            <el-icon><Tools /></el-icon>
          </div>
          <div class="card-info">
            <h3 class="card-title">可用工具</h3>
            <p class="card-subtitle">MCP工具集成</p>
          </div>
        </div>
        <div class="card-body">
          <div class="stats-value">{{ toolsCount }}</div>
          <div class="stats-trend positive">
            <el-icon><TrendCharts /></el-icon>
            <span>工具运行正常</span>
          </div>
          <div class="tools-breakdown">
            <div class="breakdown-item">
              <span class="category">K8s工具</span>
              <span class="count">{{ toolsBreakdown.k8s }}</span>
            </div>
            <div class="breakdown-item">
              <span class="category">SSH工具</span>
              <span class="count">{{ toolsBreakdown.ssh }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 集群资源概览 -->
      <div class="stats-card resources-card">
        <div class="card-header">
          <div class="card-icon resources">
            <el-icon><Box /></el-icon>
          </div>
          <div class="card-info">
            <h3 class="card-title">集群资源</h3>
            <p class="card-subtitle">资源使用情况</p>
          </div>
        </div>
        <div class="card-body">
          <div class="resource-metrics">
            <div class="metric-item">
              <div class="metric-label">节点数量</div>
              <div class="metric-value">{{ clusterStats.nodes }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">Pod数量</div>
              <div class="metric-value">{{ clusterStats.pods }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">服务数量</div>
              <div class="metric-value">{{ clusterStats.services }}</div>
            </div>
          </div>
          <div class="resource-usage">
            <div class="usage-item">
              <span class="usage-label">CPU使用率</span>
              <el-progress 
                :percentage="clusterStats.cpuUsage" 
                :color="getProgressColor(clusterStats.cpuUsage)"
                :show-text="false"
              />
              <span class="usage-value">{{ clusterStats.cpuUsage }}%</span>
            </div>
            <div class="usage-item">
              <span class="usage-label">内存使用率</span>
              <el-progress 
                :percentage="clusterStats.memoryUsage" 
                :color="getProgressColor(clusterStats.memoryUsage)"
                :show-text="false"
              />
              <span class="usage-value">{{ clusterStats.memoryUsage }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="stats-card activity-card">
        <div class="card-header">
          <div class="card-icon activity">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="card-info">
            <h3 class="card-title">最近活动</h3>
            <p class="card-subtitle">系统操作记录</p>
          </div>
        </div>
        <div class="card-body">
          <div class="activity-stats">
            <div class="stat-item">
              <span class="stat-value">{{ activityStats.today }}</span>
              <span class="stat-label">今日操作</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ activityStats.week }}</span>
              <span class="stat-label">本周操作</span>
            </div>
          </div>
          <div class="last-update">
            <span class="update-label">最后更新</span>
            <span class="update-time">{{ formatTime(lastUpdateTime) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细信息面板 -->
    <div class="details-section">
      <div class="grid grid-2">
        <!-- 实时监控图表 -->
        <div class="card chart-card">
          <div class="card-header">
            <h3 class="card-title">实时监控</h3>
            <div class="chart-controls">
              <el-radio-group v-model="chartTimeRange" size="small">
                <el-radio-button label="1h">1小时</el-radio-button>
                <el-radio-button label="6h">6小时</el-radio-button>
                <el-radio-button label="24h">24小时</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="card-body">
            <div class="chart-container">
              <div class="chart-placeholder">
                <el-icon class="chart-icon"><TrendCharts /></el-icon>
                <p>监控图表</p>
                <p class="chart-desc">CPU、内存、网络实时监控数据</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 系统日志 -->
        <div class="card logs-card">
          <div class="card-header">
            <h3 class="card-title">系统日志</h3>
            <el-button size="small" @click="clearLogs" type="text">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
          <div class="card-body">
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
      </div>
    </div>

    <!-- 巡检结果对话框 -->
    <el-dialog v-model="inspectionDialogVisible" title="巡检结果" width="80%" top="5vh">
      <div class="inspection-result" v-html="inspectionMarkdown"></div>
      <template #footer>
        <el-button type="primary" @click="inspectionDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Search,
  Monitor,
  Tools,
  Box,
  Clock,
  TrendCharts,
  Delete
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'
import apiClient from '@/api/client'

// 使用Dashboard Store
const dashboardStore = useDashboardStore()

// 响应式数据
const inspectionLoading = ref(false)
const inspectionDialogVisible = ref(false)
const inspectionMarkdown = ref('')
const chartTimeRange = ref('6h')

// 从store获取数据
const loading = computed(() => dashboardStore.loading)
const systemStatus = computed(() => dashboardStore.systemStatus)
const toolsCount = computed(() => dashboardStore.toolsStats.total)
const toolsBreakdown = computed(() => ({
  k8s: dashboardStore.toolsStats.k8s,
  ssh: dashboardStore.toolsStats.ssh
}))
const clusterStats = computed(() => dashboardStore.clusterStats)
const activityStats = computed(() => dashboardStore.activityStats)
const lastUpdateTime = computed(() => dashboardStore.lastUpdateTime)
const systemLogs = computed(() => dashboardStore.systemLogs)

// 系统健康状态
const systemHealth = computed(() => dashboardStore.systemHealthStatus())

let refreshTimer = null

// 方法
const refreshAllData = async () => {
  try {
    await dashboardStore.refreshAllData()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('数据刷新失败')
  }
}

const runInspection = async () => {
  inspectionLoading.value = true
  try {
    const result = await dashboardStore.runInspection({
      scope: { includeNamespaces: ['default', 'kube-system'], maxDepth: 2 },
      options: { sendToDingTalk: true, includeAnomalies: true }
    })
    
    // 格式化巡检结果
    if (result.analysisMarkdown) {
      inspectionMarkdown.value = result.analysisMarkdown
    } else {
      inspectionMarkdown.value = `
        <h3>🔍 系统巡检报告</h3>
        <p><strong>巡检时间:</strong> ${new Date().toLocaleString()}</p>
        <h4>✅ 检查项目</h4>
        <ul>
          <li>集群节点状态: ${result.nodes || '检查中'}</li>
          <li>Pod运行状态: ${result.pods || '检查中'}</li>
          <li>服务可用性: ${result.services || '检查中'}</li>
          <li>资源使用率: ${result.resources || '检查中'}</li>
        </ul>
        <h4>📊 性能指标</h4>
        <ul>
          <li>CPU使用率: ${clusterStats.value.cpuUsage}% (${clusterStats.value.cpuUsage < 80 ? '正常' : '偏高'})</li>
          <li>内存使用率: ${clusterStats.value.memoryUsage}% (${clusterStats.value.memoryUsage < 80 ? '正常' : '偏高'})</li>
          <li>存储使用率: ${clusterStats.value.storageUsage}% (${clusterStats.value.storageUsage < 80 ? '正常' : '偏高'})</li>
        </ul>
        <h4>💡 建议</h4>
        <p>${result.suggestions || '系统运行状态良好，无需特殊处理。'}</p>
      `
    }
    
    inspectionDialogVisible.value = true
    ElMessage.success('巡检完成')
  } catch (error) {
    console.error('巡检失败:', error)
    ElMessage.error('巡检失败')
  } finally {
    inspectionLoading.value = false
  }
}

const clearLogs = () => {
  dashboardStore.clearLogs()
  ElMessage.success('日志已清空')
}

const formatTime = (time) => {
  return time.toLocaleString('zh-CN')
}

const formatLogTime = (time) => {
  return time.toLocaleTimeString('zh-CN')
}

const getProgressColor = (percentage) => {
  if (percentage < 60) return '#10b981'
  if (percentage < 80) return '#f59e0b'
  return '#ef4444'
}

// 生命周期
onMounted(() => {
  // 初始化数据
  refreshAllData()
  
  // 每30秒自动刷新数据
  refreshTimer = setInterval(() => {
    dashboardStore.refreshAllData()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard-page {
  min-height: 100%;
  background: var(--bg-secondary);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* 统计卡片容器 */
.stats-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.stats-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--primary-gradient);
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  
  &.health {
    background: var(--success-gradient);
    color: white;
    box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
  }
  
  &.tools {
    background: var(--primary-gradient-blue);
    color: white;
    box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
  }
  
  &.resources {
    background: var(--primary-gradient);
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  }
  
  &.activity {
    background: var(--warning-gradient);
    color: white;
    box-shadow: 0 4px 15px rgba(255, 154, 158, 0.3);
  }
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.card-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* 健康状态卡片 */
.health-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-md);
  
  &.online {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success-color);
  }
}

.health-score {
  font-size: 2rem;
  font-weight: 700;
  color: var(--success-color);
}

.score-unit {
  font-size: 1rem;
  color: var(--text-secondary);
}

.health-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.label {
  color: var(--text-secondary);
}

.status {
  font-weight: 500;
  
  &.online {
    color: var(--success-color);
  }
  
  &.offline {
    color: var(--danger-color);
  }
}

/* 工具卡片 */
.stats-value {
  font-size: 3rem;
  font-weight: 700;
  color: var(--primary-color);
  line-height: 1;
  margin-bottom: var(--spacing-sm);
}

.stats-trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.875rem;
  margin-bottom: var(--spacing-md);
  
  &.positive {
    color: var(--success-color);
  }
}

.tools-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.category {
  color: var(--text-secondary);
}

.count {
  font-weight: 600;
  color: var(--text-primary);
}

/* 资源卡片 */
.resource-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.metric-item {
  text-align: center;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.resource-usage {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.usage-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.usage-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  min-width: 80px;
}

.usage-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 40px;
  text-align: right;
}

/* 活动卡片 */
.activity-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.last-update {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-light);
  font-size: 0.875rem;
}

.update-label {
  color: var(--text-secondary);
}

.update-time {
  color: var(--text-primary);
  font-weight: 500;
}

/* 详细信息面板 */
.details-section {
  margin-top: var(--spacing-xl);
}

.chart-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
  color: var(--text-secondary);
}

.chart-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
  color: var(--text-tertiary);
}

.chart-desc {
  font-size: 0.875rem;
  margin-top: var(--spacing-xs);
}

/* 日志样式 */
.logs-container {
  max-height: 300px;
  overflow-y: auto;
  font-family: var(--font-mono);
}

.log-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-xs) 0;
  font-size: 0.75rem;
  border-bottom: 1px solid var(--border-light);
  
  &:last-child {
    border-bottom: none;
  }
}

.log-time {
  color: var(--text-tertiary);
  margin-right: var(--spacing-sm);
  min-width: 80px;
}

.log-level {
  margin-right: var(--spacing-sm);
  min-width: 60px;
  font-weight: 600;
  text-transform: uppercase;
  
  .log-item.info & {
    color: var(--info-color);
  }
  
  .log-item.success & {
    color: var(--success-color);
  }
  
  .log-item.error & {
    color: var(--danger-color);
  }
}

.log-message {
  color: var(--text-primary);
  flex: 1;
}

/* 巡检结果样式 */
.inspection-result {
  max-height: 60vh;
  overflow-y: auto;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .stats-cards-container {
    grid-template-columns: 1fr;
  }
  
  .resource-metrics {
    grid-template-columns: 1fr;
  }
  
  .activity-stats {
    grid-template-columns: 1fr;
  }
}
</style>
