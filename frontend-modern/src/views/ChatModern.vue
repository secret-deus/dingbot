<template>
  <div class="modern-chat-page">
    <!-- 现代化头部 -->
    <header class="modern-chat-header">
      <div class="header-content">
        <div class="header-left">
          <button 
            @click="toggleSidebar"
            class="sidebar-toggle-btn"
            :class="{ 'active': sidebarVisible }"
          >
            <el-icon><Menu v-if="!sidebarVisible" /><Close v-else /></el-icon>
          </button>
          
          <div class="page-info">
            <h1 class="page-title">智能对话</h1>
            <div class="status-indicators">
              <div class="status-badge" :class="connectionStatusClass">
                <div class="status-dot"></div>
                <span>{{ connectionStatusText }}</span>
              </div>
              <div v-if="chatStats.totalMessages > 0" class="message-count">
                {{ chatStats.totalMessages }} 条消息
              </div>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <el-button 
            type="primary" 
            @click="createNewChat"
            class="modern-btn primary"
          >
            <el-icon><Plus /></el-icon>
            新建对话
          </el-button>
          
          <el-dropdown @command="handleMenuCommand" class="actions-dropdown">
            <el-button class="modern-btn secondary">
              <el-icon><Setting /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu class="modern-dropdown">
                <el-dropdown-item command="search">
                  <el-icon><Search /></el-icon>
                  搜索消息
                </el-dropdown-item>
                <el-dropdown-item command="export" :disabled="!chatStore.hasMessages">
                  <el-icon><Download /></el-icon>
                  导出对话
                </el-dropdown-item>
                <el-dropdown-item command="settings" divided>
                  <el-icon><Settings /></el-icon>
                  聊天设置
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="modern-chat-body">
      <!-- 侧边栏 -->
      <aside 
        class="modern-sidebar"
        :class="{ 'visible': sidebarVisible }"
      >
        <div class="sidebar-content">
          <ChatHistory @session-switched="handleSessionSwitch" />
        </div>
      </aside>

      <!-- 聊天主区域 -->
      <main class="modern-chat-main">
        <div class="chat-container">
          <!-- AI供应商选择器 -->
          <div class="provider-selector-modern">
            <div class="provider-header">
              <el-icon class="provider-icon"><Monitor /></el-icon>
              <span class="provider-label">AI 助手</span>
            </div>
            <div class="provider-options">
              <div 
                v-for="(provider, id) in availableProviders" 
                :key="id"
                :class="[
                  'provider-option',
                  { 'active': currentProvider === id },
                  { 'disabled': !provider.available }
                ]"
                @click="switchProvider(id)"
              >
                <div class="provider-avatar">{{ provider.icon || '🤖' }}</div>
                <div class="provider-details">
                  <div class="provider-name">{{ provider.name }}</div>
                  <div class="provider-model">{{ provider.model }}</div>
                </div>
                <div class="provider-status">
                  <div 
                    class="status-indicator" 
                    :class="{ 'online': provider.available }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 消息区域 -->
          <div class="messages-area" ref="messagesContainer">
            <!-- 欢迎界面 -->
                          <div v-if="!chatStore.hasMessages" class="welcome-screen">
              <div class="welcome-content">
                <div class="welcome-avatar">
                  <el-icon><Monitor /></el-icon>
                </div>
                <h2 class="welcome-title">钉钉K8s运维机器人</h2>
                <p class="welcome-description">
                  我是您的智能Kubernetes运维助手，可以帮助您管理集群、查看状态、执行运维操作。
                </p>
                <div class="quick-actions">
                  <h3 class="quick-actions-title">快速开始</h3>
                  <div class="action-cards">
                    <div 
                      v-for="example in exampleQuestions" 
                      :key="example.text"
                      class="action-card"
                      @click="setInputMessage(example.text)"
                    >
                      <el-icon class="action-icon">
                        <Monitor />
                      </el-icon>
                      <span class="action-text">{{ example.text }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 消息列表 -->
            <div class="messages-list">
              <div 
                v-for="message in chatStore.messages" 
                :key="message.id"
                :id="`message-${message.id}`"
                class="message-wrapper"
              >
                <!-- 用户消息 -->
                <div v-if="message.type === 'user'" class="message user-message">
                  <div class="message-content">
                    <div class="message-bubble user-bubble">
                      {{ message.content }}
                    </div>
                    <div class="message-meta">
                      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                    </div>
                  </div>
                  <div class="message-avatar">
                    <el-avatar :size="36" class="user-avatar">
                      <el-icon><User /></el-icon>
                    </el-avatar>
                  </div>
                </div>

                <!-- 系统消息 -->
                <div v-else-if="message.type === 'system'" class="message system-message">
                  <div class="system-bubble">
                    <el-icon class="system-icon"><InfoFilled /></el-icon>
                    <span>{{ message.content }}</span>
                  </div>
                </div>

                <!-- AI助手消息 -->
                <div v-else-if="message.type === 'assistant'" class="message assistant-message">
                  <div class="message-avatar">
                    <el-avatar :size="36" class="assistant-avatar">
                      <el-icon><Monitor /></el-icon>
                    </el-avatar>
                  </div>
                  <div class="message-content">
                    <!-- 工具调用状态 -->
                    <div v-if="getMessageToolCalls(message.id).length > 0" class="tool-calls-modern">
                      <div 
                        v-for="toolCall in getMessageToolCalls(message.id)" 
                        :key="toolCall.id"
                        class="tool-call-modern"
                        :class="toolCall.status"
                      >
                        <div class="tool-call-icon">
                          <el-icon>
                            <Loading v-if="toolCall.status === 'calling'" />
                            <Check v-else-if="toolCall.status === 'success'" />
                            <Close v-else-if="toolCall.status === 'error'" />
                          </el-icon>
                        </div>
                        <div class="tool-call-info">
                          <span class="tool-name">{{ getToolDisplayName(toolCall.tool) }}</span>
                          <span class="tool-status">{{ getToolStatusText(toolCall.status) }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div class="message-bubble assistant-bubble">
                      <div 
                        class="message-text markdown-content"
                        v-html="formatMessageContent(message.content, message.status === 'streaming')"
                      ></div>
                      <span 
                        v-if="message.status === 'streaming' && showTypingCursor" 
                        class="typing-cursor"
                      >|</span>
                    </div>
                    <div class="message-meta">
                      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                      <el-tag 
                        v-if="message.status === 'streaming'" 
                        type="info" 
                        size="small"
                        class="streaming-tag"
                      >
                        输入中...
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 连接错误提示 -->
            <div v-if="chatStore.connectionError" class="connection-error-modern">
              <div class="error-content">
                <el-icon class="error-icon"><Warning /></el-icon>
                <div class="error-text">
                  <h4>{{ connectionErrorTitle }}</h4>
                  <p>{{ chatStore.connectionError }}</p>
                </div>
                <el-button 
                  type="primary" 
                  @click="reconnect"
                  :loading="reconnecting"
                  class="reconnect-btn"
                >
                  重新连接
                </el-button>
              </div>
            </div>
          </div>

          <!-- 现代化输入区域 -->
          <div class="modern-input-area">
            <div class="input-container">
              <!-- MCP工具状态 -->
              <div class="input-header">
                <div class="mcp-control">
                  <el-switch
                    v-model="mcpEnabled"
                    size="small"
                    :active-color="'var(--success-500)'"
                    :inactive-color="'var(--neutral-300)'"
                    @change="handleMcpToggle"
                  />
                  <span class="mcp-label">MCP工具</span>
                  <el-tooltip content="开启后AI可调用K8s、SSH等运维工具" placement="top">
                    <el-icon class="mcp-help"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
                <div class="connection-indicator" :class="{ 'connected': chatStore.isConnected }">
                  <div class="connection-dot"></div>
                  <span>{{ chatStore.isConnected ? '已连接' : '未连接' }}</span>
                </div>
              </div>

              <!-- 输入框 -->
              <div class="input-wrapper">
                <el-input
                  v-model="inputMessage"
                  type="textarea"
                  :rows="inputRows"
                  placeholder="请输入您的问题或需求..."
                  @keydown="handleKeydown"
                  :disabled="!chatStore.canSendMessage"
                  class="modern-input"
                  resize="none"
                  :maxlength="2000"
                  show-word-limit
                />
                <div class="input-actions">
                  <el-button 
                    @click="clearChat" 
                    :disabled="!chatStore.hasMessages"
                    class="modern-btn secondary small"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                  <el-button 
                    type="primary" 
                    @click="sendMessage" 
                    :loading="chatStore.isStreaming"
                    :disabled="!inputMessage.trim() || !chatStore.canSendMessage"
                    class="modern-btn primary"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </div>
              </div>

              <!-- 快捷提示 -->
              <div class="input-footer">
                <span class="shortcut-hint">
                  <kbd>Ctrl</kbd> + <kbd>Enter</kbd> 发送消息
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 对话框保持原有功能 -->
    <!-- 设置对话框 -->
    <el-dialog
      v-model="settingsDialogVisible"
      title="聊天设置"
      width="400px"
      class="modern-dialog"
    >
      <!-- 设置内容保持不变 -->
      <el-form :model="chatSettings" label-width="120px">
        <el-form-item label="启用工具调用">
          <el-switch v-model="chatSettings.enableTools" />
        </el-form-item>
        <el-form-item label="自动滚动">
          <el-switch v-model="chatSettings.autoScroll" />
        </el-form-item>
        <el-form-item label="显示时间戳">
          <el-switch v-model="chatSettings.showTimestamp" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resetSettings">重置</el-button>
          <el-button type="primary" @click="saveSettings">保存</el-button>
        </div>
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
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Menu, Close, Plus, Search, Download, Setting as Settings,
  User, InfoFilled, Loading, Check, Warning, QuestionFilled,
  Delete, Position, Monitor
} from '@element-plus/icons-vue'
import ChatHistory from '@/components/ChatHistory.vue'
import MessageSearch from '@/components/MessageSearch.vue'
import { useChatStore } from '@/stores/chat'
import { api, llmProvidersApi } from '@/api/client'
import { formatMessageContent } from '@/utils/markdown'

// 响应式数据
const chatStore = useChatStore()
const inputMessage = ref('')
const sidebarVisible = ref(true)
const settingsDialogVisible = ref(false)
const searchDialogVisible = ref(false)
const messagesContainer = ref(null)
const showTypingCursor = ref(true)
const reconnecting = ref(false)
const mcpEnabled = ref(true)
const currentSessionKey = ref(0)

// 供应商相关数据
const availableProviders = ref({})
const currentProvider = ref('')

// 聊天设置
const chatSettings = ref({
  enableTools: true,
  autoScroll: true,
  showTimestamp: true,
  maxMessages: 200,
  showSidebar: true
})

// 计算属性
const inputRows = computed(() => {
  const lines = inputMessage.value.split('\n').length
  return Math.min(Math.max(lines, 1), 4)
})

const connectionStatusClass = computed(() => {
  if (!chatStore.isConnected) return 'disconnected'
  if (chatStore.isStreaming) return 'streaming'
  return 'connected'
})

const connectionStatusText = computed(() => {
  if (!chatStore.isConnected) return '未连接'
  if (chatStore.isStreaming) return '对话中'
  return '已连接'
})

const connectionErrorTitle = computed(() => {
  if (chatStore.retryCount > 0) {
    return `连接失败 (重试 ${chatStore.retryCount}/${chatStore.maxRetries})`
  }
  return '连接中断'
})

const chatStats = computed(() => chatStore.getSessionStats)

// 示例问题
const exampleQuestions = [
  { text: '查看所有命名空间的pod状态', icon: 'Monitor' },
  { text: '显示default命名空间下运行中的服务', icon: 'Monitor' },
  { text: '检查集群节点健康状况', icon: 'Monitor' },
  { text: '查看最近的容器日志', icon: 'Monitor' }
]

// 方法 - 保持原有逻辑
const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value
}

const handleSessionSwitch = (sessionId) => {
  currentSessionKey.value++
  ElMessage.success('已切换到选中的对话')
}

const createNewChat = () => {
  const session = chatStore.createSession()
  currentSessionKey.value++
  ElMessage.success('已创建新对话')
}

const handleMenuCommand = (command) => {
  switch (command) {
    case 'search':
      searchDialogVisible.value = true
      break
    case 'export':
      exportCurrentChat()
      break
    case 'settings':
      settingsDialogVisible.value = true
      break
  }
}

const exportCurrentChat = () => {
  // 导出逻辑保持不变
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

const saveSettings = () => {
  localStorage.setItem('chatSettings', JSON.stringify(chatSettings.value))
  settingsDialogVisible.value = false
  ElMessage.success('设置已保存')
}

const resetSettings = () => {
  chatSettings.value = {
    enableTools: true,
    autoScroll: true,
    showTimestamp: true,
    maxMessages: 200,
    showSidebar: true
  }
}

// 供应商管理
const loadAvailableProviders = async () => {
  try {
    const response = await llmProvidersApi.getAvailableProviders()
    if (response.success) {
      availableProviders.value = response.data.providers
      currentProvider.value = response.data.current_provider
    }
  } catch (error) {
    console.error('加载供应商列表失败:', error)
  }
}

const switchProvider = async (providerId) => {
  if (!availableProviders.value[providerId]?.available) {
    ElMessage.warning('该供应商不可用，请检查配置')
    return
  }

  if (providerId === currentProvider.value) return

  try {
    const response = await llmProvidersApi.switchProvider(providerId)
    if (response.success) {
      currentProvider.value = providerId
      ElMessage.success(response.message)
      
      chatStore.addMessage({
        type: 'system',
        content: `已切换到 ${availableProviders.value[providerId].name}`,
        timestamp: Date.now()
      })
      
      await scrollToBottom()
    } else {
      ElMessage.error(response.message || '切换供应商失败')
    }
  } catch (error) {
    console.error('切换供应商失败:', error)
    ElMessage.error('切换供应商失败')
  }
}

// 工具调用相关
const getMessageToolCalls = (messageId) => {
  return chatStore.getToolCallsForMessage(messageId)
}

const getToolDisplayName = (toolName) => {
  const toolNames = {
    'k8s_get_pods': 'K8s Pod查询',
    'k8s_get_services': 'K8s服务查询',
    'k8s_get_nodes': 'K8s节点查询',
    'ssh_execute': 'SSH命令执行',
    'k8s_get_logs': 'K8s日志查询'
  }
  return toolNames[toolName] || toolName
}

const getToolStatusText = (status) => {
  const statusTexts = {
    'calling': '执行中',
    'success': '成功',
    'error': '失败'
  }
  return statusTexts[status] || status
}

const formatTime = (timestamp) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now - time
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  
  if (diffSec < 60) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  
  return time.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 消息发送
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !chatStore.canSendMessage) {
    return
  }

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  chatStore.addMessage({
    type: 'user',
    content: userMessage
  })

  await scrollToBottom()
  await startStreamChat(userMessage)
}

// 流式聊天 - 保持原有逻辑
const startStreamChat = async (message) => {
  try {
    const streamMessage = chatStore.startStreamMessage()
    
    const response = await fetch('/api/v2/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        enable_tools: mcpEnabled.value
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`)
    }

    chatStore.setConnected(true)
    chatStore.resetRetry()
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const messages = buffer.split('\n')
        buffer = messages.pop() || ''
        
        for (const message of messages) {
          await processSSEMessage(message)
        }
      }
      
      if (buffer.trim()) {
        await processSSELine(buffer)
      }
      
      chatStore.finishStreamMessage()
      
    } finally {
      reader.releaseLock()
    }
    
  } catch (error) {
    console.error('启动流式聊天失败:', error)
    chatStore.finishStreamMessage()
    handleStreamError(error)
  }
}

// SSE消息处理 - 保持原有逻辑
const processSSEMessage = async (message) => {
  const lines = message.split('\n')
  for (const line of lines) {
    if (line.startsWith('data:')) {
      await processSSELine(line)
    }
  }
}

const processSSELine = async (line) => {
  if (line.startsWith('data: ')) {
    const dataContent = line.slice(6)
    
    if (dataContent.trim() === '[DONE]') {
      chatStore.finishStreamMessage()
      return
    }
    
    if (dataContent.includes('__UPDATE_CONTENT__:') && dataContent.includes('__END_UPDATE__')) {
      await handleContentUpdate(dataContent)
      return
    }
    
    try {
      const jsonData = JSON.parse(dataContent)
      await handleStructuredEvent(jsonData)
    } catch (jsonError) {
      if (dataContent === '') {
        chatStore.appendStreamContent('\n')
      } else {
        chatStore.appendStreamContent(dataContent)
      }
      
      setTimeout(() => {
        scrollToBottom()
      }, 10)
    }
  }
}

const handleContentUpdate = async (dataContent) => {
  try {
    const startMarker = '__UPDATE_CONTENT__:'
    const endMarker = '__END_UPDATE__'
    
    const startIndex = dataContent.indexOf(startMarker) + startMarker.length
    const endIndex = dataContent.indexOf(endMarker)
    
    if (startIndex < startMarker.length || endIndex === -1) {
      return
    }
    
    const updateJson = dataContent.substring(startIndex, endIndex)
    const updateInstruction = JSON.parse(updateJson)
    
    if (updateInstruction.type === 'content_update' && updateInstruction.content) {
      chatStore.replaceStreamContent(updateInstruction.content)
      await scrollToBottom()
    }
    
  } catch (error) {
    console.error('处理内容更新指令失败:', error)
  }
}

const handleStructuredEvent = async (data) => {
  switch (data.type) {
    case 'error':
      const errorMessage = data.message || '未知错误'
      await nextTick(() => {
        chatStore.appendStreamContent(`\n\n❌ 错误: ${errorMessage}`)
      })
      ElMessage.error(errorMessage)
      break
      
    case 'tool_call':
      handleToolCall(data)
      break
      
    case 'tool_result':
      if (data.success) {
        await nextTick(() => {
          chatStore.appendStreamContent(`\n✅ 工具执行成功: ${data.tool}`)
        })
      } else {
        await nextTick(() => {
          chatStore.appendStreamContent(`\n❌ 工具执行失败: ${data.tool} - ${data.error}`)
        })
      }
      break
      
    default:
      if (data.content) {
        await nextTick(() => {
          chatStore.appendStreamContent(data.content)
        })
        setTimeout(() => {
          scrollToBottom()
        }, 10)
      }
  }
}

const handleToolCall = (data) => {
  if (data.status === 'calling') {
    chatStore.addToolCall({
      tool: data.tool,
      status: 'calling',
      parameters: data.parameters || {}
    })
  } else {
    const toolCalls = chatStore.toolCalls
    const toolCall = toolCalls.find(tc => 
      tc.tool === data.tool && 
      tc.messageId === chatStore.currentStreamMessage?.id
    )
    
    if (toolCall) {
      chatStore.updateToolCall(toolCall.id, {
        status: data.status,
        result: data.result || null
      })
    }
  }
}

const handleStreamError = (error) => {
  console.error('流式聊天连接错误:', error)
  
  let errorMessage = '连接中断，请检查网络或重试'
  
  if (error.message.includes('HTTP 401')) {
    errorMessage = '认证失败，请检查API密钥配置'
  } else if (error.message.includes('HTTP 403')) {
    errorMessage = '权限不足，请联系管理员'
  } else if (error.message.includes('HTTP 429')) {
    errorMessage = '请求过于频繁，请稍后重试'
  } else if (error.message.includes('HTTP 500')) {
    errorMessage = '服务器内部错误，请稍后重试'
  }
  
  chatStore.setConnectionError(errorMessage)
  chatStore.setConnected(false)
  chatStore.cancelStreamMessage()
  ElMessage.error(errorMessage)
}

const reconnect = async () => {
  reconnecting.value = true
  
  try {
    await api.system.getV2Status()
    chatStore.setConnected(true)
    chatStore.resetRetry()
    ElMessage.success('重新连接成功')
  } catch (error) {
    console.error('重连失败:', error)
    ElMessage.error('重连失败，请检查网络连接')
  } finally {
    reconnecting.value = false
  }
}

// 其他方法
const handleKeydown = (event) => {
  if (event.ctrlKey && event.key === 'Enter') {
    event.preventDefault()
    sendMessage()
  }
}

const setInputMessage = (message) => {
  inputMessage.value = message
}

const handleMcpToggle = () => {
  if (mcpEnabled.value) {
    ElMessage.success('MCP工具已启用，AI可以调用K8s、SSH等运维工具')
  } else {
    ElMessage.info('MCP工具已禁用，AI将仅提供文本回复')
  }
}

const clearChat = async () => {
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
    ElMessage.success('当前对话已清空')
  } catch {
    // 用户取消
  }
}

const scrollToBottom = async () => {
  try {
    await nextTick()
    if (messagesContainer.value && messagesContainer.value.scrollTop !== undefined) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  } catch (error) {
    console.warn('滚动到底部失败:', error)
  }
}

const handleScrollToMessage = (messageId) => {
  const message = chatStore.messages.find(msg => msg.id === messageId)
  if (message) {
    try {
      const messageElement = document.getElementById(`message-${messageId}`)
      if (messageElement && messageElement.offsetTop !== undefined) {
        messagesContainer.value.scrollTop = messageElement.offsetTop - 100
      }
    } catch (error) {
      console.warn('滚动到消息失败:', error)
    }
  }
}

// 打字机光标闪烁
const startTypingCursor = () => {
  setInterval(() => {
    showTypingCursor.value = !showTypingCursor.value
  }, 500)
}

// 生命周期
onMounted(async () => {
  startTypingCursor()
  loadAvailableProviders()
  
  try {
    await chatStore.loadFromStorage()
    await nextTick()
    currentSessionKey.value++
  } catch (error) {
    console.error('聊天历史加载失败:', error)
    ElMessage.error('加载聊天历史失败，已创建新对话')
    currentSessionKey.value++
  }
})

onUnmounted(() => {
  try {
    if (messagesContainer.value) {
      messagesContainer.value = null
    }
  } catch (error) {
    console.warn('组件卸载清理失败:', error)
  }
})

// 监听消息变化，自动滚动
watch(
  () => chatStore.messages.length,
  () => {
    scrollToBottom()
  }
)

watch(() => chatStore.currentStreamMessage?.content, () => {
  scrollToBottom()
})
</script>

<style scoped>
/* 现代化聊天页面样式 */
.modern-chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  font-family: var(--font-sans);
}

/* 现代化头部 */
.modern-chat-header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
  z-index: var(--z-sticky);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  max-width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex: 1;
  min-width: 0;
}

.sidebar-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--neutral-100);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-out);
}

.sidebar-toggle-btn:hover {
  background: var(--neutral-200);
  color: var(--text-primary);
}

.sidebar-toggle-btn.active {
  background: var(--primary-100);
  color: var(--primary-600);
}

.page-info {
  flex: 1;
  min-width: 0;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
}

.status-indicators {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--duration-200) var(--ease-out);
}

.status-badge.connected {
  background: var(--success-50);
  color: var(--success-600);
}

.status-badge.streaming {
  background: var(--warning-50);
  color: var(--warning-600);
}

.status-badge.disconnected {
  background: var(--error-50);
  color: var(--error-600);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: currentColor;
  animation: pulse var(--duration-1000) infinite;
}

.message-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  padding: var(--space-1) var(--space-3);
  background: var(--neutral-100);
  border-radius: var(--radius-full);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* 现代化按钮 */
.modern-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-out);
  text-decoration: none;
}

.modern-btn.primary {
  background: var(--primary-500);
  color: var(--text-inverse);
  border-color: var(--primary-500);
}

.modern-btn.primary:hover {
  background: var(--primary-600);
  border-color: var(--primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.modern-btn.secondary {
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-color: var(--border-primary);
}

.modern-btn.secondary:hover {
  background: var(--neutral-50);
  color: var(--text-primary);
  border-color: var(--border-secondary);
}

.modern-btn.small {
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-xs);
}

/* 主体内容 */
.modern-chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 现代化侧边栏 */
.modern-sidebar {
  width: 0;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-primary);
  transition: width var(--duration-300) var(--ease-out);
  overflow: hidden;
}

.modern-sidebar.visible {
  width: 320px;
}

.sidebar-content {
  width: 320px;
  height: 100%;
  overflow: hidden;
}

/* 聊天主区域 */
.modern-chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 现代化供应商选择器 */
.provider-selector-modern {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  padding: var(--space-4) var(--space-6);
}

.provider-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.provider-icon {
  color: var(--primary-500);
}

.provider-options {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.provider-option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  background: var(--bg-primary);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-out);
  min-width: 140px;
}

.provider-option:hover {
  border-color: var(--primary-300);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.provider-option.active {
  border-color: var(--primary-500);
  background: var(--primary-50);
  box-shadow: var(--shadow-md);
}

.provider-option.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--neutral-50);
}

.provider-option.disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--border-primary);
}

.provider-avatar {
  font-size: var(--text-lg);
  line-height: 1;
}

.provider-details {
  flex: 1;
  min-width: 0;
}

.provider-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-model {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--error-500);
  transition: background-color var(--duration-200) var(--ease-out);
}

.status-indicator.online {
  background: var(--success-500);
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
  scroll-behavior: smooth;
}

/* 欢迎界面 */
.welcome-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.welcome-content {
  text-align: center;
  max-width: 600px;
  padding: var(--space-8);
}

.welcome-avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--space-6) auto;
  background: var(--primary-100);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-4xl);
  color: var(--primary-600);
}

.welcome-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0 0 var(--space-4) 0;
}

.welcome-description {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-8) 0;
}

.quick-actions-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-4) 0;
}

.action-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

.action-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-out);
  text-align: left;
}

.action-card:hover {
  border-color: var(--primary-300);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.action-icon {
  font-size: var(--text-xl);
  color: var(--primary-500);
}

.action-text {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

/* 消息列表 */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.message-wrapper {
  animation: fadeInUp var(--duration-300) var(--ease-out);
}

.message {
  display: flex;
  gap: var(--space-3);
  max-width: 100%;
}

.message.user-message {
  flex-direction: row-reverse;
}

.message.system-message {
  justify-content: center;
  margin: var(--space-4) 0;
}

.message-avatar {
  flex-shrink: 0;
}

.user-avatar {
  background: var(--primary-500);
  color: var(--text-inverse);
}

.assistant-avatar {
  background: var(--neutral-100);
  color: var(--primary-500);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-bubble {
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-2xl);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  word-wrap: break-word;
  position: relative;
}

.user-bubble {
  background: var(--primary-500);
  color: var(--text-inverse);
  border-bottom-right-radius: var(--radius-md);
  max-width: 70%;
  margin-left: auto;
}

.assistant-bubble {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  border-bottom-left-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  max-width: 85%;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.user-message .message-meta {
  justify-content: flex-end;
}

.streaming-tag {
  font-size: var(--text-xs);
}

/* 系统消息 */
.system-bubble {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--info-50);
  color: var(--info-600);
  border: 1px solid var(--info-200);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  max-width: 400px;
}

.system-icon {
  font-size: var(--text-base);
}

/* 工具调用 */
.tool-calls-modern {
  margin-bottom: var(--space-3);
  padding: var(--space-3);
  background: var(--neutral-50);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--primary-500);
}

.tool-call-modern {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
}

.tool-call-modern:not(:last-child) {
  border-bottom: 1px solid var(--border-primary);
  margin-bottom: var(--space-2);
  padding-bottom: var(--space-2);
}

.tool-call-icon {
  font-size: var(--text-base);
}

.tool-call-modern.calling .tool-call-icon {
  color: var(--primary-500);
}

.tool-call-modern.success .tool-call-icon {
  color: var(--success-500);
}

.tool-call-modern.error .tool-call-icon {
  color: var(--error-500);
}

.tool-call-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.tool-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.tool-status {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

/* 打字机效果 */
.typing-cursor {
  display: inline-block;
  animation: blink var(--duration-1000) infinite;
  font-weight: var(--font-bold);
  color: var(--primary-500);
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 连接错误 */
.connection-error-modern {
  margin: var(--space-6) 0;
  padding: var(--space-4);
  background: var(--error-50);
  border: 1px solid var(--error-200);
  border-radius: var(--radius-xl);
}

.error-content {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.error-icon {
  font-size: var(--text-xl);
  color: var(--error-500);
  flex-shrink: 0;
}

.error-text {
  flex: 1;
}

.error-text h4 {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--error-600);
  margin: 0 0 var(--space-1) 0;
}

.error-text p {
  font-size: var(--text-sm);
  color: var(--error-600);
  margin: 0;
}

.reconnect-btn {
  flex-shrink: 0;
}

/* 现代化输入区域 */
.modern-input-area {
  background: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
  padding: var(--space-4) var(--space-6);
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.mcp-control {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--neutral-50);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.mcp-label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.mcp-help {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  cursor: help;
}

.connection-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.connection-indicator.connected {
  color: var(--success-600);
}

.connection-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--error-500);
}

.connection-indicator.connected .connection-dot {
  background: var(--success-500);
  animation: pulse var(--duration-1000) infinite;
}

.input-wrapper {
  position: relative;
}

.modern-input {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  transition: all var(--duration-200) var(--ease-out);
}

.modern-input:focus-within {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.input-actions {
  position: absolute;
  bottom: var(--space-3);
  right: var(--space-3);
  display: flex;
  gap: var(--space-2);
}

.input-footer {
  display: flex;
  justify-content: center;
  margin-top: var(--space-3);
}

.shortcut-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.shortcut-hint kbd {
  padding: 2px var(--space-1);
  background: var(--neutral-100);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-base);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
}

/* Markdown 内容样式 */
.markdown-content {
  line-height: var(--leading-relaxed);
  color: inherit;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: var(--space-4) 0 var(--space-2) 0;
}

.markdown-content h1 { font-size: var(--text-xl); }
.markdown-content h2 { font-size: var(--text-lg); }
.markdown-content h3 { font-size: var(--text-base); }

.markdown-content p {
  margin: var(--space-2) 0;
}

.markdown-content code {
  background: var(--neutral-100);
  padding: 2px var(--space-1);
  border-radius: var(--radius-base);
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.markdown-content pre {
  background: var(--neutral-800);
  color: var(--neutral-100);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  margin: var(--space-4) 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-content ul,
.markdown-content ol {
  margin: var(--space-2) 0;
  padding-left: var(--space-6);
}

.markdown-content li {
  margin: var(--space-1) 0;
}

.markdown-content blockquote {
  border-left: 4px solid var(--primary-500);
  margin: var(--space-4) 0;
  padding: var(--space-2) var(--space-4);
  background: var(--neutral-50);
  color: var(--text-secondary);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
}

.markdown-content table {
  width: 100%;
  margin: var(--space-4) 0;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.markdown-content th,
.markdown-content td {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--border-primary);
}

.markdown-content th {
  background: var(--neutral-50);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.markdown-content tr:last-child td {
  border-bottom: none;
}

.markdown-content tr:hover td {
  background: var(--neutral-50);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: var(--space-3) var(--space-4);
  }
  
  .page-title {
    font-size: var(--text-lg);
  }
  
  .modern-sidebar.visible {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: var(--z-modal);
    width: 280px;
  }
  
  .messages-area {
    padding: var(--space-4) var(--space-5);
  }
  
  .modern-input-area {
    padding: var(--space-3) var(--space-4);
  }
  
  .input-header {
    flex-direction: column;
    gap: var(--space-2);
    align-items: stretch;
  }
  
  .action-cards {
    grid-template-columns: 1fr;
  }
  
  .message-bubble {
    font-size: var(--text-sm);
  }
  
  .user-bubble,
  .assistant-bubble {
    max-width: 85%;
  }
  
  .messages-list {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    gap: var(--space-3);
    align-items: stretch;
  }
  
  .header-left {
    flex-direction: column;
    gap: var(--space-2);
    align-items: flex-start;
  }
  
  .status-indicators {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .provider-options {
    flex-direction: column;
  }
  
  .provider-option {
    min-width: auto;
  }
}

/* 现代化对话框 */
.modern-dialog {
  border-radius: var(--radius-2xl);
  overflow: hidden;
}

.modern-dialog .el-dialog__header {
  background: var(--neutral-50);
  border-bottom: 1px solid var(--border-primary);
}

.modern-dialog .el-dialog__body {
  padding: var(--space-6);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* 现代化下拉菜单 */
.modern-dropdown {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modern-dropdown .el-dropdown-menu__item {
  padding: var(--space-3) var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-200) var(--ease-out);
}

.modern-dropdown .el-dropdown-menu__item:hover {
  background: var(--neutral-50);
}
</style>
