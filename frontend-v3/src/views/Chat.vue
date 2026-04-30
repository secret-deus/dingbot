<template>
  <div style="display: flex; height: 100%; gap: 12px">
    <n-card style="width: 240px; flex-shrink: 0" size="small" title="会话列表">
      <template #header-extra>
        <n-button size="tiny" @click="newSession">新建</n-button>
      </template>
      <n-spin v-if="sessionStore.loading" />
      <n-list v-else hoverable clickable>
        <n-list-item v-for="s in sessionStore.sessions" :key="s.id" @click="selectSession(s.id)" :style="{ background: s.id === chatStore.activeSessionId ? '#2a2a2a' : 'transparent' }">
          <n-thing :title="s.title" :description="s.updated_at?.slice(0, 16)" />
        </n-list-item>
      </n-list>
    </n-card>
    <n-card style="flex: 1; display: flex; flex-direction: column" size="small">
      <template #header>{{ currentTitle }}</template>
      <div ref="messageListRef" style="flex: 1; overflow-y: auto; padding: 8px">
        <div v-if="!chatStore.activeSessionId" style="text-align: center; color: #666; padding: 40px">选择或新建一个会话开始对话</div>
        <template v-else>
          <MessageBubble v-for="msg in chatStore.messages" :key="msg.id" :message="msg" />
          <div v-if="chatStore.streaming" class="streaming-msg">
            <MessageBubble :message="{ id: 'streaming', role: 'assistant', content: chatStore.streamingContent, created_at: '' }" />
            <n-spin size="small" />
          </div>
        </template>
      </div>
      <ChatInput v-if="chatStore.activeSessionId" :disabled="chatStore.streaming" @send="onSend" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { NCard, NList, NListItem, NThing, NButton, NSpin } from 'naive-ui'
import { useSessionStore } from '@/stores/session'
import { useChatStore } from '@/stores/chat'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import { SSE } from 'sse.js'

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const messageListRef = ref<HTMLElement>()

const currentTitle = computed(() => {
  const s = sessionStore.sessions.find((s) => s.id === chatStore.activeSessionId)
  return s?.title || '智能对话'
})

onMounted(() => sessionStore.fetchSessions())

async function newSession() {
  const id = await sessionStore.createSession()
  chatStore.setSession(id)
}

async function selectSession(id: string) {
  await chatStore.loadMessages(id)
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

watch(() => chatStore.messages.length, () => nextTick(scrollToBottom))

function onSend(content: string) {
  chatStore.addMessage({
    id: Date.now().toString(),
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  })
  chatStore.streaming = true
  chatStore.streamingContent = ''

  const sse = new SSE('/api/v2/chat/sessions/' + chatStore.activeSessionId + '/stream', {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
    payload: JSON.stringify({ content }),
    method: 'POST',
  })

  sse.addEventListener('token', (e: any) => {
    const data = JSON.parse(e.data)
    chatStore.appendStream(data.content)
    nextTick(scrollToBottom)
  })

  sse.addEventListener('tool_call', (e: any) => {
    const data = JSON.parse(e.data)
    chatStore.appendStream(`\n🔧 调用工具: ${data.tool_call?.function?.name || '?'}\n`)
  })

  sse.addEventListener('tool_result', () => {
    chatStore.appendStream(`📋 工具结果已返回\n`)
  })

  sse.addEventListener('done', () => {
    chatStore.finalizeStream()
    sessionStore.fetchSessions()
  })

  sse.addEventListener('error', () => {
    chatStore.appendStream('\n❌ 发生错误\n')
    chatStore.finalizeStream()
  })
}
</script>

<style scoped>
.streaming-msg { display: flex; align-items: flex-start; gap: 8px; }
</style>
