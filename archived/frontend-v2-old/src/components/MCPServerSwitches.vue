<template>
  <div class="mcp-server-switches">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载MCP服务器...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <el-icon><Warning /></el-icon>
      <span>{{ error }}</span>
      <el-button size="small" @click="loadServers">重试</el-button>
    </div>

    <!-- 服务器开关列表 -->
    <div v-else class="servers-switches">
      <div class="global-status">
        <span class="status-text">
          AI上下文: {{ enabledCount }}/{{ servers.length }} 已纳入
          <span v-if="connectedCount > 0" class="connected-info">
            · runtime {{ connectedCount }} online
          </span>
        </span>
        <el-button
          v-if="servers.length > 1"
          size="small"
          @click="toggleAll"
          :type="allEnabled ? 'warning' : 'success'"
        >
          {{ allEnabled ? '全部排除' : '全部纳入' }}
        </el-button>
      </div>

      <!-- 单个服务器开关 -->
      <div class="server-switches">
        <div
          v-for="server in servers"
          :key="server.name"
          class="server-switch-item"
          :class="{
            'enabled': server.enabled,
            'connected': server.connected,
            'disconnected': server.enabled && !server.connected
          }"
        >
          <div class="server-info">
            <div class="server-name">
              {{ server.display_name }}
              <el-tag
                size="small"
                :type="server.enabled ? 'success' : 'info'"
              >
                {{ server.enabled ? '已纳入' : '未纳入' }}
              </el-tag>
            </div>
            <div class="server-details">
              <span class="server-type">{{ server.type.toUpperCase() }}</span>
              <span class="runtime-state" :class="{ online: server.connected }">
                {{ server.connected ? 'runtime online' : 'runtime standby' }}
              </span>
              <span v-if="server.tools_count > 0" class="tools-count">
                {{ server.tools_count }} 个工具
              </span>
              <span v-if="server.host && server.port" class="server-address">
                {{ server.host }}:{{ server.port }}
              </span>
            </div>
          </div>

          <div class="server-controls">
            <el-switch
              v-model="server.enabled"
              size="small"
              active-color="var(--ops-success)"
              :inactive-color="'#DCDFE6'"
              inline-prompt
              active-text="纳入"
              inactive-text="排除"
              @change="toggleServer(server.name, server.enabled)"
              :loading="server.switching"
            />
          </div>
        </div>
      </div>

      <!-- 工具提示 -->
      <div v-if="servers.length > 0" class="mcp-tooltip">
        <el-icon><InfoFilled /></el-icon>
        <span>MCP runtime 常驻运行；开关只控制 AI 是否把该工具源纳入上下文和可调用范围</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Warning, InfoFilled } from '@element-plus/icons-vue'
import apiClient from '@/api/client'

// Props
const props = defineProps({
  // 是否自动加载
  autoLoad: {
    type: Boolean,
    default: true
  },
  // 是否显示全局控制
  showGlobalControls: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['servers-changed', 'server-toggled'])

// 响应式数据
const loading = ref(false)
const error = ref(null)
const servers = ref([])

// 计算属性
const enabledCount = computed(() => servers.value.filter(s => s.enabled).length)
const connectedCount = computed(() => servers.value.filter(s => s.connected).length)
const allEnabled = computed(() => servers.value.length > 0 && servers.value.every(s => s.enabled))

// 方法
const loadServers = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await apiClient.get('/v2/mcp/servers/status')
    servers.value = response.data.servers.map(server => ({
      ...server,
      switching: false
    }))

    emit('servers-changed', {
      servers: servers.value,
      total_enabled: response.data.total_enabled,
      total_connected: response.data.total_connected
    })
  } catch (e) {
    console.error('加载MCP服务器失败:', e)
    error.value = e.response?.data?.error?.message || e.response?.data?.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// 刷新服务器状态（不显示loading）
const refreshServerStatus = async () => {
  try {
    const response = await apiClient.get('/v2/mcp/servers/status')
    if (response.data.servers) {
      // 保持当前的状态，只更新服务器数据
      const currentStates = {}
      servers.value.forEach(server => {
        currentStates[server.name] = {
          switching: server.switching
        }
      })

      servers.value = response.data.servers.map(server => ({
        ...server,
        switching: currentStates[server.name]?.switching || false
      }))

      emit('servers-changed', {
        servers: servers.value,
        total_enabled: response.data.total_enabled,
        total_connected: response.data.total_connected
      })
    }
  } catch (e) {
    console.error('刷新服务器状态失败:', e)
    // 静默失败，不显示错误消息
  }
}

const toggleServer = async (serverName, enabled) => {
  const server = servers.value.find(s => s.name === serverName)
  if (!server) return

  // 乐观更新：立即更新UI状态
  const originalEnabled = server.enabled
  server.enabled = enabled
  server.switching = true

  try {
    const configResponse = await apiClient.post(`/v2/mcp/config/servers/${serverName}/toggle`)
    await refreshServerStatus()

    emit('server-toggled', {
      server: serverName,
      enabled: enabled,
      server_info: server,
      should_refresh_tools: true
    })

    ElMessage.success(configResponse.data.message || `${serverName} 已${enabled ? '纳入' : '排除'} AI 上下文`)

  } catch (e) {
    console.error('切换服务器状态失败:', e)
    // 回滚状态
    server.enabled = originalEnabled
    ElMessage.error(e.response?.data?.error?.message || e.response?.data?.detail || e.message || '操作失败')

    // 失败后也刷新一次状态，确保数据一致性
    await refreshServerStatus()
  } finally {
    server.switching = false
  }
}

const toggleAll = async () => {
  const targetState = !allEnabled.value
  const serverStates = {}

  // 保存原始状态用于回滚
  const originalStates = {}
  servers.value.forEach(server => {
    originalStates[server.name] = server.enabled
    serverStates[server.name] = targetState
    // 乐观更新：立即更新UI状态
    server.enabled = targetState
    server.switching = true
  })

  try {
    const response = await apiClient.post('/v2/mcp/servers/batch-toggle', {
      servers: serverStates
    })

    ElMessage.success(`已${targetState ? '纳入' : '排除'}所有MCP服务器`)

    // 操作成功后，立即刷新服务器状态以获取最新的连接状态
    await refreshServerStatus()

  } catch (e) {
    console.error('批量切换失败:', e)
    // 回滚状态
    servers.value.forEach(server => {
      server.enabled = originalStates[server.name]
    })
    ElMessage.error(e.response?.data?.error?.message || e.response?.data?.detail || e.message || '批量操作失败')

    // 失败后也刷新一次状态，确保数据一致性
    await refreshServerStatus()
  } finally {
    // 清除所有switching状态
    servers.value.forEach(server => {
      server.switching = false
    })
  }
}

// 暴露方法给父组件
defineExpose({
  loadServers,
  refreshServerStatus,
  toggleServer,
  toggleAll,
  servers: computed(() => servers.value),
  enabledCount,
  connectedCount
})

// 生命周期
onMounted(() => {
  if (props.autoLoad) {
    loadServers()
  }
})
</script>

<style scoped>
.mcp-server-switches {
  width: 100%;
}

.loading-state, .error-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: #9da08e;
  font-size: 14px;
}

.error-state {
  color: var(--el-color-danger);
}

.servers-switches {
  width: 100%;
}

.global-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #151712;
  border: 1px solid #2a2d24;
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.status-text {
  color: #e6e2d8;
  font-weight: 500;
}

.connected-info {
  color: #9fcf96;
  font-weight: normal;
}

.server-switches {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.server-switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #2a2d24;
  border-radius: 8px;
  transition: all 0.2s;
  gap: 8px; /* 添加间距，防止内容挤压 */
  min-width: 0; /* 允许flex子元素收缩 */
}

.server-switch-item:hover {
  border-color: rgba(214, 168, 79, 0.32);
  background: rgba(214, 168, 79, 0.06);
}

.server-switch-item.enabled {
  border-color: rgba(143, 191, 135, 0.3);
  background: rgba(143, 191, 135, 0.06);
}

.server-switch-item.connected {
  border-color: rgba(143, 191, 135, 0.48);
}

.server-switch-item.disconnected {
  border-color: rgba(143, 191, 135, 0.3);
  background: rgba(143, 191, 135, 0.06);
}

.server-info {
  flex: 1;
  min-width: 0; /* 允许flex子元素收缩 */
  overflow: hidden; /* 防止内容溢出 */
}

.server-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #f1efe7;
  margin-bottom: 4px;
}

.server-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #9da08e;
}

.server-type {
  background: rgba(148, 148, 132, 0.12);
  color: #c7c3b3;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.tools-count {
  color: #e0b45a;
}

.runtime-state {
  color: var(--ops-muted);
}

.runtime-state.online {
  color: var(--ops-success);
}

.server-address {
  font-family: monospace;
}

.server-controls {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  justify-content: flex-end;
  min-width: 0; /* 允许flex子元素收缩 */
  flex-shrink: 1; /* 允许收缩 */
}

.mcp-tooltip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-top: 8px;
  font-size: 12px;
  color: #9da08e;
  background: #151712;
  border: 1px solid #2a2d24;
  border-radius: 8px;
}

.mcp-tooltip .el-icon {
  color: #d6a84f;
}

.mcp-server-switches :deep(.el-button) {
  border-color: #3a3d30 !important;
  background: #151712 !important;
  color: #e6e2d8 !important;
  box-shadow: none !important;
}

.mcp-server-switches :deep(.el-button--primary),
.mcp-server-switches :deep(.el-button--warning),
.mcp-server-switches :deep(.el-button--success) {
  border-color: rgba(214, 168, 79, 0.34) !important;
  background: rgba(214, 168, 79, 0.08) !important;
  color: #e4bd68 !important;
}

.mcp-server-switches :deep(.el-switch.is-checked .el-switch__core) {
  border-color: #8fbf87 !important;
  background-color: #8fbf87 !important;
}

.mcp-server-switches :deep(.el-switch__core) {
  border-color: #3a3d30 !important;
  background-color: #1b1d17 !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .server-switch-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .server-controls {
    align-self: flex-end;
  }

  .global-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
