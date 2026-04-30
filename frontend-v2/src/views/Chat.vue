<template>
  <div class="chat-page chat-cockpit-page">
    <section class="chat-command-strip">
      <div class="command-copy">
        <p class="eyebrow">AI MISSION CONTROL</p>
        <h1>智能对话</h1>
        <span>{{ activeMissionLine }}</span>
      </div>

      <div class="command-status">
        <div class="command-actions">
          <el-tooltip :content="sidebarVisible ? '收起历史' : '展开历史'" placement="bottom">
            <el-button size="small" circle @click="toggleSidebar">
              <el-icon><Burger v-if="!sidebarVisible" /><Close v-else /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="新建诊断" placement="bottom">
            <el-button size="small" circle @click="createNewChat">
              <el-icon><ChatDotSquare /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="检索证据" placement="bottom">
            <el-button size="small" circle @click="showMessageSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </el-tooltip>
          <el-dropdown @command="handleMenuCommand">
            <el-button size="small" circle>
              <el-icon><Setting /></el-icon>
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
        <div class="status-pill" :class="{ live: chatStore.isConnected, warning: chatStore.isStreaming }">
          <span class="status-dot"></span>
          {{ connectionStatusText }}
        </div>
        <div class="status-pill">
          <span class="status-dot cyan"></span>
          Local MCP
        </div>
        <div class="status-pill">
          <span class="status-dot amber"></span>
          只读优先
        </div>
      </div>
    </section>

    <div class="chat-body cockpit-grid" :class="{ 'history-collapsed': !sidebarVisible }">
      <!-- 历史记录侧边栏 -->
      <el-aside
        :width="sidebarVisible ? '280px' : '0px'"
        class="history-sidebar cockpit-panel"
        :class="{ 'is-hidden': !sidebarVisible }"
      >
        <div v-if="sidebarVisible" class="sidebar-content">
          <ChatHistory
            @session-switched="handleSessionSwitch"
            @collapse="collapseHistorySidebar"
          />
        </div>
      </el-aside>

      <!-- 主聊天区域 -->
      <el-main class="chat-main cockpit-panel">
        <div class="mission-head">
          <div>
            <p class="eyebrow">MISSION STREAM</p>
            <h2>AI Mission Stream</h2>
            <span>把运维问题转成可审计的诊断链路：先读状态，再列证据，最后给下一步。</span>
          </div>
          <div class="mission-stats">
            <div class="mission-stat">
              <strong>{{ toolBusCount }}</strong>
              <span>Tools</span>
            </div>
            <div class="mission-stat">
              <strong>{{ riskyOpsCount }}</strong>
              <span>Risky Ops</span>
            </div>
            <div class="mission-stat">
              <strong>{{ confidenceScore }}</strong>
              <span>Confidence</span>
            </div>
          </div>
        </div>
        <StreamChat
          :auto-connect="true"
          :enable-tools="chatSettings.enableTools"
          :key="currentSessionKey"
          class="stream-chat-container"
        />
      </el-main>

      <aside class="context-sidebar cockpit-panel">
        <div class="context-head">
          <div>
            <p class="eyebrow">CONTEXT STACK</p>
            <h3>上下文与工具总线</h3>
          </div>
          <el-button size="small" circle @click="refreshStorageInfo">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>

        <div class="context-body">
          <section class="context-card">
            <h4>当前范围</h4>
            <div class="mini-grid">
              <div class="mini-tile">
                <span>Session</span>
                <strong>{{ currentSessionName }}</strong>
              </div>
              <div class="mini-tile">
                <span>Messages</span>
                <strong>{{ chatStore.messages.length }}</strong>
              </div>
              <div class="mini-tile">
                <span>Mode</span>
                <strong>{{ chatSettings.enableTools ? 'Tools On' : 'Chat Only' }}</strong>
              </div>
              <div class="mini-tile">
                <span>Audit</span>
                <strong>On</strong>
              </div>
            </div>
          </section>

          <section class="context-card">
            <h4>工具状态</h4>
            <div class="runbook-stack">
              <div class="runbook-item">
                <span class="status-dot"></span>
                K8s / ECS Builtin MCP ready
              </div>
              <div class="runbook-item">
                <span class="status-dot cyan"></span>
                {{ chatStore.toolCalls.length }} tool calls in history
              </div>
              <div class="runbook-item">
                <span class="status-dot amber"></span>
                变更动作需要二次确认
              </div>
            </div>
          </section>

          <section class="context-card">
            <h4>快捷动作</h4>
            <div class="quick-actions">
              <button @click="createNewChat">新建诊断</button>
              <button @click="showMessageSearch">检索证据</button>
              <button @click="settingsDialogVisible = true">工具策略</button>
            </div>
          </section>
        </div>
      </aside>
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
const currentSessionName = computed(() => chatStore.currentSession?.title || '未命名诊断')
const activeMissionLine = computed(() => {
  if (chatStore.isStreaming) return 'AI 正在读取事件、日志和工具结果'
  if (chatStore.hasMessages) return `当前会话：${currentSessionName.value}`
  return '选择一个任务，开始一次可审计的运维诊断'
})
const toolBusCount = computed(() => chatSettings.value.enableTools ? 21 : 0)
const riskyOpsCount = computed(() => (chatStore.toolCalls || []).filter((item) => item?.risk === 'high').length)
const confidenceScore = computed(() => {
  if (!chatStore.isConnected) return '0%'
  if (chatStore.isStreaming) return '...'
  return chatStore.hasMessages ? '92%' : 'READY'
})

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

const collapseHistorySidebar = () => {
  sidebarVisible.value = false
  chatSettings.value.showSidebar = false
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
  /* 更偏企业风的浅色背景 */
  background: var(--background-page, #f6f8fa);
}

.chat-header-card {
  margin: 10px 12px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.chat-header-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.chat-header-card :deep(.el-card__body) {
  padding: 12px 14px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-toggle {
  padding: 6px;
  font-size: 16px;
  border-radius: 8px;
}

.page-title {
  font-size: 18px;
  font-weight: 650;
  color: #111827;
  margin: 0;
  letter-spacing: 0.2px;
}

.chat-status {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chat-status :deep(.el-tag) {
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
}

.chat-status :deep(.el-tag--success) {
  border-color: rgba(16, 185, 129, 0.25);
  background: rgba(16, 185, 129, 0.06);
  color: #065f46;
}

.chat-status :deep(.el-tag--warning) {
  border-color: rgba(245, 158, 11, 0.25);
  background: rgba(245, 158, 11, 0.06);
  color: #92400e;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions :deep(.el-button) {
  border-radius: 10px;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.history-sidebar {
  background: var(--background-page, #f6f8fa);
  border-right: 1px solid #e5e7eb;
  box-shadow: none;
  transition: width 0.3s ease;
  overflow: hidden;
}

.history-sidebar.is-hidden {
  border-right: none;
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
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 2px solid #f093fb;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(240, 147, 251, 0.2);
  border-color: #f5576c;
}

.stat-label {
  font-size: 12px;
  color: #9333ea;
  margin-bottom: 4px;
  font-weight: 600;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #ec4899;
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

/* Cockpit redesign overrides */
.chat-cockpit-page {
  --cockpit-bg: #070b0e;
  --cockpit-panel: #0e1418;
  --cockpit-panel-2: #111a1f;
  --cockpit-border: #26343b;
  --cockpit-border-strong: #31505a;
  --cockpit-text: #edf7f7;
  --cockpit-muted: #8ea0a8;
  --cockpit-cyan: #35d9f4;
  --cockpit-green: #4ee6a0;
  --cockpit-amber: #ffbe55;
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 14px;
  padding: 0;
  background:
    linear-gradient(180deg, rgba(53, 217, 244, 0.06), transparent 38%),
    radial-gradient(circle at 84% 18%, rgba(78, 230, 160, 0.08), transparent 28%),
    var(--cockpit-bg) !important;
  color: var(--cockpit-text);
}

.chat-command-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 92px;
  padding: 16px 18px;
  border: 1px solid var(--cockpit-border);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(53, 217, 244, 0.08), rgba(17, 26, 31, 0.94) 40%),
    var(--cockpit-panel);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.command-copy {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 5px;
  color: var(--cockpit-cyan);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.command-copy h1 {
  margin: 0 0 5px;
  color: var(--cockpit-text);
  font-size: 25px;
  line-height: 1.15;
  letter-spacing: 0;
}

.command-copy span,
.mission-head span {
  display: block;
  color: var(--cockpit-muted);
  font-size: 13px;
  line-height: 1.55;
}

.command-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.command-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding-right: 6px;
  margin-right: 2px;
  border-right: 1px solid var(--cockpit-border);
}

.command-actions :deep(.el-button) {
  border-color: var(--cockpit-border) !important;
  background: #0a1114 !important;
  color: var(--cockpit-cyan) !important;
}

.command-actions :deep(.el-button:hover) {
  border-color: var(--cockpit-cyan) !important;
  background: rgba(53, 217, 244, 0.12) !important;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid var(--cockpit-border);
  border-radius: 999px;
  background: rgba(8, 13, 16, 0.82);
  color: #bed0d6;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.status-pill.live {
  border-color: rgba(78, 230, 160, 0.35);
  color: var(--cockpit-green);
}

.status-pill.warning {
  border-color: rgba(255, 190, 85, 0.45);
  color: var(--cockpit-amber);
}

.status-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 999px;
  background: var(--cockpit-green);
  box-shadow: 0 0 12px rgba(78, 230, 160, 0.85);
}

.status-dot.cyan {
  background: var(--cockpit-cyan);
  box-shadow: 0 0 12px rgba(53, 217, 244, 0.85);
}

.status-dot.amber {
  background: var(--cockpit-amber);
  box-shadow: 0 0 12px rgba(255, 190, 85, 0.75);
}

.chat-cockpit-page .cockpit-grid {
  display: grid !important;
  grid-template-columns: 280px minmax(420px, 1fr) 300px;
  gap: 14px;
  min-height: 0;
  overflow: hidden;
  border: 0 !important;
  background: transparent !important;
}

.chat-cockpit-page .cockpit-grid.history-collapsed {
  grid-template-columns: minmax(420px, 1fr) 300px;
}

.chat-cockpit-page .history-sidebar.is-hidden {
  display: none !important;
}

.chat-cockpit-page .cockpit-panel {
  min-height: 0;
  border: 1px solid var(--cockpit-border) !important;
  border-radius: 8px !important;
  background: rgba(14, 20, 24, 0.96) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

.chat-cockpit-page .history-sidebar {
  width: auto !important;
  border-right: 1px solid var(--cockpit-border) !important;
}

.chat-cockpit-page .sidebar-content {
  width: 280px !important;
  height: 100%;
}

.chat-cockpit-page .chat-main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-width: 0;
  padding: 0 !important;
}

.mission-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--cockpit-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0));
}

.mission-head h2,
.context-head h3,
.context-card h4 {
  margin: 0;
  color: var(--cockpit-text);
  letter-spacing: 0;
}

.mission-head h2 {
  margin-bottom: 4px;
  font-size: 18px;
}

.mission-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(72px, 1fr));
  gap: 8px;
  flex: 0 0 250px;
}

.mission-stat {
  min-height: 50px;
  padding: 8px 10px;
  border: 1px solid var(--cockpit-border);
  border-radius: 8px;
  background: rgba(7, 11, 14, 0.76);
}

.mission-stat strong {
  display: block;
  color: var(--cockpit-cyan);
  font-size: 18px;
  line-height: 1.1;
}

.mission-stat span {
  margin-top: 4px;
  color: var(--cockpit-muted);
  font-size: 11px;
  text-transform: uppercase;
}

.chat-cockpit-page .stream-chat-container {
  min-height: 0;
  height: 100%;
}

.context-sidebar {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.context-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--cockpit-border);
}

.context-head h3 {
  font-size: 15px;
}

.context-head :deep(.el-button) {
  border-color: var(--cockpit-border);
  background: #0a1114;
  color: var(--cockpit-cyan);
}

.context-body {
  min-height: 0;
  overflow: auto;
  padding: 14px;
}

.context-card {
  padding: 14px;
  border: 1px solid var(--cockpit-border);
  border-radius: 8px;
  background: rgba(7, 11, 14, 0.62);
}

.context-card + .context-card {
  margin-top: 12px;
}

.context-card h4 {
  margin-bottom: 12px;
  font-size: 13px;
}

.mini-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.mini-tile {
  min-width: 0;
  padding: 10px;
  border-radius: 8px;
  background: rgba(17, 26, 31, 0.9);
  border: 1px solid rgba(49, 80, 90, 0.55);
}

.mini-tile span {
  display: block;
  margin-bottom: 4px;
  color: var(--cockpit-muted);
  font-size: 11px;
}

.mini-tile strong {
  display: block;
  overflow: hidden;
  color: var(--cockpit-text);
  font-size: 13px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.runbook-stack {
  display: grid;
  gap: 9px;
}

.runbook-item {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 32px;
  color: #c6d6dc;
  font-size: 12px;
  line-height: 1.4;
}

.quick-actions {
  display: grid;
  gap: 8px;
}

.quick-actions button {
  width: 100%;
  height: 34px;
  border: 1px solid var(--cockpit-border-strong);
  border-radius: 8px;
  background: rgba(53, 217, 244, 0.08);
  color: var(--cockpit-cyan);
  font-weight: 800;
  cursor: pointer;
}

.quick-actions button:hover {
  border-color: var(--cockpit-cyan);
  background: rgba(53, 217, 244, 0.14);
}

.chat-cockpit-page :deep(.chat-history) {
  background: transparent;
  color: var(--cockpit-text);
}

.chat-cockpit-page :deep(.history-header-card),
.chat-cockpit-page :deep(.search-section-card),
.chat-cockpit-page :deep(.session-card) {
  border-color: var(--cockpit-border) !important;
  border-radius: 8px !important;
  background: rgba(7, 11, 14, 0.55) !important;
  color: var(--cockpit-text);
  box-shadow: none !important;
}

.chat-cockpit-page :deep(.session-card-active) {
  border-color: rgba(53, 217, 244, 0.72) !important;
  background: rgba(53, 217, 244, 0.12) !important;
}

.chat-cockpit-page :deep(.session-title),
.chat-cockpit-page :deep(.history-title h3),
.chat-cockpit-page :deep(.storage-info) {
  color: var(--cockpit-text) !important;
}

.chat-cockpit-page :deep(.session-meta),
.chat-cockpit-page :deep(.history-title p),
.chat-cockpit-page :deep(.el-empty__description p) {
  color: var(--cockpit-muted) !important;
}

.chat-cockpit-page :deep(.el-input__wrapper) {
  border-color: var(--cockpit-border) !important;
  background: #0a1114 !important;
  box-shadow: none !important;
}

.chat-cockpit-page :deep(.el-input__inner) {
  color: var(--cockpit-text) !important;
}

@media (max-width: 1280px) {
  .chat-cockpit-page .cockpit-grid {
    grid-template-columns: 220px minmax(0, 1fr) 230px;
  }

  .chat-cockpit-page .sidebar-content {
    width: 220px !important;
  }

  .mission-stats {
    flex-basis: 218px;
  }

  .context-body {
    padding: 12px;
  }

  .context-card {
    padding: 12px;
  }

  .mini-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 940px) {
  .chat-cockpit-page .cockpit-grid,
  .chat-cockpit-page .cockpit-grid.history-collapsed {
    grid-template-columns: minmax(0, 1fr);
  }

  .chat-cockpit-page .history-sidebar {
    position: fixed;
    inset: 76px auto 18px 88px;
    z-index: 40;
    display: block !important;
    width: 280px !important;
    max-width: calc(100vw - 108px);
  }

  .chat-cockpit-page .history-sidebar.is-hidden {
    display: none !important;
  }

  .context-sidebar {
    display: none;
  }

  .mission-head {
    align-items: stretch;
    flex-direction: column;
  }

  .mission-stats {
    flex: 1 1 auto;
    width: 100%;
  }
}

@media (max-width: 760px) {
  .chat-cockpit-page {
    gap: 10px;
  }

  .chat-command-strip {
    align-items: flex-start;
    flex-direction: column;
    min-height: 0;
  }

  .command-status {
    justify-content: flex-start;
  }

  .command-actions {
    width: 100%;
    padding-right: 0;
    margin-right: 0;
    border-right: 0;
  }

  .mission-stats {
    grid-template-columns: 1fr;
  }
}
</style>
