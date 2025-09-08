<template>
  <div class="api-test-page">
    <div class="page-header">
      <h1 class="page-title">API连接测试</h1>
      <p class="page-subtitle">测试后端API连接状态</p>
    </div>
    
    <div class="test-container">
      <div class="test-section">
        <h3>系统API测试</h3>
        <div class="test-buttons">
          <el-button @click="testHealth" :loading="healthLoading">
            测试健康检查
          </el-button>
          <el-button @click="testStatus" :loading="statusLoading">
            测试系统状态
          </el-button>
          <el-button @click="testTools" :loading="toolsLoading">
            测试工具列表
          </el-button>
        </div>
      </div>
      
      <div class="test-section">
        <h3>聊天API测试</h3>
        <div class="chat-test">
          <el-input
            v-model="testMessage"
            placeholder="输入测试消息"
            style="margin-bottom: 10px;"
          />
          <el-button @click="testChat" :loading="chatLoading">
            测试聊天
          </el-button>
        </div>
      </div>
      
      <div class="results-section">
        <h3>测试结果</h3>
        <div class="results-container">
          <pre>{{ testResults }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/api/client'

const healthLoading = ref(false)
const statusLoading = ref(false)
const toolsLoading = ref(false)
const chatLoading = ref(false)
const testMessage = ref('测试消息')
const testResults = ref('')

const addResult = (title, data) => {
  const timestamp = new Date().toLocaleTimeString()
  testResults.value += `\n[${timestamp}] ${title}:\n${JSON.stringify(data, null, 2)}\n`
}

const testHealth = async () => {
  healthLoading.value = true
  try {
    const response = await apiClient.system.getV2Health()
    addResult('健康检查成功', response.data)
    ElMessage.success('健康检查成功')
  } catch (error) {
    addResult('健康检查失败', { error: error.message, status: error.response?.status })
    ElMessage.error('健康检查失败')
  } finally {
    healthLoading.value = false
  }
}

const testStatus = async () => {
  statusLoading.value = true
  try {
    const response = await apiClient.system.getStatus()
    addResult('系统状态成功', response.data)
    ElMessage.success('系统状态获取成功')
  } catch (error) {
    addResult('系统状态失败', { error: error.message, status: error.response?.status })
    ElMessage.error('系统状态获取失败')
  } finally {
    statusLoading.value = false
  }
}

const testTools = async () => {
  toolsLoading.value = true
  try {
    const response = await apiClient.system.getTools()
    addResult('工具列表成功', response.data)
    ElMessage.success('工具列表获取成功')
  } catch (error) {
    addResult('工具列表失败', { error: error.message, status: error.response?.status })
    ElMessage.error('工具列表获取失败')
  } finally {
    toolsLoading.value = false
  }
}

const testChat = async () => {
  if (!testMessage.value.trim()) {
    ElMessage.warning('请输入测试消息')
    return
  }
  
  chatLoading.value = true
  try {
    addResult('开始聊天测试', { message: testMessage.value })
    
    await apiClient.chat.streamChat(testMessage.value, {
      onMessage: (data) => {
        addResult('聊天响应', data)
      },
      onError: (error) => {
        addResult('聊天错误', { error: error.message })
      }
    })
    
    ElMessage.success('聊天测试完成')
  } catch (error) {
    addResult('聊天测试失败', { error: error.message, status: error.response?.status })
    ElMessage.error('聊天测试失败')
  } finally {
    chatLoading.value = false
  }
}
</script>

<style scoped>
.api-test-page {
  padding: var(--spacing-lg);
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

.test-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.test-section {
  background: var(--bg-card);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.test-section h3 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.test-buttons {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.chat-test {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.results-section {
  background: var(--bg-card);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.results-container {
  background: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  max-height: 400px;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.results-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>

