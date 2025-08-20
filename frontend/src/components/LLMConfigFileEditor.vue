<template>
  <div class="llm-config-editor">
    <el-card class="config-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>LLM 配置编辑器</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="saveConfig" :loading="saving">
              <el-icon><Check /></el-icon>
              保存配置
            </el-button>
            <el-button size="small" @click="refreshConfig" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button size="small" @click="validateConfig" :loading="validating">
              <el-icon><CircleCheck /></el-icon>
              验证配置
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
      
      <div v-if="validationResult" class="validation-container">
        <el-alert
          :title="validationResult.valid ? '配置验证通过' : '配置验证失败'"
          :type="validationResult.valid ? 'success' : 'error'"
          show-icon
          :closable="true"
          @close="validationResult = null"
        >
          <div v-if="validationResult.errors && validationResult.errors.length > 0">
            <p><strong>错误:</strong></p>
            <ul>
              <li v-for="error in validationResult.errors" :key="error">{{ error }}</li>
            </ul>
          </div>
          <div v-if="validationResult.warnings && validationResult.warnings.length > 0">
            <p><strong>警告:</strong></p>
            <ul>
              <li v-for="warning in validationResult.warnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>
          <div v-if="validationResult.valid">
            <p>提供商数量: {{ validationResult.provider_count }}</p>
            <p>已启用提供商: {{ validationResult.enabled_provider_count }}</p>
          </div>
        </el-alert>
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
              <el-tooltip content="导入配置" placement="top">
                <el-button size="small" @click="showImportDialog = true">
                  <el-icon><Upload /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="导出配置" placement="top">
                <el-button size="small" @click="exportConfig">
                  <el-icon><Download /></el-icon>
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
            placeholder="请输入LLM配置JSON..."
            @input="onConfigChange"
          />
          
          <div class="validation-status">
            <el-tag v-if="isValidJson" type="success">
              <el-icon><CircleCheck /></el-icon>
              JSON 格式有效
            </el-tag>
            <el-tag v-else type="danger">
              <el-icon><CircleClose /></el-icon>
              JSON 格式无效: {{ jsonError }}
            </el-tag>
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
              <div class="preview-item">
                <span class="label">默认提供商:</span>
                <span class="value">{{ parsedConfig.default_provider || '未设置' }}</span>
              </div>
            </div>
            
            <div class="preview-section">
              <h4>提供商 ({{ parsedConfig.providers?.length || 0 }})</h4>
              <div class="providers-container">
                <el-tag 
                  v-for="provider in parsedConfig.providers" 
                  :key="provider.id"
                  :type="provider.enabled ? 'success' : 'info'"
                  class="preview-tag"
                >
                  {{ provider.name || provider.id }}
                  <span class="provider-model">({{ provider.model }})</span>
                </el-tag>
                <div v-if="!parsedConfig.providers?.length" class="empty-message">
                  无提供商配置
                </div>
              </div>
            </div>
            
            <div class="preview-section" v-if="parsedConfig.global_settings">
              <h4>全局设置</h4>
              <div class="settings-grid">
                <div class="preview-item">
                  <span class="label">超时时间:</span>
                  <span class="value">{{ parsedConfig.global_settings.timeout || 30 }}s</span>
                </div>
                <div class="preview-item">
                  <span class="label">重试次数:</span>
                  <span class="value">{{ parsedConfig.global_settings.max_retries || 3 }}</span>
                </div>
                <div class="preview-item">
                  <span class="label">启用缓存:</span>
                  <span class="value">{{ parsedConfig.global_settings.enable_cache ? '是' : '否' }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="preview-error">
            无法解析配置，请检查JSON格式
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 备份管理 -->
    <el-card class="backup-card" shadow="hover" v-if="!loading && !error">
      <template #header>
        <div class="card-header">
          <span>配置备份</span>
          <el-button size="small" @click="loadBackups" :loading="backupsLoading">
            <el-icon><Refresh /></el-icon>
            刷新备份
          </el-button>
        </div>
      </template>
      
      <div v-if="backups.length > 0" class="backups-container">
        <el-table :data="backups" size="small">
          <el-table-column prop="name" label="备份名称" width="200" />
          <el-table-column prop="created" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created) }}
            </template>
          </el-table-column>
          <el-table-column prop="size" label="文件大小" width="100">
            <template #default="scope">
              {{ formatFileSize(scope.row.size) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button size="small" type="primary" @click="restoreBackup(scope.row.name)">
                恢复
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else class="no-backups">
        <p>暂无配置备份</p>
      </div>
    </el-card>
    
    <!-- 导入配置对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入LLM配置"
      width="600px"
    >
      <el-upload
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".json"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将JSON文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            仅支持JSON格式的配置文件
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button type="primary" @click="importConfig" :disabled="!selectedFile">
            导入
          </el-button>
        </span>
      </template>
    </el-dialog>
    
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
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Check, Refresh, Operation, CopyDocument, Upload, Download, 
  CircleCheck, CircleClose, SuccessFilled, CircleCloseFilled, UploadFilled 
} from '@element-plus/icons-vue'
import axios from 'axios'

// Props定义
const props = defineProps({
  initialConfig: {
    type: String,
    default: ''
  }
})

// Emits定义
const emit = defineEmits(['config-save', 'config-reload'])

// 响应式状态
const configJson = ref('')
const originalConfig = ref(null)
const loading = ref(false)
const saving = ref(false)
const validating = ref(false)
const backupsLoading = ref(false)
const error = ref(null)
const jsonError = ref('')
const warnings = ref([])
const validationResult = ref(null)
const backups = ref([])

// 导入/导出相关
const showImportDialog = ref(false)
const selectedFile = ref(null)
const fileList = ref([])

// 保存结果对话框
const saveResultVisible = ref(false)
const saveSuccess = ref(false)
const saveResultMessage = ref('')
const saveError = ref('')

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
  warnings.value = []
  
  try {
    console.log('开始加载LLM配置...')
    const response = await axios.get('/api/v2/llm/config/current', {
      timeout: 10000
    })
    
    if (response.data) {
      originalConfig.value = response.data
      configJson.value = JSON.stringify(response.data, null, 2)
      console.log('✅ LLM配置加载成功')
      
      // 检查配置完整性
      if (!response.data.providers || !Array.isArray(response.data.providers)) {
        warnings.value.push('配置缺少providers数组，可能需要添加提供商配置')
      } else if (response.data.providers.length === 0) {
        warnings.value.push('当前没有配置任何LLM提供商')
      }
      
      if (!response.data.default_provider) {
        warnings.value.push('未设置默认提供商，建议配置default_provider字段')
      }
    } else {
      throw new Error('服务器返回空配置')
    }
  } catch (e) {
    console.error('加载LLM配置失败:', e)
    error.value = e.response?.data?.detail || e.message || '未知错误'
    
    // 创建默认配置模板
    const defaultConfig = {
      "version": "1.0",
      "name": "LLM配置",
      "description": "大语言模型提供商配置",
      "default_provider": null,
      "providers": [],
      "global_settings": {
        "timeout": 30,
        "max_retries": 3,
        "enable_cache": true,
        "cache_timeout": 300
      }
    }
    
    originalConfig.value = defaultConfig
    configJson.value = JSON.stringify(defaultConfig, null, 2)
    warnings.value = ['无法加载现有配置，已创建基本模板。请添加提供商配置后保存。']
  } finally {
    loading.value = false
  }
}

const refreshConfig = () => {
  loadConfig()
  // 发送重载事件
  emit('config-reload')
}

const validateConfig = async () => {
  if (!isValidJson.value) {
    ElMessage.error('JSON格式无效，无法验证')
    return
  }
  
  validating.value = true
  validationResult.value = null
  
  try {
    const response = await axios.post('/api/v2/llm/config/validate', {}, {
      timeout: 10000
    })
    
    validationResult.value = response.data
    
    if (response.data.valid) {
      ElMessage.success('配置验证通过')
    } else {
      ElMessage.warning('配置验证发现问题，请查看详情')
    }
  } catch (e) {
    console.error('配置验证失败:', e)
    ElMessage.error(`验证失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    validating.value = false
  }
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

const exportConfig = async () => {
  try {
    const response = await axios.get('/api/v2/llm/config/export', {
      responseType: 'blob'
    })
    
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `llm_config_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('配置导出成功')
  } catch (e) {
    console.error('导出配置失败:', e)
    ElMessage.error(`导出失败: ${e.response?.data?.detail || e.message}`)
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  fileList.value = [file]
}

const importConfig = () => {
  if (!selectedFile.value) {
    ElMessage.error('请选择配置文件')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const configText = e.target.result
      const config = JSON.parse(configText)
      
      configJson.value = JSON.stringify(config, null, 2)
      showImportDialog.value = false
      fileList.value = []
      selectedFile.value = null
      
      ElMessage.success('配置导入成功，请检查后保存')
    } catch (error) {
      ElMessage.error(`配置文件格式无效: ${error.message}`)
    }
  }
  
  reader.readAsText(selectedFile.value)
}

const onConfigChange = () => {
  // 配置变更时清除验证结果
  validationResult.value = null
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
    
    console.log('开始保存LLM配置...')
    const response = await axios.post('/api/v2/llm/config/update', {
      config: config
    }, {
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.data && response.data.message) {
      saveSuccess.value = true
      saveResultMessage.value = response.data.message
      originalConfig.value = JSON.parse(JSON.stringify(config))
      console.log('✅ LLM配置保存成功')
      
      // 发送保存事件
      emit('config-save', configJson.value)
      
      // 重新加载备份列表
      loadBackups()
    } else {
      throw new Error('保存失败，服务器返回未知状态')
    }
  } catch (e) {
    console.error('保存LLM配置失败:', e)
    saveSuccess.value = false
    saveResultMessage.value = 'LLM配置保存失败'
    
    if (e.response) {
      const errorDetail = e.response.data?.detail || e.response.data?.message || e.message
      saveError.value = `服务器错误 (${e.response.status}): ${errorDetail}`
    } else if (e.request) {
      saveError.value = `网络错误: 服务器没有响应 (${e.message})`
    } else {
      saveError.value = `请求错误: ${e.message}`
    }
  } finally {
    saving.value = false
    saveResultVisible.value = true
  }
}

const loadBackups = async () => {
  backupsLoading.value = true
  
  try {
    const response = await axios.get('/api/v2/llm/config/backups')
    backups.value = response.data || []
  } catch (e) {
    console.error('加载备份列表失败:', e)
    ElMessage.error('加载备份列表失败')
    backups.value = []
  } finally {
    backupsLoading.value = false
  }
}

const restoreBackup = async (backupName) => {
  try {
    await ElMessageBox.confirm(
      `确定要恢复备份 "${backupName}" 吗？当前配置将被覆盖。`,
      '确认恢复',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await axios.post(`/api/v2/llm/config/restore/${backupName}`)
    
    if (response.data && response.data.message) {
      ElMessage.success(response.data.message)
      await loadConfig() // 重新加载配置
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('恢复备份失败:', e)
      ElMessage.error(`恢复失败: ${e.response?.data?.detail || e.message}`)
    }
  }
}

const handleAfterSave = () => {
  saveResultVisible.value = false
  refreshConfig()
}

// 工具函数
const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 监听初始配置变化
watch(() => props.initialConfig, (newConfig) => {
  if (newConfig && newConfig.trim()) {
    try {
      JSON.parse(newConfig) // 验证JSON格式
      configJson.value = newConfig
      originalConfig.value = JSON.parse(newConfig)
    } catch (error) {
      console.warn('接收到的初始配置格式无效:', error)
    }
  }
}, { immediate: true })

// 生命周期钩子
onMounted(async () => {
  // 如果没有初始配置，则从API加载
  if (!props.initialConfig?.trim()) {
    await loadConfig()
  }
  await loadBackups()
})
</script>

<style scoped>
.llm-config-editor {
  width: 100%;
}

.config-card, .backup-card {
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

.warnings-container, .validation-container {
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
  max-height: 600px;
  overflow-y: auto;
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
  width: 100px;
  flex-shrink: 0;
}

.preview-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.provider-model {
  font-size: 11px;
  opacity: 0.8;
  margin-left: 4px;
}

.providers-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.settings-grid {
  display: grid;
  gap: 8px;
}

.empty-message {
  font-style: italic;
  color: #909399;
}

.preview-error {
  color: #f56c6c;
  font-style: italic;
}

.backups-container {
  overflow-x: auto;
}

.no-backups {
  text-align: center;
  padding: 20px;
  color: #909399;
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
  max-height: 200px;
}

.error-details pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
}

.upload-demo {
  width: 100%;
}

.el-upload__tip {
  color: #606266;
  font-size: 12px;
  margin-top: 7px;
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