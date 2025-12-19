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
      <!-- 全局状态显示 -->
      <div class="global-status">
        <span class="status-text">
          MCP服务器: {{ enabledCount }}/{{ servers.length }} 已启用
          <span v-if="connectedCount > 0" class="connected-info">
            ({{ connectedCount }} 已连接)
          </span>
        </span>
        <el-button 
          v-if="servers.length > 1"
          size="small" 
          @click="toggleAll"
          :type="allEnabled ? 'warning' : 'success'"
        >
          {{ allEnabled ? '全部禁用' : '全部启用' }}
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
                :type="server.connected ? 'success' : (server.enabled ? 'warning' : 'info')"
              >
                {{ server.connected ? '已连接' : (server.enabled ? '未连接' : '已禁用') }}
              </el-tag>
            </div>
            <div class="server-details">
              <span class="server-type">{{ server.type.toUpperCase() }}</span>
              <span v-if="server.tools_count > 0" class="tools-count">
                {{ server.tools_count }} 个工具
              </span>
              <span v-if="server.host && server.port" class="server-address">
                {{ server.host }}:{{ server.port }}
              </span>
            </div>
          </div>
          
          <div class="server-controls">
            <!-- 连接控制按钮 -->
            <div class="connection-controls" v-if="server.enabled">
              <el-button
                v-if="!server.connected"
                size="small"
                type="success"
                :icon="Connection"
                @click="connectServer(server.name)"
                :loading="server.connecting"
                title="连接服务器"
              >
                连接
              </el-button>
              <el-button
                v-else
                size="small"
                type="warning"
                :icon="Close"
                @click="disconnectServer(server.name)"
                :loading="server.disconnecting"
                title="断开连接"
              >
                断开
              </el-button>
              <el-button
                v-if="server.connected"
                size="small"
                type="primary"
                :icon="Refresh"
                @click="reconnectServer(server.name)"
                :loading="server.reconnecting"
                title="重新连接"
              >
                重连
              </el-button>
            </div>
            
            <!-- 启用/禁用开关 -->
            <el-switch
              v-model="server.enabled"
              size="small"
              :active-color="'#67C23A'"
              :inactive-color="'#DCDFE6'"
              @change="toggleServer(server.name, server.enabled)"
              :loading="server.switching"
            />
          </div>
        </div>
      </div>
      
      <!-- 工具提示 -->
      <div v-if="servers.length > 0" class="mcp-tooltip">
        <el-icon><InfoFilled /></el-icon>
        <span>启用后AI可调用对应服务器的运维工具</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Warning, InfoFilled, Connection, Close, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

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
    const response = await axios.get('/api/v2/mcp/servers/status')
    servers.value = response.data.servers.map(server => ({
      ...server,
      switching: false, // 添加切换状态
      connecting: false, // 添加连接状态
      disconnecting: false, // 添加断开状态
      reconnecting: false // 添加重连状态
    }))
    
    emit('servers-changed', {
      servers: servers.value,
      total_enabled: response.data.total_enabled,
      total_connected: response.data.total_connected
    })
  } catch (e) {
    console.error('加载MCP服务器失败:', e)
    error.value = e.response?.data?.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

// 刷新服务器状态（不显示loading）
const refreshServerStatus = async () => {
  try {
    const response = await axios.get('/api/v2/mcp/servers/status')
    if (response.data.servers) {
      // 保持当前的状态，只更新服务器数据
      const currentStates = {}
      servers.value.forEach(server => {
        currentStates[server.name] = {
          switching: server.switching,
          connecting: server.connecting,
          disconnecting: server.disconnecting,
          reconnecting: server.reconnecting
        }
      })
      
      servers.value = response.data.servers.map(server => ({
        ...server,
        switching: currentStates[server.name]?.switching || false,
        connecting: currentStates[server.name]?.connecting || false,
        disconnecting: currentStates[server.name]?.disconnecting || false,
        reconnecting: currentStates[server.name]?.reconnecting || false
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

// 连接服务器
const connectServer = async (serverName) => {
  const server = servers.value.find(s => s.name === serverName)
  if (!server) return
  
  server.connecting = true
  
  try {
    const response = await axios.post(`/api/v2/mcp/servers/${serverName}/connect`)
    
    ElMessage.success(response.data.message)
    
    // 刷新状态
    await refreshServerStatus()
    
  } catch (e) {
    console.error('连接服务器失败:', e)
    ElMessage.error(e.response?.data?.detail || e.message || '连接失败')
  } finally {
    server.connecting = false
  }
}

// 断开服务器连接
const disconnectServer = async (serverName) => {
  const server = servers.value.find(s => s.name === serverName)
  if (!server) return
  
  server.disconnecting = true
  
  try {
    const response = await axios.post(`/api/v2/mcp/servers/${serverName}/disconnect`)
    
    ElMessage.success(response.data.message)
    
    // 刷新状态
    await refreshServerStatus()
    
  } catch (e) {
    console.error('断开连接失败:', e)
    ElMessage.error(e.response?.data?.detail || e.message || '断开连接失败')
  } finally {
    server.disconnecting = false
  }
}

// 重新连接服务器
const reconnectServer = async (serverName) => {
  const server = servers.value.find(s => s.name === serverName)
  if (!server) return
  
  server.reconnecting = true
  
  try {
    const response = await axios.post(`/api/v2/mcp/servers/${serverName}/reconnect`)
    
    ElMessage.success(response.data.message)
    
    // 刷新状态
    await refreshServerStatus()
    
  } catch (e) {
    console.error('重连服务器失败:', e)
    ElMessage.error(e.response?.data?.detail || e.message || '重连失败')
  } finally {
    server.reconnecting = false
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
    // 1. 首先更新配置（启用/禁用）
    const configResponse = await axios.post(`/api/v2/mcp/config/servers/${serverName}/toggle`)
    
    // 2. 根据启用状态自动连接或断开
    if (enabled) {
      // 启用时自动连接
      console.log(`🔌 服务器 ${serverName} 已启用，正在自动连接...`)
      server.connecting = true
      
      try {
        const connectResponse = await axios.post(`/api/v2/mcp/servers/${serverName}/connect`)
        console.log(`✅ 服务器 ${serverName} 自动连接成功`)
      } catch (connectError) {
        console.warn(`⚠️ 服务器 ${serverName} 自动连接失败:`, connectError)
        // 连接失败不影响配置更新，只是警告
      } finally {
        server.connecting = false
      }
    } else {
      // 禁用时自动断开
      console.log(`🔌 服务器 ${serverName} 已禁用，正在自动断开连接...`)
      server.disconnecting = true
      
      try {
        const disconnectResponse = await axios.post(`/api/v2/mcp/servers/${serverName}/disconnect`)
        console.log(`✅ 服务器 ${serverName} 自动断开成功`)
      } catch (disconnectError) {
        console.warn(`⚠️ 服务器 ${serverName} 自动断开失败:`, disconnectError)
        // 断开失败不影响配置更新，只是警告
      } finally {
        server.disconnecting = false
      }
    }
    
    // 3. 刷新服务器状态和工具列表
    await refreshServerStatus()
    
    // 4. 通知父组件刷新工具列表
    emit('server-toggled', {
      server: serverName,
      enabled: enabled,
      server_info: server,
      should_refresh_tools: true // 标记需要刷新工具列表
    })
    
    ElMessage.success(`${configResponse.data.message}${enabled ? '并已自动连接' : '并已自动断开'}`)
    
  } catch (e) {
    console.error('切换服务器状态失败:', e)
    // 回滚状态
    server.enabled = originalEnabled
    ElMessage.error(e.response?.data?.detail || e.message || '操作失败')
    
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
    const response = await axios.post('/api/v2/mcp/servers/batch-toggle', {
      servers: serverStates
    })
    
    ElMessage.success(`已${targetState ? '启用' : '禁用'}所有MCP服务器`)
    
    // 操作成功后，立即刷新服务器状态以获取最新的连接状态
    await refreshServerStatus()
    
  } catch (e) {
    console.error('批量切换失败:', e)
    // 回滚状态
    servers.value.forEach(server => {
      server.enabled = originalStates[server.name]
    })
    ElMessage.error(e.response?.data?.detail || e.message || '批量操作失败')
    
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
  connectServer,
  disconnectServer,
  reconnectServer,
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
  color: var(--el-text-color-secondary);
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
  background: var(--el-bg-color-page);
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 13px;
}

.status-text {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.connected-info {
  color: var(--el-color-success);
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
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  transition: all 0.2s;
  gap: 8px; /* 添加间距，防止内容挤压 */
  min-width: 0; /* 允许flex子元素收缩 */
}

.server-switch-item:hover {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.server-switch-item.enabled {
  border-color: var(--el-color-success-light-5);
  background: var(--el-color-success-light-9);
}

.server-switch-item.connected {
  border-color: var(--el-color-success);
}

.server-switch-item.disconnected {
  border-color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
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
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.server-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.server-type {
  background: var(--el-color-info-light-8);
  color: var(--el-color-info);
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.tools-count {
  color: var(--el-color-primary);
}

.server-address {
  font-family: monospace;
}

.server-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  min-width: 0; /* 允许flex子元素收缩 */
  flex-shrink: 1; /* 允许收缩 */
}

.connection-controls {
  display: flex;
  gap: 4px;
  flex-wrap: wrap; /* 允许按钮换行 */
  justify-content: flex-end;
  max-width: 100%; /* 限制最大宽度 */
}

.connection-controls .el-button {
  padding: 4px 8px;
  font-size: 12px;
  flex-shrink: 1; /* 允许按钮收缩 */
  white-space: nowrap; /* 防止按钮文字换行 */
}

.mcp-tooltip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.mcp-tooltip .el-icon {
  color: var(--el-color-info);
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
