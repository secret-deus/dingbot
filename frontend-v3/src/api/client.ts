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
  executions: (id: string, limit = 20) =>
    request<TaskExecution[]>({ method: 'get', url: `/scheduler/tasks/${id}/executions`, params: { limit } }),
}

// --- System ---
export const systemApi = {
  health: () => request<HealthStatus>({ method: 'get', url: '/config/health' }),
  llmConfig: () => request<LLMConfig>({ method: 'get', url: '/config/llm' }),
  updateLlmConfig: (data: Partial<LLMConfig>) =>
    request<{ updated: string[] }>({ method: 'patch', url: '/config/llm', data }),
  auditLogs: (params?: { actor?: string; action?: string; limit?: number }) =>
    request<AuditLog[]>({ method: 'get', url: '/config/audit', params }),
}

// Re-export types used in API signatures
import type {
  Session, Message, MCPTool, ScheduledTask, TaskExecution,
  AuditLog, LLMConfig, HealthStatus,
} from '@/types'
