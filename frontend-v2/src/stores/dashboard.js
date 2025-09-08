import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import apiClient from '@/api/client'

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态数据
  const loading = ref(false)
  const lastUpdateTime = ref(new Date())
  
  // 系统状态
  const systemStatus = reactive({
    healthy: false,
    mcp_client: false,
    llm_processor: false,
    dingtalk_bot: false
  })
  
  // 工具统计
  const toolsStats = reactive({
    total: 0,
    k8s: 0,
    ssh: 0,
    enabled: 0
  })
  
  // 集群统计
  const clusterStats = reactive({
    nodes: 0,
    pods: 0,
    services: 0,
    deployments: 0,
    cpuUsage: 0,
    memoryUsage: 0,
    storageUsage: 0
  })
  
  // 活动统计
  const activityStats = reactive({
    today: 0,
    week: 0,
    month: 0,
    totalOperations: 0
  })
  
  // 系统日志
  const systemLogs = ref([])
  
  // 方法
  const fetchSystemStatus = async () => {
    try {
      const response = await apiClient.system.getV2Health()
      const data = response.data
      
      Object.assign(systemStatus, {
        healthy: data.healthy || false,
        mcp_client: data.components?.mcp_client || false,
        llm_processor: data.components?.llm_processor || false,
        dingtalk_bot: data.components?.dingtalk_bot || false
      })
      
      return data
    } catch (error) {
      console.error('获取系统状态失败:', error)
      // 设置默认值
      Object.assign(systemStatus, {
        healthy: false,
        mcp_client: false,
        llm_processor: false,
        dingtalk_bot: false
      })
      throw error
    }
  }
  
  const fetchToolsStats = async () => {
    try {
      const response = await apiClient.system.getTools()
      const data = response.data
      
      const tools = data.tools || []
      const k8sTools = tools.filter(tool => tool.category === 'kubernetes' || tool.name.includes('k8s'))
      const sshTools = tools.filter(tool => tool.category === 'ssh' || tool.name.includes('ssh'))
      
      Object.assign(toolsStats, {
        total: tools.length,
        k8s: k8sTools.length,
        ssh: sshTools.length,
        enabled: tools.filter(tool => tool.enabled !== false).length
      })
      
      return data
    } catch (error) {
      console.error('获取工具统计失败:', error)
      Object.assign(toolsStats, {
        total: 0,
        k8s: 0,
        ssh: 0,
        enabled: 0
      })
      throw error
    }
  }
  
  const fetchClusterStats = async () => {
    try {
      // 尝试获取真实的集群数据
      const response = await apiClient.monitoring.getClusterStatus()
      const data = response.data
      
      Object.assign(clusterStats, {
        nodes: data.nodes || 0,
        pods: data.pods || 0,
        services: data.services || 0,
        deployments: data.deployments || 0,
        cpuUsage: data.cpu_usage || 0,
        memoryUsage: data.memory_usage || 0,
        storageUsage: data.storage_usage || 0
      })
      
      return data
    } catch (error) {
      console.error('获取集群统计失败，尝试使用工具API:', error)
      
      try {
        // 如果监控API失败，尝试使用MCP工具获取数据
        const toolsResponse = await apiClient.system.getTools()
        const tools = toolsResponse.data.tools || []
        
        // 通过工具调用获取集群信息
        // 这里可以调用k8s-get-nodes, k8s-get-pods等工具
        
        // 暂时设置基础数据，避免显示随机数据
        Object.assign(clusterStats, {
          nodes: 0,
          pods: 0,
          services: 0,
          deployments: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          storageUsage: 0
        })
        
        return { message: '集群数据获取中...' }
      } catch (toolError) {
        console.error('工具API也失败:', toolError)
        // 设置默认值而不是随机数据
        Object.assign(clusterStats, {
          nodes: 0,
          pods: 0,
          services: 0,
          deployments: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          storageUsage: 0
        })
        throw toolError
      }
    }
  }
  
  const fetchActivityStats = async () => {
    try {
      // 这里可以调用实际的API获取活动统计
      // const response = await apiClient.monitoring.getActivityStats()
      
      // 模拟数据
      Object.assign(activityStats, {
        today: Math.floor(Math.random() * 200) + 100,
        week: Math.floor(Math.random() * 1000) + 500,
        month: Math.floor(Math.random() * 5000) + 2000,
        totalOperations: Math.floor(Math.random() * 50000) + 10000
      })
    } catch (error) {
      console.error('获取活动统计失败:', error)
    }
  }
  
  const addLog = (level, message) => {
    const log = {
      id: Date.now(),
      time: new Date(),
      level,
      message
    }
    
    systemLogs.value.unshift(log)
    
    // 保持最多50条日志
    if (systemLogs.value.length > 50) {
      systemLogs.value = systemLogs.value.slice(0, 50)
    }
  }
  
  const clearLogs = () => {
    systemLogs.value = []
  }
  
  const refreshAllData = async () => {
    loading.value = true
    
    try {
      await Promise.allSettled([
        fetchSystemStatus(),
        fetchToolsStats(),
        fetchClusterStats(),
        fetchActivityStats()
      ])
      
      lastUpdateTime.value = new Date()
      addLog('success', '数据刷新成功')
      
      return true
    } catch (error) {
      addLog('error', '数据刷新失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  const runInspection = async (options = {}) => {
    try {
      const response = await apiClient.inspection.run(options)
      const data = response.data
      
      addLog('success', '系统巡检完成')
      
      return data
    } catch (error) {
      addLog('error', '系统巡检失败')
      throw error
    }
  }
  
  // 计算属性
  const systemHealthScore = () => {
    const components = [
      systemStatus.mcp_client,
      systemStatus.llm_processor,
      systemStatus.dingtalk_bot
    ]
    
    const healthyCount = components.filter(Boolean).length
    return Math.round((healthyCount / components.length) * 100)
  }
  
  const systemHealthStatus = () => {
    const score = systemHealthScore()
    
    if (score >= 90) return { status: 'online', text: '运行正常' }
    if (score >= 70) return { status: 'warning', text: '部分异常' }
    return { status: 'offline', text: '系统异常' }
  }
  
  return {
    // 状态
    loading,
    lastUpdateTime,
    systemStatus,
    toolsStats,
    clusterStats,
    activityStats,
    systemLogs,
    
    // 方法
    fetchSystemStatus,
    fetchToolsStats,
    fetchClusterStats,
    fetchActivityStats,
    addLog,
    clearLogs,
    refreshAllData,
    runInspection,
    
    // 计算属性
    systemHealthScore,
    systemHealthStatus
  }
})
