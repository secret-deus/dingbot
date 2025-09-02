<template>
  <div class="mcp-config-editor">
    <el-card class="config-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>MCP 配置编辑器</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="saveConfig" :loading="saving">
              <el-icon><Check /></el-icon>
              保存配置
            </el-button>
            <el-button size="small" @click="refreshConfig" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-alert
          title="加载配置失败"
          type="error"
          :description="error"
          show-icon
          :closable="false"
        />
        <el-button class="retry-button" type="primary" @click="refreshConfig">
          重试
        </el-button>
      </div>
      
      <div v-if="warnings && warnings.length > 0" class="warnings-container">
        <el-alert
          v-for="(warning, index) in warnings"
          :key="index"
          title="警告"
          type="warning"
          :description="warning"
          show-icon
          :closable="true"
          @close="warnings.splice(index, 1)"
          class="warning-item"
        />
      </div>
      
      <div v-else class="editor-container">
        <!-- 配置编辑器 -->
        <div class="json-editor-container">
          <div class="editor-header">
            <span>JSON 配置</span>
            <div class="editor-actions">
              <el-tooltip content="格式化JSON" placement="top">
                <el-button size="small" @click="formatJson">
                  <el-icon><Operation /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="复制JSON" placement="top">
                <el-button size="small" @click="copyJson">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
          
          <el-input
            v-model="configJson"
            type="textarea"
            :rows="20"
            resize="vertical"
            spellcheck="false"
            @input="onConfigChange"
          />
          
          <div class="validation-status">
            <el-tag v-if="isValidJson" type="success">JSON 格式有效</el-tag>
            <el-tag v-else type="danger">JSON 格式无效: {{ jsonError }}</el-tag>
          </div>
        </div>
        
        <!-- 配置预览 -->
        <div class="config-preview">
          <h3>配置概览</h3>
          
          <div v-if="parsedConfig" class="preview-content">
            <div class="preview-section">
              <h4>基本信息</h4>
              <div class="preview-item">
                <span class="label">名称:</span>
                <span class="value">{{ parsedConfig.name }}</span>
              </div>
              <div class="preview-item">
                <span class="label">描述:</span>
                <span class="value">{{ parsedConfig.description }}</span>
              </div>
              <div class="preview-item">
                <span class="label">版本:</span>
                <span class="value">{{ parsedConfig.version }}</span>
              </div>
            </div>
            
            <div class="preview-section">
              <h4>服务器 ({{ parsedConfig.servers?.length || 0 }})</h4>
              <el-tag 
                v-for="server in parsedConfig.servers" 
                :key="server.name"
                :type="server.enabled ? 'success' : 'info'"
                class="preview-tag"
              >
                {{ server.name }} ({{ server.type }})
              </el-tag>
              <div v-if="!parsedConfig.servers?.length" class="empty-message">
                无服务器配置
              </div>
            </div>
            
            <div class="preview-section">
              <h4>工具 ({{ parsedConfig.tools?.length || 0 }})</h4>
              <div class="tools-container">
                <el-tag 
                  v-for="tool in parsedConfig.tools?.slice(0, 10)" 
                  :key="tool.name"
                  :type="tool.enabled ? 'success' : 'info'"
                  class="preview-tag"
                >
                  {{ tool.name }}
                </el-tag>
                <div v-if="parsedConfig.tools?.length > 10" class="more-tools">
                  还有 {{ parsedConfig.tools.length - 10 }} 个工具...
                </div>
              </div>
              <div v-if="!parsedConfig.tools?.length" class="empty-message">
                无工具配置
              </div>
            </div>
          </div>
          
          <div v-else class="preview-error">
            无法解析配置，请检查JSON格式
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 保存结果提示 -->
    <el-dialog
      v-model="saveResultVisible"
      :title="saveSuccess ? '保存成功' : '保存失败'"
      width="400px"
    >
      <div class="save-result">
        <el-icon v-if="saveSuccess" class="success-icon" :size="48"><SuccessFilled /></el-icon>
        <el-icon v-else class="error-icon" :size="48"><CircleCloseFilled /></el-icon>
        
        <p>{{ saveResultMessage }}</p>
        
        <div v-if="!saveSuccess" class="error-details">
          <p>错误详情:</p>
          <pre>{{ saveError }}</pre>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="saveResultVisible = false">关闭</el-button>
          <el-button v-if="saveSuccess" type="primary" @click="handleAfterSave">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh, Operation, CopyDocument, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式状态
const configJson = ref('')
const originalConfig = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref(null)
const jsonError = ref('')
const saveResultVisible = ref(false)
const saveSuccess = ref(false)
const saveResultMessage = ref('')
const saveError = ref('')
const warnings = ref([])

// 计算属性
const isValidJson = computed(() => {
  try {
    if (!configJson.value.trim()) return false
    JSON.parse(configJson.value)
    jsonError.value = ''
    return true
  } catch (e) {
    jsonError.value = e.message
    return false
  }
})

const parsedConfig = computed(() => {
  if (!isValidJson.value) return null
  try {
    return JSON.parse(configJson.value)
  } catch {
    return null
  }
})

const hasChanges = computed(() => {
  if (!originalConfig.value || !parsedConfig.value) return false
  return JSON.stringify(originalConfig.value) !== JSON.stringify(parsedConfig.value)
})

// 方法
const loadConfig = async () => {
  loading.value = true
  error.value = null
  
  try {
    // 尝试从两个可能的位置加载配置
    let configData = null
    let loadErrors = []
    
    // 首先尝试从统一的API端点加载
    try {
      console.log('尝试从统一API端点加载配置...')
      const response = await axios.get('/api/v2/mcp/config/current', {
        timeout: 10000
      })
      
      if (response.data && typeof response.data === 'object') {
        configData = response.data
        console.log('✅ 从统一API端点成功加载配置')
      }
    } catch (e) {
      console.warn('无法从统一API端点加载配置，尝试备用方法', e)
      loadErrors.push(`统一API加载失败: ${e.message}`)
      
      // 备用方法：尝试从特定文件路径加载
      const configPaths = [
        'backend/config/mcp_config.json',
        'config/mcp_config.json'
      ]
      
      for (const path of configPaths) {
        if (configData) break // 如果已经加载成功，跳过剩余尝试
        
        try {
          console.log(`尝试从 ${path} 加载配置...`)
          const response = await axios.get('/api/v2/mcp/config/file', {
            params: { path },
            timeout: 8000
          })
          
          if (response.data && typeof response.data === 'object') {
            configData = response.data
            console.log(`✅ 从 ${path} 成功加载配置`)
          }
        } catch (e) {
          console.warn(`无法从 ${path} 加载配置`, e)
          loadErrors.push(`${path} 加载失败: ${e.message}`)
        }
      }
    }
    
    if (configData) {
      originalConfig.value = configData
      configJson.value = JSON.stringify(configData, null, 2)
      
      // 检查配置是否有基本结构
      if (!configData.servers || !Array.isArray(configData.servers)) {
        console.warn('⚠️ 加载的配置缺少servers数组')
        warnings.value = ['配置缺少servers数组，可能需要初始化']
      }
      
      if (!configData.tools || !Array.isArray(configData.tools)) {
        console.warn('⚠️ 加载的配置缺少tools数组')
        warnings.value = (warnings.value || []).concat(['配置缺少tools数组，可能需要初始化'])
      }
    } else {
      // 如果所有尝试都失败，创建一个基本的配置模板
      console.warn('⚠️ 所有加载尝试失败，创建基本配置模板')
      const defaultConfig = {
        "version": "1.0",
        "name": "MCP配置",
        "description": "MCP服务器和工具配置",
        "global_config": {
          "timeout": 30000,
          "retry_attempts": 3,
          "retry_delay": 1000,
          "max_concurrent_calls": 5,
          "enable_cache": true,
          "cache_timeout": 300000
        },
        "servers": [],
        "tools": [],
        "security": {
          "enable_audit": true,
          "audit_log_path": "logs/mcp_audit.log",
          "rate_limit": {
            "enabled": true,
            "requests_per_minute": 100
          }
        },
        "logging": {
          "level": "INFO",
          "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
      }
      
      originalConfig.value = defaultConfig
      configJson.value = JSON.stringify(defaultConfig, null, 2)
      
      // 设置警告而不是错误，允许用户编辑和保存新配置
      warnings.value = ['无法加载现有配置，已创建基本模板。请添加服务器和工具配置后保存。']
      error.value = `加载失败: ${loadErrors.join('; ')}`
    }
  } catch (e) {
    console.error('加载配置失败:', e)
    error.value = e.response?.data?.detail || e.message || '未知错误'
    
    // 创建最小可用的配置模板
    const minimalConfig = {
      "version": "1.0",
      "name": "MCP配置",
      "description": "基本MCP配置",
      "servers": [],
      "tools": []
    }
    
    originalConfig.value = minimalConfig
    configJson.value = JSON.stringify(minimalConfig, null, 2)
  } finally {
    loading.value = false
  }
}

const refreshConfig = () => {
  loadConfig()
}

const formatJson = () => {
  try {
    if (!configJson.value.trim()) return
    const parsed = JSON.parse(configJson.value)
    configJson.value = JSON.stringify(parsed, null, 2)
    ElMessage.success('JSON已格式化')
  } catch (e) {
    ElMessage.error(`格式化失败: ${e.message}`)
  }
}

const copyJson = () => {
  try {
    navigator.clipboard.writeText(configJson.value)
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    ElMessage.error(`复制失败: ${e.message}`)
  }
}

const onConfigChange = () => {
  // 可以添加防抖处理
}

const saveConfig = async () => {
  if (!isValidJson.value) {
    ElMessage.error('JSON格式无效，无法保存')
    return
  }
  
  saving.value = true
  saveSuccess.value = false
  saveError.value = ''
  
  try {
    const config = JSON.parse(configJson.value)
    
    // 添加请求超时和重试逻辑
    const maxRetries = 3
    let retryCount = 0
    let lastError = null
    
    while (retryCount <= maxRetries) {
      try {
        console.log(`尝试保存配置 (尝试 ${retryCount + 1}/${maxRetries + 1})`)
        
        // 使用新的API端点保存配置
        const response = await axios.post('/api/v2/mcp/config/update', {
          config_data: config
        }, {
          timeout: 15000, // 15秒超时
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        
        if (response.data && response.data.success) {
          saveSuccess.value = true
          saveResultMessage.value = '配置保存成功！'
          
          // 记录警告信息
          if (response.data.warnings && response.data.warnings.length > 0) {
            saveResultMessage.value += `\n\n警告：\n${response.data.warnings.join('\n')}`
          }
          
          originalConfig.value = JSON.parse(JSON.stringify(config)) // 深拷贝
          console.log('配置保存成功:', response.data)
          break // 成功后退出循环
        } else {
          throw new Error(response.data?.message || '保存失败，服务器返回未知状态')
        }
      } catch (err) {
        lastError = err
        retryCount++
        
        console.warn(`保存失败 (${retryCount}/${maxRetries + 1})...`, err)
        
        if (retryCount <= maxRetries) {
          // 指数退避策略
          const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 5000)
          console.log(`等待 ${delay}ms 后重试...`)
          await new Promise(resolve => setTimeout(resolve, delay))
        } else {
          throw err // 重试次数用完，抛出最后一个错误
        }
      }
    }
  } catch (e) {
    console.error('保存配置失败:', e)
    saveSuccess.value = false
    saveResultMessage.value = '配置保存失败'
    
    // 增强错误信息
    if (e.response) {
      // 服务器响应错误
      const errorDetail = e.response.data?.detail || e.response.data?.message || e.message || '未知错误'
      saveError.value = `服务器错误 (${e.response.status}): ${errorDetail}`
      
      // 添加更多调试信息
      if (e.response.data) {
        try {
          const dataStr = typeof e.response.data === 'object' ? 
            JSON.stringify(e.response.data, null, 2) : 
            String(e.response.data)
          
          if (dataStr.length > 500) {
            saveError.value += `\n\n响应数据 (截断): ${dataStr.substring(0, 500)}...`
          } else {
            saveError.value += `\n\n响应数据: ${dataStr}`
          }
        } catch (jsonErr) {
          saveError.value += `\n\n无法解析响应数据: ${jsonErr.message}`
        }
      }
    } else if (e.request) {
      // 请求发送但没有收到响应
      saveError.value = `网络错误: 服务器没有响应 (${e.message})`
      saveError.value += '\n\n可能原因: 服务器超时、网络问题或后端服务未运行'
    } else {
      // 请求设置时出错
      saveError.value = `请求错误: ${e.message || '未知错误'}`
    }
  } finally {
    saving.value = false
    saveResultVisible.value = true
  }
}

const handleAfterSave = () => {
  saveResultVisible.value = false
  refreshConfig()
}

// 生命周期钩子
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.mcp-config-editor {
  width: 100%;
}

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-container {
  padding: 20px;
}

.error-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.retry-button {
  width: 120px;
}

.warnings-container {
  padding: 10px 20px;
  margin-bottom: 15px;
}

.warning-item {
  margin-bottom: 10px;
}

.editor-container {
  display: flex;
  gap: 20px;
}

.json-editor-container {
  flex: 3;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.editor-actions {
  display: flex;
  gap: 5px;
}

.validation-status {
  margin-top: 10px;
}

.config-preview {
  flex: 2;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-section {
  margin-bottom: 15px;
}

.preview-section h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #606266;
}

.preview-item {
  display: flex;
  margin-bottom: 5px;
}

.preview-item .label {
  font-weight: bold;
  width: 80px;
}

.preview-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.tools-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.more-tools {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.empty-message {
  font-style: italic;
  color: #909399;
}

.preview-error {
  color: #f56c6c;
  font-style: italic;
}

.save-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding: 10px;
}

.success-icon {
  color: #67c23a;
}

.error-icon {
  color: #f56c6c;
}

.error-details {
  width: 100%;
  margin-top: 10px;
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  overflow: auto;
}

.error-details pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 1200px) {
  .editor-container {
    flex-direction: column;
  }
  
  .json-editor-container, .config-preview {
    flex: 1;
  }
}
</style>