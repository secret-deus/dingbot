<template>
  <div class="stream-chat">
    <!-- 消息列表区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div class="messages-wrapper">
        <!-- 欢迎消息（轻量面板） -->
        <div v-if="!chatStore.hasMessages" class="welcome-card">
          <div class="welcome-content">
            <div class="welcome-icon">AI</div>
            <h3>AI Mission Stream 已就绪</h3>
            <p>输入一个运维目标，我会按只读诊断、证据链、下一步动作组织结果，并保留工具调用轨迹。</p>
            <div class="example-questions">
              <h4>试试这些问题：</h4>
              <div class="question-chips">
                <el-button
                  v-for="example in exampleQuestions"
                  :key="example"
                  class="question-chip"
                  size="small"
                  text
                  @click="setInputMessage(example)"
                >
                  <el-icon class="question-icon"><Position /></el-icon>
                  <span>{{ example }}</span>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 消息列表 - 卡片式布局 -->
        <div
          v-for="message in chatStore.messages"
          :key="message.id"
          :id="`message-${message.id}`"
          :class="['message-card', `message-card-${message.type}`]"
        >
          <!-- 用户消息卡片 -->
          <div v-if="message.type === 'user'" class="user-message-card">
            <div class="card-content user-content">
              {{ message.content }}
            </div>
            <div class="bubble-meta">{{ formatTime(message.timestamp) }}</div>
          </div>

          <!-- 系统消息卡片 -->
          <div v-else-if="message.type === 'system'" class="system-message-card">
            <div class="system-content">
              <el-icon class="system-icon"><InfoFilled /></el-icon>
              <span>{{ message.content }}</span>
            </div>
          </div>

          <!-- AI助手消息卡片 -->
          <div v-else-if="message.type === 'assistant'" class="assistant-message-card">
            <div class="message-meta">
              <div class="meta-left">
                <span class="meta-role">AI</span>
                <div v-if="message.status === 'streaming'" class="meta-spinner">
                  <div class="spinner-container">
                    <div class="spinner"></div>
                  </div>
                </div>
              </div>
              <span class="meta-time">{{ formatTime(message.timestamp) }}</span>
            </div>

            <!-- 工具调用状态卡片 - 折叠式设计 -->
            <div v-if="getMessageToolCalls(message.id).length > 0" class="tool-calls-card">
              <div
                v-for="toolCall in getMessageToolCalls(message.id)"
                :key="toolCall.id"
                class="tool-call-card-wrapper"
              >
                <div
                  :class="['tool-call-card', `tool-call-${toolCall.status}`, { 'tool-call-expanded': isToolCallExpanded(message.id, toolCall.id) }]"
                  @click="toggleToolCallExpand(message.id, toolCall.id)"
                >
                  <!-- 卡片头部：始终可见 -->
                  <div class="tool-call-header">
                    <div v-if="toolCall.status === 'calling'" class="tool-icon-wrapper">
                      <div class="tool-spinner"></div>
                    </div>
                    <el-icon v-else class="tool-icon">
                      <Check v-if="toolCall.status === 'success'" />
                      <Close v-else-if="toolCall.status === 'error'" />
                    </el-icon>
                    <span class="tool-name">{{ getToolDisplayName(toolCall.tool) }}</span>
                    <el-tag
                      :type="toolCall.status === 'success' ? 'success' : toolCall.status === 'error' ? 'danger' : 'info'"
                      size="small"
                      effect="plain"
                      class="tool-status-tag"
                    >
                      {{ getToolStatusText(toolCall.status) }}
                    </el-tag>
                    <span v-if="toolCall.duration" class="tool-duration">
                      ({{ toolCall.duration }}秒)
                    </span>
                    <el-icon class="expand-icon" :class="{ 'expanded': isToolCallExpanded(message.id, toolCall.id) }">
                      <ArrowRight />
                    </el-icon>
                  </div>

                  <!-- 详细信息：可折叠 -->
                  <el-collapse-transition>
                    <div v-show="isToolCallExpanded(message.id, toolCall.id)" class="tool-call-details">
                      <!-- 参数信息 -->
                      <div v-if="toolCall.parameters && Object.keys(toolCall.parameters).length > 0" class="tool-detail-section">
                        <div class="tool-detail-label">参数</div>
                        <pre class="tool-detail-content">{{ JSON.stringify(toolCall.parameters, null, 2) }}</pre>
                      </div>

                      <!-- 结果信息 -->
                      <div v-if="toolCall.result" class="tool-detail-section">
                        <div class="tool-detail-label">结果</div>
                        <div class="tool-detail-content">
                          <pre v-if="typeof toolCall.result === 'object'">{{ JSON.stringify(toolCall.result, null, 2) }}</pre>
                          <div v-else>{{ toolCall.result }}</div>
                        </div>
                      </div>

                      <!-- 错误信息 -->
                      <div v-if="toolCall.status === 'error' && toolCall.error" class="tool-detail-section">
                        <div class="tool-detail-label">错误</div>
                        <div class="tool-detail-content error-content">{{ toolCall.error }}</div>
                      </div>
                    </div>
                  </el-collapse-transition>
                </div>
              </div>
            </div>

            <!-- 消息内容（带打字机效果） -->
            <div class="card-content assistant-content" @click="handleMarkdownClicks">
              <div
                v-if="message.status === 'streaming'"
                class="typing-text markdown-content"
                v-html="formatMessageContent(filterToolCallMessages(message.content), true)"
              ></div>
              <div
                v-else
                class="markdown-content"
                v-html="formatMessageContent(filterToolCallMessages(message.content), false)"
              ></div>
              <!-- 优化的等待动画 -->
              <div v-if="message.status === 'streaming' && (!message.content || message.content.trim() === '')" class="loading-animation">
                <div class="wave-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
                <span class="loading-text">AI正在思考中...</span>
              </div>
              <!-- 打字时的转圈动画 -->
              <div
                v-else-if="message.status === 'streaming'"
                class="typing-spinner-wrapper"
              >
                <div class="typing-spinner"></div>
              </div>
            </div>
            <div class="bubble-meta">{{ formatTime(message.timestamp) }}</div>
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

    <!-- 输入区域 - 卡片式布局 -->
    <div class="chat-input-container">
      <div class="input-card">
        <div class="input-wrapper">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="inputRows"
            placeholder="输入运维问题，例如：检查 checkout 服务 5xx 的根因，只读模式，输出证据和钉钉摘要..."
            @keydown="handleKeydown"
            :disabled="!chatStore.canSendMessage"
            class="message-input"
            resize="none"
          />
          <div class="input-actions">
            <div class="input-tips">
              <el-tag
                :type="toolsAllowed ? 'success' : 'info'"
                size="small"
                effect="plain"
                class="status-tag-item"
              >
                {{ props.enableTools ? `MCP ${enabledServersCount}/${totalServersCount}` : 'Tools Off' }}
              </el-tag>
              <span class="shortcut-tip">Ctrl + Enter 发送</span>
            </div>
            <div class="action-buttons">
              <!-- MCP服务器开关 -->
              <div class="mcp-toggle">
                <el-popover
                  placement="top-end"
                  :width="320"
                  trigger="click"
                  :show-arrow="false"
                >
                  <template #reference>
                    <el-button
                      size="small"
                      :type="toolsAllowed ? 'success' : 'info'"
                      :icon="Setting"
                    >
                      {{ props.enableTools ? `MCP (${enabledServersCount}/${totalServersCount})` : 'Tools Off' }}
                    </el-button>
                  </template>

                  <div class="mcp-servers-panel">
                    <div class="panel-header">
                      <h4>MCP服务器控制</h4>
                      <span class="panel-subtitle">选择要启用的MCP服务器</span>
                    </div>

                    <MCPServerSwitches
                      ref="mcpServerSwitches"
                      :auto-load="true"
                      :show-global-controls="true"
                      @servers-changed="handleServersChanged"
                      @server-toggled="handleServerToggled"
                    />
                  </div>
                </el-popover>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Monitor, Loading, Check, Close, Delete, Position,
  VideoPause, VideoPlay, InfoFilled, Setting, CircleCheckFilled, CircleCloseFilled, ArrowRight
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { api } from '@/api/client'
import { formatMessageContent } from '@/utils/markdown'
import { loadKatex } from '@/utils/katex'
import { createChatStreamParser } from '@/shared/stream/chatStream'
import MCPServerSwitches from './MCPServerSwitches.vue'

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

const messagesContainer = ref(null)
const showTypingCursor = ref(true)
const reconnecting = ref(false)
// MCP服务器状态
const mcpServerSwitches = ref(null)
const enabledServersCount = ref(0)
const totalServersCount = ref(0)
const mcpEnabled = computed(() => enabledServersCount.value > 0)
const toolsAllowed = computed(() => props.enableTools && mcpEnabled.value)
// 工具调用展开状态管理（每个消息的展开工具ID列表）
const expandedToolCalls = ref({})

// 检查工具调用是否展开
const isToolCallExpanded = (messageId, toolCallId) => {
  const expanded = expandedToolCalls.value[messageId] || []
  return expanded.includes(toolCallId)
}

// 切换工具调用的展开/折叠状态
const toggleToolCallExpand = (messageId, toolCallId) => {
  if (!expandedToolCalls.value[messageId]) {
    expandedToolCalls.value[messageId] = []
  }

  const expanded = expandedToolCalls.value[messageId]
  const index = expanded.indexOf(toolCallId)

  if (index > -1) {
    // 如果已展开，则折叠
    expanded.splice(index, 1)
  } else {
    // 如果已折叠，则展开
    expanded.push(toolCallId)
  }
}

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
  '诊断 checkout 服务 5xx，先只读排查',
  '检查 prod 集群节点压力并列证据',
  '生成一版钉钉事故摘要',
  '查看最近 Pod 重启和关键事件'
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

// 过滤消息内容中的工具调用信息
const filterToolCallMessages = (content) => {
  if (!content) return content

  // 过滤掉工具调用相关的文本信息（支持多种格式）
  const patterns = [
    // 工具调用开始
    /🛠️\s*\*\*正在调用工具\*\*:\s*`?[^`\n]+`?.*?\n/g,
    /🛠️\s*工具执行中.*?\n/g,
    // 参数信息
    /📋\s*\*\*参数\*\*:.*?\n/g,
    // 执行中
    /⏳\s*工具执行中\.\.\..*?\n/g,
    // 执行成功（包含耗时）
    /✅\s*\*\*工具执行成功\*\*:.*?\(耗时:.*?\)\s*\n/g,
    /✅\s*\*\*工具执行成功\*\*:.*?\n/g,
    // 结果摘要
    /📊\s*\*\*结果摘要\*\*:.*?\n/g,
    // 执行失败
    /❌\s*\*\*工具执行失败\*\*:.*?\n/g,
    // 工具执行成功（简单格式）
    /✅\s*工具执行成功:.*?\n/g,
    // 工具执行失败（简单格式）
    /❌\s*工具执行失败:.*?\n/g,
  ]

  let filtered = content
  patterns.forEach(pattern => {
    filtered = filtered.replace(pattern, '')
  })

  // 清理多余的连续换行
  filtered = filtered.replace(/\n{3,}/g, '\n\n')

  return filtered.trim()
}

// 处理Markdown点击事件（目录锚点、复制按钮）
const handleMarkdownClicks = (e) => {
  const target = e.target
  if (!target) return
  // 复制按钮
  if (target.classList && target.classList.contains('copy-btn')) {
    const codeEl = target.closest('.code-block')?.querySelector('pre code')
    if (codeEl) {
      const text = codeEl.innerText || ''
      navigator.clipboard.writeText(text).then(() => {
        ElMessage.success('已复制到剪贴板')
      })
    }
  }
  // 目录锚点平滑滚动
  if (target.tagName === 'A' && target.getAttribute('href')?.startsWith('#')) {
    const id = target.getAttribute('href').slice(1)
    const el = document.getElementById(id)
    if (el) {
      e.preventDefault()
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
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

    // 使用统一 API client 发送 POST 流式请求，复用鉴权和 401 会话失效处理。
    const response = await api.chat.streamChat(message, toolsAllowed.value)

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
    const parser = createChatStreamParser(handleChatStreamEvent)

    try {
      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          console.log('流式读取完成')
          break
        }

        // 解码数据并累积到缓冲区
        await parser.push(decoder.decode(value, { stream: true }))
      }

      // 处理缓冲区中剩余的数据
      await parser.flush()

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

const handleChatStreamEvent = async (event) => {
  if (!event) {
    return
  }

  if (event.type === 'done') {
    console.log('收到结束标识')
    chatStore.finishStreamMessage()
    return
  }

  if (event.type === 'legacy_content_update') {
    await handleContentUpdate(event.rawContent)
    return
  }

  await handleStructuredEvent(event)
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
    const dataContent = line.slice(6)  // 保留原始空白，后续自行判断

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
      appendStreamTextChunk(dataContent)
    }
  }
}

const appendStreamTextChunk = (content) => {
  let chunk = content
  // 对于纯空白片段：保留一个换行，但不累积多行
  if (!chunk || chunk.trim() === '') {
    const prevNL = (chatStore.currentStreamMessage?.content || '').endsWith('\n')
    if (!prevNL) {
      chatStore.appendStreamContent('\n')
    }
    return
  }
  // 防抖：若当前已以换行结束且新片段以换行开始，则合并为一个
  const prev = chatStore.currentStreamMessage?.content || ''
  if ((prev.endsWith('\n') || prev.endsWith('\r\n')) && /^\n+/.test(chunk)) {
    chunk = chunk.replace(/^\n+/, '\n')
  }
  // 追加并折叠连续3个以上的换行
  const combined = prev + chunk
  const collapsed = combined.replace(/\n{3,}/g, '\n\n')
  if (collapsed !== combined && chatStore.replaceStreamContent) {
    chatStore.replaceStreamContent(collapsed)
  } else {
    chatStore.appendStreamContent(chunk)
  }
  // 延迟滚动以确保DOM已更新
  setTimeout(() => {
    scrollToBottom()
  }, 10)
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
      case 'message_delta':
        appendStreamTextChunk(data.content || '')
        break

      case 'final':
        if (data.content) {
          appendStreamTextChunk(data.content)
        }
        chatStore.finishStreamMessage()
        break

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

      case 'tool_call_start':
        // 工具调用开始 - 创建工具调用卡片,状态为calling
        console.log('工具调用开始:', data)
        chatStore.addToolCall({
          id: data.id || data.tool_call?.id,
          tool: data.tool || data.tool_call?.name,
          status: 'calling',
          parameters: data.arguments || {}
        })
        // 初始化展开状态为折叠
        const messageId = chatStore.currentStreamMessage?.id
        if (messageId && !expandedToolCalls.value[messageId]) {
          expandedToolCalls.value[messageId] = []
        }
        break

      case 'tool_call_update':
      case 'tool_call_result':
        // 工具调用状态更新 - 更新工具调用卡片的状态和结果
        console.log('工具调用状态更新:', data)
        const toolCalls = chatStore.toolCalls
        const toolCall = toolCalls.find(tc =>
          tc.id === (data.id || data.tool_call?.id) ||
          (tc.tool === (data.tool || data.tool_call?.name) && tc.messageId === chatStore.currentStreamMessage?.id)
        )

        if (toolCall) {
          chatStore.updateToolCall(toolCall.id, {
            status: data.status || data.tool_call?.status || (data.success === false ? 'error' : 'success'),
            result: data.result || null,
            duration: data.duration || data.tool_call?.duration || null,
            error: data.error || null
          })
        }
        break

      case 'tool_call':
        // 处理工具调用(旧格式,兼容)
        handleToolCall(data)
        break

      case 'tool_result':
        // 处理工具结果 - 不再在消息内容中显示，只更新工具调用状态
        // 工具调用状态已通过 tool_call 事件更新，这里不需要额外处理
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
    const toolCall = chatStore.addToolCall({
      tool: data.tool,
      status: 'calling',
      parameters: data.parameters || {}
    })
    // 初始化展开状态为折叠（默认不展开）
    const messageId = chatStore.currentStreamMessage?.id
    if (messageId && !expandedToolCalls.value[messageId]) {
      expandedToolCalls.value[messageId] = []
    }
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
        result: data.result || null,
        duration: data.duration || null,
        error: data.error || null
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

// MCP服务器状态变化处理
const handleServersChanged = (data) => {
  enabledServersCount.value = data.total_enabled
  totalServersCount.value = data.servers.length

  if (data.total_enabled > 0) {
    const serverNames = data.servers
      .filter(s => s.enabled)
      .map(s => s.display_name)
      .join('、')
    ElMessage.success(`已启用 ${data.total_enabled} 个MCP服务器: ${serverNames}`)
  } else {
    ElMessage.info('所有MCP服务器已禁用，AI将仅提供文本回复')
  }
}

const handleServerToggled = async (data) => {
  // 如果需要刷新工具列表
  if (data.should_refresh_tools) {
    console.log('🔄 MCP服务器状态变更，正在刷新工具列表...')

    try {
      // 获取最新的工具列表
      const response = await api.system.getTools()
      const toolsCount = response.data.tools ? response.data.tools.length : 0

      console.log(`🛠️ 工具列表已更新，当前可用工具: ${toolsCount} 个`)

      // 显示更详细的状态信息
      if (data.enabled) {
        ElMessage.success(`${data.server_info.display_name} 已启用并连接，当前可用工具: ${toolsCount} 个`)
      } else {
        ElMessage.info(`${data.server_info.display_name} 已禁用并断开，当前可用工具: ${toolsCount} 个`)
      }
    } catch (error) {
      console.error('刷新工具列表失败:', error)
      // 降级显示基本信息
      if (data.enabled) {
        ElMessage.success(`${data.server_info.display_name} 服务器已启用`)
      } else {
        ElMessage.info(`${data.server_info.display_name} 服务器已禁用`)
      }
    }
  } else {
    // 没有要求刷新工具列表，显示基本信息
    if (data.enabled) {
      ElMessage.success(`${data.server_info.display_name} 服务器已启用`)
    } else {
      ElMessage.info(`${data.server_info.display_name} 服务器已禁用`)
    }
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

/* 欢迎消息卡片：大卡片采用浅色+轻微阴影 */
.welcome-card {
  max-width: 800px;
  margin: 40px auto;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96));
  border: 1px solid rgba(59, 130, 246, 0.14);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

.welcome-content {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.2));
}

.welcome-content h3 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 600;
}

.welcome-content p {
  margin: 0 0 32px 0;
  font-size: 16px;
  line-height: 1.6;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  color: var(--text-secondary);
}

.example-questions h4 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.question-chip {
  border-radius: 999px !important;
  border: 1px solid rgba(59, 130, 246, 0.18) !important;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.95), rgba(255, 255, 255, 0.95)) !important;
  color: #1f2937 !important;
  padding: 6px 10px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: hidden;
}

.question-chip::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.4s ease, height 0.4s ease;
}

.question-chip:hover {
  border-color: rgba(147, 51, 234, 0.22) !important;
  background: linear-gradient(180deg, rgba(250, 245, 255, 0.95), rgba(255, 255, 255, 0.95)) !important;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
}

.question-chip:hover::before {
  width: 200px;
  height: 200px;
}

.question-chip:active {
  transform: translateY(0) scale(0.98);
}

.question-icon {
  color: #667eea;
  font-size: 16px;
}

/* 消息卡片 */
.message-card {
  margin-bottom: 20px;
  animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 100%;
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.message-card:hover {
  transform: translateY(-2px);
}

/* 用户消息卡片：改为浅色气泡 */
.user-message-card {
  margin-left: auto;
  max-width: 75%;
  border-radius: 14px;
  background: var(--indigo-bg, #eef2ff);
  border: 2px solid var(--indigo-border, #c7d2fe);
  border-right: 4px solid var(--indigo-color, #6366f1);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 12px 14px;
  position: relative;
}

.user-message-card:hover {
  border-color: var(--indigo-color, #6366f1);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: none;
}

.card-avatar {
  display: none;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 0px;
}

.card-author {
  display: none;
}

.user-message-card .card-author {
  color: #1f2937;
}

.assistant-message-card .card-author {
  color: var(--text-primary);
}

.card-time {
  display: none;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meta-left {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.meta-role {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  letter-spacing: 0.2px;
}

.meta-time {
  font-size: 11px;
  color: #9ca3af;
}

.meta-spinner .spinner-container {
  width: 12px;
  height: 12px;
}

.bubble-meta {
  font-size: 11px;
  color: #9ca3af;
  text-align: right;
}

.user-message-card .card-time {
  color: #6b7280;
}

.assistant-message-card .card-time {
  color: var(--text-secondary);
}

.user-content {
  color: #111827;
  font-size: 14px;
  line-height: 1.65;
  word-wrap: break-word;
}

/* AI助手消息卡片：大面积内容，使用白底浅色风格 */
.assistant-message-card {
  margin-right: auto;
  max-width: 85%;
  min-width: 300px;
  border-radius: 14px;
  background: #ffffff;
  border: 2px solid var(--purple-border, #e9d5ff);
  border-left: 4px solid var(--purple-color, #9333ea);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  max-height: 80vh; /* 限制最大高度，避免过长 */
  overflow: hidden; /* 外层容器不滚动 */
  position: relative;
}

.assistant-message-card:hover {
  box-shadow: 0 8px 24px rgba(147, 51, 234, 0.15);
  border-color: var(--purple-color, #9333ea);
  transform: translateY(-2px);
}

/* 消息元信息区域 */
.assistant-message-card .message-meta {
  flex-shrink: 0;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

/* 工具调用卡片容器 */
.assistant-message-card .tool-calls-card {
  flex-shrink: 0;
  margin-bottom: 12px;
}

/* 消息内容区域 - 可滚动 */
.assistant-message-card .card-content.assistant-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0; /* 允许flex子元素收缩 */
  max-height: calc(80vh - 200px); /* 为元信息和工具卡片预留空间 */
  padding-right: 4px; /* 为滚动条预留空间 */
}

/* 滚动条样式 */
.assistant-message-card .card-content.assistant-content::-webkit-scrollbar {
  width: 6px;
}

.assistant-message-card .card-content.assistant-content::-webkit-scrollbar-track {
  background: transparent;
}

.assistant-message-card .card-content.assistant-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.assistant-message-card .card-content.assistant-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* 时间戳元信息 */
.assistant-message-card .bubble-meta {
  flex-shrink: 0;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

/* 当消息包含表格时，扩大卡片宽度 */
.assistant-message-card .markdown-content table {
  min-width: 600px;
  width: 100%;
  table-layout: auto;
}

.assistant-content {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.7;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* AI思考中状态指示器 */
.streaming-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
}

.spinner-container {
  width: 12px;
  height: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(59, 130, 246, 0.18);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.streaming-text {
  display: none;
}

/* 系统消息卡片 */
.system-message-card {
  max-width: 500px;
  margin: 16px auto;
  border-radius: 12px;
  background: rgba(240, 249, 255, 0.8);
  border: 1px solid rgba(186, 230, 253, 0.5);
  box-shadow: none;
}

.system-message-card {
  padding: 12px 16px;
}

.system-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #0369a1;
  text-align: center;
  justify-content: center;
}

.system-icon {
  font-size: 16px;
  color: #0369a1;
}

/* 工具调用状态卡片 - 折叠式设计 */
.tool-calls-card {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.tool-call-card-wrapper {
  width: 100%;
}

.tool-call-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  margin-bottom: 0;
  box-shadow: none;
  position: relative;
  overflow: hidden;
}

.tool-call-card:hover {
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.15);
  transform: translateX(4px);
}

.tool-call-card.tool-call-calling {
  border-left: 4px solid var(--info-color, #3b82f6);
  background: var(--indigo-bg, #eef2ff);
  border-color: var(--indigo-border, #c7d2fe);
}

.tool-call-card.tool-call-success {
  border-left: 4px solid var(--success-color, #10b981);
  background: var(--teal-bg, #f0fdfa);
  border-color: var(--teal-border, #ccfbf1);
}

.tool-call-card.tool-call-error {
  border-left: 4px solid var(--danger-color, #ef4444);
  background: var(--pink-bg, #fdf2f8);
  border-color: var(--pink-border, #fce7f3);
}

.tool-call-card {
  padding: 10px 12px;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  width: 100%;
}

.tool-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.tool-icon-wrapper {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(64, 158, 255, 0.2);
  border-top-color: #409EFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.tool-call-calling .tool-icon-wrapper .tool-spinner {
  border-top-color: #409EFF;
  border-right-color: rgba(64, 158, 255, 0.3);
  border-bottom-color: rgba(64, 158, 255, 0.2);
  border-left-color: rgba(64, 158, 255, 0.3);
}

.tool-call-success .tool-icon {
  color: #67C23A;
}

.tool-call-error .tool-icon {
  color: #F56C6C;
}

.tool-name {
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
}

.tool-status-tag {
  flex-shrink: 0;
}

.tool-duration {
  font-size: 11px;
  color: var(--text-secondary);
  margin-left: 4px;
}

.expand-icon {
  margin-left: auto;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.expand-icon.expanded {
  transform: rotate(90deg);
  color: var(--primary-color);
}

.tool-call-card:hover .expand-icon {
  color: var(--primary-color);
  transform: scale(1.1);
}

.tool-call-card:hover .expand-icon.expanded {
  transform: rotate(90deg) scale(1.1);
}

.tool-call-details {
  padding: 12px 0 0 0;
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    max-height: 1000px;
    transform: translateY(0);
  }
}

.tool-detail-section {
  margin-bottom: 12px;
}

.tool-detail-section:last-child {
  margin-bottom: 0;
}

.tool-detail-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.tool-detail-content {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.8);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.tool-detail-content pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.tool-detail-content.error-content {
  color: #F56C6C;
  background: rgba(245, 108, 108, 0.05);
  border-color: rgba(245, 108, 108, 0.2);
}

/* 消息内容 */
.card-content {
  position: relative;
  margin-top: 0;
}

.assistant-content {
  padding-left: 0;
  margin-top: 12px;
}

.user-content {
  margin-top: 0;
}

.typing-text {
  display: block;
}

/* 优化的等待动画 */
.loading-animation {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
  animation: fadeIn 0.3s ease-in;
}

.wave-dots {
  display: flex;
  gap: 6px;
  align-items: center;
}

.wave-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  animation: wave 1.4s ease-in-out infinite;
}

.wave-dots .dot:nth-child(1) {
  animation-delay: 0s;
}

.wave-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.wave-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes wave {
  0%, 60%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  30% {
    transform: scale(1.4);
    opacity: 1;
  }
}

.loading-text {
  font-size: 14px;
  color: #667eea;
  font-weight: 500;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin-left: 2px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 打字时的转圈动画 */
.typing-spinner-wrapper {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  vertical-align: middle;
}

.typing-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

/* 代码样式 */
.message-content :deep(pre) {
  background: #f7f9fc;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 6px 0;
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

/* 输入区域 - 卡片式布局 */
.chat-input-container {
  background: var(--background-page, #f6f8fa);
  border-top: 1px solid #e5e7eb;
  padding: 12px 12px;
}

.input-card {
  max-width: 1000px;
  margin: 0 auto;
  border-radius: 12px;
  background: #ffffff;
  border: 2px solid var(--orange-border, #fed7aa);
  border-bottom: 3px solid var(--orange-color, #f97316);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 12px 12px;
  position: relative;
}

.input-card:hover {
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.15);
  border-color: var(--orange-color, #f97316);
  transform: translateY(-2px);
}

.input-card:focus-within {
  box-shadow: 0 8px 24px rgba(249, 115, 22, 0.2);
  border-color: var(--orange-color, #f97316);
}

.input-wrapper {
  width: 100%;
}

.message-input {
  margin-bottom: 12px;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  line-height: 1.6;
}

.message-input :deep(.el-textarea__inner):focus {
  border-color: rgba(59, 130, 246, 0.55);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  transform: scale(1.01);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.input-tips {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  flex-wrap: wrap;
}

.status-tag-item {
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 8px;
}

.shortcut-tip {
  display: none;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons :deep(.el-button) {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-buttons :deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-buttons :deep(.el-button:active) {
  transform: translateY(0);
}

/* MCP开关样式 */
.mcp-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.20);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mcp-toggle:hover {
  background: rgba(59, 130, 246, 0.10);
  border-color: rgba(59, 130, 246, 0.30);
  transform: scale(1.05);
}

.mcp-info-icon {
  font-size: 14px;
  color: var(--text-secondary);
  cursor: help;
  transition: color 0.3s ease;
}

.mcp-servers-panel {
  padding: 0;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: 12px;
}

.panel-header h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.panel-subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.mcp-info-icon:hover {
  color: #409EFF;
}

/* Markdown 内容样式 */
.markdown-content {
  line-height: 1.65;
  white-space: normal; /* 避免把模板中的换行当作可见空行 */
  word-break: break-word;
  overflow-wrap: anywhere;
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
  margin: 12px 0 6px 0;
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-content h1 { font-size: 1.5em; }
.markdown-content h2 { font-size: 1.3em; }
.markdown-content h3 { font-size: 1.15em; }

.markdown-content p {
  margin: 10px 0;
}

/* 紧凑段落间距 */
.markdown-content p + p {
  margin-top: 16px;
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
  background: #1f2937;
  color: #e5e7eb;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0 14px 0; /* 稍微放宽上下间距 */
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-content ul,
.markdown-content ol {
  margin: 6px 0;
  padding-left: 24px;
  list-style-position: outside;
}

.markdown-content li {
  margin: 0;
  line-height: 1.55;
  margin-bottom: 3px;
}

.markdown-content li p {
  margin: 0;
}

/* 嵌套列表间距 */
.markdown-content li > ul,
.markdown-content li > ol {
  margin-top: 4px;
  margin-bottom: 4px;
}

/* 列表项之间更紧凑 */
.markdown-content li + li {
  margin-top: 3px;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-size: 14px;
  border: 1px solid #e4e7ed !important;
  min-width: 600px; /* 设置最小宽度防止过度压缩 */
}

.markdown-content th,
.markdown-content td {
  border-right: 1px solid #e9edf3 !important;
  border-bottom: 1px solid #e9edf3 !important;
  padding: 10px 12px;
  text-align: center;
  vertical-align: middle;
}

.markdown-content th {
  background: #f7f9fc;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.3px;
  border-bottom: 1px solid #e9edf3 !important;
  text-align: center;
}

.markdown-content th:first-child,
.markdown-content td:first-child {
  text-align: left;
  font-weight: 600;
}

.markdown-content td {
  background: #fff;
  transition: background-color 0.15s ease;
}

.markdown-content tr:hover td {
  background: #f8fbff;
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


/* 让通过 v-html 注入的 markdown 内容也应用到间距（使用 :deep 穿透 scoped） */
.message-content :deep(.markdown-content) {
  line-height: 1.65;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.message-content :deep(.markdown-content h1),
.message-content :deep(.markdown-content h2),
.message-content :deep(.markdown-content h3),
.message-content :deep(.markdown-content h4),
.message-content :deep(.markdown-content h5),
.message-content :deep(.markdown-content h6) {
  margin: 12px 0 6px 0;
}

.message-content :deep(.markdown-content p) {
  margin: 10px 0;
}

.message-content :deep(.markdown-content p + p) {
  margin-top: 16px;
}

.message-content :deep(.markdown-content pre) {
  margin: 12px 0 14px 0;
}

.message-content :deep(.markdown-content ul),
.message-content :deep(.markdown-content ol) {
  margin: 6px 0;
}

.message-content :deep(.markdown-content li) {
  line-height: 1.55;
  margin-bottom: 3px;
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

/* 为消息卡片添加延迟，实现依次出现的效果 */
.message-card:nth-child(1) { animation-delay: 0s; }
.message-card:nth-child(2) { animation-delay: 0.05s; }
.message-card:nth-child(3) { animation-delay: 0.1s; }
.message-card:nth-child(4) { animation-delay: 0.15s; }
.message-card:nth-child(5) { animation-delay: 0.2s; }
.message-card:nth-child(n+6) { animation-delay: 0.25s; }

/* 响应式 */
@media (max-width: 768px) {
  .chat-messages {
    padding: 12px;
  }

  .user-message-card,
  .assistant-message-card {
    max-width: 95%;
    max-height: 75vh;
  }

  .assistant-message-card .card-content.assistant-content {
    max-height: calc(75vh - 180px);
  }

  .welcome-card {
    margin: 20px auto;
    max-width: 95%;
  }

  .input-card {
    max-width: 100%;
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

  .card-header {
    flex-wrap: wrap;
    gap: 8px;
  }

  .question-chip {
    width: 100%;
    justify-content: flex-start;
  }
}

/* Cockpit stream overrides */
.stream-chat {
  --stream-bg: #0a0f12;
  --stream-panel: #10171b;
  --stream-panel-2: #121d22;
  --stream-border: #26343b;
  --stream-border-strong: #31505a;
  --stream-text: #edf7f7;
  --stream-muted: #8ea0a8;
  --stream-cyan: #35d9f4;
  --stream-green: #4ee6a0;
  --stream-amber: #ffbe55;
  height: 100%;
  min-height: 0;
  background: var(--stream-bg) !important;
  color: var(--stream-text);
}

.chat-messages {
  min-height: 0;
  padding: 18px !important;
  background:
    linear-gradient(180deg, rgba(53, 217, 244, 0.035), rgba(7, 11, 14, 0) 28%),
    var(--stream-bg) !important;
}

.messages-wrapper {
  width: 100%;
  max-width: none !important;
  padding: 0 !important;
}

.welcome-card {
  max-width: 760px !important;
  margin: 18px auto !important;
  border: 1px solid var(--stream-border) !important;
  border-radius: 8px !important;
  background:
    linear-gradient(135deg, rgba(53, 217, 244, 0.1), rgba(18, 29, 34, 0.96) 34%),
    var(--stream-panel) !important;
  box-shadow: none !important;
}

.welcome-card:hover {
  transform: none !important;
  box-shadow: none !important;
}

.welcome-content {
  padding: 18px !important;
  text-align: left !important;
}

.welcome-icon {
  width: 42px !important;
  height: 42px !important;
  margin: 0 0 12px !important;
  border: 1px solid rgba(53, 217, 244, 0.55);
  border-radius: 8px !important;
  background: rgba(53, 217, 244, 0.12) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
  color: var(--stream-cyan);
  font-size: 14px !important;
  font-weight: 900;
}

.welcome-content h3 {
  margin: 0 0 8px !important;
  color: var(--stream-text) !important;
  font-size: 20px !important;
  letter-spacing: 0 !important;
}

.welcome-content p {
  max-width: 620px;
  margin: 0 0 14px !important;
  color: var(--stream-muted) !important;
  font-size: 14px !important;
  line-height: 1.7 !important;
}

.example-questions h4 {
  margin: 0 0 10px !important;
  color: #c8d8de !important;
  font-size: 12px !important;
}

.question-chips {
  justify-content: flex-start !important;
  gap: 8px !important;
}

.question-chip {
  min-height: 34px !important;
  border: 1px solid var(--stream-border) !important;
  border-radius: 8px !important;
  background: rgba(7, 11, 14, 0.72) !important;
  color: #c8d8de !important;
  font-weight: 700 !important;
}

.question-chip::before {
  display: none !important;
}

.question-chip:hover {
  border-color: var(--stream-cyan) !important;
  background: rgba(53, 217, 244, 0.12) !important;
  color: var(--stream-cyan) !important;
  transform: none !important;
}

.question-icon {
  color: var(--stream-cyan) !important;
}

.message-card {
  margin-bottom: 14px !important;
  animation: none !important;
}

.user-message-card,
.assistant-message-card {
  border-radius: 8px !important;
  box-shadow: none !important;
}

.user-message-card {
  max-width: min(76%, 780px) !important;
  margin-left: auto !important;
  padding: 13px 14px !important;
  border: 1px solid rgba(53, 217, 244, 0.32) !important;
  background: linear-gradient(135deg, rgba(22, 57, 64, 0.95), rgba(12, 24, 28, 0.95)) !important;
  color: var(--stream-text) !important;
}

.user-message-card:hover,
.assistant-message-card:hover,
.tool-call-card:hover,
.input-card:hover {
  transform: none !important;
}

.assistant-message-card {
  max-width: min(88%, 980px) !important;
  padding: 14px !important;
  border: 1px solid var(--stream-border) !important;
  background: rgba(16, 23, 27, 0.96) !important;
  color: var(--stream-text) !important;
}

.message-meta {
  margin-bottom: 12px !important;
  padding-bottom: 10px !important;
  border-bottom: 1px solid rgba(38, 52, 59, 0.8);
}

.meta-role {
  color: var(--stream-cyan) !important;
  font-size: 11px !important;
  font-weight: 900 !important;
  letter-spacing: 0 !important;
  text-transform: uppercase;
}

.meta-time,
.bubble-meta,
.shortcut-tip {
  color: var(--stream-muted) !important;
}

.card-content,
.assistant-content {
  color: var(--stream-text) !important;
}

.system-content {
  border: 1px solid rgba(255, 190, 85, 0.34) !important;
  border-radius: 8px !important;
  background: rgba(255, 190, 85, 0.08) !important;
  color: #ffd99a !important;
}

.tool-calls-card {
  margin-bottom: 12px !important;
}

.tool-call-card {
  border: 1px solid var(--stream-border) !important;
  border-radius: 8px !important;
  background: rgba(7, 11, 14, 0.62) !important;
  box-shadow: none !important;
}

.tool-call-success {
  border-color: rgba(78, 230, 160, 0.34) !important;
  background: rgba(78, 230, 160, 0.08) !important;
}

.tool-call-calling {
  border-color: rgba(53, 217, 244, 0.36) !important;
  background: rgba(53, 217, 244, 0.08) !important;
}

.tool-call-error {
  border-color: rgba(248, 113, 113, 0.42) !important;
  background: rgba(248, 113, 113, 0.08) !important;
}

.tool-name {
  color: var(--stream-text) !important;
  font-weight: 800;
}

.tool-duration,
.tool-detail-label {
  color: var(--stream-muted) !important;
}

.tool-detail-content {
  border: 1px solid var(--stream-border) !important;
  border-radius: 8px !important;
  background: #070b0e !important;
  color: #d4e4e8 !important;
}

.chat-input-container {
  padding: 10px 13px !important;
  border-top: 1px solid var(--stream-border) !important;
  background: rgba(7, 11, 14, 0.96) !important;
}

.input-card {
  max-width: none !important;
  margin: 0 !important;
  padding: 10px !important;
  border: 1px solid var(--stream-border-strong) !important;
  border-radius: 8px !important;
  background: var(--stream-panel) !important;
  box-shadow: none !important;
}

.message-input :deep(.el-textarea__inner) {
  min-height: 46px !important;
  border: 1px solid var(--stream-border) !important;
  border-radius: 8px !important;
  background: #070b0e !important;
  box-shadow: none !important;
  color: var(--stream-text) !important;
  line-height: 1.55 !important;
}

.message-input :deep(.el-textarea__inner::placeholder) {
  color: #5f737b !important;
}

.input-actions {
  margin-top: 8px !important;
}

.status-tag-item {
  border-color: rgba(53, 217, 244, 0.34) !important;
  background: rgba(53, 217, 244, 0.08) !important;
  color: var(--stream-cyan) !important;
}

.mcp-toggle :deep(.el-button),
.action-buttons :deep(.el-button) {
  border-color: var(--stream-border) !important;
  border-radius: 8px !important;
  background: #0a1114 !important;
  color: #c8d8de !important;
}

.action-buttons :deep(.el-button--primary) {
  border-color: rgba(53, 217, 244, 0.72) !important;
  background: rgba(53, 217, 244, 0.16) !important;
  color: var(--stream-cyan) !important;
}

.mcp-servers-panel {
  color: #1f2937;
}

.loading-text {
  color: var(--stream-muted) !important;
}

.markdown-content {
  color: #d7e7eb !important;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin: 14px 0 10px !important;
  padding: 0 0 0 10px !important;
  border-left: 3px solid var(--stream-cyan) !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--stream-text) !important;
}

.markdown-content h1::before,
.markdown-content h2::before {
  display: none !important;
}

.markdown-content p,
.markdown-content li {
  color: #d7e7eb !important;
}

.markdown-content strong {
  color: var(--stream-green) !important;
  font-size: 1em !important;
}

.markdown-content code {
  border: 1px solid var(--stream-border) !important;
  border-radius: 6px !important;
  background: #070b0e !important;
  color: var(--stream-cyan) !important;
}

.markdown-content pre,
.markdown-content blockquote {
  border-color: var(--stream-border) !important;
  border-radius: 8px !important;
  background: #070b0e !important;
  color: #d7e7eb !important;
}

.markdown-content table {
  border: 1px solid var(--stream-border) !important;
  border-radius: 8px !important;
  background: #070b0e !important;
  box-shadow: none !important;
}

.markdown-content th {
  border-color: var(--stream-border) !important;
  background: rgba(53, 217, 244, 0.12) !important;
  color: var(--stream-cyan) !important;
}

.markdown-content td {
  border-color: var(--stream-border) !important;
  background: rgba(16, 23, 27, 0.84) !important;
  color: #d7e7eb !important;
}

.markdown-content tr:nth-child(even) td,
.markdown-content tr:last-child td {
  background: rgba(18, 29, 34, 0.84) !important;
}

.markdown-content a {
  color: var(--stream-cyan) !important;
}

@media (max-width: 1280px) {
  .question-chip:nth-child(n+3) {
    display: none !important;
  }
}

@media (max-width: 768px) {
  .chat-messages {
    padding: 12px !important;
  }

  .user-message-card,
  .assistant-message-card {
    max-width: 100% !important;
  }

  .welcome-content {
    padding: 18px !important;
  }

  .input-actions {
    align-items: stretch !important;
  }
}
</style>
