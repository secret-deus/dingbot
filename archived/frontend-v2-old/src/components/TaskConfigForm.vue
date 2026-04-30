<template>
  <div class="task-config-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      @submit.prevent
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h3 class="section-title">基本信息</h3>
        
        <el-form-item label="任务名称" prop="name" required>
          <el-input
            v-model="formData.name"
            placeholder="请输入任务名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="任务类型" prop="task_type" required>
          <el-select
            v-model="formData.task_type"
            placeholder="请选择任务类型"
            @change="onTaskTypeChange"
            style="width: 100%"
          >
            <el-option
              v-for="type in taskTypes"
              :key="type.type"
              :label="type.name"
              :value="type.type"
            >
              <div class="task-type-option">
                <div class="type-name">{{ type.name }}</div>
                <div class="type-description">{{ type.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </div>

      <!-- 调度配置 -->
      <div class="form-section">
        <h3 class="section-title">调度配置</h3>
        
        <el-form-item label="执行计划" prop="cron_expression" required>
          <CronEditor
            v-model="formData.cron_expression"
            @validate="onCronValidate"
          />
        </el-form-item>

        <el-form-item label="启用状态" prop="enabled">
          <el-switch
            v-model="formData.enabled"
            active-text="启用"
            inactive-text="禁用"
          />
          <div class="field-help">
            启用后任务将按照设定的计划自动执行
          </div>
        </el-form-item>
      </div>

      <!-- 执行配置 -->
      <div class="form-section">
        <h3 class="section-title">执行配置</h3>
        
        <el-form-item label="超时时间" prop="timeout_seconds">
          <el-input-number
            v-model="formData.timeout_seconds"
            :min="30"
            :max="3600"
            :step="30"
            controls-position="right"
            style="width: 200px"
          />
          <span class="field-unit">秒</span>
          <div class="field-help">
            任务执行的最大时间限制，超时将被强制终止
          </div>
        </el-form-item>

        <el-form-item label="最大重试" prop="max_retries">
          <el-input-number
            v-model="formData.max_retries"
            :min="0"
            :max="10"
            :step="1"
            controls-position="right"
            style="width: 200px"
          />
          <span class="field-unit">次</span>
          <div class="field-help">
            任务失败时的最大重试次数
          </div>
        </el-form-item>

        <el-form-item label="通知级别" prop="notification_level">
          <el-radio-group v-model="formData.notification_level">
            <el-radio label="none">无通知</el-radio>
            <el-radio label="error">仅错误</el-radio>
            <el-radio label="all">全部通知</el-radio>
          </el-radio-group>
          <div class="field-help">
            选择何时发送通知到钉钉群
          </div>
        </el-form-item>
      </div>

      <!-- 任务特定配置 -->
      <div v-if="formData.task_type" class="form-section">
        <h3 class="section-title">{{ getTaskTypeConfig().title }}</h3>
        
        <!-- 集群巡检配置 -->
        <template v-if="formData.task_type === 'cluster_check'">
          <el-form-item label="巡检范围" prop="config.scope">
            <el-checkbox-group v-model="formData.config.scope.includeNamespaces">
              <el-checkbox label="default">默认命名空间</el-checkbox>
              <el-checkbox label="kube-system">系统命名空间</el-checkbox>
              <el-checkbox label="monitoring">监控命名空间</el-checkbox>
              <el-checkbox label="ingress-nginx">Ingress命名空间</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="巡检深度" prop="config.scope.maxDepth">
            <el-slider
              v-model="formData.config.scope.maxDepth"
              :min="1"
              :max="5"
              :marks="{ 1: '基础', 3: '标准', 5: '深度' }"
              style="width: 300px"
            />
          </el-form-item>

          <el-form-item label="巡检选项">
            <el-checkbox v-model="formData.config.options.sendToDingTalk">
              发送到钉钉群
            </el-checkbox>
            <el-checkbox v-model="formData.config.options.includeAnomalies">
              包含异常检测
            </el-checkbox>
            <el-checkbox v-model="formData.config.options.generateReport">
              生成详细报告
            </el-checkbox>
          </el-form-item>
        </template>

        <!-- 资源分析配置 -->
        <template v-if="formData.task_type === 'resource_analysis'">
          <el-form-item label="分析指标" prop="config.metrics">
            <el-checkbox-group v-model="formData.config.metrics">
              <el-checkbox label="cpu">CPU使用率</el-checkbox>
              <el-checkbox label="memory">内存使用率</el-checkbox>
              <el-checkbox label="disk">磁盘使用率</el-checkbox>
              <el-checkbox label="network">网络流量</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="时间范围" prop="config.timeRange">
            <el-select v-model="formData.config.timeRange" style="width: 200px">
              <el-option label="最近1小时" value="1h" />
              <el-option label="最近6小时" value="6h" />
              <el-option label="最近24小时" value="24h" />
              <el-option label="最近7天" value="7d" />
            </el-select>
          </el-form-item>

          <el-form-item label="阈值设置">
            <div class="threshold-config">
              <div class="threshold-item">
                <span class="threshold-label">CPU警告阈值:</span>
                <el-input-number
                  v-model="formData.config.thresholds.cpu.warning"
                  :min="0"
                  :max="100"
                  :precision="1"
                  controls-position="right"
                  style="width: 120px"
                />
                <span class="threshold-unit">%</span>
              </div>
              <div class="threshold-item">
                <span class="threshold-label">内存警告阈值:</span>
                <el-input-number
                  v-model="formData.config.thresholds.memory.warning"
                  :min="0"
                  :max="100"
                  :precision="1"
                  controls-position="right"
                  style="width: 120px"
                />
                <span class="threshold-unit">%</span>
              </div>
            </div>
          </el-form-item>
        </template>

        <!-- 健康监控配置 -->
        <template v-if="formData.task_type === 'health_monitor'">
          <el-form-item label="监控组件" prop="config.components">
            <el-checkbox-group v-model="formData.config.components">
              <el-checkbox label="api-server">API Server</el-checkbox>
              <el-checkbox label="etcd">ETCD</el-checkbox>
              <el-checkbox label="controller-manager">Controller Manager</el-checkbox>
              <el-checkbox label="scheduler">Scheduler</el-checkbox>
              <el-checkbox label="kubelet">Kubelet</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="检查间隔" prop="config.checkInterval">
            <el-input-number
              v-model="formData.config.checkInterval"
              :min="30"
              :max="3600"
              :step="30"
              controls-position="right"
              style="width: 200px"
            />
            <span class="field-unit">秒</span>
          </el-form-item>

          <el-form-item label="失败阈值" prop="config.failureThreshold">
            <el-input-number
              v-model="formData.config.failureThreshold"
              :min="1"
              :max="10"
              :step="1"
              controls-position="right"
              style="width: 200px"
            />
            <span class="field-unit">次</span>
            <div class="field-help">
              连续失败多少次后触发告警
            </div>
          </el-form-item>
        </template>

        <!-- 自定义任务配置 -->
        <template v-if="formData.task_type === 'custom'">
          <el-form-item label="工具调用" prop="config.tools" required>
            <div class="tools-config">
              <div
                v-for="(tool, index) in formData.config.tools"
                :key="index"
                class="tool-item"
              >
                <el-card class="tool-card" shadow="hover">
                  <div class="tool-header">
                    <span class="tool-title">工具 {{ index + 1 }}</span>
                    <el-button
                      size="small"
                      type="danger"
                      @click="removeTool(index)"
                      :disabled="formData.config.tools.length === 1"
                    >
                      删除
                    </el-button>
                  </div>
                  
                  <el-form-item label="工具名称" :prop="`config.tools.${index}.name`" required>
                    <el-select
                      v-model="tool.name"
                      placeholder="选择MCP工具"
                      filterable
                      style="width: 100%"
                    >
                      <el-option
                        v-for="availableTool in availableTools"
                        :key="availableTool.name"
                        :label="availableTool.name"
                        :value="availableTool.name"
                      >
                        <div class="tool-option">
                          <div class="tool-name">{{ availableTool.name }}</div>
                          <div class="tool-desc">{{ availableTool.description }}</div>
                        </div>
                      </el-option>
                    </el-select>
                  </el-form-item>

                  <el-form-item label="参数配置" :prop="`config.tools.${index}.parameters`">
                    <el-input
                      v-model="tool.parameters"
                      type="textarea"
                      :rows="3"
                      placeholder="JSON格式的参数配置（可选）"
                    />
                  </el-form-item>
                </el-card>
              </div>
              
              <el-button
                type="dashed"
                @click="addTool"
                style="width: 100%; margin-top: 16px"
              >
                <el-icon><Plus /></el-icon>
                添加工具
              </el-button>
            </div>
          </el-form-item>
        </template>
      </div>

      <!-- 表单操作 -->
      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ isEditing ? '更新任务' : '创建任务' }}
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, schedulerApiUtils, SCHEDULER_CONSTANTS } from '@/api/client'
import CronEditor from './CronEditor.vue'

// Props
const props = defineProps({
  task: {
    type: Object,
    default: null
  },
  isEditing: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['save', 'cancel'])

// 响应式数据
const formRef = ref(null)
const saving = ref(false)
const taskTypes = ref([])
const availableTools = ref([])

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  task_type: '',
  cron_expression: '0 0 * * *',
  enabled: true,
  timeout_seconds: 300,
  max_retries: 3,
  notification_level: 'error',
  config: {}
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 1, max: 100, message: '任务名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  cron_expression: [
    { required: true, message: '请设置执行计划', trigger: 'blur' },
    { validator: validateCronExpression, trigger: 'blur' }
  ],
  timeout_seconds: [
    { type: 'number', min: 30, max: 3600, message: '超时时间必须在30-3600秒之间', trigger: 'blur' }
  ],
  max_retries: [
    { type: 'number', min: 0, max: 10, message: '重试次数必须在0-10次之间', trigger: 'blur' }
  ]
}

// 计算属性
const isEditing = computed(() => props.isEditing)

// 方法
const loadTaskTypes = async () => {
  try {
    const response = await api.scheduler.getTaskTypes()
    taskTypes.value = response.data.task_types || []
  } catch (error) {
    console.error('获取任务类型失败:', error)
    ElMessage.error('获取任务类型失败')
  }
}

const loadAvailableTools = async () => {
  try {
    const response = await api.system.getTools()
    availableTools.value = response.data.tools || []
  } catch (error) {
    console.error('获取可用工具失败:', error)
  }
}

const initFormData = () => {
  if (props.task) {
    // 编辑模式：填充现有任务数据
    Object.assign(formData, {
      name: props.task.name || '',
      description: props.task.description || '',
      task_type: props.task.task_type || '',
      cron_expression: props.task.cron_expression || '0 0 * * *',
      enabled: props.task.enabled !== undefined ? props.task.enabled : true,
      timeout_seconds: props.task.timeout_seconds || 300,
      max_retries: props.task.max_retries || 3,
      notification_level: props.task.notification_level || 'error',
      config: props.task.config || {}
    })
  } else {
    // 创建模式：使用默认值
    resetFormData()
  }
}

const resetFormData = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    task_type: '',
    cron_expression: '0 0 * * *',
    enabled: true,
    timeout_seconds: 300,
    max_retries: 3,
    notification_level: 'error',
    config: {}
  })
}

const onTaskTypeChange = (taskType) => {
  // 根据任务类型初始化配置
  switch (taskType) {
    case 'cluster_check':
      formData.config = {
        scope: {
          includeNamespaces: ['default', 'kube-system'],
          maxDepth: 2
        },
        options: {
          sendToDingTalk: true,
          includeAnomalies: true,
          generateReport: false
        }
      }
      break
    case 'resource_analysis':
      formData.config = {
        metrics: ['cpu', 'memory'],
        timeRange: '24h',
        thresholds: {
          cpu: { warning: 80, critical: 90 },
          memory: { warning: 85, critical: 95 }
        }
      }
      break
    case 'health_monitor':
      formData.config = {
        components: ['api-server', 'etcd', 'controller-manager'],
        checkInterval: 300,
        failureThreshold: 3
      }
      break
    case 'custom':
      formData.config = {
        tools: [
          {
            name: '',
            parameters: ''
          }
        ]
      }
      break
    default:
      formData.config = {}
  }
}

const getTaskTypeConfig = () => {
  const configs = {
    cluster_check: { title: '集群巡检配置' },
    resource_analysis: { title: '资源分析配置' },
    health_monitor: { title: '健康监控配置' },
    custom: { title: '自定义工具配置' }
  }
  return configs[formData.task_type] || { title: '任务配置' }
}

const addTool = () => {
  if (formData.config.tools) {
    formData.config.tools.push({
      name: '',
      parameters: ''
    })
  }
}

const removeTool = (index) => {
  if (formData.config.tools && formData.config.tools.length > 1) {
    formData.config.tools.splice(index, 1)
  }
}

const onCronValidate = (isValid, error) => {
  if (!isValid) {
    ElMessage.error(`Cron表达式错误: ${error}`)
  }
}

// 验证函数
function validateCronExpression(rule, value, callback) {
  if (!value) {
    callback(new Error('请设置执行计划'))
    return
  }
  
  const validation = schedulerApiUtils.validators.validateCronFormat(value)
  if (!validation.valid) {
    callback(new Error(validation.message))
  } else {
    callback()
  }
}

// 表单操作
const handleSave = async () => {
  try {
    // 表单验证
    await formRef.value.validate()
    
    saving.value = true
    
    // 准备提交数据
    const submitData = { ...formData }
    
    // 处理自定义任务的参数
    if (submitData.task_type === 'custom' && submitData.config.tools) {
      submitData.config.tools = submitData.config.tools.map(tool => ({
        ...tool,
        parameters: tool.parameters ? JSON.parse(tool.parameters) : {}
      }))
    }
    
    emit('save', submitData)
  } catch (error) {
    if (error.name === 'SyntaxError') {
      ElMessage.error('JSON参数格式错误，请检查参数配置')
    } else {
      console.error('表单验证失败:', error)
    }
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadTaskTypes(),
    loadAvailableTools()
  ])
  initFormData()
})

// 监听props变化
watch(() => props.task, () => {
  initFormData()
}, { deep: true })
</script>

<style scoped>
.task-config-form {
  max-width: 800px;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-extra-light);
}

.form-section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--primary-color);
}

.task-type-option {
  display: flex;
  flex-direction: column;
}

.type-name {
  font-weight: 500;
  color: var(--text-primary);
}

.type-description {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.field-help {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.field-unit {
  margin-left: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.threshold-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.threshold-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.threshold-label {
  min-width: 120px;
  font-size: 14px;
  color: var(--text-primary);
}

.threshold-unit {
  margin-left: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.tools-config {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 16px;
  background: var(--background-base);
}

.tool-item {
  margin-bottom: 16px;
}

.tool-item:last-child {
  margin-bottom: 0;
}

.tool-card {
  border: 1px solid var(--border-light);
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tool-title {
  font-weight: 500;
  color: var(--text-primary);
}

.tool-option {
  display: flex;
  flex-direction: column;
}

.tool-name {
  font-weight: 500;
  color: var(--text-primary);
}

.tool-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid var(--border-extra-light);
  margin-top: 32px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-primary);
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 24px;
}

:deep(.el-slider) {
  margin: 16px 0;
}
</style>
