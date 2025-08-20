import axios from 'axios'
import { ElMessage } from 'element-plus'

// API基础URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
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
    // 获取支持的提供商
    getProviders: () => apiClient.get('/v2/config/providers'),
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

// 多供应商LLM配置API
export const llmProvidersApi = {
  // 获取多供应商配置
  async getProvidersConfig() {
    const response = await fetch(`${API_BASE}/config/llm/providers`);
    return await response.json();
  },

  // 保存多供应商配置
  async saveProvidersConfig(config) {
    const response = await fetch(`${API_BASE}/config/llm/providers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config)
    });
    return await response.json();
  },

  // 获取供应商模板
  async getProviderTemplates() {
    const response = await fetch(`${API_BASE}/config/llm/providers/templates`);
    return await response.json();
  },

  // 获取可用供应商列表
  async getAvailableProviders() {
    const response = await fetch(`${API_BASE}/llm/providers/available`);
    return await response.json();
  },

  // 切换供应商
  async switchProvider(providerId) {
    const response = await fetch(`${API_BASE}/llm/providers/switch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ provider_id: providerId })
    });
    return await response.json();
  },

  // 获取供应商统计
  async getProviderStats() {
    const response = await fetch(`${API_BASE}/llm/providers/stats`);
    return await response.json();
  }
}; 