<template>
  <article :class="['assistant-run-card', status]">
    <header class="run-card-head">
      <div>
        <span class="card-kicker">{{ kicker }}</span>
        <h3>{{ title }}</h3>
      </div>
      <span :class="['run-status', status]">{{ statusLabel }}</span>
    </header>

    <section class="answer-body">
      <div v-if="message.content" class="content assistant-content" v-html="renderedContent" />
      <p v-else class="empty-answer">{{ emptyAnswerText }}</p>
    </section>

    <section v-if="toolRows.length" class="tool-summary" aria-label="调用工具">
      <span v-for="row in toolRows" :key="row.id" class="tool-chip">{{ row.name }}</span>
    </section>

    <section v-if="toolRows.length" class="execution-chain" aria-label="执行链路">
      <div class="chain-title">执行链路</div>
      <div class="chain-list">
        <article v-for="row in toolRows" :key="row.id" class="chain-row">
          <span class="chain-dot" />
          <div class="chain-main">
            <div class="chain-row-head">
              <strong>{{ row.name }}</strong>
              <span :class="['chain-state', row.state]">{{ row.stateLabel }}</span>
            </div>
            <small>{{ row.summary }}</small>
            <div v-if="row.confirmation" class="confirmation-panel">
              <div>
                <strong>需要确认</strong>
                <span>{{ confirmationLabel(row.confirmation) }}</span>
              </div>
              <n-button
                size="tiny"
                type="warning"
                :loading="confirmingToolCallId === row.id"
                :disabled="props.streaming"
                @click="confirmTool(row.id)"
              >
                确认执行
              </n-button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <details v-if="toolRows.length" class="technical-details">
      <summary>技术细节</summary>
      <div class="details-stack">
        <section v-for="row in toolRows" :key="`${row.id}-details`" class="detail-block">
          <div class="detail-head">
            <strong>{{ row.name }}</strong>
            <span>{{ row.stateLabel }}</span>
          </div>
          <details>
            <summary>参数</summary>
            <pre>{{ row.arguments }}</pre>
          </details>
          <p v-if="row.resultSummary" class="result-summary">结果摘要：{{ row.resultSummary }}</p>
          <details v-if="row.rawResult">
            <summary>原始结果</summary>
            <pre>{{ row.rawResult }}</pre>
          </details>
          <ToolCandidateCards v-if="row.toolSearchPayload" :payload="row.toolSearchPayload" />
        </section>
      </div>
    </details>

    <footer class="card-actions">
      <n-button secondary size="small" :disabled="!hasCopyableAnswer" @click="copyAnswer">复制回答</n-button>
      <n-button v-if="toolRows.length" secondary size="small" @click="goToMcp">
        {{ hasToolSearch ? '打开工具管理' : '查看 MCP 工具' }}
      </n-button>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, useMessage } from 'naive-ui'
import { marked } from 'marked'
import 'highlight.js/styles/github.css'
import { chatApi } from '@/api/client'
import ToolCandidateCards from './ToolCandidateCards.vue'
import type { Message, ToolConfirmation, ToolResult, ToolSearchResponse } from '@/types'

const props = defineProps<{ message: Message; streaming?: boolean }>()
const emit = defineEmits<{ 'tool-confirmed': [] }>()

const router = useRouter()
const messageApi = useMessage()
const confirmingToolCallId = ref('')

const resultsByCallId = computed(() => {
  const map = new Map<string, ToolResult>()
  for (const result of props.message.tool_results || []) {
    map.set(result.tool_call_id, result)
  }
  return map
})

const toolRows = computed(() =>
  (props.message.tool_calls || []).map((call) => {
    const result = resultsByCallId.value.get(call.id)
    const toolSearchPayload = toolSearchResult(result)
    const confirmation = confirmationResult(result)
    const state = confirmation ? 'needs-confirmation' : result ? 'done' : props.streaming ? 'waiting' : 'called'
    return {
      id: call.id,
      name: call.function.name,
      arguments: formatArgs(call.function.arguments),
      state,
      stateLabel: state === 'needs-confirmation' ? '待确认' : state === 'done' ? '有结果' : state === 'waiting' ? '等待中' : '已调用',
      summary: confirmation ? '写入或高危工具需要人工确认后才会执行。' : result ? '工具已返回结果，摘要和候选内容收在技术细节中。' : '已发起工具调用，正在等待返回。',
      resultSummary: result ? summarizeResult(result.result) : '',
      rawResult: result ? formatUnknown(result.result) : '',
      toolSearchPayload,
      confirmation,
    }
  }),
)

const hasToolSearch = computed(() => toolRows.value.some((row) => Boolean(row.toolSearchPayload)))
const hasCopyableAnswer = computed(() => Boolean(props.message.content?.trim()))
const hasAnyToolCall = computed(() => toolRows.value.length > 0)
const hasIncompleteToolCall = computed(() => toolRows.value.some((row) => row.state !== 'done'))
const hasErrorText = computed(() => /发生错误|执行失败|请求失败|error/i.test(props.message.content || ''))
const failed = computed(() => {
  if (props.streaming) return false
  return hasErrorText.value || (hasAnyToolCall.value && hasIncompleteToolCall.value)
})
const status = computed(() => {
  if (props.streaming) return 'running'
  if (failed.value) return 'failed'
  return 'ready'
})
const statusLabel = computed(() => {
  if (status.value === 'running') return '执行中'
  if (status.value === 'failed') return hasErrorText.value ? '执行失败' : '执行未完成'
  return '已完成'
})
const kicker = computed(() => (props.message.role === 'system' ? 'System Note' : props.message.role === 'tool' ? 'Tool Result' : 'Bot Answer'))
const title = computed(() => {
  if (status.value === 'running') return '正在组织回答'
  if (status.value === 'failed') return hasErrorText.value ? '执行失败' : '执行未完成'
  const heading = firstMarkdownHeading(props.message.content)
  if (heading) return heading
  if (toolRows.value.length) return '已按证据链组织排障结果'
  if (!hasCopyableAnswer.value) return '已记录助手事件'
  return '已生成回答'
})
const emptyAnswerText = computed(() => {
  if (props.streaming) return '正在等待模型输出...'
  if (toolRows.value.length) return '本轮没有返回可展示正文，执行链路已保留。'
  return '本轮没有返回可展示正文。'
})
const renderedContent = computed(() => {
  const raw = props.message.content || ''
  try {
    return marked.parse(raw) as string
  } catch {
    return escapeHtml(raw)
  }
})

async function copyAnswer() {
  const text = props.message.content?.trim()
  if (!text) {
    messageApi.info('暂无可复制内容')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    messageApi.success('回答已复制')
  } catch {
    messageApi.error('复制失败，请手动选择文本')
  }
}

function goToMcp() {
  router.push({ name: 'MCPConfig' })
}

async function confirmTool(toolCallId: string) {
  if (props.streaming || confirmingToolCallId.value) return
  confirmingToolCallId.value = toolCallId
  try {
    await chatApi.confirmToolCall(props.message.id, toolCallId)
    messageApi.success('已确认并执行工具')
    emit('tool-confirmed')
  } catch (error) {
    messageApi.error(errorMessage(error, '确认执行失败'))
  } finally {
    confirmingToolCallId.value = ''
  }
}

function formatArgs(argsStr: string): string {
  try {
    return JSON.stringify(JSON.parse(argsStr), null, 2)
  } catch {
    return argsStr || '{}'
  }
}

function firstMarkdownHeading(value: string) {
  const line = value.trim().split('\n').find((item) => item.trim())
  const match = line?.match(/^#{1,3}\s+(.{1,42})$/)
  return match?.[1]?.trim() || ''
}

function toolSearchResult(result?: ToolResult): ToolSearchResponse | null {
  if (!result || result.tool_name !== 'toolsearch') return null
  const payload = unwrapToolPayload(result.result)
  if (payload && typeof payload === 'object' && ('results' in payload || 'reason' in payload)) {
    return payload as ToolSearchResponse
  }
  return null
}

function confirmationResult(result?: ToolResult): ToolConfirmation | null {
  const payload = unwrapToolPayload(result?.result)
  if (!payload || typeof payload !== 'object') return null
  const candidate = payload as { requires_confirmation?: boolean; confirmation?: unknown }
  if (candidate.requires_confirmation !== true || !candidate.confirmation || typeof candidate.confirmation !== 'object') {
    return null
  }
  const confirmation = candidate.confirmation as ToolConfirmation
  return confirmation.token ? confirmation : null
}

function confirmationLabel(confirmation: ToolConfirmation) {
  const level = confirmation.dangerLevel === 'dangerous' ? '高危' : '写入'
  return `${level}操作 · ${confirmation.tool}`
}

function unwrapToolPayload(value: unknown): unknown {
  if (value && typeof value === 'object' && 'result' in value) {
    return unwrapToolPayload((value as { result: unknown }).result)
  }
  if (typeof value === 'string') {
    try {
      return JSON.parse(value)
    } catch {
      return value
    }
  }
  return value
}

function summarizeResult(value: unknown): string {
  const unwrapped = unwrapToolPayload(value)
  if (typeof unwrapped === 'string') {
    return unwrapped.length > 160 ? `${unwrapped.slice(0, 160)}...` : unwrapped
  }
  if (Array.isArray(unwrapped)) {
    return `数组结果，${unwrapped.length} 条记录`
  }
  if (unwrapped && typeof unwrapped === 'object') {
    const keys = Object.keys(unwrapped as Record<string, unknown>).slice(0, 6)
    return keys.length ? `对象结果，字段：${keys.join(', ')}` : '对象结果'
  }
  if (unwrapped === undefined || unwrapped === null) return '空结果'
  return String(unwrapped)
}

function formatUnknown(value: unknown): string {
  const unwrapped = unwrapToolPayload(value)
  if (typeof unwrapped === 'string') return unwrapped
  try {
    return JSON.stringify(unwrapped, null, 2)
  } catch {
    return String(unwrapped)
  }
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function errorMessage(error: unknown, fallback: string) {
  const maybe = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = maybe.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'reason' in detail) {
    return `确认被拒绝：${String((detail as { reason?: unknown }).reason)}`
  }
  return maybe.message || fallback
}
</script>

<style scoped>
.assistant-run-card {
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface-lift);
  box-shadow: var(--dr-shadow);
}

.run-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-height: 56px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: var(--dr-bg-page);
}

.card-kicker,
.chain-title {
  display: block;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
  font-weight: 650;
  text-transform: uppercase;
}

.run-card-head h3 {
  margin: 4px 0 0;
  color: var(--dr-text);
  font-size: var(--dr-text-lg);
  font-weight: 650;
  line-height: 1.35;
}

.run-status,
.chain-state {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: var(--dr-text-xs);
  font-weight: 650;
  white-space: nowrap;
}

.run-status.ready,
.chain-state.done {
  background: var(--dr-green-soft);
  color: var(--dr-green);
}

.run-status.running,
.chain-state.waiting {
  background: var(--dr-amber-soft);
  color: var(--dr-amber);
}

.run-status.failed {
  background: var(--dr-red-soft);
  color: var(--dr-red);
}

.chain-state.called {
  background: var(--dr-blue-soft);
  color: var(--dr-blue);
}

.chain-state.needs-confirmation {
  background: var(--dr-amber-soft);
  color: var(--dr-amber);
}

.answer-body {
  padding: 14px 16px 0;
}

.empty-answer {
  margin: 0 0 14px;
  color: var(--dr-text-muted);
}

.content {
  color: var(--dr-text-soft);
  line-height: 1.62;
  word-break: break-word;
}

.content :deep(p:first-child) {
  margin-top: 0;
}

.content :deep(p:last-child) {
  margin-bottom: 0;
}

.content :deep(pre) {
  overflow-x: auto;
  padding: 12px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #fbf8f1;
}

.content :deep(code) {
  font-size: var(--dr-text-sm);
}

.tool-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 16px 0;
}

.tool-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 9px;
  border: 1px solid #e5cfc5;
  border-radius: var(--dr-radius);
  background: var(--dr-accent-wash);
  color: var(--dr-accent-deep);
  font-family: var(--dr-font-mono);
  font-size: var(--dr-text-xs);
}

.execution-chain {
  padding: 16px;
}

.chain-list {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

.chain-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #fffdf8;
}

.chain-dot {
  width: 7px;
  height: 7px;
  margin-top: 8px;
  border-radius: 50%;
  background: var(--dr-accent);
}

.chain-main {
  min-width: 0;
}

.chain-row-head,
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.chain-row strong,
.detail-head strong {
  color: var(--dr-text);
  font-weight: 650;
  overflow-wrap: anywhere;
}

.chain-row small {
  display: block;
  margin-top: 4px;
  color: var(--dr-text-muted);
  line-height: 1.45;
}

.confirmation-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding: 10px;
  border: 1px solid #f0d18b;
  border-radius: var(--dr-radius);
  background: #fff8e6;
}

.confirmation-panel div {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.confirmation-panel strong {
  color: var(--dr-text);
  font-size: var(--dr-text-sm);
}

.confirmation-panel span {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
  overflow-wrap: anywhere;
}

.technical-details {
  border-top: 1px solid var(--dr-border-soft);
  background: var(--dr-bg-page);
}

.technical-details > summary {
  min-height: 42px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  color: var(--dr-text-soft);
  cursor: pointer;
  font-weight: 610;
}

.details-stack {
  display: grid;
  gap: 12px;
  padding: 0 16px 16px;
}

.detail-block {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: var(--dr-surface);
}

.detail-head span,
.result-summary {
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
}

.detail-block summary {
  color: var(--dr-text-soft);
  cursor: pointer;
  font-size: var(--dr-text-sm);
  font-weight: 610;
}

.detail-block pre {
  max-height: 220px;
  margin: 8px 0 0;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--dr-border-soft);
  border-radius: var(--dr-radius);
  background: #fbf8f1;
  color: var(--dr-text-soft);
  font-family: var(--dr-font-mono);
  font-size: var(--dr-text-xs);
  line-height: 1.5;
}

.result-summary {
  margin: 0;
  line-height: 1.5;
}

.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px 16px;
}

@media (max-width: 820px) {
  .run-card-head,
  .chain-row-head,
  .detail-head {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
