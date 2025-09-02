<template>
  <div class="settings-page">
    <div class="settings-header">
      <h1 class="page-title">配置管理</h1>
      <el-button type="primary" @click="saveAllSettings">
        <el-icon><Check /></el-icon>
        保存所有配置
      </el-button>
    </div>
    
    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane label="LLM表单配置" name="llm-form">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">大语言模型配置</h3>
            <div class="card-header-actions">
              <!-- 配置模式切换器 -->
              <div class="config-mode-switcher">
                <el-radio-group v-model="activeConfigMode" size="small" @change="switchConfigMode">
                  <el-radio-button label="form">表单模式</el-radio-button>
                  <el-radio-button label="file">文件模式</el-radio-button>
                </el-radio-group>
              </div>
              
              <!-- 配置同步控制 -->
              <div class="config-sync-control">
                <el-switch
                  v-model="configSyncMode"
                  active-text="自动同步"
                  inactive-text=""
                  size="small"
                />
                <el-tooltip content="启用后，在两种模式间自动同步配置" placement="top">
                  <el-icon><Warning /></el-icon>
                </el-tooltip>
              </div>
              
              <!-- 手动同步按钮 -->
              <div class="manual-sync-buttons">
                <el-button size="small" @click="syncFormToFile">
                  <el-icon><CircleCheck /></el-icon>
                  同步到文件
                </el-button>
                <el-button size="small" @click="syncFileToForm">
                  <el-icon><CircleCheck /></el-icon>
                  从文件同步
                </el-button>
              </div>
              
              <!-- 配置同步状态指示器 -->
              <div class="config-sync-status" :class="syncStatusClass">
                <el-icon><component :is="syncStatusIcon" /></el-icon>
                <span class="sync-text">{{ syncStatusText }}</span>
              </div>
              <el-switch
                v-model="llmConfig.enabled"
                :active-text="llmConfig.enabled ? '已启用' : '已禁用'"
                :inactive-text="''"
                active-color="#13ce66"
                inactive-color="#ff4949"
                class="llm-enable-switch"
                @change="handleLLMEnabledChange"
              />
              <el-button 
                size="small" 
                @click="testLLMConfig"
                :disabled="!llmConfig.enabled"
              >
                <el-icon><Link /></el-icon>
                测试连接
              </el-button>
              <el-button 
                size="small" 
                type="warning"
                @click="reloadLLMConfig"
                :loading="reloadLoading"
              >
                <el-icon><Refresh /></el-icon>
                重新加载
              </el-button>
            </div>
          </div>
          <div class="config-form" :class="{ 'disabled': !llmConfig.enabled }">
            <el-form :model="llmConfig" label-width="120px" :disabled="!llmConfig.enabled">
              <el-form-item label="提供商:">
                <el-select 
                  v-model="llmConfig.provider" 
                  placeholder="选择LLM提供商"
                  @change="handleProviderChange"
                >
                  <el-option 
                    v-for="provider in providers" 
                    :key="provider.id" 
                    :label="provider.name" 
                    :value="provider.id"
                  >
                    <span>{{ provider.name }}</span>
                    <span style="color: #8492a6; font-size: 12px; margin-left: 8px;">
                      {{ provider.description }}
                    </span>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="模型名称:">
                <el-autocomplete
                  v-model="llmConfig.model"
                  :fetch-suggestions="getModelSuggestions"
                  :placeholder="currentProvider?.default_models?.[0] || '输入模型名称'"
                  style="width: 100%"
                />
              </el-form-item>
              
              <!-- API密钥 - ollama不需要 -->
              <el-form-item 
                v-if="currentProvider && currentProvider.required_fields.includes('api_key')"
                label="API密钥:"
              >
                <el-input 
                  v-model="llmConfig.api_key" 
                  type="password" 
                  placeholder="输入API密钥" 
                />
              </el-form-item>
              
              <!-- Base URL - 根据提供商决定是否必填 -->
              <el-form-item 
                :label="currentProvider && currentProvider.required_fields.includes('base_url') ? 'Base URL*:' : 'Base URL:'"
              >
                <el-input 
                  v-model="llmConfig.base_url" 
                  :placeholder="getBaseUrlPlaceholder()" 
                />
                <div v-if="llmConfig.provider === 'ollama'" class="form-help">
                  默认: http://localhost:11434/v1
                </div>
              </el-form-item>
              
              <!-- Azure特有字段 -->
              <el-form-item 
                v-if="currentProvider && currentProvider.required_fields.includes('deployment_name')"
                label="部署名称*:"
              >
                <el-input 
                  v-model="llmConfig.deployment_name" 
                  placeholder="Azure OpenAI部署名称" 
                />
              </el-form-item>
              
              <el-form-item 
                v-if="currentProvider && currentProvider.optional_fields.includes('api_version')"
                label="API版本:"
              >
                <el-input 
                  v-model="llmConfig.api_version" 
                  placeholder="如: 2023-12-01-preview" 
                />
              </el-form-item>
              
              <!-- 组织ID - OpenAI特有 -->
              <el-form-item 
                v-if="currentProvider && currentProvider.optional_fields.includes('organization')"
                label="组织ID:"
              >
                <el-input 
                  v-model="llmConfig.organization" 
                  placeholder="可选，OpenAI组织ID" 
                />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="LLM文件配置" name="llm-file">
        <LLMConfigFileEditor 
          :initial-config="llmFileConfig"
          @config-save="handleFileSave"
          @config-reload="handleFileReload"
        />
      </el-tab-pane>
      
      <el-tab-pane label="MCP配置" name="mcp">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">MCP客户端配置</h3>
            <el-button size="small" @click="refreshMCPStatus">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>
          <div class="config-form">
            <el-form :model="mcpConfig" label-width="120px">
              <el-form-item label="超时时间:">
                <el-input-number v-model="mcpConfig.timeout" :min="1000" :max="60000" />
                <span class="unit">毫秒</span>
              </el-form-item>
              <el-form-item label="重试次数:">
                <el-input-number v-model="mcpConfig.retry_attempts" :min="1" :max="10" />
              </el-form-item>
              <el-form-item label="并发数:">
                <el-input-number v-model="mcpConfig.max_concurrent_calls" :min="1" :max="20" />
              </el-form-item>
              <el-form-item label="启用缓存:">
                <el-switch v-model="mcpConfig.enable_cache" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="系统信息" name="system">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">系统状态</h3>
            <span class="status-indicator online">运行中</span>
          </div>
          <div class="system-info">
            <div class="info-item">
              <span class="label">前端版本:</span>
              <span class="value">1.0.0</span>
            </div>
            <div class="info-item">
              <span class="label">API版本:</span>
              <span class="value">v2.0</span>
            </div>
            <div class="info-item">
              <span class="label">构建时间:</span>
              <span class="value">{{ buildTime }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Link, Refresh, CircleCheck, Warning, CircleClose } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import LLMConfigFileEditor from '@/components/LLMConfigFileEditor.vue'

const activeTab = ref('llm-form') // 默认使用表单配置
const buildTime = ref(new Date().toLocaleString())
const reloadLoading = ref(false)

// 双模式配置管理
const activeConfigMode = ref('form') // 'form' or 'file'
const llmFileConfig = ref('') // 文件配置内容
const configSyncMode = ref(false) // 是否启用配置同步

// 配置同步状态
const configSyncStatus = ref({
  synced: true,
  runtime_config: null,
  saved_config: null,
  last_check: null
})

// 提供商数据
const providers = ref([])
const providersLoading = ref(false)

// LLM配置，增加更多字段
const llmConfig = ref({
  enabled: true, // 新增：LLM启用状态
  provider: 'openai',
  model: 'gpt-3.5-turbo',
  api_key: '',
  base_url: '',
  deployment_name: '', // Azure专用
  api_version: '', // Azure专用  
  organization: '' // OpenAI专用
})

const mcpConfig = ref({
  timeout: 30000,
  retry_attempts: 3,
  max_concurrent_calls: 5,
  enable_cache: true
})

// 计算属性：获取当前选择的提供商信息
const currentProvider = computed(() => {
  return providers.value.find(p => p.id === llmConfig.value.provider)
})

// 配置同步状态相关计算属性
const syncStatusClass = computed(() => {
  if (!configSyncStatus.value.synced) return 'status-warning'
  return 'status-success'
})

const syncStatusIcon = computed(() => {
  if (!configSyncStatus.value.synced) return Warning
  return CircleCheck
})

const syncStatusText = computed(() => {
  if (!configSyncStatus.value.synced) return '配置未同步'
  return '配置已同步'
})

// 加载支持的提供商
const loadProviders = async () => {
  try {
    providersLoading.value = true
    const response = await api.config.getProviders()
    providers.value = response.data.data.llm_providers || []
    console.log('已加载提供商:', providers.value)
  } catch (error) {
    console.error('加载提供商失败:', error)
    ElMessage.error('加载提供商列表失败')
    // 使用备用的硬编码列表
    providers.value = [
      { id: 'openai', name: 'OpenAI', description: 'OpenAI GPT models', required_fields: ['api_key'], default_models: ['gpt-3.5-turbo'] }
    ]
  } finally {
    providersLoading.value = false
  }
}

// 处理提供商变化
const handleProviderChange = (providerId) => {
  const provider = providers.value.find(p => p.id === providerId)
  if (provider) {
    // 根据提供商设置默认模型
    if (provider.default_models && provider.default_models.length > 0) {
      llmConfig.value.model = provider.default_models[0]
    }
    
    // 清除不适用的字段
    if (!provider.required_fields.includes('api_key') && !provider.optional_fields?.includes('api_key')) {
      llmConfig.value.api_key = ''
    }
    if (!provider.required_fields.includes('deployment_name')) {
      llmConfig.value.deployment_name = ''
    }
    if (!provider.optional_fields?.includes('organization')) {
      llmConfig.value.organization = ''
    }
    
    console.log('提供商已切换到:', provider.name)
  }
}

// 获取模型建议
const getModelSuggestions = (queryString, callback) => {
  if (!currentProvider.value) {
    callback([])
    return
  }
  
  const suggestions = currentProvider.value.default_models?.map(model => ({
    value: model,
    label: model
  })) || []
  
  if (queryString) {
    const filtered = suggestions.filter(item => 
      item.value.toLowerCase().includes(queryString.toLowerCase())
    )
    callback(filtered)
  } else {
    callback(suggestions)
  }
}

// 获取Base URL占位符
const getBaseUrlPlaceholder = () => {
  if (!currentProvider.value) return '可选，自定义API地址'
  
  const placeholders = {
    'ollama': 'http://localhost:11434/v1',
    'azure': 'https://your-resource.openai.azure.com/',
    'zhipu': 'https://open.bigmodel.cn/api/paas/v4/',
    'qwen': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'custom': '输入您的API地址'
  }
  
  const placeholder = placeholders[llmConfig.value.provider] || '可选，自定义API地址'
  const isRequired = currentProvider.value.required_fields.includes('base_url')
  
  return isRequired ? `${placeholder} (必填)` : placeholder
}

const saveAllSettings = async () => {
  try {
    // 显示配置更新功能暂不支持的提示
    ElMessageBox.alert(
      '配置更新功能暂不支持，请直接修改环境变量文件后重启服务。完整的配置管理功能将在v2.0版本中实现。',
      '功能暂不支持',
      {
        confirmButtonText: '我知道了',
        type: 'info',
        dangerouslyUseHTMLString: true,
        message: `
          <div>
            <p><strong>当前版本采用环境变量配置方案</strong></p>
            <p>请在项目根目录的 <code>config.env</code> 文件中修改以下环境变量：</p>
            <ul style="text-align: left; margin: 10px 0;">
              <li><code>LLM_PROVIDER</code> - LLM供应商</li>
              <li><code>LLM_MODEL</code> - 模型名称</li>
              <li><code>LLM_API_KEY</code> - API密钥</li>
              <li><code>LLM_BASE_URL</code> - API基础URL（可选）</li>
            </ul>
            <p>修改后请重启服务以应用新配置。</p>
          </div>
        `
      }
    )
    
    console.log('LLM配置（仅显示）:', llmConfig.value)
    console.log('MCP配置（仅显示）:', mcpConfig.value)
  } catch (error) {
    console.error('显示配置提示失败:', error)
  }
}

// 双模式配置同步处理函数
const syncFormToFile = () => {
  try {
    // 将表单配置转换为文件配置格式
    const formConfig = {
      version: "1.0",
      name: "LLM配置",
      description: "从表单配置同步的LLM配置",
      default_provider: llmConfig.value.provider,
      providers: [
        {
          id: llmConfig.value.provider,
          name: getProviderDisplayName(llmConfig.value.provider),
          enabled: llmConfig.value.enabled,
          model: llmConfig.value.model,
          api_key: llmConfig.value.api_key,
          base_url: llmConfig.value.base_url,
          deployment_name: llmConfig.value.deployment_name,
          api_version: llmConfig.value.api_version,
          organization: llmConfig.value.organization,
          temperature: 0.7,
          max_tokens: 2000,
          timeout: 30
        }
      ],
      global_settings: {
        timeout: 30,
        max_retries: 3,
        enable_cache: true
      }
    }
    
    llmFileConfig.value = JSON.stringify(formConfig, null, 2)
    ElMessage.success('表单配置已同步到文件配置')
  } catch (error) {
    console.error('同步表单到文件配置失败:', error)
    ElMessage.error(`同步失败: ${error.message}`)
  }
}

const syncFileToForm = () => {
  try {
    if (!llmFileConfig.value.trim()) {
      ElMessage.warning('文件配置为空，无法同步')
      return
    }
    
    const fileConfig = JSON.parse(llmFileConfig.value)
    
    // 获取第一个提供商的配置
    const firstProvider = fileConfig.providers?.[0]
    if (firstProvider) {
      llmConfig.value = {
        enabled: firstProvider.enabled !== undefined ? firstProvider.enabled : true,
        provider: firstProvider.id || 'openai',
        model: firstProvider.model || 'gpt-3.5-turbo',
        api_key: firstProvider.api_key || '',
        base_url: firstProvider.base_url || '',
        deployment_name: firstProvider.deployment_name || '',
        api_version: firstProvider.api_version || '',
        organization: firstProvider.organization || ''
      }
      
      ElMessage.success('文件配置已同步到表单配置')
    } else {
      ElMessage.warning('文件配置中没有找到提供商配置')
    }
  } catch (error) {
    console.error('同步文件到表单配置失败:', error)
    ElMessage.error(`同步失败: ${error.message}`)
  }
}

const getProviderDisplayName = (providerId) => {
  const provider = providers.value.find(p => p.id === providerId)
  return provider ? provider.name : providerId
}

// 处理文件配置保存
const handleFileSave = (config) => {
  llmFileConfig.value = config
  if (configSyncMode.value) {
    syncFileToForm()
  }
}

// 处理文件配置重载
const handleFileReload = () => {
  if (configSyncMode.value) {
    syncFormToFile()
  }
}

// 切换配置模式
const switchConfigMode = (mode) => {
  if (mode === 'file' && activeConfigMode.value === 'form') {
    // 从表单切换到文件模式时，提示是否同步
    ElMessageBox.confirm(
      '是否将当前表单配置同步到文件配置？',
      '切换到文件配置',
      {
        confirmButtonText: '同步',
        cancelButtonText: '不同步',
        type: 'info'
      }
    ).then(() => {
      syncFormToFile()
      activeConfigMode.value = mode
      activeTab.value = 'llm-file'
    }).catch(() => {
      activeConfigMode.value = mode
      activeTab.value = 'llm-file'
    })
  } else if (mode === 'form' && activeConfigMode.value === 'file') {
    // 从文件切换到表单模式时，提示是否同步
    ElMessageBox.confirm(
      '是否将当前文件配置同步到表单配置？',
      '切换到表单配置',
      {
        confirmButtonText: '同步',
        cancelButtonText: '不同步',
        type: 'info'
      }
    ).then(() => {
      syncFileToForm()
      activeConfigMode.value = mode
      activeTab.value = 'llm-form'
    }).catch(() => {
      activeConfigMode.value = mode
      activeTab.value = 'llm-form'
    })
  } else {
    activeConfigMode.value = mode
    activeTab.value = mode === 'form' ? 'llm-form' : 'llm-file'
  }
}

// 检查配置同步状态
const checkConfigSync = async () => {
  try {
    const response = await api.config.getLLMRuntimeConfig()
    if (response.data.success) {
      configSyncStatus.value = {
        synced: response.data.config_synced,
        runtime_config: response.data.runtime_config,
        saved_config: response.data.saved_config,
        last_check: new Date().toISOString()
      }
      
      if (!response.data.config_synced) {
        ElMessage.warning('检测到配置不同步，建议点击"重新加载"按钮')
      }
    }
  } catch (error) {
    console.error('检查配置同步状态失败:', error)
    configSyncStatus.value.synced = false
  }
}

// 重新加载LLM配置
const reloadLLMConfig = async () => {
  try {
    reloadLoading.value = true
    
    // 显示重载功能暂不支持的提示
    ElMessage.info('配置热重载功能暂不支持，请重启服务以应用新的环境变量配置。')
    
    // 重新加载当前配置显示
    await loadCurrentLLMConfig()
    
    ElMessage.success('已刷新配置显示')
  } catch (error) {
    console.error('刷新配置显示失败:', error)
    ElMessage.error('刷新失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    reloadLoading.value = false
  }
}

// LLM启用状态变化处理
const handleLLMEnabledChange = (enabled) => {
  if (enabled) {
    ElMessage.success('LLM功能已启用')
  } else {
    ElMessage.warning('LLM功能已禁用，聊天功能将受限')
  }
  console.log('LLM启用状态:', enabled)
  
  // 可以在这里添加自动保存逻辑
  // saveAllSettings()
}

const testLLMConfig = () => {
  if (!llmConfig.value.enabled) {
    ElMessage.warning('请先启用LLM功能')
    return
  }
  
  ElMessage.info('配置测试功能暂不支持，将在v2.0版本中实现。')
}

const refreshMCPStatus = () => {
  ElMessage.success('MCP状态已刷新')
  // TODO: 实现状态刷新
}

// 加载当前LLM配置
const loadCurrentLLMConfig = async () => {
  try {
    const response = await api.config.getLLMConfig()
    if (response.data.success && response.data.config) {
      const config = response.data.config
      
      // 更新配置，确保enabled字段有默认值
      llmConfig.value = {
        enabled: config.enabled !== undefined ? config.enabled : true,
        provider: config.provider || 'openai',
        model: config.model || 'gpt-3.5-turbo',
        api_key: config.api_key || '',
        base_url: config.base_url || '',
        deployment_name: config.deployment_name || '',
        api_version: config.api_version || '',
        organization: config.organization || ''
      }
      
      console.log('已加载LLM配置:', llmConfig.value)
    }
  } catch (error) {
    console.error('加载LLM配置失败:', error)
    ElMessage.error('加载LLM配置失败')
  }
}

onMounted(async () => {
  // 加载提供商列表
  await loadProviders()
  // 加载当前配置
  await loadCurrentLLMConfig()
  // 检查配置同步状态
  await checkConfigSync()
})
</script>

<style scoped>
.settings-page {
  height: 100%;
  overflow-y: auto;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.settings-tabs {
  height: calc(100% - 80px);
}

.config-form {
  margin-top: 20px;
  transition: opacity 0.3s ease;
}

.config-form.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.card-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.config-mode-switcher {
  margin-right: 8px;
}

.config-sync-control {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: 8px;
}

.manual-sync-buttons {
  display: flex;
  gap: 8px;
  margin-right: 12px;
}

.manual-sync-buttons .el-button {
  font-size: 12px;
  padding: 6px 8px;
}

.config-sync-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-right: 8px;
}

.config-sync-status.status-success {
  background-color: #f0f9ff;
  color: #059669;
  border: 1px solid #bbf7d0;
}

.config-sync-status.status-warning {
  background-color: #fffbeb;
  color: #d97706;
  border: 1px solid #fed7aa;
}

.config-sync-status .sync-text {
  margin-left: 2px;
}

.llm-enable-switch {
  margin-right: 8px;
}

.unit {
  margin-left: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.system-info {
  margin-top: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-extra-light);
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  color: var(--text-secondary);
  font-size: 14px;
}

.value {
  color: var(--text-primary);
  font-weight: 500;
}

.form-help {
  color: #6c757d;
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.4;
}

.el-select-dropdown__item span:last-child {
  float: right;
}

/* 提供商选择器的描述文本样式 */
:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 8px 20px;
  line-height: 1.4;
}
</style> 