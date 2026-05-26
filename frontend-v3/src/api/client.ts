import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'

const client: AxiosInstance = axios.create({
  baseURL: '/api/v2',
  timeout: 600_000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = `${import.meta.env.BASE_URL}login`
    }
    return Promise.reject(err)
  },
)

async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const res = await client.request<T>(config)
  return res.data
}

// --- Auth ---
export const authApi = {
  login: (username: string, password: string) =>
    request<{ access_token: string; username: string; role: string }>({
      method: 'post', url: '/auth/login', data: { username, password },
    }),
  me: () => request<{ username: string; role: string }>({ method: 'get', url: '/auth/me' }),
}

export const userApi = {
  list: (limit = 100, offset = 0) =>
    request<User[]>({ method: 'get', url: '/auth/users', params: { limit, offset } }),
  create: (data: { username: string; password: string; display_name?: string; role: User['role'] }) =>
    request<{ id: string; username: string; role: string }>({ method: 'post', url: '/auth/register', data }),
  update: (username: string, data: Partial<Pick<User, 'display_name' | 'role' | 'is_active'>>) =>
    request<User>({ method: 'patch', url: `/auth/users/${username}`, data }),
}

// --- Sessions ---
export const sessionApi = {
  list: (limit = 50, offset = 0) =>
    request<Session[]>({ method: 'get', url: '/chat/sessions', params: { limit, offset } }),
  create: (title = '新对话', skill_id?: string) =>
    request<{ id: string; title: string }>({ method: 'post', url: '/chat/sessions', data: { title, skill_id } }),
  delete: (id: string) => request<void>({ method: 'delete', url: `/chat/sessions/${id}` }),
  messages: (id: string) =>
    request<Message[]>({ method: 'get', url: `/chat/sessions/${id}/messages` }),
}

// --- Chat ---
export const chatApi = {
  streamUrl: (sessionId: string) => `/api/v2/chat/sessions/${sessionId}/stream`,
  confirmToolCall: (messageId: string, toolCallId: string) =>
    request<{ result: unknown }>({
      method: 'post',
      url: `/chat/messages/${messageId}/tool-calls/${toolCallId}/confirm`,
    }),
}

// --- Tools ---
export const toolApi = {
  list: () => request<{ tools: MCPTool[] }>({ method: 'get', url: '/config/tools' }),
}

// --- Scheduler ---
export const schedulerApi = {
  list: (limit = 50, offset = 0) =>
    request<ScheduledTask[]>({ method: 'get', url: '/scheduler/tasks', params: { limit, offset } }),
  create: (data: { name: string; cron_expr: string; prompt: string; skill_id?: string; notify_dingtalk?: boolean }) =>
    request<{ id: string }>({ method: 'post', url: '/scheduler/tasks', data }),
  update: (id: string, data: Partial<ScheduledTask>) =>
    request<{ id: string }>({ method: 'patch', url: `/scheduler/tasks/${id}`, data }),
  delete: (id: string) => request<void>({ method: 'delete', url: `/scheduler/tasks/${id}` }),
  run: (id: string) =>
    request<{ execution_id: string; status: string; result?: string; error?: string }>({
      method: 'post', url: `/scheduler/tasks/${id}/run`,
    }),
  executions: (id: string, limit = 20) =>
    request<TaskExecution[]>({ method: 'get', url: `/scheduler/tasks/${id}/executions`, params: { limit } }),
}

// --- System ---
export const systemApi = {
  health: () => request<HealthStatus>({ method: 'get', url: '/config/health' }),
  dashboard: () => request<DashboardSummary>({ method: 'get', url: '/config/dashboard' }),
  mcpConfig: () => request<MCPConfig>({ method: 'get', url: '/config/mcp' }),
  updateMcpConfig: (data: {
    k8s?: Partial<Pick<K8sMCPConfig, 'enabled' | 'kubeconfig_path' | 'namespace' | 'in_cluster'>>
    ecs?: Partial<Pick<ECSMCPConfig, 'enabled' | 'region_id'>> & { access_key_id?: string; access_key_secret?: string }
    aliyun?: Partial<Pick<AliyunMCPConfig, 'enabled' | 'default_region_id' | 'allowed_regions' | 'required_tags' | 'allowed_instance_ids'>> & {
      access_key_id?: string
      access_key_secret?: string
      sls?: { mappings?: Array<Record<string, unknown>> }
    }
  }) => request<MCPConfig>({ method: 'patch', url: '/config/mcp', data }),
  k8sKnowledgeGraph: (params?: { namespace?: string; all_namespaces?: boolean; auto_sync?: boolean }) =>
    request<K8sKnowledgeGraph>({ method: 'get', url: '/config/k8s/knowledge-graph', params }),
  syncK8sKnowledgeGraph: (data: { namespace?: string; all_namespaces?: boolean }) =>
    request<K8sKnowledgeGraphSyncResult>({ method: 'post', url: '/config/k8s/knowledge-graph/sync', data }),
  llmConfig: () => request<LLMConfig>({ method: 'get', url: '/config/llm' }),
  updateLlmConfig: (data: Partial<LLMConfig> & { api_key?: string; provider?: Partial<LLMProviderConfig> & { api_key?: string }; provider_id?: string }) =>
    request<{ updated: string[]; restart_required: boolean; active: boolean }>({ method: 'patch', url: '/config/llm', data }),
  deleteLlmProvider: (id: string) => request<void>({ method: 'delete', url: `/config/llm/providers/${id}` }),
  auditLogs: (params?: {
    actor?: string
    action?: string
    resource?: string
    resource_id?: string
    result?: string
    limit?: number
  }) =>
    request<AuditLog[]>({ method: 'get', url: '/config/audit', params }),
}

// Re-export types used in API signatures
import type {
  User, Session, Message, MCPTool, ScheduledTask, TaskExecution,
  AuditLog, LLMConfig, LLMProviderConfig, HealthStatus,
  MCPConfig, K8sMCPConfig, ECSMCPConfig, AliyunMCPConfig,
  K8sKnowledgeGraph, K8sKnowledgeGraphSyncResult,
  DashboardSummary,
} from '@/types'
