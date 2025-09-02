<template>
  <div class="stream-chat">
    <!-- 添加供应商选择区域 -->
    <div class="provider-selector">
      <div class="provider-header">
        <el-icon><Setting /></el-icon>
        <span>AI 供应商</span>
      </div>
      <div class="provider-list">
        <div 
          v-for="(provider, id) in availableProviders" 
          :key="id"
          :class="['provider-item', { 'active': currentProvider === id, 'unavailable': !provider.available }]"
          @click="switchProvider(id)"
        >
          <div class="provider-icon">{{ provider.icon || '🤖' }}</div>
          <div class="provider-info">
            <div class="provider-name">{{ provider.name }}</div>
            <div class="provider-model">{{ provider.model }}</div>
          </div>
          <div class="provider-status">
            <el-icon v-if="provider.available" class="status-available"><CircleCheckFilled /></el-icon>
            <el-icon v-else class="status-unavailable"><CircleCloseFilled /></el-icon>
          </div>
        </div>
      </div>
    </div>
    <!-- 消息列表区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div class="messages-wrapper">
        <!-- 欢迎消息 -->
        <div v-if="!chatStore.hasMessages" class="welcome-message">
          <div class="welcome-icon">🤖</div>
          <h3>钉钉K8s运维机器人</h3>
          <p>我是您的智能Kubernetes运维助手，可以帮助您管理集群、查看状态、执行运维操作。请告诉我您需要什么帮助。</p>
          <div class="example-questions">
            <h4>试试这些问题：</h4>
            <div class="question-chips">
              <el-tag 
                v-for="example in exampleQuestions" 
                :key="example"
                @click="setInputMessage(example)"
                class="question-chip"
                type="primary"
                effect="plain"
              >
                {{ example }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div 
          v-for="message in chatStore.messages" 
          :key="message.id"
          :id="`message-${message.id}`"
          :class="['message-item', `message-${message.type}`]"
        >
          <!-- 用户消息 -->
          <div v-if="message.type === 'user'" class="user-message">
            <div class="message-meta">
              <el-avatar :size="32" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div class="message-bubble user-bubble">
              {{ message.content }}
            </div>
          </div>

          <!-- 系统消息 -->
          <div v-else-if="message.type === 'system'" class="system-message">
            <div class="system-content">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ message.content }}</span>
            </div>
          </div>

          <!-- AI助手消息 -->
          <div v-else-if="message.type === 'assistant'" class="assistant-message">
            <div class="message-meta">
              <el-avatar :size="32" class="assistant-avatar" style="background-color: #409EFF;">
                <el-icon><Monitor /></el-icon>
              </el-avatar>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              <el-tag 
                v-if="message.status === 'streaming'" 
                type="info" 
                size="small"
                class="status-tag"
              >
                输入中...
              </el-tag>
            </div>
            <div class="message-bubble assistant-bubble">
              <!-- 工具调用状态 -->
              <div v-if="getMessageToolCalls(message.id).length > 0" class="tool-calls">
                <div 
                  v-for="toolCall in getMessageToolCalls(message.id)" 
                  :key="toolCall.id"
                  class="tool-call-item"
                >
                  <el-icon class="tool-icon">
                    <Loading v-if="toolCall.status === 'calling'" />
                    <Check v-else-if="toolCall.status === 'success'" />
                    <Close v-else-if="toolCall.status === 'error'" />
                  </el-icon>
                  <span class="tool-name">{{ getToolDisplayName(toolCall.tool) }}</span>
                  <span class="tool-status" :class="toolCall.status">
                    {{ getToolStatusText(toolCall.status) }}
                  </span>
                </div>
              </div>
              
              <!-- 消息内容（带打字机效果） -->
              <div class="message-content">
                <div 
                  v-if="message.status === 'streaming'" 
                  class="typing-text markdown-content"
                  v-html="formatMessageContent(message.content, true)"
                ></div>
                <div 
                  v-else 
                  class="markdown-content"
                  v-html="formatMessageContent(message.content, false)"
                ></div>
                <span 
                  v-if="message.status === 'streaming' && showTypingCursor" 
                  class="typing-cursor"
                >|</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 连接状态提示 -->
        <div v-if="chatStore.connectionError" class="connection-error">
          <el-alert
            :title="connectionErrorTitle"
            :description="chatStore.connectionError"
            type="error"
            show-icon
            :closable="false"
          >
            <template #default>
              <el-button 
                size="small" 
                type="primary" 
                @click="reconnect"
                :loading="reconnecting"
              >
                重新连接
              </el-button>
            </template>
          </el-alert>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="inputRows"
          placeholder="请输入您的问题或需求... (Ctrl + Enter 发送)"
          @keydown="handleKeydown"
          :disabled="!chatStore.canSendMessage"
          class="message-input"
          resize="none"
        />
        <div class="input-actions">
          <div class="input-tips">
            <span class="connection-status" :class="{ connected: chatStore.isConnected }">
              <el-icon><VideoPause v-if="!chatStore.isConnected" /><VideoPlay v-else /></el-icon>
              {{ chatStore.isConnected ? '已连接' : '未连接' }}
            </span>
            <span class="mcp-status" :class="{ enabled: mcpEnabled }">
              🛠️ MCP {{ mcpEnabled ? '已启用' : '已禁用' }}
            </span>
            <span class="shortcut-tip">Ctrl + Enter 发送</span>
          </div>
          <div class="action-buttons">
            <!-- MCP工具开关 -->
            <div class="mcp-toggle">
              <el-switch
                v-model="mcpEnabled"
                size="small"
                active-text="MCP"
                inactive-text="MCP"
                :active-color="'#67C23A'"
                :inactive-color="'#DCDFE6'"
                @change="handleMcpToggle"
              />
              <el-tooltip 
                content="开启后AI可调用K8s、SSH等运维工具" 
                placement="top"
              >
                <el-icon class="mcp-info-icon">
                  <InfoFilled />
                </el-icon>
              </el-tooltip>
            </div>
            <el-button 
              @click="clearChat" 
              size="small"
              :disabled="!chatStore.hasMessages"
            >
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button 
              type="primary" 
              @click="sendMessage" 
              :loading="chatStore.isStreaming"
              :disabled="!inputMessage.trim() || !chatStore.canSendMessage"
              size="small"
            >
              <el-icon><Position /></el-icon>
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  User, Monitor, Loading, Check, Close, Delete, Position, 
  VideoPause, VideoPlay, InfoFilled, Setting, CircleCheckFilled, CircleCloseFilled 
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { api, llmProvidersApi } from '@/api/client'
import { formatMessageContent } from '@/utils/markdown'
import { loadKatex } from '@/utils/katex'

// Props
const props = defineProps({
  autoConnect: {
    type: Boolean,
    default: true
  },
  enableTools: {
    type: Boolean,
    default: true
  }
})

// 响应式数据
const chatStore = useChatStore()
const inputMessage = ref('')

// 供应商相关数据
const availableProviders = ref({})
const currentProvider = ref('')
const isLoadingProviders = ref(false)
const messagesContainer = ref(null)
const showTypingCursor = ref(true)
const reconnecting = ref(false)
// 添加MCP开关状态
const mcpEnabled = ref(props.enableTools)

// 计算属性
const inputRows = computed(() => {
  const lines = inputMessage.value.split('\n').length
  return Math.min(Math.max(lines, 1), 4)
})

const connectionErrorTitle = computed(() => {
  if (chatStore.retryCount > 0) {
    return `连接失败 (重试 ${chatStore.retryCount}/${chatStore.maxRetries})`
  }
  return '连接中断'
})

// 示例问题
const exampleQuestions = [
  '查看所有命名空间的pod状态',
  '显示default命名空间下运行中的服务',
  '检查集群节点健康状况',
  '查看最近的容器日志'
]

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

// formatMessageContent 已从 @/utils/markdown 导入

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

// 供应商管理方法
const loadAvailableProviders = async () => {
  try {
    isLoadingProviders.value = true
    const response = await llmProvidersApi.getAvailableProviders()
    if (response.success) {
      availableProviders.value = response.data.providers
      currentProvider.value = response.data.current_provider
    }
  } catch (error) {
    console.error('加载供应商列表失败:', error)
    ElMessage.error('加载供应商列表失败')
  } finally {
    isLoadingProviders.value = false
  }
}

const switchProvider = async (providerId) => {
  if (!availableProviders.value[providerId]?.available) {
    ElMessage.warning('该供应商不可用，请检查配置')
    return
  }

  if (providerId === currentProvider.value) {
    return // 已经是当前供应商
  }

  try {
    const response = await llmProvidersApi.switchProvider(providerId)
    if (response.success) {
      currentProvider.value = providerId
      ElMessage.success(response.message)
      
      // 添加系统消息提示切换
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

// 消息发送
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !chatStore.canSendMessage) {
    return
  }

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  chatStore.addMessage({
    type: 'user',
    content: userMessage
  })

  // 滚动到底部
  await scrollToBottom()

  // 开始流式聊天
  await startStreamChat(userMessage)
}

// 优化的流式聊天
const startStreamChat = async (message) => {
  try {
    console.log('开始流式聊天:', message)
    
    // 确保DOM已准备好
    await nextTick()
    
    // 开始流式消息
    const streamMessage = chatStore.startStreamMessage()
    console.log('创建流式消息:', streamMessage)
    
    // 使用fetch API发送POST请求（因为EventSource只支持GET）
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

    console.log('收到响应:', response.status, response.statusText)

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`)
    }

    // 连接状态管理
    chatStore.setConnected(true)
    chatStore.resetRetry()
    
    // 创建ReadableStream读取器处理SSE
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('流式读取完成')
          break
        }
        
        // 解码数据并累积到缓冲区
        buffer += decoder.decode(value, { stream: true })
        
        // 按SSE消息分割处理（SSE消息以\n结尾）
        const messages = buffer.split('\n')
        
        // 保留最后一个消息（可能不完整）
        buffer = messages.pop() || ''
        
        for (const message of messages) {
          // 🔧 修复：不再跳过空消息，因为可能包含换行符信息
            console.log('处理SSE消息:', message)
            await processSSEMessage(message)
        }
      }
      
      // 处理缓冲区中剩余的数据
      if (buffer.trim()) {
        console.log('处理剩余数据:', buffer)
        await processSSELine(buffer)
      }
      
      // 完成流式消息
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

// 处理SSE消息数据
const processSSEMessage = async (message) => {
  // SSE消息可能包含多行，需要逐行处理
  const lines = message.split('\n')
  for (const line of lines) {
    // 🔧 修复：处理所有以"data:"开头的行
    if (line.startsWith('data:')) {
      await processSSELine(line)
    }
  }
}

// 处理SSE行数据
const processSSELine = async (line) => {
  if (line.startsWith('data: ')) {
    const dataContent = line.slice(6)  // 不要trim()，保留空白字符
    
    // 检查结束标识
    if (dataContent.trim() === '[DONE]') {
      console.log('收到结束标识')
      chatStore.finishStreamMessage()
      return
    }
    
    // 🔧 检查内容更新指令
    if (dataContent.includes('__UPDATE_CONTENT__:') && dataContent.includes('__END_UPDATE__')) {
      console.log('检测到内容更新指令')
      await handleContentUpdate(dataContent)
      return
    }
    
    // 尝试解析为JSON
    try {
      const jsonData = JSON.parse(dataContent)
      console.log('解析JSON事件数据:', jsonData)
      await handleStructuredEvent(jsonData)
    } catch (jsonError) {
      // 不是JSON，当作普通文本处理
      console.log('处理文本内容:', dataContent)
      
      // 处理内容：如果是空内容，代表换行符；否则直接添加内容
      if (dataContent === '') {
        // 空的data:行代表换行符
        chatStore.appendStreamContent('\n')
      } else {
        chatStore.appendStreamContent(dataContent)
      }
      
      // 延迟滚动以确保DOM已更新
      setTimeout(() => {
        scrollToBottom()
      }, 10)
    }
  }
}

// 🔧 处理内容更新指令
const handleContentUpdate = async (dataContent) => {
  try {
    // 提取更新指令的JSON部分
    const startMarker = '__UPDATE_CONTENT__:'
    const endMarker = '__END_UPDATE__'
    
    const startIndex = dataContent.indexOf(startMarker) + startMarker.length
    const endIndex = dataContent.indexOf(endMarker)
    
    if (startIndex < startMarker.length || endIndex === -1) {
      console.error('无效的内容更新指令格式')
      return
    }
    
    const updateJson = dataContent.substring(startIndex, endIndex)
    const updateInstruction = JSON.parse(updateJson)
    
    console.log('🔧 处理内容更新:', updateInstruction)
    
    if (updateInstruction.type === 'content_update' && updateInstruction.content) {
      // 用完整恢复的内容替换当前流式消息的内容
      chatStore.replaceStreamContent(updateInstruction.content)
      
      console.log('✅ 内容已更新，原因:', updateInstruction.reason)
      console.log('📝 新内容长度:', updateInstruction.content.length)
      
      // 滚动到底部
      await scrollToBottom()
    }
    
  } catch (error) {
    console.error('处理内容更新指令失败:', error)
  }
}

// 处理结构化事件数据
const handleStructuredEvent = async (data) => {
  console.log('处理结构化事件:', data.type, data)
  
  try {
    switch (data.type) {
      case 'error':
        // 处理错误
        const errorMessage = data.message || '未知错误'
        const suggestions = data.suggestions || []
        
        await nextTick(() => {
          chatStore.appendStreamContent(`\n\n❌ 错误: ${errorMessage}`)
        })
        
        if (suggestions.length > 0) {
          await nextTick(() => {
            chatStore.appendStreamContent(`\n\n💡 建议:\n${suggestions.map(s => `• ${s}`).join('\n')}`)
          })
        }
        
        // 显示用户友好的错误提示
        ElMessage.error(errorMessage)
        break
        
      case 'tool_call':
        // 处理工具调用
        handleToolCall(data)
        break
        
      case 'tool_result':
        // 处理工具结果
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
        
      case 'status':
        // 处理状态更新
        console.log('状态更新:', data.message)
        break
        
      default:
        console.warn('未知的结构化事件类型:', data.type, data)
        // 如果有内容，当作文本处理
        if (data.content) {
          await nextTick(() => {
            chatStore.appendStreamContent(data.content)
          })
          setTimeout(() => {
            scrollToBottom()
          }, 10)
        }
    }
  } catch (error) {
    console.error('处理结构化事件失败:', error)
  }
}

// 流式事件处理
const handleStreamEvent = async (data) => {
  console.log('处理事件:', data.type, data)
  
  switch (data.type) {
    case 'start':
      // 开始标记
      console.log('流式聊天开始:', data.message_id)
      break
      
    case 'token':
      // 追加消息内容（后端使用token而不是message）
      console.log('追加消息内容:', data.content)
      chatStore.appendStreamContent(data.content)
      await scrollToBottom()
      break
      
    case 'message':
      // 兼容旧的message事件类型
      console.log('追加消息内容:', data.content)
      chatStore.appendStreamContent(data.content)
      await scrollToBottom()
      break
      
    case 'tool_call':
      // 处理工具调用
      handleToolCall(data)
      break
      
    case 'error':
      // 处理错误
      chatStore.appendStreamContent(`\n\n❌ 错误: ${data.message}`)
      break
      
    case 'complete':
      // 完成流式输出（后端使用complete而不是done）
      console.log('流式输出完成')
      chatStore.finishStreamMessage()
      break
      
    case 'done':
      // 兼容旧的done事件类型
      console.log('流式输出完成')
      chatStore.finishStreamMessage()
      break
      
    default:
      console.warn('未知的流式事件类型:', data.type, data)
  }
}

// 工具调用处理
const handleToolCall = (data) => {
  if (data.status === 'calling') {
    // 新的工具调用
    chatStore.addToolCall({
      tool: data.tool,
      status: 'calling',
      parameters: data.parameters || {}
    })
  } else {
    // 更新工具调用状态
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

// 优化的流式错误处理
const handleStreamError = (error) => {
  console.error('流式聊天连接错误:', error)
  
  // 根据错误类型提供不同的处理
  let errorMessage = '连接中断，请检查网络或重试'
  let shouldRetry = true
  
  if (error.message.includes('HTTP 401')) {
    errorMessage = '认证失败，请检查API密钥配置'
    shouldRetry = false
  } else if (error.message.includes('HTTP 403')) {
    errorMessage = '权限不足，请联系管理员'
    shouldRetry = false
  } else if (error.message.includes('HTTP 429')) {
    errorMessage = '请求过于频繁，请稍后重试'
    shouldRetry = true
  } else if (error.message.includes('HTTP 500')) {
    errorMessage = '服务器内部错误，请稍后重试'
    shouldRetry = true
  } else if (error.message.includes('HTTP 503')) {
    errorMessage = '服务暂时不可用，请稍后重试'
    shouldRetry = true
  } else if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
    errorMessage = '网络连接失败，请检查网络状态'
    shouldRetry = true
  }
  
  chatStore.setConnectionError(errorMessage)
  chatStore.setConnected(false)
  chatStore.cancelStreamMessage()
  
  // 显示用户友好的错误提示
  ElMessage.error(errorMessage)
  
  // 自动重连逻辑（仅在应该重试的情况下）
  if (shouldRetry && chatStore.incrementRetry()) {
    const retryDelay = Math.min(2000 * Math.pow(2, chatStore.retryCount - 1), 30000) // 指数退避，最大30秒
    console.log(`将在 ${retryDelay}ms 后重试 (第 ${chatStore.retryCount} 次)`)
    
    setTimeout(() => {
      console.log('开始自动重连...')
      reconnect()
    }, retryDelay)
  } else if (!shouldRetry) {
    console.log('错误类型不支持自动重连')
  } else {
    console.log('已达到最大重试次数')
    ElMessage.warning('已达到最大重试次数，请手动重新连接')
  }
}

// 重连
const reconnect = async () => {
  reconnecting.value = true
  
  try {
    // 测试API连接
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

// 键盘事件处理
const handleKeydown = (event) => {
  if (event.ctrlKey && event.key === 'Enter') {
    event.preventDefault()
    sendMessage()
  }
}

// 设置输入消息（点击示例问题）
const setInputMessage = (message) => {
  inputMessage.value = message
}

// MCP状态变化提示
const handleMcpToggle = () => {
  if (mcpEnabled.value) {
    ElMessage.success('MCP工具已启用，AI可以调用K8s、SSH等运维工具')
  } else {
    ElMessage.info('MCP工具已禁用，AI将仅提供文本回复')
  }
}

// 清空聊天
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

// 自动滚动到底部
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

// 打字机光标闪烁
const startTypingCursor = () => {
  setInterval(() => {
    showTypingCursor.value = !showTypingCursor.value
  }, 500)
}

// 生命周期
onMounted(() => {
  startTypingCursor()
  
  // 加载可用的供应商列表
  loadAvailableProviders()
  
  if (props.autoConnect) {
    // 初始化连接状态检查
    reconnect()
  }
  
  // 确保DOM完全加载后再进行操作
  nextTick(() => {
    // 验证DOM元素是否正确挂载
    if (messagesContainer.value) {
      console.log('消息容器已正确挂载')
    } else {
      console.warn('消息容器挂载失败')
    }
  })
})

onUnmounted(() => {
  // 清理资源
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
    nextTick(async () => {
      // 暂时禁用KaTeX渲染以修复DOM错误
      // await loadKatex()
      // 暂时禁用KaTeX渲染以修复DOM insertBefore错误
      console.log('消息渲染完成，KaTeX渲染已禁用')
    })
  }
)

watch(() => chatStore.currentStreamMessage?.content, () => {
  scrollToBottom()
})
</script>

<style scoped>
.stream-chat {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  scroll-behavior: smooth;
}

.messages-wrapper {
  max-width: 100%;
  margin: 0;
  width: 100%;
  padding: 0 15px;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-message h3 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
  font-size: 24px;
}

.welcome-message p {
  margin: 0 0 32px 0;
  font-size: 16px;
  line-height: 1.6;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.example-questions h4 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
  font-size: 16px;
}

.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.question-chip {
  cursor: pointer;
  transition: all 0.3s;
}

.question-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 消息项 */
.message-item {
  margin-bottom: 24px;
  animation: fadeInUp 0.3s ease-out;
}

.message-meta {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.message-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.status-tag {
  margin-left: auto;
}

/* 消息气泡 */
.message-bubble {
  max-width: 80%;
  padding: 20px 24px;
  border-radius: 20px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 15px;
  min-height: 40px;
}

/* 包含表格的消息气泡需要更大的宽度 */
.assistant-bubble .markdown-content {
  min-width: 0; /* 允许收缩 */
}

/* 当消息包含表格时，扩大气泡宽度 */
.assistant-message .message-bubble {
  max-width: 95%;
}

.user-message {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-bubble {
  background: linear-gradient(135deg, #409EFF, #66b1ff);
  color: white;
  border-bottom-right-radius: 6px;
}

.assistant-message {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.assistant-bubble {
  background: white;
  color: var(--text-primary);
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 工具调用状态 */
.tool-calls {
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #409EFF;
}

.tool-call-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
}

.tool-call-item:last-child {
  margin-bottom: 0;
}

.tool-icon {
  font-size: 14px;
}

.tool-name {
  font-weight: 500;
  color: var(--text-primary);
}

.tool-status {
  margin-left: auto;
  font-size: 12px;
}

.tool-status.calling {
  color: #409EFF;
}

.tool-status.success {
  color: #67C23A;
}

.tool-status.error {
  color: #F56C6C;
}

/* 消息内容 */
.message-content {
  position: relative;
  padding-left: 12px;
}

.typing-text {
  display: block;
}

.typing-cursor {
  display: inline-block;
  animation: blink 1s infinite;
  font-weight: bold;
  color: #409EFF;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 代码样式 */
.message-content :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(code) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

/* 连接错误 */
.connection-error {
  margin: 16px 0;
}

/* 输入区域 */
.chat-input {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 16px 20px;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.message-input {
  margin-bottom: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-tips {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.connection-status.connected {
  color: var(--success-color);
}

.mcp-status {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #F56C6C;
  font-size: 12px;
}

.mcp-status.enabled {
  color: #67C23A;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* MCP开关样式 */
.mcp-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(64, 158, 255, 0.05);
  border: 1px solid rgba(64, 158, 255, 0.2);
  transition: all 0.3s ease;
}

.mcp-toggle:hover {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

.mcp-info-icon {
  font-size: 14px;
  color: var(--text-secondary);
  cursor: help;
  transition: color 0.3s ease;
}

.mcp-info-icon:hover {
  color: #409EFF;
}

/* Markdown 内容样式 */
.markdown-content {
  line-height: 1.5;
  white-space: pre-wrap;
}

/* 整体紧凑模式 */
.markdown-content > *:first-child {
  margin-top: 0;
}

.markdown-content > *:last-child {
  margin-bottom: 0;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 8px 0 2px 0;
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-content h1 { font-size: 1.5em; }
.markdown-content h2 { font-size: 1.3em; }
.markdown-content h3 { font-size: 1.15em; }

.markdown-content p {
  margin: 1px 0;
}

/* 紧凑段落间距 */
.markdown-content p + p {
  margin-top: 4px;
}

.markdown-content h1:first-child,
.markdown-content h2:first-child,
.markdown-content h3:first-child,
.markdown-content h4:first-child,
.markdown-content h5:first-child,
.markdown-content h6:first-child {
  margin-top: 0;
}

.markdown-content code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background: #2d3748;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 6px 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-content ul,
.markdown-content ol {
  margin: 2px 0;
  padding-left: 24px;
  list-style-position: outside;
}

.markdown-content li {
  margin: 0;
  line-height: 1.4;
  margin-bottom: 1px;
}

.markdown-content li p {
  margin: 0;
}

/* 嵌套列表间距 */
.markdown-content li > ul,
.markdown-content li > ol {
  margin-top: 1px;
  margin-bottom: 1px;
}

/* 列表项之间更紧凑 */
.markdown-content li + li {
  margin-top: 1px;
}

.text-content ul,
.text-content ol {
  margin: 2px 0;
  padding-left: 24px;
  list-style-position: outside;
}

.text-content li {
  margin: 0;
  line-height: 1.4;
  margin-bottom: 1px;
}

.text-content {
  line-height: 1.5;
}

.markdown-content blockquote {
  border-left: 4px solid #409EFF;
  margin: 6px 0;
  padding: 6px 12px;
  background: #f8f9fa;
  color: #666;
}

.markdown-content table {
  border-collapse: separate !important;
  border-spacing: 0 !important;
  width: 100%;
  margin: 16px 0;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  border: 2px solid #409EFF !important;
  min-width: 600px; /* 设置最小宽度防止过度压缩 */
}

.markdown-content th,
.markdown-content td {
  border-right: 1px solid #e4e7ed !important;
  border-bottom: 1px solid #e4e7ed !important;
  padding: 12px 15px;
  text-align: center;
  vertical-align: middle;
}

.markdown-content th {
  background: linear-gradient(135deg, #409EFF, #36a3f7);
  color: white;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #409EFF !important;
  text-align: center;
}

.markdown-content th:first-child,
.markdown-content td:first-child {
  text-align: left;
  font-weight: 600;
}

.markdown-content td {
  background: #fff;
  transition: background-color 0.2s ease;
}

.markdown-content tr:hover td {
  background: #f8fafe;
}

.markdown-content tr:nth-child(even) td {
  background: #fafbfc;
}

.markdown-content tr:nth-child(even):hover td {
  background: #f0f6ff;
}

.markdown-content a {
  color: #409EFF;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

/* 集群巡检统计数据特殊样式 */
.markdown-content h2 + p,
.markdown-content h3 + p {
  margin-top: 8px;
}

/* 数字统计高亮 */
.markdown-content td:last-child {
  font-weight: 600;
  color: #409EFF;
  text-align: center;
}

/* 总计行特殊样式 */
.markdown-content tr:last-child td {
  background: #f0f9ff !important;
  border-top: 2px solid #409EFF;
  font-weight: 600;
}

.markdown-content tr:last-child td:first-child {
  color: #409EFF;
}

/* 命名空间表格样式优化 */
.markdown-content table + h3,
.markdown-content table + h2 {
  margin-top: 20px;
  color: #2c3e50;
  border-bottom: 2px solid #e4e7ed;
  padding-bottom: 8px;
}

/* 为0值添加特殊样式 */
.markdown-content td.zero-value {
  color: #909399;
  font-style: italic;
}

.markdown-content td.number-cell {
  background: #f0f9ff;
  font-weight: 700;
  color: #409EFF;
  text-align: center;
}

.markdown-content td.placeholder-cell {
  background: #fafbfc;
  color: #c0c4cc;
  font-weight: normal;
  text-align: center !important;
  font-style: italic;
}

/* 指标标题美化 */
.markdown-content h1,
.markdown-content h2 {
  color: #2c3e50;
  margin: 16px 0 12px 0;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-left: 4px solid #409EFF;
  border-radius: 0 8px 8px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: relative;
}

.markdown-content h1::before,
.markdown-content h2::before {
  content: "📊";
  margin-right: 8px;
  font-size: 0.9em;
}

/* 统计卡片样式 */
.markdown-content p.stats-item,
.markdown-content .stats-highlight {
  background: linear-gradient(135deg, #f6f9fc 0%, #e9ecef 100%);
  border-left: 4px solid #409EFF;
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 0 8px 8px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  font-weight: 500;
}

/* 关键指标数字突出显示 */
.markdown-content strong {
  color: #409EFF;
  font-size: 1.1em;
  font-weight: 700;
}

/* 表格容器增强 */
.markdown-content > table {
  margin: 16px 0;
  border: 3px solid #2c3e50 !important;
  border-radius: 8px;
  overflow: visible;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 空值或零值的特殊处理 */
.markdown-content td {
  position: relative;
}

.markdown-content td:empty::after {
  content: "—";
  color: #c0c4cc;
  font-style: normal;
}

/* 确保表格边框显示 */
.markdown-content th:last-child,
.markdown-content td:last-child {
  border-right: none !important;
}

.markdown-content tr:last-child td {
  border-bottom: none !important;
}

/* 表格容器 - 处理水平滚动 */
.markdown-content {
  overflow-x: auto; /* 允许水平滚动 */
}

/* 响应式表格 */
@media (max-width: 768px) {
  .markdown-content table {
    font-size: 11px;
    min-width: 500px; /* 在小屏幕上减少最小宽度 */
  }
  
  .markdown-content th,
  .markdown-content td {
    padding: 6px 8px;
    white-space: nowrap; /* 防止文本换行 */
  }
}

/* 供应商选择器样式 */
.provider-selector {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 16px 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.provider-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.provider-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  min-width: 120px;
}

.provider-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.provider-item.active {
  border-color: #409EFF;
  background: #ecf5ff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.provider-item.unavailable {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f7fa;
}

.provider-item.unavailable:hover {
  border-color: #e4e7ed;
  box-shadow: none;
}

.provider-icon {
  font-size: 18px;
  line-height: 1;
}

.provider-info {
  flex: 1;
  min-width: 0;
}

.provider-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-model {
  color: var(--text-secondary);
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-status {
  display: flex;
  align-items: center;
}

.status-available {
  color: #67c23a;
  font-size: 14px;
}

.status-unavailable {
  color: #f56c6c;
  font-size: 14px;
}

/* 系统消息样式 */
.system-message {
  margin: 16px 0;
  display: flex;
  justify-content: center;
}

.system-content {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 20px;
  font-size: 13px;
  color: #0369a1;
  max-width: 400px;
  text-align: center;
}

.system-content .el-icon {
  font-size: 14px;
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-messages {
    padding: 12px;
  }
  
  .message-bubble {
    max-width: 85%;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .input-tips {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .action-buttons {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .mcp-toggle {
    order: -1;
    align-self: center;
  }
}
</style>