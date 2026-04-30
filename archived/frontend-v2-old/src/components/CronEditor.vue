<template>
  <div class="cron-editor">
    <!-- 编辑模式切换 -->
    <div class="editor-header">
      <el-radio-group v-model="editMode" @change="onEditModeChange">
        <el-radio-button label="visual">可视化编辑</el-radio-button>
        <el-radio-button label="text">文本编辑</el-radio-button>
      </el-radio-group>
      
      <div class="header-actions">
        <el-button size="small" @click="showTemplates = true">
          <el-icon><Collection /></el-icon>
          模板
        </el-button>
        <el-button size="small" @click="validateExpression">
          <el-icon><Check /></el-icon>
          验证
        </el-button>
      </div>
    </div>

    <!-- 可视化编辑器 -->
    <div v-if="editMode === 'visual'" class="visual-editor">
      <div class="cron-fields">
        <!-- 分钟 -->
        <div class="field-group">
          <label class="field-label">分钟</label>
          <el-select
            v-model="cronParts.minute"
            @change="updateCronExpression"
            style="width: 100%"
          >
            <el-option label="每分钟" value="*" />
            <el-option label="每5分钟" value="*/5" />
            <el-option label="每10分钟" value="*/10" />
            <el-option label="每15分钟" value="*/15" />
            <el-option label="每30分钟" value="*/30" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-input
            v-if="cronParts.minute === 'custom'"
            v-model="customParts.minute"
            @input="updateCronExpression"
            placeholder="0-59"
            style="margin-top: 8px"
          />
        </div>

        <!-- 小时 -->
        <div class="field-group">
          <label class="field-label">小时</label>
          <el-select
            v-model="cronParts.hour"
            @change="updateCronExpression"
            style="width: 100%"
          >
            <el-option label="每小时" value="*" />
            <el-option label="每2小时" value="*/2" />
            <el-option label="每6小时" value="*/6" />
            <el-option label="每12小时" value="*/12" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-input
            v-if="cronParts.hour === 'custom'"
            v-model="customParts.hour"
            @input="updateCronExpression"
            placeholder="0-23"
            style="margin-top: 8px"
          />
        </div>

        <!-- 日 -->
        <div class="field-group">
          <label class="field-label">日</label>
          <el-select
            v-model="cronParts.day"
            @change="updateCronExpression"
            style="width: 100%"
          >
            <el-option label="每天" value="*" />
            <el-option label="每2天" value="*/2" />
            <el-option label="每周一" value="1" />
            <el-option label="月初" value="1" />
            <el-option label="月末" value="L" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-input
            v-if="cronParts.day === 'custom'"
            v-model="customParts.day"
            @input="updateCronExpression"
            placeholder="1-31"
            style="margin-top: 8px"
          />
        </div>

        <!-- 月 -->
        <div class="field-group">
          <label class="field-label">月</label>
          <el-select
            v-model="cronParts.month"
            @change="updateCronExpression"
            style="width: 100%"
          >
            <el-option label="每月" value="*" />
            <el-option label="每季度" value="*/3" />
            <el-option label="每半年" value="*/6" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-input
            v-if="cronParts.month === 'custom'"
            v-model="customParts.month"
            @input="updateCronExpression"
            placeholder="1-12"
            style="margin-top: 8px"
          />
        </div>

        <!-- 星期 -->
        <div class="field-group">
          <label class="field-label">星期</label>
          <el-select
            v-model="cronParts.weekday"
            @change="updateCronExpression"
            style="width: 100%"
          >
            <el-option label="每天" value="*" />
            <el-option label="工作日" value="1-5" />
            <el-option label="周末" value="0,6" />
            <el-option label="周一" value="1" />
            <el-option label="周二" value="2" />
            <el-option label="周三" value="3" />
            <el-option label="周四" value="4" />
            <el-option label="周五" value="5" />
            <el-option label="周六" value="6" />
            <el-option label="周日" value="0" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-input
            v-if="cronParts.weekday === 'custom'"
            v-model="customParts.weekday"
            @input="updateCronExpression"
            placeholder="0-6"
            style="margin-top: 8px"
          />
        </div>
      </div>
    </div>

    <!-- 文本编辑器 -->
    <div v-else class="text-editor">
      <el-input
        v-model="textExpression"
        @input="onTextInput"
        placeholder="请输入Cron表达式，格式：分 时 日 月 周"
        style="font-family: 'Consolas', 'Monaco', monospace"
      />
      <div class="cron-help">
        <span class="help-text">格式说明：分钟(0-59) 小时(0-23) 日(1-31) 月(1-12) 周(0-6)</span>
      </div>
    </div>

    <!-- 表达式预览 -->
    <div class="expression-preview">
      <div class="preview-header">
        <span class="preview-label">当前表达式:</span>
        <code class="expression-code">{{ currentExpression }}</code>
      </div>
      
      <div class="preview-description">
        <span class="description-label">执行说明:</span>
        <span :class="['description-text', validationResult.valid ? 'valid' : 'invalid']">
          {{ validationResult.description }}
        </span>
      </div>

      <!-- 下次执行时间预览 -->
      <div v-if="validationResult.valid && nextRuns.length > 0" class="next-runs">
        <span class="next-runs-label">接下来5次执行时间:</span>
        <ul class="next-runs-list">
          <li v-for="(time, index) in nextRuns" :key="index" class="next-run-item">
            {{ formatDateTime(time) }}
          </li>
        </ul>
      </div>

      <!-- 验证错误 -->
      <div v-if="!validationResult.valid" class="validation-error">
        <el-alert
          :title="validationResult.error"
          type="error"
          :closable="false"
          show-icon
        />
      </div>
    </div>

    <!-- 模板选择对话框 -->
    <el-dialog
      v-model="showTemplates"
      title="Cron表达式模板"
      width="600px"
    >
      <div class="templates-grid">
        <div
          v-for="template in cronTemplates"
          :key="template.name"
          class="template-item"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <span class="template-name">{{ template.name }}</span>
            <code class="template-expression">{{ template.expression }}</code>
          </div>
          <div class="template-description">{{ template.description }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Collection, Check } from '@element-plus/icons-vue'
import { api, schedulerApiUtils, SCHEDULER_CONSTANTS } from '@/api/client'

// Props & Emits
const props = defineProps({
  modelValue: {
    type: String,
    default: '0 0 * * *'
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

// 响应式数据
const editMode = ref('visual')
const showTemplates = ref(false)
const textExpression = ref('')
const cronTemplates = ref([])
const nextRuns = ref([])

// Cron部分
const cronParts = reactive({
  minute: '*',
  hour: '*',
  day: '*',
  month: '*',
  weekday: '*'
})

const customParts = reactive({
  minute: '',
  hour: '',
  day: '',
  month: '',
  weekday: ''
})

// 验证结果
const validationResult = reactive({
  valid: true,
  error: '',
  description: ''
})

// 计算属性
const currentExpression = computed(() => {
  if (editMode.value === 'text') {
    return textExpression.value
  } else {
    return buildCronExpression()
  }
})

// 方法
const buildCronExpression = () => {
  const parts = []
  
  // 分钟
  if (cronParts.minute === 'custom') {
    parts.push(customParts.minute || '*')
  } else {
    parts.push(cronParts.minute)
  }
  
  // 小时
  if (cronParts.hour === 'custom') {
    parts.push(customParts.hour || '*')
  } else {
    parts.push(cronParts.hour)
  }
  
  // 日
  if (cronParts.day === 'custom') {
    parts.push(customParts.day || '*')
  } else {
    parts.push(cronParts.day)
  }
  
  // 月
  if (cronParts.month === 'custom') {
    parts.push(customParts.month || '*')
  } else {
    parts.push(cronParts.month)
  }
  
  // 星期
  if (cronParts.weekday === 'custom') {
    parts.push(customParts.weekday || '*')
  } else {
    parts.push(cronParts.weekday)
  }
  
  return parts.join(' ')
}

const parseCronExpression = (expression) => {
  const parts = expression.split(' ')
  if (parts.length !== 5) return
  
  // 解析各部分
  cronParts.minute = parts[0] === '*' || parts[0].includes('/') ? parts[0] : 'custom'
  cronParts.hour = parts[1] === '*' || parts[1].includes('/') ? parts[1] : 'custom'
  cronParts.day = parts[2] === '*' || parts[2].includes('/') ? parts[2] : 'custom'
  cronParts.month = parts[3] === '*' || parts[3].includes('/') ? parts[3] : 'custom'
  cronParts.weekday = parts[4] === '*' || parts[4].includes('/') || ['1-5', '0,6'].includes(parts[4]) ? parts[4] : 'custom'
  
  // 设置自定义值
  if (cronParts.minute === 'custom') customParts.minute = parts[0]
  if (cronParts.hour === 'custom') customParts.hour = parts[1]
  if (cronParts.day === 'custom') customParts.day = parts[2]
  if (cronParts.month === 'custom') customParts.month = parts[3]
  if (cronParts.weekday === 'custom') customParts.weekday = parts[4]
}

const updateCronExpression = () => {
  const expression = buildCronExpression()
  emit('update:modelValue', expression)
  validateExpression()
}

const onTextInput = () => {
  emit('update:modelValue', textExpression.value)
  validateExpression()
}

const onEditModeChange = (mode) => {
  if (mode === 'text') {
    textExpression.value = currentExpression.value
  } else {
    parseCronExpression(textExpression.value)
  }
}

const validateExpression = async () => {
  const expression = currentExpression.value
  
  if (!expression) {
    validationResult.valid = false
    validationResult.error = 'Cron表达式不能为空'
    validationResult.description = '请输入有效的Cron表达式'
    emit('validate', false, validationResult.error)
    return
  }
  
  try {
    const response = await api.scheduler.validateCron(expression)
    const data = response.data
    
    validationResult.valid = data.valid
    validationResult.error = data.error_message || ''
    validationResult.description = data.description || ''
    nextRuns.value = data.next_runs || []
    
    emit('validate', data.valid, data.error_message)
    
    if (!data.valid) {
      ElMessage.error(`Cron表达式验证失败: ${data.error_message}`)
    }
  } catch (error) {
    validationResult.valid = false
    validationResult.error = '验证请求失败'
    validationResult.description = '无法验证Cron表达式'
    emit('validate', false, '验证请求失败')
    console.error('验证Cron表达式失败:', error)
  }
}

const loadCronTemplates = async () => {
  try {
    const response = await api.scheduler.getCronTemplates()
    cronTemplates.value = response.data.templates || []
  } catch (error) {
    console.error('获取Cron模板失败:', error)
    // 使用本地模板作为后备
    cronTemplates.value = [
      { name: '每分钟', expression: '* * * * *', description: '每分钟执行一次' },
      { name: '每5分钟', expression: '*/5 * * * *', description: '每5分钟执行一次' },
      { name: '每15分钟', expression: '*/15 * * * *', description: '每15分钟执行一次' },
      { name: '每30分钟', expression: '*/30 * * * *', description: '每30分钟执行一次' },
      { name: '每小时', expression: '0 * * * *', description: '每小时整点执行' },
      { name: '每6小时', expression: '0 */6 * * *', description: '每6小时执行一次' },
      { name: '每天午夜', expression: '0 0 * * *', description: '每天午夜12点执行' },
      { name: '每天上午9点', expression: '0 9 * * *', description: '每天上午9点执行' },
      { name: '工作日上午9点', expression: '0 9 * * 1-5', description: '周一到周五上午9点执行' },
      { name: '每周日午夜', expression: '0 0 * * 0', description: '每周日午夜执行' },
      { name: '每月1号午夜', expression: '0 0 1 * *', description: '每月1号午夜执行' }
    ]
  }
}

const selectTemplate = (template) => {
  if (editMode.value === 'text') {
    textExpression.value = template.expression
    onTextInput()
  } else {
    parseCronExpression(template.expression)
    updateCronExpression()
  }
  showTemplates.value = false
  ElMessage.success(`已应用模板: ${template.name}`)
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 监听器
watch(() => props.modelValue, (newValue) => {
  if (editMode.value === 'text') {
    textExpression.value = newValue
  } else {
    parseCronExpression(newValue)
  }
  validateExpression()
}, { immediate: true })

// 生命周期
onMounted(() => {
  loadCronTemplates()
  validateExpression()
})
</script>

<style scoped>
.cron-editor {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 16px;
  background: var(--background-base);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.visual-editor {
  margin-bottom: 16px;
}

.cron-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.text-editor {
  margin-bottom: 16px;
}

.cron-help {
  margin-top: 8px;
}

.help-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.expression-preview {
  border-top: 1px solid var(--border-extra-light);
  padding-top: 16px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.preview-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.expression-code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  background: var(--background-light);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-light);
}

.preview-description {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.description-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.description-text {
  font-size: 14px;
}

.description-text.valid {
  color: var(--success-color);
}

.description-text.invalid {
  color: var(--danger-color);
}

.next-runs {
  margin-top: 12px;
}

.next-runs-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  display: block;
  margin-bottom: 8px;
}

.next-runs-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.next-run-item {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 2px 0;
  font-family: 'Consolas', 'Monaco', monospace;
}

.validation-error {
  margin-top: 12px;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.template-item {
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: var(--primary-color);
  background: var(--primary-color-light);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 500;
  color: var(--text-primary);
}

.template-expression {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  background: var(--background-light);
  padding: 2px 6px;
  border-radius: 3px;
  color: var(--text-secondary);
}

.template-description {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
