export interface User {
  id: string
  username: string
  role: 'admin' | 'operator' | 'viewer'
  display_name: string
  is_active: boolean
}

export interface Session {
  id: string
  title: string
  skill_id?: string
  created_at: string
  updated_at: string
}

export interface ToolCall {
  id: string
  type: 'function'
  function: { name: string; arguments: string }
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
  created_at: string
}

export interface MCPTool {
  name: string
  description: string
  inputSchema: Record<string, unknown>
  server: string
}

export interface ScheduledTask {
  id: string
  name: string
  cron_expr: string
  prompt: string
  skill_id?: string
  notify_dingtalk: boolean
  status: 'active' | 'paused' | 'disabled'
  last_run_at?: string
  created_at: string
}

export interface TaskExecution {
  id: string
  status: string
  started_at: string
  finished_at?: string
  error?: string
}

export interface AuditLog {
  id: number
  actor: string
  action: string
  resource: string
  result: string
  ip?: string
  created_at: string
}

export interface LLMConfig {
  model: string
  base_url?: string
  temperature: number
  max_tokens: number
  masking_enabled: boolean
}

export interface HealthStatus {
  status: string
  version: string
  llm_enabled: boolean
  mcp_servers: Record<string, { connected: boolean; tools: number }>
}
