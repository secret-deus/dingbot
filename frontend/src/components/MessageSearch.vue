<template>
  <div class="message-search">
    <el-dialog
      v-model="visible"
      title="搜索消息"
      width="700px"
      :before-close="handleClose"
      class="search-dialog"
    >
      <!-- 搜索输入 -->
      <div class="search-input-section">
        <el-input
          v-model="searchQuery"
          placeholder="输入要搜索的消息内容..."
          clearable
          @input="handleSearch"
          @clear="clearSearch"
          size="large"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #suffix>
            <el-button
              v-if="searchQuery"
              type="text"
              size="small"
              @click="handleSearch"
            >
              搜索
            </el-button>
          </template>
        </el-input>
        
        <div class="search-options">
          <el-checkbox v-model="searchCurrentSession">仅搜索当前对话</el-checkbox>
          <el-checkbox v-model="caseSensitive">区分大小写</el-checkbox>
        </div>
      </div>
      
      <!-- 搜索结果 -->
      <div class="search-results">
        <div v-if="searching" class="search-status">
          <el-icon class="loading-icon"><Loading /></el-icon>
          正在搜索...
        </div>
        
        <div v-else-if="searchQuery && searchResults.length === 0" class="search-status">
          <el-icon><DocumentRemove /></el-icon>
          没有找到匹配的消息
        </div>
        
        <div v-else-if="searchResults.length > 0" class="results-list">
          <div class="results-header">
            <span class="results-count">找到 {{ searchResults.length }} 条相关消息</span>
            <el-button size="small" @click="exportSearchResults">
              <el-icon><Download /></el-icon>
              导出结果
            </el-button>
          </div>
          
          <div
            v-for="(result, index) in searchResults"
            :key="`${result.sessionId}-${result.messageIndex}`"
            class="result-item"
            @click="jumpToMessage(result)"
          >
            <div class="result-header">
              <div class="session-info">
                <el-icon><ChatDotSquare /></el-icon>
                <span class="session-title">{{ result.sessionTitle }}</span>
                <el-tag v-if="result.sessionId === chatStore.currentSessionId" type="success" size="small">
                  当前会话
                </el-tag>
              </div>
              <div class="message-meta">
                <span class="message-time">{{ formatTime(result.message.timestamp) }}</span>
                <el-tag :type="result.message.type === 'user' ? 'primary' : 'info'" size="small">
                  {{ result.message.type === 'user' ? '用户' : 'AI助手' }}
                </el-tag>
              </div>
            </div>
            
            <div class="result-content">
              <div class="matched-message">
                <span v-html="highlightSearchTerm(result.message.content)"></span>
              </div>
              
              <!-- 上下文消息 -->
              <div v-if="showContext && result.context.length > 1" class="context-messages">
                <el-divider content-position="left">
                  <span class="context-label">上下文</span>
                </el-divider>
                <div
                  v-for="(contextMsg, ctxIndex) in result.context"
                  :key="ctxIndex"
                  :class="['context-message', { 
                    'highlight': contextMsg === result.message,
                    [`type-${contextMsg.type}`]: true 
                  }]"
                >
                  <span class="message-type-icon">
                    <el-icon v-if="contextMsg.type === 'user'"><User /></el-icon>
                    <el-icon v-else><Monitor /></el-icon>
                  </span>
                  <span class="context-content">
                    {{ contextMsg.content.length > 100 ? 
                       contextMsg.content.slice(0, 100) + '...' : 
                       contextMsg.content }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="!searchQuery" class="search-placeholder">
          <div class="placeholder-content">
            <el-icon class="placeholder-icon"><Search /></el-icon>
            <h3>搜索消息</h3>
            <p>输入关键词搜索所有对话中的消息内容</p>
            <div class="search-tips">
              <h4>搜索技巧：</h4>
              <ul>
                <li>支持模糊匹配，会搜索包含关键词的所有消息</li>
                <li>勾选"仅搜索当前对话"可限制搜索范围</li>
                <li>支持搜索用户消息和AI回复</li>
                <li>点击搜索结果可跳转到对应的对话</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 对话框底部 -->
      <template #footer>
        <div class="dialog-footer">
          <div class="footer-options">
            <el-checkbox v-model="showContext">显示上下文</el-checkbox>
          </div>
          
          <div class="footer-actions">
            <el-button @click="handleClose">关闭</el-button>
            <el-button 
              v-if="searchResults.length > 0" 
              type="primary" 
              @click="exportSearchResults"
            >
              导出搜索结果
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, Loading, DocumentRemove, Download, ChatDotSquare,
  User, Monitor
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'jump-to-message'])

// 响应式数据
const chatStore = useChatStore()
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const searchCurrentSession = ref(false)
const caseSensitive = ref(false)
const showContext = ref(true)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  searching.value = true
  
  try {
    // 使用chat store的搜索功能
    const sessionId = searchCurrentSession.value ? chatStore.currentSessionId : null
    let query = searchQuery.value.trim()
    
    // 如果不区分大小写，转换查询
    if (!caseSensitive.value) {
      query = query.toLowerCase()
    }
    
    const results = chatStore.searchMessages(query, sessionId)
    
    // 如果不区分大小写，需要重新过滤结果
    if (!caseSensitive.value) {
      searchResults.value = results.filter(result => 
        result.message.content.toLowerCase().includes(query)
      )
    } else {
      searchResults.value = results
    }
    
    ElMessage.success(`找到 ${searchResults.value.length} 条相关消息`)
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败，请重试')
  } finally {
    searching.value = false
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
}

const handleClose = () => {
  visible.value = false
  clearSearch()
}

const jumpToMessage = (result) => {
  // 如果不是当前会话，需要切换会话
  if (result.sessionId !== chatStore.currentSessionId) {
    chatStore.switchToSession(result.sessionId)
  }
  
  // 通知父组件跳转到消息
  emit('jump-to-message', {
    sessionId: result.sessionId,
    messageIndex: result.messageIndex,
    messageId: result.message.id
  })
  
  handleClose()
  ElMessage.success(`已跳转到 "${result.sessionTitle}" 中的消息`)
}

const highlightSearchTerm = (content) => {
  if (!searchQuery.value) return content
  
  let query = searchQuery.value.trim()
  let searchContent = content
  
  // 处理大小写
  if (!caseSensitive.value) {
    query = query.toLowerCase()
    searchContent = content.toLowerCase()
  }
  
  // 查找匹配位置
  const index = searchContent.indexOf(query)
  if (index === -1) return content
  
  // 高亮显示
  const beforeMatch = content.slice(0, index)
  const match = content.slice(index, index + query.length)
  const afterMatch = content.slice(index + query.length)
  
  return `${beforeMatch}<mark class="search-highlight">${match}</mark>${afterMatch}`
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

const exportSearchResults = () => {
  try {
    const exportData = {
      version: '1.0',
      searchQuery: searchQuery.value,
      searchDate: new Date(),
      results: searchResults.value.map(result => ({
        sessionTitle: result.sessionTitle,
        sessionId: result.sessionId,
        message: result.message,
        messageIndex: result.messageIndex
      }))
    }
    
    const dataStr = JSON.stringify(exportData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = `search_results_${searchQuery.value.slice(0, 10)}_${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    
    URL.revokeObjectURL(link.href)
    ElMessage.success('搜索结果已导出')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出搜索结果失败')
  }
}

// 监听搜索查询变化
watch(searchQuery, (newQuery) => {
  if (newQuery.trim()) {
    // 防抖搜索
    clearTimeout(searchQuery.timer)
    searchQuery.timer = setTimeout(() => {
      handleSearch()
    }, 300)
  } else {
    searchResults.value = []
  }
})

// 监听搜索选项变化
watch([searchCurrentSession, caseSensitive], () => {
  if (searchQuery.value.trim()) {
    handleSearch()
  }
})
</script>

<style scoped>
.message-search {
  /* 对话框样式在全局样式中定义 */
}

.search-dialog {
  max-height: 80vh;
}

.search-input-section {
  margin-bottom: 20px;
}

.search-input {
  margin-bottom: 12px;
}

.search-options {
  display: flex;
  gap: 16px;
  font-size: 14px;
}

.search-results {
  max-height: 60vh;
  overflow-y: auto;
}

.search-status {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-size: 14px;
  gap: 8px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.results-list {
  /* 结果列表样式 */
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.results-count {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.result-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.result-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.session-title {
  font-weight: 500;
  color: var(--text-primary);
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.message-time {
  color: var(--text-secondary);
}

.result-content {
  /* 结果内容样式 */
}

.matched-message {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.context-messages {
  margin-top: 16px;
}

.context-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.context-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 6px;
  font-size: 13px;
  transition: background-color 0.3s;
}

.context-message.highlight {
  background: #e6f7ff;
  border-left: 3px solid #409EFF;
}

.context-message.type-user {
  background: #f0f8ff;
}

.context-message.type-assistant {
  background: #f9f9f9;
}

.message-type-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.context-content {
  flex: 1;
  color: var(--text-secondary);
  line-height: 1.4;
}

.search-placeholder {
  padding: 40px 20px;
  text-align: center;
}

.placeholder-content h3 {
  margin: 16px 0 8px 0;
  color: var(--text-primary);
}

.placeholder-content p {
  margin: 0 0 24px 0;
  color: var(--text-secondary);
}

.placeholder-icon {
  font-size: 48px;
  color: var(--text-lighter);
}

.search-tips {
  text-align: left;
  max-width: 400px;
  margin: 0 auto;
}

.search-tips h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.search-tips ul {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.search-tips li {
  margin-bottom: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-options {
  font-size: 14px;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

/* 全局搜索高亮样式 */
:deep(.search-highlight) {
  background: linear-gradient(120deg, #ffd700 0%, #ffed4e 100%);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-dialog {
    width: 95% !important;
    margin: 10px;
  }
  
  .result-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .session-info {
    width: 100%;
  }
  
  .message-meta {
    align-self: flex-end;
  }
  
  .dialog-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .footer-actions {
    justify-content: center;
  }
}
</style> 