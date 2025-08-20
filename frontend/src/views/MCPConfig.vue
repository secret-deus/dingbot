<template>
  <div class="mcp-config-page">
    <div class="page-header">
      <h1>MCP 配置管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="refreshPage">
          <el-icon><Refresh /></el-icon>
          刷新页面
        </el-button>
      </div>
    </div>
    
    <el-tabs v-model="activeTab" class="config-tabs">
      <el-tab-pane label="配置编辑器" name="editor">
        <MCPConfigEditor />
      </el-tab-pane>
      
      <el-tab-pane label="服务器管理" name="servers">
        <div class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>MCP 服务器列表</span>
                <el-button type="primary" size="small" @click="loadServers">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            
            <div v-if="loadingServers" class="loading-container">
              <el-skeleton :rows="5" animated />
            </div>
            
            <div v-else-if="serverError" class="error-container">
              <el-alert
                title="加载服务器失败"
                type="error"
                :description="serverError"
                show-icon
                :closable="false"
              />
            </div>
            
            <div v-else-if="servers.length === 0" class="empty-container">
              <el-empty description="暂无服务器配置" />
            </div>
            
            <div v-else class="servers-list">
              <el-table :data="servers" style="width: 100%">
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="type" label="类型" width="120" />
                <el-table-column label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.enabled ? 'success' : 'info'">
                      {{ scope.row.enabled ? '启用' : '禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="tools_count" label="工具数量" width="100" />
                <el-table-column label="操作">
                  <template #default="scope">
                    <el-button 
                      size="small" 
                      :type="scope.row.enabled ? 'warning' : 'success'"
                      @click="toggleServer(scope.row.name)"
                    >
                      {{ scope.row.enabled ? '禁用' : '启用' }}
                    </el-button>
                    <el-button 
                      size="small" 
                      type="primary"
                      @click="testConnection(scope.row.name)"
                    >
                      测试连接
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="工具管理" name="tools">
        <div class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>MCP 工具列表</span>
                <el-button type="primary" size="small" @click="loadTools">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            
            <div v-if="loadingTools" class="loading-container">
              <el-skeleton :rows="5" animated />
            </div>
            
            <div v-else-if="toolsError" class="error-container">
              <el-alert
                title="加载工具失败"
                type="error"
                :description="toolsError"
                show-icon
                :closable="false"
              />
            </div>
            
            <div v-else-if="tools.length === 0" class="empty-container">
              <el-empty description="暂无工具配置" />
            </div>
            
            <div v-else class="tools-list">
              <el-table :data="tools" style="width: 100%">
                <el-table-column prop="name" label="名称" width="180" />
                <el-table-column prop="description" label="描述" />
                <el-table-column prop="category" label="分类" width="120" />
                <el-table-column label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.enabled ? 'success' : 'info'">
                      {{ scope.row.enabled ? '启用' : '禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="server" label="服务器" width="150" />
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button 
                      size="small" 
                      :type="scope.row.enabled ? 'warning' : 'success'"
                      @click="toggleTool(scope.row.name)"
                    >
                      {{ scope.row.enabled ? '禁用' : '启用' }}
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="配置验证" name="validation">
        <div class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>MCP 配置验证</span>
                <el-button type="primary" size="small" @click="validateConfig" :loading="validating">
                  <el-icon><Check /></el-icon>
                  验证配置
                </el-button>
              </div>
            </template>
            
            <div v-if="validating" class="loading-container">
              <el-skeleton :rows="5" animated />
            </div>
            
            <div v-else-if="validationError" class="error-container">
              <el-alert
                title="配置验证失败"
                type="error"
                :description="validationError"
                show-icon
                :closable="false"
              />
            </div>
            
            <div v-else-if="validationResult" class="validation-result">
              <el-result
                :icon="validationResult.valid ? 'success' : 'warning'"
                :title="validationResult.valid ? '配置验证通过' : '配置验证存在问题'"
                :sub-title="validationResult.valid ? '所有配置项验证通过' : '配置存在一些问题，但可能不影响使用'"
              >
                <template #extra>
                  <div class="validation-details">
                    <div v-if="validationResult.errors.length > 0" class="validation-section">
                      <h3>错误 ({{ validationResult.errors.length }})</h3>
                      <el-alert
                        v-for="(error, index) in validationResult.errors"
                        :key="'error-' + index"
                        type="error"
                        :title="error"
                        :closable="false"
                        show-icon
                        class="validation-item"
                      />
                    </div>
                    
                    <div v-if="validationResult.warnings.length > 0" class="validation-section">
                      <h3>警告 ({{ validationResult.warnings.length }})</h3>
                      <el-alert
                        v-for="(warning, index) in validationResult.warnings"
                        :key="'warning-' + index"
                        type="warning"
                        :title="warning"
                        :closable="false"
                        show-icon
                        class="validation-item"
                      />
                    </div>
                    
                    <div class="validation-section">
                      <h3>服务器状态</h3>
                      <el-descriptions :column="1" border>
                        <el-descriptions-item 
                          v-for="(status, server) in validationResult.server_status" 
                          :key="server"
                          :label="server"
                        >
                          <el-tag 
                            :type="status === 'connected' ? 'success' : 'warning'"
                          >
                            {{ status === 'connected' ? '已连接' : '连接失败' }}
                          </el-tag>
                        </el-descriptions-item>
                      </el-descriptions>
                    </div>
                  </div>
                </template>
              </el-result>
            </div>
            
            <div v-else class="empty-validation">
              <el-empty description='点击"验证配置"按钮开始验证' />
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 连接测试结果对话框 -->
    <el-dialog
      v-model="connectionTestVisible"
      :title="connectionTestResult ? '连接测试结果' : '测试中...'"
      width="400px"
    >
      <div v-if="connectionTestResult" class="connection-test-result">
        <el-result
          :icon="connectionTestResult.connected ? 'success' : 'error'"
          :title="connectionTestResult.connected ? '连接成功' : '连接失败'"
          :sub-title="connectionTestResult.message"
        >
          <template #extra>
            <div class="connection-details">
              <p><strong>服务器:</strong> {{ connectionTestResult.server_name }}</p>
              <p><strong>状态:</strong> {{ connectionTestResult.status }}</p>
            </div>
          </template>
        </el-result>
      </div>
      
      <div v-else class="connection-test-loading">
        <el-skeleton :rows="3" animated />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Check } from '@element-plus/icons-vue'
import axios from 'axios'
import MCPConfigEditor from '@/components/MCPConfigEditor.vue'

// 响应式状态
const activeTab = ref('editor')

// 服务器管理
const servers = ref([])
const loadingServers = ref(false)
const serverError = ref(null)

// 工具管理
const tools = ref([])
const loadingTools = ref(false)
const toolsError = ref(null)

// 配置验证
const validationResult = ref(null)
const validating = ref(false)
const validationError = ref(null)

// 连接测试
const connectionTestVisible = ref(false)
const connectionTestResult = ref(null)
const testingConnection = ref(false)

// 方法
const refreshPage = () => {
  window.location.reload()
}

const loadServers = async () => {
  loadingServers.value = true
  serverError.value = null
  
  try {
    const response = await axios.get('/api/v2/mcp/config/servers')
    servers.value = response.data
  } catch (e) {
    console.error('加载服务器失败:', e)
    serverError.value = e.response?.data?.detail || e.message || '未知错误'
  } finally {
    loadingServers.value = false
  }
}

const loadTools = async () => {
  loadingTools.value = true
  toolsError.value = null
  
  try {
    const response = await axios.get('/api/v2/mcp/config/tools')
    tools.value = response.data
  } catch (e) {
    console.error('加载工具失败:', e)
    toolsError.value = e.response?.data?.detail || e.message || '未知错误'
  } finally {
    loadingTools.value = false
  }
}

const toggleServer = async (serverName) => {
  try {
    const response = await axios.post(`/api/v2/mcp/config/servers/${serverName}/toggle`)
    ElMessage.success(response.data.message)
    await loadServers()
  } catch (e) {
    console.error('切换服务器状态失败:', e)
    ElMessage.error(e.response?.data?.detail || e.message || '操作失败')
  }
}

const toggleTool = async (toolName) => {
  try {
    const response = await axios.post(`/api/v2/mcp/config/tools/${toolName}/toggle`)
    ElMessage.success(response.data.message)
    await loadTools()
  } catch (e) {
    console.error('切换工具状态失败:', e)
    ElMessage.error(e.response?.data?.detail || e.message || '操作失败')
  }
}

const validateConfig = async () => {
  validating.value = true
  validationError.value = null
  validationResult.value = null
  
  try {
    const response = await axios.post('/api/v2/mcp/config/validate')
    validationResult.value = response.data
  } catch (e) {
    console.error('配置验证失败:', e)
    validationError.value = e.response?.data?.detail || e.message || '未知错误'
  } finally {
    validating.value = false
  }
}

const testConnection = async (serverName) => {
  connectionTestVisible.value = true
  connectionTestResult.value = null
  testingConnection.value = true
  
  try {
    const response = await axios.post(`/api/v2/mcp/config/test/${serverName}`)
    connectionTestResult.value = response.data
  } catch (e) {
    console.error('连接测试失败:', e)
    connectionTestResult.value = {
      server_name: serverName,
      status: 'error',
      connected: false,
      message: e.response?.data?.detail || e.message || '测试失败'
    }
  } finally {
    testingConnection.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  loadServers()
  loadTools()
})
</script>

<style scoped>
.mcp-config-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.config-tabs {
  margin-bottom: 20px;
}

.tab-content {
  padding: 10px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container, .error-container, .empty-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.validation-result {
  padding: 20px 0;
}

.validation-details {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.validation-section {
  margin-bottom: 20px;
}

.validation-section h3 {
  margin-bottom: 10px;
  font-size: 16px;
  color: var(--text-primary);
}

.validation-item {
  margin-bottom: 10px;
}

.empty-validation {
  padding: 40px 0;
}

.connection-test-result {
  padding: 20px 0;
}

.connection-details {
  text-align: left;
  margin-top: 20px;
}

.connection-test-loading {
  padding: 20px;
}
</style>