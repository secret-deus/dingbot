<template>
  <div class="chat-page">
    <div class="page-header">
      <h1 class="page-title">智能对话</h1>
      <p class="page-subtitle">与K8s运维助手进行智能对话</p>
    </div>
    
    <div class="chat-container">
      <div class="chat-interface">
        <!-- 聊天消息区域 -->
        <div class="messages-area" ref="messagesArea">
          <div 
            v-for="message in messages" 
            :key="message.id"
            :class="['message', message.type]"
          >
            <div class="message-avatar">
              <el-icon v-if="message.type === 'user'"><User /></el-icon>
              <el-icon v-else><Robot /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="message.content"></div>
              <div class="message-time">{{ formatTime(message.time) }}</div>
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="isLoading" class="message assistant loading">
            <div class="message-avatar">
              <el-icon><Robot /></el-icon>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入您的问题，例如：查看集群状态、重启某个Pod..."
              @keydown.ctrl.enter="sendMessage"
              :disabled="isLoading"
            />
            <div class="input-actions">
              <el-button 
                type="primary" 
                @click="sendMessage"
                :loading="isLoading"
                :disabled="!inputMessage.trim()"
              >
                <el-icon><Send /></el-icon>
                发送 (Ctrl+Enter)
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, User, Robot, Send } from '@element-plus/icons-vue'
import apiClient from '@/api/client'

// 响应式数据
const inputMessage = ref('')
const isLoading = ref(false)
const messages = ref([
  {
    id: 1,
    type: 'assistant',
    content: '您好！我是K8s运维助手，可以帮您管理集群、查看状态、执行运维操作。请问有什么可以帮您的吗？',
    time: new Date()
  }
])
const messagesArea = ref(null)

// 方法
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: inputMessage.value,
    time: new Date()
  }
  
  messages.value.push(userMessage)
  const messageText = inputMessage.value
  inputMessage.value = ''
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 发送到后端
  isLoading.value = true
  
  try {
    // 使用流式API
    let assistantMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      content: '',
      time: new Date()
    }
    
    messages.value.push(assistantMessage)
    
    await apiClient.chat.streamChat(messageText, {
      onMessage: (data) => {
        if (data.type === 'content') {
          assistantMessage.content += data.content
        } else if (data.type === 'complete') {
          assistantMessage.content = data.content || assistantMessage.content
        }
        
        // 滚动到底部
        nextTick(() => scrollToBottom())
      },
      onError: (error) => {
        console.error('流式聊天错误:', error)
        assistantMessage.content = '抱歉，处理您的请求时出现了错误，请稍后重试。'
        ElMessage.error('聊天请求失败')
      }
    })
    
  } catch (error) {
    console.error('发送消息失败:', error)
    
    // 添加错误消息
    messages.value.push({
      id: Date.now() + 2,
      type: 'assistant',
      content: '抱歉，处理您的请求时出现了错误，请稍后重试。',
      time: new Date()
    })
    
    ElMessage.error('发送消息失败')
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight
  }
}

const formatTime = (time) => {
  return time.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 生命周期
onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.chat-interface {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  background: var(--bg-secondary);
}

.message {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  
  &.user {
    flex-direction: row-reverse;
    
    .message-content {
      background: var(--primary-gradient);
      color: white;
      border-radius: var(--radius-lg) var(--radius-sm) var(--radius-lg) var(--radius-lg);
    }
    
    .message-avatar {
      background: var(--primary-color);
    }
  }
  
  &.assistant {
    .message-content {
      background: var(--bg-card);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg);
    }
    
    .message-avatar {
      background: var(--success-gradient);
    }
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: var(--spacing-xs);
  opacity: 0.7;
}

.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-secondary);
    animation: typing 1.4s infinite ease-in-out;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-area {
  border-top: 1px solid var(--border-light);
  background: var(--bg-card);
  padding: var(--spacing-lg);
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

/* 自定义滚动条 */
.messages-area::-webkit-scrollbar {
  width: 6px;
}

.messages-area::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 3px;
}

.messages-area::-webkit-scrollbar-thumb {
  background: var(--border-dark);
  border-radius: 3px;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style>
