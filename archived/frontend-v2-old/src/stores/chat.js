import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import {
  storageManager,
  StorageError,
  StorageQuotaError,
  StorageSecurityError,
  STORAGE_KEYS
} from '@/utils/storage'

// Debounced save utility
let saveTimeout = null
const debouncedSave = (saveFunction, delay = 1000) => {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }
  saveTimeout = setTimeout(() => {
    saveFunction()
    saveTimeout = null
  }, delay)
}

// Persistence middleware - 持久化中间件
class PersistenceMiddleware {
  constructor(saveFunction) {
    this.saveFunction = saveFunction
    this.isEnabled = true
    this.saveQueue = new Set()
    this.lastSaveTime = 0
    this.minSaveInterval = 100 // 最小保存间隔（毫秒）
  }

  // 启用/禁用自动保存
  setEnabled(enabled) {
    this.isEnabled = enabled
    console.log(`持久化中间件已${enabled ? '启用' : '禁用'}`)
  }

  // 触发保存操作
  triggerSave(operation, delay = 500) {
    if (!this.isEnabled) return

    const now = Date.now()
    const timeSinceLastSave = now - this.lastSaveTime

    // 防止过于频繁的保存操作
    if (timeSinceLastSave < this.minSaveInterval) {
      delay = Math.max(delay, this.minSaveInterval - timeSinceLastSave)
    }

    this.saveQueue.add(operation)

    debouncedSave(() => {
      if (this.saveQueue.size > 0) {
        // 执行持久化操作
        this.saveQueue.clear()
        this.lastSaveTime = Date.now()
        this.saveFunction()
      }
    }, delay)
  }

  // 立即保存（用于重要操作）
  immediateSave(operation) {
    if (!this.isEnabled) return

    console.log(`⚡ 立即执行持久化操作: ${operation}`)
    this.saveQueue.clear() // 清除队列中的延迟保存
    this.lastSaveTime = Date.now()
    this.saveFunction()
  }

  // 批量保存（用于多个相关操作）
  batchSave(operations, delay = 300) {
    if (!this.isEnabled) return

    operations.forEach(op => this.saveQueue.add(op))
    this.triggerSave('batch', delay)
  }
}

export const useChatStore = defineStore('chat', () => {
  // 当前会话状态
  const currentSessionId = ref(null)
  const messages = ref([])
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const currentStreamMessage = ref(null)
  const toolCalls = ref([])
  const connectionError = ref(null)
  const retryCount = ref(0)
  const maxRetries = ref(3)

  // 初始化持久化中间件（延迟初始化，因为saveToStorage还未定义）
  let persistenceMiddleware = null

  // 会话管理
  const sessions = ref(new Map()) // sessionId -> session对象
  const sessionHistory = ref([]) // 会话历史列表
  const maxSessions = ref(50) // 最大会话数量

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const canSendMessage = computed(() => isConnected.value && !isStreaming.value)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])
  const currentSession = computed(() => {
    if (!currentSessionId.value) return null
    return sessions.value.get(currentSessionId.value)
  })

  const toDate = (value, fallback = new Date()) => {
    if (value instanceof Date) return value
    const date = new Date(value || fallback)
    return Number.isNaN(date.getTime()) ? fallback : date
  }

  const getSessionMessageCount = (session) => {
    if (Array.isArray(session?.messages)) return session.messages.length
    return session?.metadata?.messageCount || 0
  }

  const buildSessionSummary = (session) => {
    const messagesForPreview = Array.isArray(session?.messages) ? session.messages : []
    const lastUserMessage = [...messagesForPreview].reverse().find((msg) => msg.type === 'user')
    const fallbackPreview = messagesForPreview[messagesForPreview.length - 1]?.content || ''
    const preview = (lastUserMessage?.content || fallbackPreview || '').replace(/\s+/g, ' ').trim()

    return {
      id: session.id,
      title: session.title || '未命名对话',
      createdAt: toDate(session.createdAt),
      updatedAt: toDate(session.updatedAt),
      preview: preview.slice(0, 96),
      metadata: {
        messageCount: getSessionMessageCount(session),
        lastActivity: toDate(session.metadata?.lastActivity || session.updatedAt),
        tags: Array.isArray(session.metadata?.tags) ? [...session.metadata.tags] : []
      }
    }
  }

  const syncSessionSummary = (sessionId) => {
    const session = sessions.value.get(sessionId)
    if (!session) return

    const summary = buildSessionSummary(session)
    const index = sessionHistory.value.findIndex(item => item.id === sessionId)
    if (index === -1) {
      sessionHistory.value.unshift(summary)
    } else {
      sessionHistory.value[index] = summary
    }
  }

  const refreshSessionHistory = () => {
    const summaries = Array.from(sessions.value.values()).map(buildSessionSummary)
    summaries.sort((a, b) => toDate(b.metadata.lastActivity || b.updatedAt) - toDate(a.metadata.lastActivity || a.updatedAt))
    sessionHistory.value = summaries
  }

  const syncCurrentSession = () => {
    if (currentSessionId.value && sessions.value.has(currentSessionId.value)) {
      const currentSess = sessions.value.get(currentSessionId.value)
      currentSess.messages = [...messages.value]
      currentSess.toolCalls = [...toolCalls.value]
      currentSess.updatedAt = new Date()
      currentSess.metadata = {
        ...(currentSess.metadata || {}),
        messageCount: messages.value.length,
        lastActivity: new Date(),
        tags: Array.isArray(currentSess.metadata?.tags) ? currentSess.metadata.tags : []
      }
      syncSessionSummary(currentSessionId.value)
    }
  }

  // 会话验证和修复
  const validateSession = (session) => {
    try {
      // 检查必需字段
      if (!session || typeof session !== 'object') {
        return { valid: false, errors: ['会话对象无效'] }
      }

      const errors = []

      // 验证基本字段
      if (!session.id || typeof session.id !== 'string') {
        errors.push('会话ID无效')
      }

      if (!session.title || typeof session.title !== 'string') {
        errors.push('会话标题无效')
      }

      if (!session.createdAt || !(session.createdAt instanceof Date)) {
        errors.push('创建时间无效')
      }

      if (!session.updatedAt || !(session.updatedAt instanceof Date)) {
        errors.push('更新时间无效')
      }

      // 验证消息数组
      if (!Array.isArray(session.messages)) {
        errors.push('消息数组无效')
      } else {
        session.messages.forEach((msg, index) => {
          if (!msg.id || !msg.content === undefined || !msg.timestamp) {
            errors.push(`消息 ${index} 数据不完整`)
          }
        })
      }

      // 验证工具调用数组
      if (!Array.isArray(session.toolCalls)) {
        errors.push('工具调用数组无效')
      }

      // 验证元数据
      if (!session.metadata || typeof session.metadata !== 'object') {
        errors.push('元数据无效')
      } else {
        if (typeof session.metadata.messageCount !== 'number') {
          errors.push('消息计数无效')
        }
        if (!Array.isArray(session.metadata.tags)) {
          errors.push('标签数组无效')
        }
      }

      return {
        valid: errors.length === 0,
        errors
      }
    } catch (error) {
      return {
        valid: false,
        errors: [`验证过程出错: ${error.message}`]
      }
    }
  }

  const repairSession = (session) => {
    try {
      const repairedSession = { ...session }

      // 修复基本字段
      if (!repairedSession.id) {
        repairedSession.id = `repaired_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
      }

      if (!repairedSession.title) {
        repairedSession.title = '修复的对话'
      }

      if (!repairedSession.createdAt || !(repairedSession.createdAt instanceof Date)) {
        repairedSession.createdAt = new Date()
      }

      if (!repairedSession.updatedAt || !(repairedSession.updatedAt instanceof Date)) {
        repairedSession.updatedAt = new Date()
      }

      // 修复消息数组
      if (!Array.isArray(repairedSession.messages)) {
        repairedSession.messages = []
      } else {
        repairedSession.messages = repairedSession.messages.map((msg, index) => ({
          id: msg.id || `repaired_msg_${Date.now()}_${index}`,
          type: msg.type || 'user',
          content: msg.content || '',
          timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp || Date.now()),
          status: msg.status || 'sent',
          toolCalls: Array.isArray(msg.toolCalls) ? msg.toolCalls : [],
          metadata: msg.metadata || {}
        }))
      }

      // 修复工具调用数组
      if (!Array.isArray(repairedSession.toolCalls)) {
        repairedSession.toolCalls = []
      }

      // 修复元数据
      if (!repairedSession.metadata || typeof repairedSession.metadata !== 'object') {
        repairedSession.metadata = {}
      }

      repairedSession.metadata = {
        messageCount: repairedSession.messages.length,
        lastActivity: repairedSession.metadata.lastActivity instanceof Date ?
          repairedSession.metadata.lastActivity : new Date(),
        tags: Array.isArray(repairedSession.metadata.tags) ?
          repairedSession.metadata.tags : [],
        ...repairedSession.metadata
      }

      return repairedSession
    } catch (error) {
      console.error('修复会话失败:', error)
      // 返回最小可用会话
      return {
        id: `emergency_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
        title: '紧急修复的对话',
        createdAt: new Date(),
        updatedAt: new Date(),
        messages: [],
        toolCalls: [],
        metadata: {
          messageCount: 0,
          lastActivity: new Date(),
          tags: []
        }
      }
    }
  }

  // 原子会话操作
  const atomicSessionOperation = async (operation, sessionId = null) => {
    const backupData = {
      sessions: new Map(sessions.value),
      sessionHistory: [...sessionHistory.value],
      currentSessionId: currentSessionId.value,
      messages: [...messages.value],
      toolCalls: [...toolCalls.value]
    }

    try {
      const result = await operation()

      // 操作成功，保存数据
      if (persistenceMiddleware) {
        persistenceMiddleware.immediateSave('atomicSessionOperation')
      } else {
        await saveToStorage()
      }

      return { success: true, result }
    } catch (error) {
      console.error('原子操作失败，正在回滚:', error)

      // 回滚到备份状态
      sessions.value = backupData.sessions
      sessionHistory.value = backupData.sessionHistory
      currentSessionId.value = backupData.currentSessionId
      messages.value = backupData.messages
      toolCalls.value = backupData.toolCalls

      return { success: false, error: error.message }
    }
  }

  // 会话管理方法
  const createSession = (title = null) => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
    const session = {
      id: sessionId,
      title: title || `对话 ${sessionHistory.value.length + 1}`,
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: [],
      toolCalls: [],
      metadata: {
        messageCount: 0,
        lastActivity: new Date(),
        tags: []
      }
    }

    // 验证新会话
    const validation = validateSession(session)
    if (!validation.valid) {
      console.warn('新创建的会话验证失败，正在修复:', validation.errors)
      const repairedSession = repairSession(session)
      sessions.value.set(repairedSession.id, repairedSession)
      sessionHistory.value.unshift(buildSessionSummary(repairedSession))
      switchToSession(repairedSession.id)
      saveToStorage()
      return repairedSession
    }

    sessions.value.set(sessionId, session)
    sessionHistory.value.unshift(buildSessionSummary(session))

    // 限制会话数量
    if (sessionHistory.value.length > maxSessions.value) {
      const oldSession = sessionHistory.value.pop()
      sessions.value.delete(oldSession.id)
    }

    switchToSession(sessionId)
    saveToStorage()
    return session
  }

  const switchToSession = (sessionId) => {
    // 保存当前会话状态
    syncCurrentSession()

    // 切换到新会话
    currentSessionId.value = sessionId
    const session = sessions.value.get(sessionId)

    if (session) {
      messages.value = [...session.messages]
      toolCalls.value = [...session.toolCalls]

      // 更新会话顺序（最近使用的排到前面）
      const index = sessionHistory.value.findIndex(s => s.id === sessionId)
      if (index > 0) {
        const [session] = sessionHistory.value.splice(index, 1)
        sessionHistory.value.unshift(session)
      }
    } else {
      messages.value = []
      toolCalls.value = []
    }

    // 重置连接状态
    currentStreamMessage.value = null
    isStreaming.value = false
    connectionError.value = null
    saveToStorage()
  }

  const deleteSession = (sessionId) => {
    if (sessions.value.has(sessionId)) {
      sessions.value.delete(sessionId)
      const index = sessionHistory.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessionHistory.value.splice(index, 1)
      }

      // 如果删除的是当前会话，切换到最近的会话
      if (currentSessionId.value === sessionId) {
        if (sessionHistory.value.length > 0) {
          switchToSession(sessionHistory.value[0].id)
        } else {
          // 创建新会话
          createSession()
        }
      }

      saveToStorage()
    }
  }

  const updateSessionTitle = (sessionId, newTitle) => {
    const session = sessions.value.get(sessionId)
    if (session) {
      session.title = newTitle
      session.updatedAt = new Date()
      syncSessionSummary(sessionId)
      saveToStorage()
    }
  }

  const addSessionTag = (sessionId, tag) => {
    const session = sessions.value.get(sessionId)
    if (session && !session.metadata.tags.includes(tag)) {
      session.metadata.tags.push(tag)
      session.updatedAt = new Date()
      syncSessionSummary(sessionId)
      saveToStorage()
    }
  }

  const removeSessionTag = (sessionId, tag) => {
    const session = sessions.value.get(sessionId)
    if (session) {
      const index = session.metadata.tags.indexOf(tag)
      if (index !== -1) {
        session.metadata.tags.splice(index, 1)
        session.updatedAt = new Date()
        syncSessionSummary(sessionId)
        saveToStorage()
      }
    }
  }

  // 性能优化 - 搜索索引
  const searchIndex = ref(new Map()) // 消息内容搜索索引
  const sessionIndex = ref(new Map()) // 会话元数据索引

  const buildSearchIndex = () => {
    try {
      console.log('🔍 构建搜索索引...')

      searchIndex.value.clear()
      sessionIndex.value.clear()

      for (const [sessionId, session] of sessions.value) {
        // 构建会话索引
        const sessionKeywords = [
          session.title.toLowerCase(),
          ...session.metadata.tags.map(tag => tag.toLowerCase()),
          sessionId.toLowerCase()
        ]

        sessionIndex.value.set(sessionId, {
          keywords: sessionKeywords,
          createdAt: session.createdAt,
          updatedAt: session.updatedAt,
          messageCount: session.messages.length,
          lastActivity: session.metadata.lastActivity
        })

        // 构建消息内容索引
        session.messages.forEach((message, index) => {
          const words = message.content.toLowerCase().split(/\s+/)
          words.forEach(word => {
            if (word.length > 2) { // 忽略太短的词
              if (!searchIndex.value.has(word)) {
                searchIndex.value.set(word, [])
              }
              searchIndex.value.get(word).push({
                sessionId,
                messageIndex: index,
                messageId: message.id,
                timestamp: message.timestamp
              })
            }
          })
        })
      }

      console.log(`✅ 搜索索引构建完成: ${searchIndex.value.size} 个词条, ${sessionIndex.value.size} 个会话`)
    } catch (error) {
      console.error('构建搜索索引失败:', error)
    }
  }

  // 优化的搜索功能
  const searchSessions = (query, options = {}) => {
    const { tags = [], dateRange = null, messageCountRange = null, useIndex = true } = options

    if (!useIndex || searchIndex.value.size === 0) {
      // 回退到原始搜索
      return searchSessionsOriginal(query, options)
    }

    try {
      let candidateSessions = new Set()

      // 使用索引进行文本搜索
      if (query) {
        const searchTerms = query.toLowerCase().split(/\s+/)

        for (const term of searchTerms) {
          // 精确匹配
          if (searchIndex.value.has(term)) {
            searchIndex.value.get(term).forEach(result => {
              candidateSessions.add(result.sessionId)
            })
          }

          // 前缀匹配
          for (const [word, results] of searchIndex.value) {
            if (word.startsWith(term)) {
              results.forEach(result => {
                candidateSessions.add(result.sessionId)
              })
            }
          }
        }

        // 会话标题和标签搜索
        for (const [sessionId, sessionData] of sessionIndex.value) {
          if (sessionData.keywords.some(keyword =>
            searchTerms.some(term => keyword.includes(term))
          )) {
            candidateSessions.add(sessionId)
          }
        }
      } else {
        // 无查询条件时，包含所有会话
        candidateSessions = new Set(sessions.value.keys())
      }

      // 应用其他过滤条件
      const filtered = Array.from(candidateSessions)
        .map(sessionId => sessions.value.get(sessionId))
        .filter(session => {
          if (!session) return false

          // 标签过滤
          if (tags.length > 0) {
            const hasTag = tags.some(tag => session.metadata.tags.includes(tag))
            if (!hasTag) return false
          }

          // 日期范围过滤
          if (dateRange) {
            const sessionDate = new Date(session.createdAt)
            if (dateRange.start && sessionDate < dateRange.start) return false
            if (dateRange.end && sessionDate > dateRange.end) return false
          }

          // 消息数量过滤
          if (messageCountRange) {
            const count = session.metadata.messageCount
            if (messageCountRange.min && count < messageCountRange.min) return false
            if (messageCountRange.max && count > messageCountRange.max) return false
          }

          return true
        })
        .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)) // 按更新时间排序

      return filtered
    } catch (error) {
      console.error('索引搜索失败，回退到原始搜索:', error)
      return searchSessionsOriginal(query, options)
    }
  }

  // 原始搜索方法（作为回退）
  const searchSessionsOriginal = (query, options = {}) => {
    const { tags = [], dateRange = null, messageCountRange = null } = options

    let filtered = sessionHistory.value.filter(session => {
      const fullSession = sessions.value.get(session.id) || session
      // 文本搜索
      if (query) {
        const searchText = query.toLowerCase()
        const titleMatch = session.title.toLowerCase().includes(searchText)
        const messageMatch = (fullSession.messages || []).some(msg =>
          msg.content.toLowerCase().includes(searchText)
        )
        if (!titleMatch && !messageMatch) return false
      }

      // 标签过滤
      if (tags.length > 0) {
        const hasTag = tags.some(tag => session.metadata.tags.includes(tag))
        if (!hasTag) return false
      }

      // 日期范围过滤
      if (dateRange) {
        const sessionDate = new Date(session.createdAt)
        if (dateRange.start && sessionDate < dateRange.start) return false
        if (dateRange.end && sessionDate > dateRange.end) return false
      }

      // 消息数量过滤
      if (messageCountRange) {
        const count = getSessionMessageCount(fullSession)
        if (messageCountRange.min && count < messageCountRange.min) return false
        if (messageCountRange.max && count > messageCountRange.max) return false
      }

      return true
    })

    return filtered
  }

  const searchMessages = (query, sessionId = null) => {
    const searchText = query.toLowerCase()
    const results = []

    const sessionsToSearch = sessionId ?
      [sessions.value.get(sessionId)].filter(Boolean) :
      Array.from(sessions.value.values())

    sessionsToSearch.forEach(session => {
      session.messages.forEach((message, index) => {
        if (message.content.toLowerCase().includes(searchText)) {
          results.push({
            sessionId: session.id,
            sessionTitle: session.title,
            messageIndex: index,
            message: message,
            context: getMessageContext(session.messages, index)
          })
        }
      })
    })

    return results.sort((a, b) =>
      new Date(b.message.timestamp) - new Date(a.message.timestamp)
    )
  }

  const getMessageContext = (messages, index, contextSize = 2) => {
    const start = Math.max(0, index - contextSize)
    const end = Math.min(messages.length, index + contextSize + 1)
    return messages.slice(start, end)
  }

  // 消息管理（现有功能保持不变，但需要同步到当前会话）
  const addMessage = (message) => {
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const newMessage = {
      id: messageId,
      type: message.type || 'user',
      content: message.content || '',
      timestamp: new Date(),
      status: message.status || 'sent',
      toolCalls: message.toolCalls || [],
      metadata: message.metadata || {}
    }

    messages.value.push(newMessage)

    // 自动生成会话标题（基于第一条用户消息）
    if (currentSession.value && !currentSession.value.title.startsWith('对话')) {
      // 已有自定义标题，不修改
    } else if (newMessage.type === 'user' && messages.value.filter(m => m.type === 'user').length === 1) {
      const title = newMessage.content.slice(0, 30) + (newMessage.content.length > 30 ? '...' : '')
      if (currentSession.value) {
        currentSession.value.title = title
      }
    }

    syncCurrentSession()

    // 自动保存（使用持久化中间件）
    if (persistenceMiddleware) {
      persistenceMiddleware.triggerSave('addMessage', 500)
    } else {
      debouncedSave(saveToStorage, 500)
    }

    return newMessage
  }

  const updateMessage = (messageId, updates) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...messages.value[messageIndex],
        ...updates,
        timestamp: messages.value[messageIndex].timestamp
      }

      // 自动保存（使用持久化中间件）
      if (persistenceMiddleware) {
        persistenceMiddleware.triggerSave('updateMessage', 500)
      } else {
        debouncedSave(saveToStorage, 500)
      }
    }
  }

  const appendToLastMessage = (content) => {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg.type === 'assistant') {
        lastMsg.content += content
        lastMsg.timestamp = new Date()

        // 自动保存（防抖）- 流式消息内容更新
        if (persistenceMiddleware) {
          persistenceMiddleware.triggerSave('appendToLastMessage', 1000)
        } else {
          debouncedSave(saveToStorage, 1000)
        }
      }
    }
  }

  // 流式消息管理（保持不变）
  const startStreamMessage = () => {
    currentStreamMessage.value = addMessage({
      type: 'assistant',
      content: '',
      status: 'streaming'
    })
    isStreaming.value = true
    return currentStreamMessage.value
  }

  const appendStreamContent = (content) => {
    if (currentStreamMessage.value) {
      currentStreamMessage.value.content += content
      currentStreamMessage.value.timestamp = new Date()
    }
  }

  const replaceStreamContent = (content) => {
    if (currentStreamMessage.value) {
      currentStreamMessage.value.content = content
      currentStreamMessage.value.timestamp = new Date()
      console.log('🔧 替换流式消息内容，新长度:', content.length)
    }
  }

  const finishStreamMessage = () => {
    if (currentStreamMessage.value) {
      currentStreamMessage.value.status = 'sent'
      currentStreamMessage.value = null
    }
    isStreaming.value = false

    // 流式消息完成时立即保存
    if (persistenceMiddleware) {
      persistenceMiddleware.immediateSave('finishStreamMessage')
    } else {
      debouncedSave(saveToStorage, 200)
    }
  }

  const cancelStreamMessage = () => {
    if (currentStreamMessage.value) {
      currentStreamMessage.value.status = 'error'
      currentStreamMessage.value.content += '\n\n[消息传输中断]'
      currentStreamMessage.value = null
    }
    isStreaming.value = false
  }

  // 工具调用管理（保持不变但添加会话同步）
  const addToolCall = (toolCall) => {
    const toolCallId = toolCall.id || `tool_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const newToolCall = {
      id: toolCallId,
      tool: toolCall.tool,
      status: toolCall.status || 'calling',
      parameters: toolCall.parameters || {},
      result: toolCall.result || null,
      timestamp: new Date(),
      messageId: currentStreamMessage.value?.id
    }
    toolCalls.value.push(newToolCall)
    return newToolCall
  }

  const updateToolCall = (toolCallId, updates) => {
    const toolCallIndex = toolCalls.value.findIndex(tc => tc.id === toolCallId)
    if (toolCallIndex !== -1) {
      toolCalls.value[toolCallIndex] = {
        ...toolCalls.value[toolCallIndex],
        ...updates
      }

      // 工具调用更新时自动保存
      if (persistenceMiddleware) {
        persistenceMiddleware.triggerSave('updateToolCall', 500)
      } else {
        debouncedSave(saveToStorage, 500)
      }
    }
  }

  const getToolCallsForMessage = (messageId) => {
    return toolCalls.value.filter(tc => tc.messageId === messageId)
  }

  // 连接状态管理（保持不变）
  const setConnected = (connected) => {
    isConnected.value = connected
    if (connected) {
      connectionError.value = null
      retryCount.value = 0
    }
  }

  const setConnectionError = (error) => {
    connectionError.value = error
    isConnected.value = false
  }

  const incrementRetry = () => {
    retryCount.value++
    return retryCount.value <= maxRetries.value
  }

  const resetRetry = () => {
    retryCount.value = 0
  }

  // 存储状态管理
  const storageStatus = ref({
    type: 'localStorage',
    isAvailable: true,
    quota: { used: 0, available: 0, percentage: 0, needsCleanup: false },
    hasFallback: false,
    lastError: null
  })

  // 数据持久化 - 增强版本
  const saveToStorage = async () => {
    try {
      syncCurrentSession()
      refreshSessionHistory()

      const data = {
        version: '2.1',
        currentSessionId: currentSessionId.value,
        sessions: Array.from(sessions.value.entries()),
        sessionHistory: sessionHistory.value,
        timestamp: new Date().toISOString()
      }

      const success = await storageManager.save(STORAGE_KEYS.CHAT_HISTORY, data)
      if (success) {
        // 更新存储状态
        storageStatus.value = storageManager.getStorageStatus()
        storageStatus.value.lastError = null
        console.log('✅ 聊天历史保存成功')
      }

      return success
    } catch (error) {
      console.error('保存聊天历史失败:', error)
      storageStatus.value.lastError = error.message

      // 根据错误类型提供用户友好的提示
      if (error instanceof StorageQuotaError) {
        console.warn('存储空间不足，建议清理旧对话')
        // 可以触发清理建议的UI提示
      } else if (error instanceof StorageSecurityError) {
        console.warn('存储访问被阻止，请检查浏览器设置')
      }

      return false
    }
  }

  // 初始化持久化中间件
  if (!persistenceMiddleware) {
    persistenceMiddleware = new PersistenceMiddleware(saveToStorage)
  }

  const loadFromStorage = async () => {
    try {
      console.log('开始加载聊天历史...')

      // 更新存储状态
      storageStatus.value = storageManager.getStorageStatus()

      const data = await storageManager.load(STORAGE_KEYS.CHAT_HISTORY)
      if (data) {


        if (String(data.version || '').startsWith('2.')) {
          // 检查是否需要渐进式加载
          const sessionEntries = Array.isArray(data.sessions) ? data.sessions : Object.entries(data.sessions)
          const totalSessions = sessionEntries.length

          if (totalSessions > 20) {
            // 大数据集，使用渐进式加载
            console.log(`📦 检测到大数据集 (${totalSessions} 个会话)，启用渐进式加载`)
            await loadSessionsProgressively(data)
          } else {
            // 小数据集，直接加载
            console.log('📦 小数据集，直接加载会话...')

            // 🔧 修复：手动转换Date对象和确保数据完整性
            const sessionEntries = Array.isArray(data.sessions) ? data.sessions : Object.entries(data.sessions)
            const processedSessions = new Map()

            sessionEntries.forEach(([sessionId, session]) => {
              // 转换Date字符串回Date对象
              const processedSession = {
                ...session,
                createdAt: new Date(session.createdAt),
                updatedAt: new Date(session.updatedAt),
                messages: session.messages ? session.messages.map(msg => ({
                  ...msg,
                  timestamp: new Date(msg.timestamp)
                })) : [],
                toolCalls: session.toolCalls ? session.toolCalls.map(tc => ({
                  ...tc,
                  timestamp: new Date(tc.timestamp)
                })) : [],
                metadata: {
                  ...session.metadata,
                  lastActivity: new Date(session.metadata?.lastActivity || session.updatedAt)
                }
              }

              console.log(`📝 处理会话 ${sessionId}: ${processedSession.messages.length} 条消息`)
              processedSessions.set(sessionId, processedSession)
            })

            sessions.value = processedSessions
            sessionHistory.value = (data.sessionHistory || Array.from(processedSessions.values())).map((session) => {
              const fullSession = processedSessions.get(session.id)
              return buildSessionSummary(fullSession || {
                ...session,
                createdAt: toDate(session.createdAt),
                updatedAt: toDate(session.updatedAt),
                messages: [],
                toolCalls: [],
                metadata: {
                  ...(session.metadata || {}),
                  lastActivity: toDate(session.metadata?.lastActivity || session.updatedAt)
                }
              })
            })

            console.log(`✅ 直接加载完成: ${sessions.value.size} 个会话`)
          }

          // 恢复当前会话
          if (data.currentSessionId && sessions.value.has(data.currentSessionId)) {
            const sessionToRestore = sessions.value.get(data.currentSessionId)
            switchToSession(data.currentSessionId)

            // 检测并修复消息丢失问题
            if (messages.value.length === 0 && sessionToRestore.messages && sessionToRestore.messages.length > 0) {
              messages.value = [...sessionToRestore.messages]
              toolCalls.value = [...(sessionToRestore.toolCalls || [])]
            }
          } else if (sessionHistory.value.length > 0) {
            switchToSession(sessionHistory.value[0].id)
          } else {
            createSession()
          }

          console.log(`📊 加载统计: ${sessions.value.size} 个会话, ${sessionHistory.value.length} 条历史记录`)
        } else {
          // 处理旧版本数据迁移
          console.log('🔄 检测到旧版本数据，开始迁移...')
          await migrateOldData(data)
        }
      } else {
        console.log('📝 未找到历史数据，创建新会话')
        createSession()
      }

      // 清除错误状态
      storageStatus.value.lastError = null

    } catch (error) {
      console.error('加载聊天历史失败:', error)
      storageStatus.value.lastError = error.message

      // 根据错误类型提供不同的恢复策略
      if (error instanceof StorageError) {
        console.warn('存储错误，尝试恢复机制')

        // 尝试从备份恢复
        try {
          const backup = await storageManager.restoreFromBackup(STORAGE_KEYS.CHAT_HISTORY)
          if (backup) {
            console.log('✅ 从备份成功恢复数据')
            // 递归调用加载备份数据
            await loadFromStorage()
            return
          }
        } catch (backupError) {
          console.warn('备份恢复也失败:', backupError)
        }
      }

      // 最后的回退：创建新会话
      console.log('🆕 创建全新会话作为回退')
      createSession()
    }
  }

  // 渐进式加载大型对话历史
  const loadSessionsProgressively = async (data, batchSize = 10) => {
    try {
      console.log('🔄 开始渐进式加载会话数据...')

      const sessionEntries = Array.isArray(data.sessions) ? data.sessions : Object.entries(data.sessions)
      const totalSessions = sessionEntries.length

      if (totalSessions <= batchSize) {
        // 小数据集，直接加载
        sessions.value = new Map(sessionEntries)
        sessionHistory.value = data.sessionHistory || []
        return
      }

      // 大数据集，分批加载
      console.log(`📦 大数据集检测到 ${totalSessions} 个会话，开始分批加载...`)

      // 首先加载最近的会话
      const recentSessions = sessionEntries.slice(0, batchSize)
      sessions.value = new Map(recentSessions)

      // 创建简化的会话历史（只包含元数据）
      sessionHistory.value = sessionEntries.map(([id, session]) => ({
        id: session.id,
        title: session.title,
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
        metadata: session.metadata,
        // 标记为未完全加载
        _isFullyLoaded: sessions.value.has(id)
      }))

      console.log(`✅ 首批加载完成: ${batchSize}/${totalSessions} 个会话`)

      // 异步加载剩余会话
      setTimeout(async () => {
        await loadRemainingSessionsInBackground(sessionEntries.slice(batchSize))
      }, 100)

    } catch (error) {
      console.error('渐进式加载失败:', error)
      // 回退到直接加载
      sessions.value = new Map(data.sessions)
      sessionHistory.value = data.sessionHistory || []
    }
  }

  // 后台加载剩余会话
  const loadRemainingSessionsInBackground = async (remainingSessions, batchSize = 5) => {
    try {
      console.log(`🔄 后台加载剩余 ${remainingSessions.length} 个会话...`)

      for (let i = 0; i < remainingSessions.length; i += batchSize) {
        const batch = remainingSessions.slice(i, i + batchSize)

        // 加载这一批会话
        batch.forEach(([id, session]) => {
          sessions.value.set(id, session)

          // 更新会话历史中的加载状态
          const historyItem = sessionHistory.value.find(s => s.id === id)
          if (historyItem) {
            historyItem._isFullyLoaded = true
          }
        })

        console.log(`✅ 后台加载进度: ${Math.min(i + batchSize, remainingSessions.length)}/${remainingSessions.length}`)

        // 让出控制权，避免阻塞UI
        await new Promise(resolve => setTimeout(resolve, 10))
      }

      console.log('✅ 所有会话后台加载完成')
    } catch (error) {
      console.error('后台加载失败:', error)
    }
  }

  // 按需加载会话详情
  const loadSessionOnDemand = async (sessionId) => {
    try {
      const session = sessions.value.get(sessionId)
      if (session && session._isFullyLoaded !== false) {
        return session // 已经完全加载
      }

      // 从存储中重新加载这个会话的完整数据
      const data = await storageManager.load(STORAGE_KEYS.CHAT_HISTORY)
      if (data && data.sessions) {
        const sessionEntries = Array.isArray(data.sessions) ? data.sessions : Object.entries(data.sessions)
        const sessionEntry = sessionEntries.find(([id]) => id === sessionId)

        if (sessionEntry) {
          const [id, fullSession] = sessionEntry
          sessions.value.set(id, fullSession)

          // 更新会话历史
          const historyItem = sessionHistory.value.find(s => s.id === id)
          if (historyItem) {
            Object.assign(historyItem, fullSession)
            historyItem._isFullyLoaded = true
          }

          console.log(`✅ 按需加载会话: ${sessionId}`)
          return fullSession
        }
      }

      return null
    } catch (error) {
      console.error(`按需加载会话失败 ${sessionId}:`, error)
      return null
    }
  }

  const migrateOldData = async (oldData) => {
    try {
      console.log('🔄 开始数据迁移，版本:', oldData.version || 'unknown')

      // 处理不同版本的数据迁移
      if (oldData.version === '1.0' || (!oldData.version && oldData.messages)) {
        // 从v1.0或无版本数据迁移
        await migrateFromV1(oldData)
      } else if (oldData.sessions && !oldData.sessionHistory) {
        // 从早期v2.0数据迁移
        await migrateFromEarlyV2(oldData)
      } else {
        console.warn('未知的数据格式，创建新会话')
        createSession()
      }

      console.log('✅ 数据迁移完成')
    } catch (error) {
      console.error('数据迁移失败:', error)
      createSession()
    }
  }

  const migrateFromV1 = async (oldData) => {
    try {
      if (oldData.messages && Array.isArray(oldData.messages)) {
        const session = createSession('迁移的对话')

        // 迁移消息数据，确保数据完整性
        session.messages = oldData.messages.map((msg, index) => ({
          id: msg.id || `migrated_msg_${Date.now()}_${index}`,
          type: msg.type || 'user',
          content: msg.content || '',
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          status: msg.status || 'sent',
          toolCalls: msg.toolCalls || [],
          metadata: msg.metadata || {}
        }))

        // 迁移工具调用数据
        session.toolCalls = (oldData.toolCalls || []).map((tc, index) => ({
          id: tc.id || `migrated_tool_${Date.now()}_${index}`,
          tool: tc.tool || 'unknown',
          status: tc.status || 'completed',
          parameters: tc.parameters || {},
          result: tc.result || null,
          timestamp: tc.timestamp ? new Date(tc.timestamp) : new Date(),
          messageId: tc.messageId || null
        }))

        // 设置会话元数据
        session.createdAt = new Date(oldData.exportTime || oldData.timestamp || Date.now())
        session.updatedAt = new Date()
        session.metadata.messageCount = session.messages.length
        session.metadata.lastActivity = new Date()

        switchToSession(session.id)
        console.log(`✅ 从v1.0迁移了 ${session.messages.length} 条消息`)
      } else {
        createSession()
      }
    } catch (error) {
      console.error('v1.0数据迁移失败:', error)
      createSession()
    }
  }

  const migrateFromEarlyV2 = async (oldData) => {
    try {
      // 从早期v2.0格式迁移（缺少sessionHistory）
      if (oldData.sessions) {
        const sessionEntries = Array.isArray(oldData.sessions) ?
          oldData.sessions : Object.entries(oldData.sessions)

        sessions.value = new Map(sessionEntries)
        sessionHistory.value = Array.from(sessions.value.values())

        // 按更新时间排序
        sessionHistory.value.sort((a, b) =>
          new Date(b.updatedAt || b.createdAt) - new Date(a.updatedAt || a.createdAt)
        )

        // 恢复当前会话
        if (oldData.currentSessionId && sessions.value.has(oldData.currentSessionId)) {
          switchToSession(oldData.currentSessionId)
        } else if (sessionHistory.value.length > 0) {
          switchToSession(sessionHistory.value[0].id)
        } else {
          createSession()
        }

        console.log(`✅ 从早期v2.0迁移了 ${sessions.value.size} 个会话`)
      } else {
        createSession()
      }
    } catch (error) {
      console.error('早期v2.0数据迁移失败:', error)
      createSession()
    }
  }

  // 数据导入导出
  const exportAllSessions = () => {
    return {
      version: '2.1',
      sessions: Object.fromEntries(sessions.value),
      sessionHistory: Array.from(sessions.value.values()).map(buildSessionSummary),
      exportTime: new Date(),
      metadata: {
        totalSessions: sessions.value.size,
        totalMessages: Array.from(sessions.value.values()).reduce(
          (sum, session) => sum + session.messages.length, 0
        )
      }
    }
  }

  const exportSession = (sessionId) => {
    const session = sessions.value.get(sessionId)
    if (!session) return null

    return {
      version: '2.1',
      session: session,
      exportTime: new Date()
    }
  }

  const importSessions = (data) => {
    if (String(data.version || '').startsWith('2.')) {
      if (data.sessions) {
        // 导入多个会话
        Object.entries(data.sessions).forEach(([id, session]) => {
          sessions.value.set(id, session)
          if (!sessionHistory.value.find(s => s.id === id)) {
            sessionHistory.value.push(buildSessionSummary(session))
          }
        })
      } else if (data.session) {
        // 导入单个会话
        const newId = `imported_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        const importedSession = {
          ...data.session,
          id: newId,
          title: `[导入] ${data.session.title}`
        }
        sessions.value.set(newId, importedSession)
        sessionHistory.value.unshift(buildSessionSummary(importedSession))
        switchToSession(newId)
      }

      saveToStorage()
      return true
    }
    return false
  }

  // 存储管理工具
  const getStorageInfo = async () => {
    try {
      await storageManager.updateStorageQuota()
      const status = storageManager.getStorageStatus()

      // 计算详细的存储使用情况
      const totalSessions = sessions.value.size
      const totalMessages = Array.from(sessions.value.values()).reduce(
        (sum, session) => sum + session.messages.length, 0
      )

      // 估算数据大小
      const dataSize = new Blob([JSON.stringify({
        sessions: Array.from(sessions.value.entries()),
        sessionHistory: sessionHistory.value
      })]).size

      return {
        ...status,
        totalSessions,
        totalMessages,
        estimatedDataSize: dataSize,
        formattedDataSize: storageManager.formatBytes(dataSize),
        needsCleanup: status.quota.needsCleanup || dataSize > 2 * 1024 * 1024 // 2MB threshold
      }
    } catch (error) {
      console.error('获取存储信息失败:', error)
      return {
        type: 'unknown',
        isAvailable: false,
        quota: { used: 0, available: 0, percentage: 0, needsCleanup: false },
        hasFallback: false,
        totalSessions: sessions.value.size,
        totalMessages: 0,
        estimatedDataSize: 0,
        formattedDataSize: '0 B',
        needsCleanup: false
      }
    }
  }

  const cleanupOldSessions = async (options = {}) => {
    try {
      const {
        maxSessions = 30,
        maxAge = 30 * 24 * 60 * 60 * 1000, // 30天
        minMessages = 1,
        strategy = 'lru' // 'lru', 'oldest', 'size-based'
      } = options

      console.log('🧹 开始清理旧会话...')

      let sessionsToRemove = []
      const now = Date.now()

      // 根据策略选择要删除的会话
      switch (strategy) {
        case 'oldest':
          // 按创建时间删除最旧的会话
          sessionsToRemove = sessionHistory.value
            .filter(session => {
              const age = now - new Date(session.createdAt).getTime()
              return age > maxAge && getSessionMessageCount(session) >= minMessages
            })
            .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
          break

        case 'size-based':
          // 按消息数量删除最小的会话
          sessionsToRemove = sessionHistory.value
            .filter(session => getSessionMessageCount(session) < minMessages)
            .sort((a, b) => getSessionMessageCount(a) - getSessionMessageCount(b))
          break

        case 'lru':
        default:
          // 按最近使用时间删除（LRU）
          sessionsToRemove = sessionHistory.value
            .filter(session => {
              const lastActivity = new Date(session.metadata.lastActivity || session.updatedAt).getTime()
              const age = now - lastActivity
              return age > maxAge && getSessionMessageCount(session) >= minMessages
            })
            .sort((a, b) => {
              const aActivity = new Date(a.metadata.lastActivity || a.updatedAt).getTime()
              const bActivity = new Date(b.metadata.lastActivity || b.updatedAt).getTime()
              return aActivity - bActivity
            })
          break
      }

      // 限制删除数量，保留最少的会话数
      if (sessionHistory.value.length - sessionsToRemove.length < 5) {
        sessionsToRemove = sessionsToRemove.slice(0, Math.max(0, sessionHistory.value.length - 5))
      }

      // 如果会话总数超过限制，删除多余的会话
      if (sessionHistory.value.length > maxSessions) {
        const excessCount = sessionHistory.value.length - maxSessions
        const additionalToRemove = sessionHistory.value
          .slice(-excessCount)
          .filter(session => !sessionsToRemove.includes(session))

        sessionsToRemove = [...sessionsToRemove, ...additionalToRemove]
      }

      // 执行删除
      let removedCount = 0
      for (const session of sessionsToRemove) {
        if (session.id !== currentSessionId.value) { // 不删除当前会话
          sessions.value.delete(session.id)
          const index = sessionHistory.value.findIndex(s => s.id === session.id)
          if (index !== -1) {
            sessionHistory.value.splice(index, 1)
            removedCount++
          }
        }
      }

      if (removedCount > 0) {
        // 保存更新后的数据
        if (persistenceMiddleware) {
          persistenceMiddleware.immediateSave('cleanupOldSessions')
        } else {
          await saveToStorage()
        }

        console.log(`✅ 清理完成，删除了 ${removedCount} 个旧会话`)
      } else {
        console.log('✅ 无需清理，所有会话都符合保留条件')
      }

      return {
        success: true,
        removedCount,
        remainingSessions: sessions.value.size,
        strategy
      }
    } catch (error) {
      console.error('清理旧会话失败:', error)
      return {
        success: false,
        error: error.message,
        removedCount: 0,
        remainingSessions: sessions.value.size,
        strategy: options.strategy || 'lru'
      }
    }
  }

  const compressStorageData = async () => {
    try {
      console.log('🗜️ 开始压缩存储数据...')

      let compressedCount = 0
      let savedBytes = 0

      // 压缩长消息内容
      for (const [sessionId, session] of sessions.value) {
        let sessionModified = false

        for (const message of session.messages) {
          if (message.content && message.content.length > 1000) {
            const originalSize = new Blob([message.content]).size

            // 简单的压缩：移除多余的空白字符
            const compressed = message.content
              .replace(/\s+/g, ' ')
              .replace(/\n\s*\n/g, '\n')
              .trim()

            if (compressed.length < message.content.length) {
              const newSize = new Blob([compressed]).size
              savedBytes += originalSize - newSize
              message.content = compressed
              message.metadata = message.metadata || {}
              message.metadata.compressed = true
              sessionModified = true
              compressedCount++
            }
          }
        }

        if (sessionModified) {
          session.updatedAt = new Date()
        }
      }

      if (compressedCount > 0) {
        // 保存压缩后的数据
        if (persistenceMiddleware) {
          persistenceMiddleware.immediateSave('compressStorageData')
        } else {
          await saveToStorage()
        }

        console.log(`✅ 压缩完成，处理了 ${compressedCount} 条消息，节省了 ${storageManager.formatBytes(savedBytes)}`)
      } else {
        console.log('✅ 无需压缩，数据已经很紧凑')
      }

      return {
        success: true,
        compressedCount,
        savedBytes,
        formattedSavedBytes: storageManager.formatBytes(savedBytes)
      }
    } catch (error) {
      console.error('压缩存储数据失败:', error)
      return {
        success: false,
        error: error.message,
        compressedCount: 0,
        savedBytes: 0
      }
    }
  }

  const performStorageHealthCheck = async () => {
    try {
      console.log('🔍 开始存储健康检查...')

      const issues = []
      const fixes = []

      // 检查数据完整性
      let corruptedSessions = 0
      let repairedSessions = 0

      for (const [sessionId, session] of sessions.value) {
        let sessionIssues = []

        // 检查必需字段
        if (!session.id || !session.title || !session.createdAt) {
          sessionIssues.push('缺少必需字段')
        }

        // 检查消息完整性
        if (!Array.isArray(session.messages)) {
          sessionIssues.push('消息数据格式错误')
          session.messages = []
          repairedSessions++
        } else {
          session.messages.forEach((msg, index) => {
            if (!msg.id || !msg.content === undefined || !msg.timestamp) {
              sessionIssues.push(`消息 ${index} 数据不完整`)
              // 修复消息数据
              msg.id = msg.id || `repaired_msg_${Date.now()}_${index}`
              msg.content = msg.content || ''
              msg.timestamp = msg.timestamp || new Date()
              msg.type = msg.type || 'user'
              msg.status = msg.status || 'sent'
              repairedSessions++
            }
          })
        }

        // 检查工具调用完整性
        if (!Array.isArray(session.toolCalls)) {
          sessionIssues.push('工具调用数据格式错误')
          session.toolCalls = []
          repairedSessions++
        }

        // 检查元数据
        if (!session.metadata) {
          sessionIssues.push('缺少元数据')
          session.metadata = {
            messageCount: session.messages.length,
            lastActivity: new Date(),
            tags: []
          }
          repairedSessions++
        }

        if (sessionIssues.length > 0) {
          corruptedSessions++
          issues.push(`会话 ${sessionId}: ${sessionIssues.join(', ')}`)
        }
      }

      // 检查会话历史一致性
      const sessionHistoryIds = new Set(sessionHistory.value.map(s => s.id))
      const sessionMapIds = new Set(sessions.value.keys())

      // 修复会话历史中缺少的会话
      for (const sessionId of sessionMapIds) {
        if (!sessionHistoryIds.has(sessionId)) {
          const session = sessions.value.get(sessionId)
          sessionHistory.value.push(buildSessionSummary(session))
          fixes.push(`添加缺少的会话历史: ${sessionId}`)
        }
      }

      // 移除会话历史中多余的会话
      sessionHistory.value = sessionHistory.value.filter(session => {
        if (!sessionMapIds.has(session.id)) {
          fixes.push(`移除多余的会话历史: ${session.id}`)
          return false
        }
        return true
      })

      // 如果有修复，保存数据
      if (fixes.length > 0 || repairedSessions > 0) {
        if (persistenceMiddleware) {
          persistenceMiddleware.immediateSave('performStorageHealthCheck')
        } else {
          await saveToStorage()
        }
      }

      const healthScore = Math.max(0, 100 - (corruptedSessions * 10) - (issues.length * 5))

      console.log(`✅ 健康检查完成，健康评分: ${healthScore}/100`)

      return {
        success: true,
        healthScore,
        totalSessions: sessions.value.size,
        corruptedSessions,
        repairedSessions,
        issues,
        fixes,
        recommendations: healthScore < 80 ? [
          '建议定期备份数据',
          '考虑清理旧会话',
          '检查存储空间使用情况'
        ] : []
      }
    } catch (error) {
      console.error('存储健康检查失败:', error)
      return {
        success: false,
        error: error.message,
        healthScore: 0,
        totalSessions: sessions.value.size,
        corruptedSessions: 0,
        repairedSessions: 0,
        issues: [error.message],
        fixes: [],
        recommendations: ['请检查存储系统状态']
      }
    }
  }

  // 错误恢复机制
  const resetToCleanState = async () => {
    try {
      console.warn('🔄 重置到干净状态...')

      // 清除所有会话数据
      sessions.value.clear()
      sessionHistory.value = []
      messages.value = []
      toolCalls.value = []
      currentSessionId.value = null
      currentStreamMessage.value = null

      // 重置存储状态
      storageStatus.value = {
        type: 'localStorage',
        isAvailable: true,
        quota: { used: 0, available: 0, percentage: 0, needsCleanup: false },
        hasFallback: false,
        lastError: null
      }

      // 清除存储中的数据
      await storageManager.resetToCleanState()

      // 创建新的干净会话
      createSession('新的开始')

      console.log('✅ 已重置到干净状态')
      return { success: true, message: '系统已重置到干净状态' }
    } catch (error) {
      console.error('重置到干净状态失败:', error)
      return { success: false, error: error.message }
    }
  }

  const createEmergencyBackup = async () => {
    try {
      console.log('创建紧急备份...')

      const backupData = {
        version: '2.1',
        timestamp: new Date().toISOString(),
        type: 'emergency_backup',
        currentSessionId: currentSessionId.value,
        sessions: Array.from(sessions.value.entries()),
        sessionHistory: Array.from(sessions.value.values()).map(buildSessionSummary),
        metadata: {
          totalSessions: sessions.value.size,
          totalMessages: Array.from(sessions.value.values()).reduce(
            (sum, session) => sum + session.messages.length, 0
          ),
          backupReason: 'emergency'
        }
      }

      // 尝试保存紧急备份
      const backupKey = `emergency_backup_${Date.now()}`
      await storageManager.save(backupKey, backupData)

      console.log('✅ 紧急备份创建成功:', backupKey)
      return { success: true, backupKey }
    } catch (error) {
      console.error('创建紧急备份失败:', error)
      return { success: false, error: error.message }
    }
  }

  const recoverFromCorruption = async () => {
    try {
      console.log('🔧 开始数据损坏恢复...')

      // 1. 创建紧急备份
      const backupResult = await createEmergencyBackup()
      if (!backupResult.success) {
        console.warn('紧急备份失败，继续恢复过程')
      }

      // 2. 验证所有会话
      const corruptedSessions = []
      const repairedSessions = []

      for (const [sessionId, session] of sessions.value) {
        const validation = validateSession(session)
        if (!validation.valid) {
          console.warn(`会话 ${sessionId} 损坏:`, validation.errors)
          corruptedSessions.push({ sessionId, errors: validation.errors })

          // 尝试修复
          try {
            const repairedSession = repairSession(session)
            sessions.value.set(sessionId, repairedSession)
            repairedSessions.push(sessionId)
            console.log(`✅ 会话 ${sessionId} 修复成功`)
          } catch (repairError) {
            console.error(`会话 ${sessionId} 修复失败:`, repairError)
            // 删除无法修复的会话
            sessions.value.delete(sessionId)
            const historyIndex = sessionHistory.value.findIndex(s => s.id === sessionId)
            if (historyIndex !== -1) {
              sessionHistory.value.splice(historyIndex, 1)
            }
          }
        }
      }

      // 3. 确保至少有一个可用会话
      if (sessions.value.size === 0) {
        console.log('所有会话都已损坏，创建新会话')
        createSession('恢复的对话')
      } else if (!currentSessionId.value || !sessions.value.has(currentSessionId.value)) {
        // 当前会话无效，切换到第一个可用会话
        const firstSession = sessionHistory.value[0]
        if (firstSession) {
          switchToSession(firstSession.id)
        }
      }

      // 4. 保存修复后的数据
      if (repairedSessions.length > 0) {
        if (persistenceMiddleware) {
          persistenceMiddleware.immediateSave('recoverFromCorruption')
        } else {
          await saveToStorage()
        }
      }

      console.log('✅ 数据损坏恢复完成')
      return {
        success: true,
        corruptedCount: corruptedSessions.length,
        repairedCount: repairedSessions.length,
        totalSessions: sessions.value.size,
        backupCreated: backupResult.success
      }
    } catch (error) {
      console.error('数据损坏恢复失败:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }

  // 工具函数
  const clearAllSessions = () => {
    sessions.value.clear()
    sessionHistory.value = []
    messages.value = []
    toolCalls.value = []
    currentSessionId.value = null
    currentStreamMessage.value = null
    createSession()
  }

  const clearCurrentSession = () => {
    if (currentSessionId.value) {
      messages.value = []
      toolCalls.value = []
      currentStreamMessage.value = null

      const session = sessions.value.get(currentSessionId.value)
      if (session) {
        session.messages = []
        session.toolCalls = []
        session.updatedAt = new Date()
        session.metadata.messageCount = 0
        session.metadata.lastActivity = new Date()
        syncSessionSummary(currentSessionId.value)
      }

      saveToStorage()
    }
  }

  const getSessionStats = computed(() => {
    const totalSessions = sessions.value.size
    const totalMessages = Array.from(sessions.value.values()).reduce(
      (sum, session) => sum + session.messages.length, 0
    )
    const averageMessages = totalSessions > 0 ? Math.round(totalMessages / totalSessions) : 0

    return {
      totalSessions,
      totalMessages,
      averageMessages,
      currentSessionMessages: messages.value.length,
      isStreaming: isStreaming.value,
      isConnected: isConnected.value
    }
  })

  // 获取所有标签
  const getAllTags = computed(() => {
    const tags = new Set()
    sessionHistory.value.forEach(session => {
      ;(session.metadata?.tags || []).forEach(tag => tags.add(tag))
    })
    return Array.from(tags).sort()
  })

  // 页面关闭前保存数据
  const handleBeforeUnload = () => {
    // 立即保存，不使用防抖
    try {
      const data = {
        version: '2.1',
        currentSessionId: currentSessionId.value,
        sessions: Array.from(sessions.value.entries()),
        sessionHistory: Array.from(sessions.value.values()).map(buildSessionSummary),
        timestamp: new Date().toISOString()
      }

      // 使用同步方式保存以确保在页面关闭前完成
      const serializedData = JSON.stringify(data)
      if (storageManager.primaryStorage) {
        storageManager.primaryStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, serializedData)
        console.log('✅ 页面关闭前数据已保存')
      }
    } catch (error) {
      console.error('页面关闭前保存失败:', error)
    }
  }

  // 设置页面关闭事件监听
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', handleBeforeUnload)

    // 页面可见性变化时也保存数据
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        handleBeforeUnload()
      }
    })
  }

  return {
    // 当前会话状态
    currentSessionId,
    messages,
    isConnected,
    isStreaming,
    currentStreamMessage,
    toolCalls,
    connectionError,
    retryCount,
    maxRetries,

    // 会话管理
    sessions,
    sessionHistory,
    currentSession,

    // 计算属性
    hasMessages,
    canSendMessage,
    lastMessage,
    getSessionStats,
    getAllTags,

    // 会话管理方法
    createSession,
    switchToSession,
    deleteSession,
    updateSessionTitle,
    addSessionTag,
    removeSessionTag,

    // 搜索和过滤
    searchSessions,
    searchMessages,

    // 消息管理
    addMessage,
    updateMessage,
    appendToLastMessage,

    // 流式消息管理
    startStreamMessage,
    appendStreamContent,
    replaceStreamContent,  // 🔧 新增：替换流式内容
    finishStreamMessage,
    cancelStreamMessage,

    // 工具调用管理
    addToolCall,
    updateToolCall,
    getToolCallsForMessage,

    // 连接状态管理
    setConnected,
    setConnectionError,
    incrementRetry,
    resetRetry,

    // 数据持久化
    saveToStorage,
    loadFromStorage,

    // 数据导入导出
    exportAllSessions,
    exportSession,
    importSessions,

    // 存储管理工具
    getStorageInfo,
    cleanupOldSessions,
    compressStorageData,
    performStorageHealthCheck,
    loadSessionOnDemand,

    // 会话管理可靠性
    validateSession,
    repairSession,
    atomicSessionOperation,

    // 错误恢复机制
    resetToCleanState,
    createEmergencyBackup,
    recoverFromCorruption,

    // 性能优化
    buildSearchIndex,
    searchIndex,
    sessionIndex,

    // 工具函数
    clearAllSessions,
    clearCurrentSession,

    // 存储状态
    storageStatus
  }
})

// 🔥 Store 自动初始化：在 store 创建后立即执行数据加载
if (typeof window !== 'undefined') {
  // 延迟执行，确保所有依赖项都已准备就绪
  setTimeout(async () => {
    try {
      console.log('🚀 Chat Store 自动初始化开始...')

      // 获取 store 实例并执行数据加载
      const store = useChatStore()
      await store.loadFromStorage()

      console.log('✅ Chat Store 自动初始化完成')
      console.log('📊 加载状态:', {
        sessionCount: store.sessionHistory.length,
        currentSessionId: store.currentSessionId,
        hasMessages: store.hasMessages,
        messageCount: store.messages.length
      })

      // 如果没有任何会话，创建一个默认会话
      if (store.sessionHistory.length === 0) {
        store.createSession('默认对话')
        console.log('🆕 已创建默认会话')
      }

    } catch (error) {
      console.error('❌ Chat Store 自动初始化失败:', error)

      // 初始化失败时创建新会话作为回退
      try {
        const store = useChatStore()
        store.createSession('默认对话')
        console.log('🆕 已创建默认会话作为回退')
      } catch (fallbackError) {
        console.error('❌ 创建回退会话也失败:', fallbackError)
      }
    }
  }, 300) // 给足够的时间让所有系统初始化完成
}
