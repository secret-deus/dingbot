<template>
  <div class="chat-page">
    <div class="chat-header">
      <div class="header-left">
        <el-button 
          type="text" 
          @click="toggleSidebar"
          class="sidebar-toggle"
        >
          <el-icon><Burger v-if="!sidebarVisible" /><Close v-else /></el-icon>
        </el-button>
        
        <h1 class="page-title">智能对话</h1>
        <div class="chat-status">
          <el-tag :type="connectionStatusType" size="small">
            <el-icon><Connection /></el-icon>
            {{ connectionStatusText }}
          </el-tag>
          <el-tag v-if="chatStats.totalMessages > 0" type="info" size="small">
            {{ chatStats.totalMessages }} 条消息
          </el-tag>
          <el-tag v-if="chatStore.currentSession" type="success" size="small">
            当前: {{ chatStore.currentSession.title }}
          </el-tag>
          <el-tag v-if="storageInfo.needsCleanup" type="warning" size="small">
            <el-icon><Warning /></el-icon>
            存储空间不足
          </el-tag>
        </div>
      </div>
      
      <div class="header-actions">
        <el-button 
          type="primary" 
          size="small"
          @click="createNewChat"
        >
          <el-icon><ChatDotSquare /></el-icon>
          新建对话
        </el-button>
        
        <el-button 
          size="small"
          @click="showMessageSearch"
        >
          <el-icon><Search /></el-icon>
          搜索消息
        </el-button>
        
        <el-dropdown @command="handleMenuCommand">
          <el-button size="small">
            聊天管理
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="clearCurrent" :disabled="!chatStore.hasMessages">
                <el-icon><Refresh /></el-icon>
                清空当前对话
              </el-dropdown-item>
              <el-dropdown-item command="exportCurrent" :disabled="!chatStore.hasMessages">
                <el-icon><Download /></el-icon>
                导出当前对话
              </el-dropdown-item>
              <el-dropdown-item command="importChat">
                <el-icon><Upload /></el-icon>
                导入对话
              </el-dropdown-item>
              <el-dropdown-item command="storageManagement">
                <el-icon><FolderOpened /></el-icon>
                存储管理
              </el-dropdown-item>
              <el-dropdown-item divided command="settings">
                <el-icon><Setting /></el-icon>
                聊天设置
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="chat-body">
      <!-- 历史记录侧边栏 -->
      <el-aside 
        :width="sidebarVisible ? '350px' : '0px'"
        class="history-sidebar"
      >
        <div v-if="sidebarVisible" class="sidebar-content">
          <ChatHistory @session-switched="handleSessionSwitch" />
        </div>
      </el-aside>
      
      <!-- 主聊天区域 -->
      <el-main class="chat-main">
        <StreamChat 
          :auto-connect="true"
          :enable-tools="chatSettings.enableTools"
          :key="currentSessionKey"
          class="stream-chat-container"
        />
      </el-main>
    </div>

    <!-- 聊天设置对话框 -->
    <el-dialog
      v-model="settingsDialogVisible"
      title="聊天设置"
      width="400px"
      :before-close="handleSettingsClose"
    >
      <el-form :model="chatSettings" label-width="120px">
        <el-form-item label="启用工具调用">
          <el-switch v-model="chatSettings.enableTools" />
          <div class="setting-help">
            启用后，AI可以调用K8s工具执行实际操作
          </div>
        </el-form-item>
        
        <el-form-item label="自动滚动">
          <el-switch v-model="chatSettings.autoScroll" />
          <div class="setting-help">
            新消息到达时自动滚动到底部
          </div>
        </el-form-item>
        
        <el-form-item label="显示时间戳">
          <el-switch v-model="chatSettings.showTimestamp" />
          <div class="setting-help">
            在消息旁显示发送时间
          </div>
        </el-form-item>
        
        <el-form-item label="最大消息数">
          <el-input-number 
            v-model="chatSettings.maxMessages" 
            :min="50" 
            :max="1000" 
            :step="50"
          />
          <div class="setting-help">
            超过此数量时自动清理旧消息
          </div>
        </el-form-item>
        
        <el-form-item label="显示历史侧栏">
          <el-switch v-model="chatSettings.showSidebar" />
          <div class="setting-help">
            显示对话历史记录侧边栏
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="resetSettings">重置</el-button>
          <el-button type="primary" @click="saveSettings">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 导入文件隐藏input -->
    <input
      ref="fileInput"
      type="file"
      accept=".json"
      style="display: none"
      @change="handleFileImport"
    />
    
    <!-- 存储管理对话框 -->
    <el-dialog
      v-model="storageDialogVisible"
      title="存储管理"
      width="600px"
      :before-close="handleStorageDialogClose"
    >
      <div class="storage-management">
        <!-- 存储状态概览 -->
        <el-card class="storage-overview" shadow="never">
          <template #header>
            <div class="card-header">
              <span>存储状态</span>
              <el-button size="small" @click="refreshStorageInfo">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <div class="storage-stats">
            <div class="stat-item">
              <div class="stat-label">存储类型</div>
              <div class="stat-value">{{ storageInfo.type }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">总会话数</div>
              <div class="stat-value">{{ storageInfo.totalSessions }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">总消息数</div>
              <div class="stat-value">{{ storageInfo.totalMessages }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">数据大小</div>
              <div class="stat-value">{{ storageInfo.formattedDataSize }}</div>
            </div>
          </div>
          
          <!-- 存储配额进度条 -->
          <div class="storage-quota" v-if="storageInfo.quota.available > 0">
            <div class="quota-label">存储使用情况</div>
            <el-progress 
              :percentage="storageInfo.quota.percentage" 
              :color="getQuotaColor(storageInfo.quota.percentage)"
              :show-text="true"
            />
            <div class="quota-info">
              已使用: {{ formatBytes(storageInfo.quota.used) }} / 
              总容量: {{ formatBytes(storageInfo.quota.available) }}
            </div>
          </div>
        </el-card>

        <!-- 存储操作 -->
        <el-card class="storage-actions" shadow="never">
          <template #header>
            <span>存储操作</span>
          </template>
          
          <div class="action-buttons">
            <el-button 
              type="warning" 
              @click="performCleanup"
              :loading="cleanupLoading"
              :disabled="storageInfo.totalSessions <= 5"
            >
              <el-icon><Delete /></el-icon>
              清理旧会话
            </el-button>
            
            <el-button 
              type="info" 
              @click="compressData"
              :loading="compressLoading"
            >
              <el-icon><FolderOpened /></el-icon>
              压缩数据
            </el-button>
            
            <el-button 
              type="success" 
              @click="performHealthCheck"
              :loading="healthCheckLoading"
            >
              <el-icon><Setting /></el-icon>
              健康检查
            </el-button>
          </div>
          
          <!-- 清理选项 -->
          <el-collapse v-model="activeCollapse" class="cleanup-options">
            <el-collapse-item title="清理选项" name="cleanup">
              <el-form :model="cleanupOptions" label-width="120px" size="small">
                <el-form-item label="清理策略">
                  <el-select v-model="cleanupOptions.strategy">
                    <el-option label="最近最少使用" value="lru" />
                    <el-option label="按创建时间" value="oldest" />
                    <el-option label="按大小" value="size-based" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="最大会话数">
                  <el-input-number 
                    v-model="cleanupOptions.maxSessions" 
                    :min="5" 
                    :max="100" 
                  />
                </el-form-item>
                
                <el-form-item label="保留天数">
                  <el-input-number 
                    v-model="cleanupOptions.maxAgeDays" 
                    :min="1" 
                    :max="365" 
                  />
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <!-- 操作结果 -->
        <el-card v-if="lastOperationResult" class="operation-result" shadow="never">
          <template #header>
            <span>操作结果</span>
          </template>
          
          <div class="result-content">
            <el-alert
              :title="lastOperationResult.title"
              :type="lastOperationResult.type"
              :description="lastOperationResult.description"
              show-icon
              :closable="false"
            />
            
            <div v-if="lastOperationResult.details" class="result-details">
              <h4>详细信息:</h4>
              <ul>
                <li v-for="detail in lastOperationResult.details" :key="detail">
                  {{ detail }}
                </li>
              </ul>
            </div>
          </div>
        </el-card>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="storageDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 消息搜索组件 -->
    <MessageSearch 
      v-model="searchDialogVisible"
      @jump-to-message="handleScrollToMessage"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ChatDotSquare, ArrowDown, Download, Upload, Setting, Connection,
  Refresh, Burger, Close, Search, Warning, FolderOpened, Delete
} from '@element-plus/icons-vue'
import StreamChat from '@/components/StreamChat.vue'
import ChatHistory from '@/components/ChatHistory.vue'
import MessageSearch from '@/components/MessageSearch.vue'
import { useChatStore } from '@/stores/chat'

// 响应式数据
const chatStore = useChatStore()
const settingsDialogVisible = ref(false)
const searchDialogVisible = ref(false)
const fileInput = ref(null)
const sidebarVisible = ref(true)
const currentSessionKey = ref(0) // 用于强制重新渲染StreamChat

// 聊天设置
const chatSettings = ref({
  enableTools: true,
  autoScroll: true,
  showTimestamp: true,
  maxMessages: 200,
  showSidebar: true
})

// 默认设置
const defaultSettings = {
  enableTools: true,
  autoScroll: true,
  showTimestamp: true,
  maxMessages: 200,
  showSidebar: true
}

// 计算属性
const connectionStatusType = computed(() => {
  if (!chatStore.isConnected) return 'danger'
  if (chatStore.isStreaming) return 'warning'
  return 'success'
})

const connectionStatusText = computed(() => {
  if (!chatStore.isConnected) return '未连接'
  if (chatStore.isStreaming) return '对话中'
  return '已连接'
})

const chatStats = computed(() => chatStore.getSessionStats)

// 存储信息
const storageInfo = ref({
  type: 'localStorage',
  isAvailable: true,
  quota: { used: 0, available: 0, percentage: 0, needsCleanup: false },
  hasFallback: false,
  totalSessions: 0,
  totalMessages: 0,
  estimatedDataSize: 0,
  formattedDataSize: '0 B',
  needsCleanup: false
})

// 存储管理对话框
const storageDialogVisible = ref(false)
const cleanupLoading = ref(false)
const compressLoading = ref(false)
const healthCheckLoading = ref(false)
const activeCollapse = ref([])
const lastOperationResult = ref(null)

// 清理选项
const cleanupOptions = ref({
  strategy: 'lru',
  maxSessions: 30,
  maxAgeDays: 30
})

// 方法
const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value
  chatSettings.value.showSidebar = sidebarVisible.value
  saveSettings()
}

const handleSessionSwitch = (sessionId) => {
  // 强制重新渲染StreamChat组件以更新消息
  currentSessionKey.value++
  ElMessage.success('已切换到选中的对话')
}

const createNewChat = () => {
  const session = chatStore.createSession()
  currentSessionKey.value++
  ElMessage.success('已创建新对话')
}

const showMessageSearch = () => {
  searchDialogVisible.value = true
}

const handleJumpToMessage = (jumpInfo) => {
  // 如果需要切换会话，先切换
  if (jumpInfo.sessionId !== chatStore.currentSessionId) {
    chatStore.switchToSession(jumpInfo.sessionId)
    currentSessionKey.value++
  }
  
  // TODO: 实现跳转到具体消息的滚动功能
  // 这里可以通过 StreamChat 组件暴露的方法来滚动到指定消息
  ElMessage.success('已跳转到指定消息')
}

const handleMenuCommand = (command) => {
  switch (command) {
    case 'clearCurrent':
      clearCurrentChat()
      break
    case 'exportCurrent':
      exportCurrentChat()
      break
    case 'importChat':
      importChatHistory()
      break
    case 'storageManagement':
      showStorageManagement()
      break
    case 'settings':
      settingsDialogVisible.value = true
      break
  }
}

const clearCurrentChat = async () => {
  if (!chatStore.hasMessages) return
  
  try {
    await ElMessageBox.confirm(
      '确定要清空当前对话吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    chatStore.clearCurrentSession()
    currentSessionKey.value++
    ElMessage.success('当前对话已清空')
  } catch {
    // 用户取消
  }
}

const exportCurrentChat = () => {
  if (!chatStore.currentSessionId) {
    ElMessage.error('没有当前对话可导出')
    return
  }
  
  try {
    const data = chatStore.exportSession(chatStore.currentSessionId)
    if (!data) {
      ElMessage.error('导出失败，会话不存在')
      return
    }
    
    const dataStr = JSON.stringify(data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = `chat_current_${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    
    URL.revokeObjectURL(link.href)
    ElMessage.success('当前对话已导出')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出当前对话失败')
  }
}

const importChatHistory = () => {
  fileInput.value?.click()
}

const handleFileImport = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const chatData = JSON.parse(e.target.result)
      
      if (chatStore.importSessions(chatData)) {
        ElMessage.success('对话导入成功')
        currentSessionKey.value++
      } else {
        ElMessage.error('导入对话失败，请检查文件格式')
      }
    } catch (error) {
      console.error('导入失败:', error)
      ElMessage.error('导入对话失败，请检查文件格式')
    }
  }
  
  reader.readAsText(file)
  
  // 清空input值，允许重复选择同一文件
  event.target.value = ''
}

const handleSettingsClose = (done) => {
  saveSettings()
  done()
}

const saveSettings = () => {
  // 保存到localStorage
  localStorage.setItem('chatSettings', JSON.stringify(chatSettings.value))
  settingsDialogVisible.value = false
  
  // 应用侧栏设置
  sidebarVisible.value = chatSettings.value.showSidebar
  
  if (settingsDialogVisible.value === false) {
    ElMessage.success('设置已保存')
  }
}

const resetSettings = () => {
  chatSettings.value = { ...defaultSettings }
}

const loadSettings = () => {
  try {
    const saved = localStorage.getItem('chatSettings')
    if (saved) {
      const settings = JSON.parse(saved)
      chatSettings.value = { ...defaultSettings, ...settings }
      sidebarVisible.value = chatSettings.value.showSidebar
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    chatSettings.value = { ...defaultSettings }
  }
}

// 消息数量管理
const checkMessageLimit = () => {
  if (chatStore.messages.length > chatSettings.value.maxMessages) {
    const removeCount = chatStore.messages.length - chatSettings.value.maxMessages
    chatStore.messages.splice(0, removeCount)
    console.log(`已清理 ${removeCount} 条旧消息`)
  }
}

// 存储管理相关方法
const showStorageManagement = async () => {
  storageDialogVisible.value = true
  await refreshStorageInfo()
}

const refreshStorageInfo = async () => {
  try {
    const info = await chatStore.getStorageInfo()
    storageInfo.value = info
  } catch (error) {
    console.error('刷新存储信息失败:', error)
    ElMessage.error('获取存储信息失败')
  }
}

const performCleanup = async () => {
  try {
    cleanupLoading.value = true
    lastOperationResult.value = null
    
    const options = {
      maxSessions: cleanupOptions.value.maxSessions,
      maxAge: cleanupOptions.value.maxAgeDays * 24 * 60 * 60 * 1000,
      strategy: cleanupOptions.value.strategy
    }
    
    const result = await chatStore.cleanupOldSessions(options)
    
    if (result.success) {
      lastOperationResult.value = {
        title: '清理完成',
        type: 'success',
        description: `成功清理了 ${result.removedCount} 个旧会话`,
        details: [
          `清理策略: ${result.strategy}`,
          `剩余会话: ${result.remainingSessions} 个`,
          `清理时间: ${new Date().toLocaleString()}`
        ]
      }
      
      ElMessage.success(`清理完成，删除了 ${result.removedCount} 个旧会话`)
      await refreshStorageInfo()
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    console.error('清理失败:', error)
    lastOperationResult.value = {
      title: '清理失败',
      type: 'error',
      description: error.message,
      details: [`错误时间: ${new Date().toLocaleString()}`]
    }
    ElMessage.error('清理旧会话失败')
  } finally {
    cleanupLoading.value = false
  }
}

const compressData = async () => {
  try {
    compressLoading.value = true
    lastOperationResult.value = null
    
    const result = await chatStore.compressStorageData()
    
    if (result.success) {
      lastOperationResult.value = {
        title: '压缩完成',
        type: 'success',
        description: `压缩了 ${result.compressedCount} 条消息，节省了 ${result.formattedSavedBytes}`,
        details: [
          `压缩消息数: ${result.compressedCount}`,
          `节省空间: ${result.formattedSavedBytes}`,
          `压缩时间: ${new Date().toLocaleString()}`
        ]
      }
      
      ElMessage.success(`数据压缩完成，节省了 ${result.formattedSavedBytes}`)
      await refreshStorageInfo()
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    console.error('压缩失败:', error)
    lastOperationResult.value = {
      title: '压缩失败',
      type: 'error',
      description: error.message,
      details: [`错误时间: ${new Date().toLocaleString()}`]
    }
    ElMessage.error('数据压缩失败')
  } finally {
    compressLoading.value = false
  }
}

const performHealthCheck = async () => {
  try {
    healthCheckLoading.value = true
    lastOperationResult.value = null
    
    const result = await chatStore.performStorageHealthCheck()
    
    if (result.success) {
      const healthLevel = result.healthScore >= 90 ? 'success' : 
                         result.healthScore >= 70 ? 'warning' : 'error'
      
      lastOperationResult.value = {
        title: `健康检查完成 (评分: ${result.healthScore}/100)`,
        type: healthLevel,
        description: `检查了 ${result.totalSessions} 个会话，修复了 ${result.repairedSessions} 个问题`,
        details: [
          `健康评分: ${result.healthScore}/100`,
          `总会话数: ${result.totalSessions}`,
          `损坏会话: ${result.corruptedSessions}`,
          `修复会话: ${result.repairedSessions}`,
          `检查时间: ${new Date().toLocaleString()}`,
          ...result.fixes.map(fix => `修复: ${fix}`),
          ...result.recommendations.map(rec => `建议: ${rec}`)
        ]
      }
      
      ElMessage.success(`健康检查完成，评分: ${result.healthScore}/100`)
      await refreshStorageInfo()
    } else {
      throw new Error(result.error)
    }
  } catch (error) {
    console.error('健康检查失败:', error)
    lastOperationResult.value = {
      title: '健康检查失败',
      type: 'error',
      description: error.message,
      details: [`错误时间: ${new Date().toLocaleString()}`]
    }
    ElMessage.error('存储健康检查失败')
  } finally {
    healthCheckLoading.value = false
  }
}

const handleStorageDialogClose = (done) => {
  lastOperationResult.value = null
  done()
}

const getQuotaColor = (percentage) => {
  if (percentage < 60) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 消息搜索相关方法
const handleScrollToMessage = (messageId) => {
  const message = chatStore.messages.find(msg => msg.id === messageId)
  if (message) {
    // 找到消息后，滚动到消息所在位置
    try {
      const chatContainer = document.querySelector('.stream-chat-container')
      if (chatContainer) {
        const messageElement = document.getElementById(`message-${messageId}`)
        if (messageElement && messageElement.offsetTop !== undefined) {
          chatContainer.scrollTop = messageElement.offsetTop - 100 // 滚动到消息上方100px
        }
      }
    } catch (error) {
      console.warn('滚动到消息失败:', error)
    }
  }
}

// 生命周期
onMounted(async () => {
  // 加载设置
  loadSettings()
  
  // 加载聊天历史
  try {
    await chatStore.loadFromStorage()
    
    // 等待数据完全更新
    await nextTick()
    
    // 强制重新渲染StreamChat以显示加载的消息
    currentSessionKey.value++
    
  } catch (error) {
    console.error('聊天历史加载失败:', error)
    ElMessage.error('加载聊天历史失败，已创建新对话')
    currentSessionKey.value++
  }
})

// 监听消息变化，检查消息数量限制
watch(() => chatStore.messages.length, () => {
  checkMessageLimit()
})

// 监听设置变化
watch(chatSettings, (newSettings) => {
  // 实时保存设置
  localStorage.setItem('chatSettings', JSON.stringify(newSettings))
  
  // 应用侧栏设置
  if (newSettings.showSidebar !== sidebarVisible.value) {
    sidebarVisible.value = newSettings.showSidebar
  }
}, { deep: true })
</script>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.chat-header {
  background: white;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sidebar-toggle {
  padding: 8px;
  font-size: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.chat-status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.history-sidebar {
  background: white;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar-content {
  width: 350px;
  height: 100%;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.stream-chat-container {
  height: 100%;
}

/* 设置对话框样式 */
.setting-help {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 存储管理对话框样式 */
.storage-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.storage-overview {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.storage-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.storage-quota {
  margin-top: 16px;
}

.quota-label {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.quota-info {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  text-align: center;
}

.storage-actions {
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.cleanup-options {
  margin-top: 16px;
}

.operation-result {
  margin-top: 16px;
}

.result-content {
  padding: 16px 0;
}

.result-details {
  margin-top: 16px;
}

.result-details h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.result-details ul {
  margin: 0;
  padding-left: 20px;
}

.result-details li {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .history-sidebar {
    width: 300px !important;
  }
  
  .sidebar-content {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-left {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .chat-status {
    justify-content: flex-start;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .history-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 1000;
    width: 280px !important;
  }
  
  .sidebar-content {
    width: 280px;
  }
  
  .chat-main {
    margin-left: 0;
  }
}

@media (max-width: 480px) {
  .chat-header {
    padding: 8px 12px;
  }
  
  .page-title {
    font-size: 16px;
  }
  
  .chat-status {
    flex-direction: column;
    gap: 4px;
  }
}
</style> 