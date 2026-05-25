import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { AliyunMCPConfig, ECSMCPConfig, HealthStatus, K8sMCPConfig, MCPConfig, MCPServerHealth, MCPTool } from '@/types'
import { systemApi, toolApi } from '@/api/client'

export const useMcpStore = defineStore('mcp', () => {
  const tools = ref<MCPTool[]>([])
  const health = ref<HealthStatus | null>(null)
  const mcpConfig = ref<MCPConfig | null>(null)
  const loading = ref(false)
  const healthLoading = ref(false)
  const configLoading = ref(false)
  const configSaving = ref(false)

  const toolsearchHealth = computed<MCPServerHealth | null>(() => health.value?.mcp_servers?.toolsearch || null)

  async function fetchTools() {
    loading.value = true
    try {
      const res = await toolApi.list()
      tools.value = res.tools
    } finally {
      loading.value = false
    }
  }

  async function fetchHealth() {
    healthLoading.value = true
    try {
      health.value = await systemApi.health()
    } finally {
      healthLoading.value = false
    }
  }

  async function fetchConfig() {
    configLoading.value = true
    try {
      mcpConfig.value = await systemApi.mcpConfig()
    } finally {
      configLoading.value = false
    }
  }

  async function saveConfig(data: {
    k8s?: Partial<Pick<K8sMCPConfig, 'enabled' | 'kubeconfig_path' | 'namespace' | 'in_cluster'>>
    ecs?: Partial<Pick<ECSMCPConfig, 'enabled' | 'region_id'>> & { access_key_id?: string; access_key_secret?: string }
    aliyun?: Partial<Pick<AliyunMCPConfig, 'enabled' | 'default_region_id' | 'allowed_regions' | 'required_tags' | 'allowed_instance_ids'>> & {
      access_key_id?: string
      access_key_secret?: string
      sls?: { mappings?: Array<Record<string, unknown>> }
    }
  }) {
    configSaving.value = true
    try {
      mcpConfig.value = await systemApi.updateMcpConfig(data)
      await Promise.all([fetchTools(), fetchHealth()])
    } finally {
      configSaving.value = false
    }
  }

  async function refresh() {
    await Promise.all([fetchTools(), fetchHealth(), fetchConfig()])
  }

  return {
    tools,
    health,
    mcpConfig,
    toolsearchHealth,
    loading,
    healthLoading,
    configLoading,
    configSaving,
    fetchTools,
    fetchHealth,
    fetchConfig,
    saveConfig,
    refresh,
  }
})
