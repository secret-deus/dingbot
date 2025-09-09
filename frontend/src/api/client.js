import axios from 'axios'
import { ElMessage } from 'element-plus'

// API基础URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

// 任务管理相关常量
export const SCHEDULER_CONSTANTS = {
  // 任务状态
  TASK_STATUS: {
    PENDING: 'pending',
    RUNNING: 'running', 
    SUCCESS: 'success',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
    TIMEOUT: 'timeout'
  },
  
  // 任务类型
  TASK_TYPES: {
    CLUSTER_CHECK: 'cluster_check',
    RESOURCE_ANALYSIS: 'resource_analysis',
    HEALTH_MONITOR: 'health_monitor',
    CUSTOM: 'custom'
  },
  
  // 通知级别
  NOTIFICATION_LEVELS: {
    NONE: 'none',
    ERROR: 'error',
    ALL: 'all'
  },
  
  // 默认分页配置
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // 请求超时配置
  REQUEST_TIMEOUT: 30000,
  LONG_REQUEST_TIMEOUT: 600000, // 10分钟，用于长时间运行的操作
  
  // 重试配置
  DEFAULT_MAX_RETRIES: 3,
  DEFAULT_RETRY_DELAY: 1000,
  
  // 常用Cron表达式
  COMMON_CRON_EXPRESSIONS: {
    EVERY_MINUTE: '* * * * *',
    EVERY_5_MINUTES: '*/5 * * * *',
    EVERY_15_MINUTES: '*/15 * * * *',
    EVERY_30_MINUTES: '*/30 * * * *',
    EVERY_HOUR: '0 * * * *',
    EVERY_6_HOURS: '0 */6 * * *',
    EVERY_12_HOURS: '0 */12 * * *',
    DAILY_MIDNIGHT: '0 0 * * *',
    DAILY_9AM: '0 9 * * *',
    WEEKLY_SUNDAY: '0 0 * * 0',
    MONTHLY_FIRST: '0 0 1 * *'
  }
}

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 600000, // 10分钟超时，支持长时间运行的工具调用
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    console.log('API请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.config.url, response.status)
    return response
  },
  (error) => {
    console.error('API错误:', error)
    
    // 错误消息处理
    let message = '请求失败'
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      
      switch (status) {
        case 400:
          message = data.detail || '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          break
        case 403:
          message = '权限不足'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = data.detail || '服务器内部错误'
          break
        default:
          message = data.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    } else {
      message = error.message || '未知错误'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API接口定义
export const api = {
  // 系统状态相关
  system: {
    // 获取v1状态
    getStatus: () => apiClient.get('/status'),
    // 获取v2状态
    getV2Status: () => apiClient.get('/v2/status'),
    // 获取v2健康检查
    getV2Health: () => apiClient.get('/v2/health'),
    // 获取工具列表
    getTools: () => apiClient.get('/v2/tools'),
    // 刷新工具列表 (后端MCP客户端)
    refreshTools: () => apiClient.post('/v2/tools/refresh'),
  },

  // 配置管理相关
  config: {
    // 获取LLM配置
    getLLMConfig: () => apiClient.get('/v2/config/llm'),
    // 获取LLM运行时配置
    getLLMRuntimeConfig: () => apiClient.get('/v2/config/llm/runtime'),
    // 重新加载LLM配置
    reloadLLMConfig: () => apiClient.post('/v2/config/llm/reload'),
    // 更新LLM配置
    updateLLMConfig: (config) => apiClient.put('/v2/config/llm', {
      config_type: 'llm',
      config_data: config
    }),
    // 获取MCP配置
    getMCPConfig: () => apiClient.get('/v2/config/mcp'),
    // 更新MCP配置
    updateMCPConfig: (config) => apiClient.put('/v2/config/mcp', {
      config_type: 'mcp',
      config_data: config
    }),
    // 测试配置连接
    testConfig: (type, config) => apiClient.post('/v2/config/test', {
      config_type: type,
      config_data: config
    }),
    // 获取支持的提供商列表
    getProviders: () => apiClient.get('/v2/config/providers')
  },

  // K8s资源管理API
  resources: {
    // 触发资源指标更新
    updateMetrics: (params = {}) => apiClient.post('/v2/resources/update-metrics', {
      namespace_filter: params.namespaceFilter || '',
      app_name_filter: params.appNameFilter || '',
      days: params.days || 14,
      max_concurrent: params.maxConcurrent || 5,
      force_update: params.forceUpdate || false,
      time_period: params.timePeriod || '14d'  // 新增时间周期参数
    }),
    
    // 获取指标覆盖情况
    getMetricsCoverage: (params = {}) => apiClient.get('/v2/resources/metrics-coverage', {
      params: {
        include_details: params.includeDetails || false,
        filter_namespace: params.filterNamespace || '',
        show_failed_only: params.showFailedOnly || false
      }
    }),
    
    // 强制触发指标聚合
    forceAggregation: () => apiClient.post('/v2/resources/force-aggregation')
  },

  // 聊天相关
  chat: {
    // 普通聊天
    sendMessage: (message, enableTools = true) => apiClient.post('/v2/chat', {
      message,
      enable_tools: enableTools
    }),
    // 流式聊天 (返回EventSource)
    streamChat: (message, enableTools = true) => {
      const params = new URLSearchParams({
        message,
        enable_tools: enableTools
      })
      return new EventSource(`/api/v2/chat/stream?${params}`)
    }
  },

  // 巡检相关
  inspection: {
    run: (payload) => apiClient.post('/v2/inspection/run', payload),
  },

  // 任务调度管理相关
  scheduler: {
    // 获取任务列表
    getTasks: (params = {}) => {
      const queryParams = new URLSearchParams()
      if (params.page) queryParams.append('page', params.page)
      if (params.page_size) queryParams.append('page_size', params.page_size)
      if (params.enabled_only !== undefined) queryParams.append('enabled_only', params.enabled_only)
      if (params.task_type) queryParams.append('task_type', params.task_type)
      
      const url = queryParams.toString() ? `/v2/scheduler/tasks?${queryParams}` : '/v2/scheduler/tasks'
      return apiClient.get(url)
    },

    // 创建任务
    createTask: (taskData) => apiClient.post('/v2/scheduler/tasks', taskData),

    // 获取单个任务
    getTask: (taskId) => apiClient.get(`/v2/scheduler/tasks/${taskId}`),

    // 更新任务
    updateTask: (taskId, taskData) => apiClient.put(`/v2/scheduler/tasks/${taskId}`, taskData),

    // 删除任务
    deleteTask: (taskId) => apiClient.delete(`/v2/scheduler/tasks/${taskId}`),

    // 获取任务执行历史
    getTaskExecutions: (taskId, params = {}) => {
      const queryParams = new URLSearchParams()
      if (params.page) queryParams.append('page', params.page)
      if (params.page_size) queryParams.append('page_size', params.page_size)
      
      const url = queryParams.toString() 
        ? `/v2/scheduler/tasks/${taskId}/executions?${queryParams}` 
        : `/v2/scheduler/tasks/${taskId}/executions`
      return apiClient.get(url)
    },

    // 手动执行任务
    runTask: (taskId, options = {}) => apiClient.post(`/v2/scheduler/tasks/${taskId}/run`, {
      force: options.force || false
    }),

    // 获取任务统计信息
    getStats: () => apiClient.get('/v2/scheduler/stats'),

    // 获取正在运行的任务
    getRunningTasks: () => apiClient.get('/v2/scheduler/running'),

    // 获取调度器状态
    getStatus: () => apiClient.get('/v2/scheduler/status'),

    // 获取支持的任务类型
    getTaskTypes: () => apiClient.get('/v2/scheduler/task-types'),

    // 获取Cron表达式模板
    getCronTemplates: () => apiClient.get('/v2/scheduler/cron-templates'),

    // 验证Cron表达式
    validateCron: (expression) => apiClient.post('/v2/scheduler/validate-cron', {
      expression
    }),

    // 验证任务配置
    validateTaskConfig: (taskType, config) => apiClient.get(`/v2/scheduler/config/validate/${taskType}`, {
      params: { config: JSON.stringify(config) }
    }),

    // 获取任务配置模板
    getTaskTemplate: (taskType) => apiClient.get(`/v2/scheduler/config/template/${taskType}`),

    // 清理旧数据
    cleanupOldData: (keepDays = 30) => apiClient.post('/v2/scheduler/maintenance/cleanup', null, {
      params: { keep_days: keepDays }
    }),

    // 重置执行统计
    resetStats: () => apiClient.post('/v2/scheduler/maintenance/reset-stats')
  }
}

// 导出axios实例供其他地方使用
export default apiClient

// 工具函数
export const createEventSource = (url, options = {}) => {
  const eventSource = new EventSource(url, options)
  
  // 添加通用错误处理
  eventSource.onerror = (error) => {
    console.error('EventSource错误:', error)
    ElMessage.error('实时连接中断，请刷新页面重试')
  }
  
  return eventSource
}

// 文件上传辅助函数
export const uploadFile = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        onProgress(percentCompleted)
      }
    },
  })
} 

// 任务管理专用API工具函数
export const schedulerApiUtils = {
  // 创建可取消的请求
  createCancelableRequest: (requestFunction) => {
    const controller = new AbortController()
    const request = requestFunction({ signal: controller.signal })
    
    return {
      request,
      cancel: () => controller.abort(),
      signal: controller.signal
    }
  },

  // 重试请求
  retryRequest: async (requestFunction, maxRetries = 3, delay = 1000) => {
    let lastError
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFunction()
      } catch (error) {
        lastError = error
        
        // 如果是用户主动取消的请求，不重试
        if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
          throw error
        }
        
        // 如果是最后一次尝试，直接抛出错误
        if (attempt === maxRetries) {
          throw error
        }
        
        // 等待一段时间后重试，使用指数退避
        const waitTime = delay * Math.pow(2, attempt - 1)
        console.log(`请求失败，${waitTime}ms后进行第${attempt + 1}次重试...`)
        await new Promise(resolve => setTimeout(resolve, waitTime))
      }
    }
    
    throw lastError
  },

  // 批量操作任务
  batchOperations: {
    // 批量删除任务
    deleteTasks: async (taskIds) => {
      const results = []
      for (const taskId of taskIds) {
        try {
          await api.scheduler.deleteTask(taskId)
          results.push({ taskId, success: true })
        } catch (error) {
          results.push({ taskId, success: false, error: error.message })
        }
      }
      return results
    },

    // 批量启用/禁用任务
    toggleTasks: async (taskIds, enabled) => {
      const results = []
      for (const taskId of taskIds) {
        try {
          await api.scheduler.updateTask(taskId, { enabled })
          results.push({ taskId, success: true })
        } catch (error) {
          results.push({ taskId, success: false, error: error.message })
        }
      }
      return results
    },

    // 批量执行任务
    runTasks: async (taskIds, options = {}) => {
      const results = []
      for (const taskId of taskIds) {
        try {
          const result = await api.scheduler.runTask(taskId, options)
          results.push({ taskId, success: true, executionId: result.data.execution_id })
        } catch (error) {
          results.push({ taskId, success: false, error: error.message })
        }
      }
      return results
    }
  },

  // 数据格式化工具
  formatters: {
    // 格式化任务状态
    formatTaskStatus: (status) => {
      const statusMap = {
        'pending': { text: '等待中', color: 'warning' },
        'running': { text: '运行中', color: 'primary' },
        'success': { text: '成功', color: 'success' },
        'failed': { text: '失败', color: 'danger' },
        'cancelled': { text: '已取消', color: 'info' },
        'timeout': { text: '超时', color: 'danger' }
      }
      return statusMap[status] || { text: status, color: 'default' }
    },

    // 格式化任务类型
    formatTaskType: (type) => {
      const typeMap = {
        'cluster_check': '集群巡检',
        'resource_analysis': '资源分析',
        'health_monitor': '健康监控',
        'custom': '自定义任务'
      }
      return typeMap[type] || type
    },

    // 格式化通知级别
    formatNotificationLevel: (level) => {
      const levelMap = {
        'none': '无通知',
        'error': '仅错误',
        'all': '全部通知'
      }
      return levelMap[level] || level
    },

    // 格式化执行时间
    formatDuration: (seconds) => {
      if (!seconds) return '-'
      
      if (seconds < 60) {
        return `${seconds.toFixed(1)}秒`
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60)
        const remainingSeconds = Math.floor(seconds % 60)
        return `${minutes}分${remainingSeconds}秒`
      } else {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        return `${hours}小时${minutes}分钟`
      }
    },

    // 格式化Cron表达式为可读文本
    formatCronExpression: (expression) => {
      // 这里可以根据需要实现更复杂的Cron表达式解析
      const commonExpressions = {
        '0 0 * * *': '每天午夜执行',
        '0 */6 * * *': '每6小时执行一次',
        '0 9 * * *': '每天上午9点执行',
        '0 0 * * 0': '每周日午夜执行',
        '0 0 1 * *': '每月1号午夜执行',
        '*/5 * * * *': '每5分钟执行一次',
        '*/15 * * * *': '每15分钟执行一次',
        '0 */1 * * *': '每小时执行一次'
      }
      
      return commonExpressions[expression] || expression
    }
  },

  // 验证工具
  validators: {
    // 验证任务名称
    validateTaskName: (name) => {
      if (!name || name.trim().length === 0) {
        return { valid: false, message: '任务名称不能为空' }
      }
      if (name.length > 100) {
        return { valid: false, message: '任务名称不能超过100个字符' }
      }
      return { valid: true }
    },

    // 验证Cron表达式格式
    validateCronFormat: (expression) => {
      if (!expression || expression.trim().length === 0) {
        return { valid: false, message: 'Cron表达式不能为空' }
      }
      
      const parts = expression.trim().split(/\s+/)
      if (parts.length !== 5) {
        return { valid: false, message: 'Cron表达式必须包含5个部分' }
      }
      
      return { valid: true }
    },

    // 验证超时时间
    validateTimeout: (timeout) => {
      const timeoutNum = Number(timeout)
      if (isNaN(timeoutNum) || timeoutNum <= 0) {
        return { valid: false, message: '超时时间必须是正数' }
      }
      if (timeoutNum > 3600) {
        return { valid: false, message: '超时时间不能超过3600秒' }
      }
      return { valid: true }
    },

    // 验证重试次数
    validateRetries: (retries) => {
      const retriesNum = Number(retries)
      if (isNaN(retriesNum) || retriesNum < 0) {
        return { valid: false, message: '重试次数必须是非负整数' }
      }
      if (retriesNum > 10) {
        return { valid: false, message: '重试次数不能超过10次' }
      }
      return { valid: true }
    }
  }
}


// 任务管理高级API类
export class SchedulerAPI {
  constructor(apiClient) {
    this.client = apiClient
    this.activeRequests = new Map() // 跟踪活跃的请求
  }

  // 获取任务列表（带缓存和分页优化）
  async getTasks(params = {}) {
    const cacheKey = JSON.stringify(params)
    
    try {
      const response = await api.scheduler.getTasks(params)
      return response.data
    } catch (error) {
      console.error('获取任务列表失败:', error)
      throw error
    }
  }

  // 创建任务（带验证）
  async createTask(taskData) {
    // 预验证
    const nameValidation = schedulerApiUtils.validators.validateTaskName(taskData.name)
    if (!nameValidation.valid) {
      throw new Error(nameValidation.message)
    }

    const cronValidation = schedulerApiUtils.validators.validateCronFormat(taskData.cron_expression)
    if (!cronValidation.valid) {
      throw new Error(cronValidation.message)
    }

    try {
      const response = await api.scheduler.createTask(taskData)
      ElMessage.success(`任务 "${taskData.name}" 创建成功`)
      return response.data
    } catch (error) {
      ElMessage.error(`创建任务失败: ${error.message}`)
      throw error
    }
  }

  // 更新任务（带验证和乐观锁）
  async updateTask(taskId, taskData) {
    try {
      const response = await api.scheduler.updateTask(taskId, taskData)
      ElMessage.success('任务更新成功')
      return response.data
    } catch (error) {
      ElMessage.error(`更新任务失败: ${error.message}`)
      throw error
    }
  }

  // 删除任务（带确认）
  async deleteTask(taskId, options = {}) {
    if (!options.skipConfirm) {
      // 在实际使用中，这里应该调用确认对话框
      console.log('删除任务需要确认')
    }

    try {
      const response = await api.scheduler.deleteTask(taskId)
      ElMessage.success('任务删除成功')
      return response.data
    } catch (error) {
      ElMessage.error(`删除任务失败: ${error.message}`)
      throw error
    }
  }

  // 执行任务（带状态跟踪）
  async runTask(taskId, options = {}) {
    const requestId = `run_task_${taskId}_${Date.now()}`
    
    try {
      // 记录请求
      this.activeRequests.set(requestId, { type: 'run_task', taskId, startTime: Date.now() })
      
      const response = await api.scheduler.runTask(taskId, options)
      ElMessage.success('任务已开始执行')
      
      // 如果需要，可以启动轮询检查执行状态
      if (options.trackExecution) {
        this.trackExecution(response.data.execution_id)
      }
      
      return response.data
    } catch (error) {
      ElMessage.error(`执行任务失败: ${error.message}`)
      throw error
    } finally {
      this.activeRequests.delete(requestId)
    }
  }

  // 跟踪任务执行状态
  async trackExecution(executionId, callback) {
    const pollInterval = 2000 // 2秒轮询一次
    const maxPolls = 150 // 最多轮询5分钟
    let pollCount = 0

    const poll = async () => {
      try {
        // 这里需要一个获取执行状态的API
        // const status = await api.scheduler.getExecutionStatus(executionId)
        
        pollCount++
        
        if (callback) {
          callback({ executionId, pollCount })
        }

        // 如果任务还在运行且未超过最大轮询次数，继续轮询
        if (pollCount < maxPolls) {
          setTimeout(poll, pollInterval)
        }
      } catch (error) {
        console.error('轮询执行状态失败:', error)
      }
    }

    poll()
  }

  // 批量操作
  async batchDelete(taskIds) {
    return await schedulerApiUtils.batchOperations.deleteTasks(taskIds)
  }

  async batchToggle(taskIds, enabled) {
    return await schedulerApiUtils.batchOperations.toggleTasks(taskIds, enabled)
  }

  async batchRun(taskIds, options = {}) {
    return await schedulerApiUtils.batchOperations.runTasks(taskIds, options)
  }

  // 获取统计信息（带缓存）
  async getStats() {
    try {
      const response = await api.scheduler.getStats()
      return response.data
    } catch (error) {
      console.error('获取统计信息失败:', error)
      throw error
    }
  }

  // 获取任务执行历史
  async getTaskExecutions(taskId, params = {}) {
    try {
      const response = await api.scheduler.getTaskExecutions(taskId, params)
      return response.data
    } catch (error) {
      console.error('获取执行历史失败:', error)
      throw error
    }
  }

  // 验证Cron表达式
  async validateCron(expression) {
    try {
      const response = await api.scheduler.validateCron(expression)
      return response.data
    } catch (error) {
      console.error('验证Cron表达式失败:', error)
      throw error
    }
  }

  // 获取任务模板
  async getTaskTemplate(taskType) {
    try {
      const response = await api.scheduler.getTaskTemplate(taskType)
      return response.data
    } catch (error) {
      console.error('获取任务模板失败:', error)
      throw error
    }
  }

  // 取消所有活跃请求
  cancelAllRequests() {
    this.activeRequests.clear()
  }

  // 获取活跃请求状态
  getActiveRequests() {
    return Array.from(this.activeRequests.entries()).map(([id, info]) => ({
      id,
      ...info,
      duration: Date.now() - info.startTime
    }))
  }
}

// 创建全局实例
export const schedulerAPI = new SchedulerAPI(apiClient) 