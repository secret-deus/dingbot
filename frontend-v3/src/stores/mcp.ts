import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MCPTool } from '@/types'
import { toolApi } from '@/api/client'

export const useMcpStore = defineStore('mcp', () => {
  const tools = ref<MCPTool[]>([])
  const loading = ref(false)

  async function fetchTools() {
    loading.value = true
    try {
      const res = await toolApi.list()
      tools.value = res.tools
    } finally {
      loading.value = false
    }
  }

  return { tools, loading, fetchTools }
})
