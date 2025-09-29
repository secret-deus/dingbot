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
import { Loading, Warning, InfoFilled } from '@element-plus/icons-vue'
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
      switching: false // 添加切换状态
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

const toggleServer = async (serverName, enabled) => {
  const server = servers.value.find(s => s.name === serverName)
  if (!server) return
  
  server.switching = true
  
  try {
    const response = await axios.post(`/api/v2/mcp/config/servers/${serverName}/toggle`)
    
    // 更新本地状态
    server.enabled = enabled
    
    ElMessage.success(response.data.message)
    
    emit('server-toggled', {
      server: serverName,
      enabled: enabled,
      server_info: server
    })
    
  } catch (e) {
    console.error('切换服务器状态失败:', e)
    // 回滚状态
    server.enabled = !enabled
    ElMessage.error(e.response?.data?.detail || e.message || '操作失败')
  } finally {
    server.switching = false
  }
}

const toggleAll = async () => {
  const targetState = !allEnabled.value
  const serverStates = {}
  
  servers.value.forEach(server => {
    serverStates[server.name] = targetState
    server.switching = true
  })
  
  try {
    const response = await axios.post('/api/v2/mcp/servers/batch-toggle', {
      servers: serverStates
    })
    
    // 更新本地状态
    servers.value.forEach(server => {
      server.enabled = targetState
      server.switching = false
    })
    
    ElMessage.success(`已${targetState ? '启用' : '禁用'}所有MCP服务器`)
    
    emit('servers-changed', {
      servers: servers.value,
      total_enabled: targetState ? servers.value.length : 0,
      total_connected: connectedCount.value
    })
    
  } catch (e) {
    console.error('批量切换失败:', e)
    // 回滚状态
    servers.value.forEach(server => {
      server.switching = false
    })
    ElMessage.error(e.response?.data?.detail || e.message || '批量操作失败')
  }
}

// 暴露方法给父组件
defineExpose({
  loadServers,
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
  align-items: center;
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
