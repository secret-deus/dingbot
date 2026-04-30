import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message } from '@/types'
import { sessionApi } from '@/api/client'

export const useChatStore = defineStore('chat', () => {
  const activeSessionId = ref('')
  const messages = ref<Message[]>([])
  const streaming = ref(false)
  const streamingContent = ref('')

  function setSession(id: string) {
    activeSessionId.value = id
    messages.value = []
    streamingContent.value = ''
  }

  async function loadMessages(sessionId: string) {
    const msgs = await sessionApi.messages(sessionId)
    messages.value = msgs
    activeSessionId.value = sessionId
  }

  function addMessage(msg: Message) {
    messages.value.push(msg)
  }

  function appendStream(content: string) {
    streamingContent.value += content
  }

  function finalizeStream() {
    if (streamingContent.value) {
      messages.value.push({
        id: Date.now().toString(),
        role: 'assistant',
        content: streamingContent.value,
        created_at: new Date().toISOString(),
      })
      streamingContent.value = ''
    }
    streaming.value = false
  }

  function reset() {
    activeSessionId.value = ''
    messages.value = []
    streaming.value = false
    streamingContent.value = ''
  }

  return {
    activeSessionId, messages, streaming, streamingContent,
    setSession, loadMessages, addMessage, appendStream, finalizeStream, reset,
  }
})
