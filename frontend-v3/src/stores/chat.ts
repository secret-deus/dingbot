import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Message, ToolCall, ToolResult } from '@/types'
import { sessionApi } from '@/api/client'

export const useChatStore = defineStore('chat', () => {
  const activeSessionId = ref('')
  const messages = ref<Message[]>([])
  const streaming = ref(false)
  const streamingContent = ref('')
  const streamingToolCalls = ref<ToolCall[]>([])
  const streamingToolResults = ref<ToolResult[]>([])
  const toolContextEnabled = ref(localStorage.getItem('toolContextEnabled') !== 'false')
  const llmProviderId = ref(localStorage.getItem('llmProviderId') || '')
  let messagesRequestVersion = 0

  watch(toolContextEnabled, (enabled) => {
    localStorage.setItem('toolContextEnabled', String(enabled))
  })

  watch(llmProviderId, (providerId) => {
    if (providerId) localStorage.setItem('llmProviderId', providerId)
    else localStorage.removeItem('llmProviderId')
  })

  function setSession(id: string) {
    messagesRequestVersion += 1
    activeSessionId.value = id
    messages.value = []
    streamingContent.value = ''
    streamingToolCalls.value = []
    streamingToolResults.value = []
  }

  async function loadMessages(sessionId: string) {
    const version = ++messagesRequestVersion
    const msgs = await sessionApi.messages(sessionId)
    if (version !== messagesRequestVersion) return false

    messages.value = msgs
    activeSessionId.value = sessionId
    return true
  }

  function addMessage(msg: Message) {
    messages.value.push(msg)
  }

  function appendStream(content: string) {
    streamingContent.value += content
  }

  function beginStream() {
    streaming.value = true
    streamingContent.value = ''
    streamingToolCalls.value = []
    streamingToolResults.value = []
  }

  function addStreamingToolCall(call: ToolCall) {
    streamingToolCalls.value.push(call)
  }

  function addStreamingToolResult(toolCallId: string, result: unknown) {
    const call = streamingToolCalls.value.find((item) => item.id === toolCallId)
    streamingToolResults.value.push({
      tool_call_id: toolCallId,
      tool_name: call?.function?.name || '',
      result,
    })
  }

  function finalizeStream() {
    if (streamingContent.value || streamingToolCalls.value.length || streamingToolResults.value.length) {
      messages.value.push({
        id: Date.now().toString(),
        role: 'assistant',
        content: streamingContent.value,
        tool_calls: streamingToolCalls.value.length ? [...streamingToolCalls.value] : undefined,
        tool_results: streamingToolResults.value.length ? [...streamingToolResults.value] : undefined,
        created_at: new Date().toISOString(),
      })
      streamingContent.value = ''
      streamingToolCalls.value = []
      streamingToolResults.value = []
    }
    streaming.value = false
  }

  function reset() {
    messagesRequestVersion += 1
    activeSessionId.value = ''
    messages.value = []
    streaming.value = false
    streamingContent.value = ''
    streamingToolCalls.value = []
    streamingToolResults.value = []
  }

  return {
    activeSessionId, messages, streaming, streamingContent, streamingToolCalls, streamingToolResults,
    toolContextEnabled, llmProviderId,
    setSession, loadMessages, addMessage, appendStream, beginStream,
    addStreamingToolCall, addStreamingToolResult, finalizeStream, reset,
  }
})
