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

export type ToolDangerLevel = 'read' | 'write' | 'dangerous'
export type ToolExecutionPolicy = 'executable' | 'catalog_only' | 'external_mcp' | 'unavailable'

export interface ToolCandidate {
  name: string
  title?: string
  category?: string
  description?: string
  tags?: string[]
  dangerLevel?: ToolDangerLevel
  server?: string
  executionPolicy?: ToolExecutionPolicy
  available?: boolean
  unavailableReason?: string
  score?: number
  matchedFields?: string[]
}

export interface ToolCandidateCategoryGroup {
  category: string
  title?: string
  total: number
  topScore?: number
  results: ToolCandidate[]
}

export interface ToolCandidateRelevanceLayer {
  name: 'direct' | 'recommended' | 'related'
  title: string
  description?: string
  total: number
  categoryGroups: ToolCandidateCategoryGroup[]
  results: ToolCandidate[]
}

export interface ToolSearchResponse {
  query?: string
  total?: number
  results?: ToolCandidate[]
  categoryGroups?: ToolCandidateCategoryGroup[]
  relevanceLayers?: ToolCandidateRelevanceLayer[]
  reason?: string
}

export interface ToolResult {
  tool_call_id: string
  tool_name: string
  result: unknown
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  tool_calls?: ToolCall[]
  tool_results?: ToolResult[]
  tool_call_id?: string
  created_at: string
}

export interface MCPTool {
  name: string
  description: string
  inputSchema: Record<string, unknown>
  server: string
  available?: boolean
  unavailableReason?: string
}

export interface CatalogCount {
  name: string
  count: number
}

export interface MCPServerHealth {
  connected: boolean
  tools: number
  available_tools?: number
  unavailable_tools?: number
  catalog_total?: number
  catalog_categories?: CatalogCount[]
  execution_policies?: CatalogCount[]
  danger_levels?: CatalogCount[]
}

export interface K8sMCPConfig {
  enabled: boolean
  kubeconfig_path: string
  namespace: string
  in_cluster: boolean
  configured: boolean
  available: boolean
  unavailable_reason?: string
}

export interface ECSMCPConfig {
  enabled: boolean
  region_id: string
  access_key_id_configured: boolean
  access_key_secret_configured: boolean
  configured: boolean
  available: boolean
  unavailable_reason?: string
}

export interface AliyunMCPConfig {
  enabled: boolean
  default_region_id: string
  allowed_regions: string[]
  required_tags: Record<string, string[]>
  allowed_instance_ids: string[]
  sls_mapping_count: number
  access_key_id_configured: boolean
  access_key_secret_configured: boolean
  configured: boolean
  available: boolean
  unavailable_reason?: string
}

export interface MCPConfig {
  config_path: string
  source: string
  restart_required: boolean
  k8s: K8sMCPConfig
  ecs: ECSMCPConfig
  aliyun: AliyunMCPConfig
}

export interface KnowledgeGraphNode {
  id: string
  kind: string
  name: string
  namespace?: string | null
  labels?: Record<string, string>
  attributes?: Record<string, unknown>
  metrics?: Record<string, unknown>
}

export interface KnowledgeGraphEdge {
  source: string
  target: string
  type: string
}

export interface KnowledgeGraphSummary {
  nodes: number
  edges: number
  node_types: Record<string, number>
  edge_types: Record<string, number>
}

export interface KnowledgeGraphCoverage {
  total_nodes: number
  nodes_with_metrics: number
  coverage: number
}

export interface K8sKnowledgeGraph {
  path: string
  updated_at?: string | null
  metadata: Record<string, unknown>
  namespace: string
  all_namespaces?: boolean
  summary: KnowledgeGraphSummary
  coverage: KnowledgeGraphCoverage
  nodes: KnowledgeGraphNode[]
  edges: KnowledgeGraphEdge[]
}

export interface K8sKnowledgeGraphSyncResult {
  path: string
  updated_at?: string | null
  summary: KnowledgeGraphSummary
  namespace: string
  all_namespaces: boolean
  graph: K8sKnowledgeGraph
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
  last_result?: string
  created_at: string
}

export interface TaskExecution {
  id: string
  status: string
  started_at: string
  finished_at?: string
  result?: string
  error?: string
}

export interface AuditLog {
  id: number
  actor: string
  action: string
  resource: string
  resource_id?: string | null
  result: string
  ip?: string
  details?: Record<string, unknown> | null
  created_at: string
}

export interface LLMProviderConfig {
  id: string
  name: string
  enabled: boolean
  model: string
  base_url?: string
  temperature: number
  max_tokens: number
  timeout?: number
  stream?: boolean
  api_key_configured: boolean
  api_key_placeholder?: boolean
}

export interface LLMConfig {
  enabled: boolean
  active: boolean
  api_key_configured: boolean
  api_key_placeholder?: boolean
  model: string
  base_url?: string
  temperature: number
  max_tokens: number
  timeout?: number
  masking_enabled: boolean
  config_path?: string
  source?: string
  default_provider?: string
  selected_provider_id?: string
  providers: LLMProviderConfig[]
  restart_required?: boolean
}

export interface HealthStatus {
  status: string
  version: string
  llm_enabled: boolean
  llm_configured?: boolean
  mcp_servers: Record<string, MCPServerHealth>
  scheduler?: {
    enabled: boolean
    running: boolean
    jobs: number
    dingtalk_enabled?: boolean
  }
}

export type DashboardTone = 'green' | 'amber' | 'red' | 'blue' | 'slate'

export interface DashboardTheme {
  background: string
  shell: string
  surface: string
  surface_alt: string
  surface_light: string
  border: string
  text: string
  muted: string
  primary: string
  accent: string
  warning: string
  danger: string
}

export interface DashboardIconPack {
  bot: string
  kubernetes: string
  mcp: string
  graph: string
  timeline: string
}

export interface DashboardCluster {
  name: string
  namespace: string
  available: boolean
  configured: boolean
  mode: string
  unavailable_reason?: string
}

export interface DashboardTools {
  total: number
  available: number
  unavailable: number
  kubernetes: number
}

export interface DashboardInsight {
  id: string
  label: string
  title: string
  detail: string
  tone: DashboardTone
  icon: string
}

export interface DashboardResourceNode {
  kind: string
  count: number
  tone: DashboardTone
  icon: string
}

export interface DashboardTimelineItem {
  id: string
  title: string
  detail: string
  tone: DashboardTone
  icon: string
}

export interface DashboardAction {
  id: string
  title: string
  route: string
  tone: DashboardTone
  icon: string
}

export interface DashboardSummary {
  theme: DashboardTheme
  icon_pack: DashboardIconPack
  cluster: DashboardCluster
  tools: DashboardTools
  knowledge_graph: {
    updated_at?: string | null
    summary: KnowledgeGraphSummary
    coverage: KnowledgeGraphCoverage
  }
  scheduler: {
    enabled: boolean
    running: boolean
    jobs: number
    dingtalk_enabled?: boolean
  }
  llm: {
    enabled: boolean
    configured: boolean
  }
  insights: DashboardInsight[]
  resource_map: DashboardResourceNode[]
  execution_timeline: DashboardTimelineItem[]
  next_actions: DashboardAction[]
}
