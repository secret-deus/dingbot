import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// API接口定义
export const apiClient = {
  // 系统相关
  system: {
    // 健康检查
    getHealth: () => api.get('/health'),
    
    // V2健康检查
    getV2Health: () => api.get('/health'),
    
    // 系统状态
    getStatus: () => api.get('/status'),
    
    // 工具列表
    getTools: () => api.get('/tools'),
    
    // 刷新工具
    refreshTools: () => api.post('/tools/refresh')
  },
  
  // 聊天相关
  chat: {
    // 发送消息
    sendMessage: (message) => api.post('/chat/stream', { message }),
    
    // 流式聊天 (SSE)
    streamChat: (message, options = {}) => {
      return new Promise((resolve, reject) => {
        const eventSource = new EventSource(`/api/v2/chat/stream?message=${encodeURIComponent(message)}`)
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (options.onMessage) {
              options.onMessage(data)
            }
          } catch (error) {
            console.error('解析SSE数据失败:', error)
          }
        }
        
        eventSource.onerror = (error) => {
          eventSource.close()
          if (options.onError) {
            options.onError(error)
          }
          reject(error)
        }
        
        eventSource.addEventListener('end', () => {
          eventSource.close()
          resolve()
        })
      })
    }
  },
  
  // MCP相关
  mcp: {
    // 获取配置
    getConfig: () => api.get('/mcp/config'),
    
    // 更新配置
    updateConfig: (config) => api.post('/mcp/config', config),
    
    // 测试连接
    testConnection: (serverName) => api.post(`/mcp/test/${serverName}`)
  },
  
  // LLM相关
  llm: {
    // 获取配置
    getConfig: () => api.get('/llm/config'),
    
    // 更新配置
    updateConfig: (config) => api.post('/llm/config', config),
    
    // 获取提供商列表
    getProviders: () => api.get('/llm/providers')
  },
  
  // 监控相关
  monitoring: {
    // 获取集群状态
    getClusterStatus: () => api.get('/monitoring/cluster'),
    
    // 获取资源使用情况
    getResourceUsage: () => api.get('/monitoring/resources'),
    
    // 获取监控指标
    getMetrics: (timeRange = '1h') => api.get(`/monitoring/metrics?range=${timeRange}`)
  },
  
  // 巡检相关
  inspection: {
    // 运行巡检
    run: (options = {}) => api.post('/inspection/run', options),
    
    // 获取巡检历史
    getHistory: () => api.get('/inspection/history'),
    
    // 获取巡检报告
    getReport: (id) => api.get(`/inspection/report/${id}`)
  }
}

export default apiClient
