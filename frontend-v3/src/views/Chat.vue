<template>
  <div :class="['chat-workbench', { 'sessions-collapsed': sessionsCollapsed }]">
    <aside class="session-rail" :aria-expanded="!sessionsCollapsed">
      <div class="rail-head">
        <div class="rail-copy">
          <div class="rail-title">对话</div>
          <div class="rail-subtitle">{{ sessionStore.sessions.length }} 个会话</div>
        </div>
        <div class="rail-actions">
          <n-button
            class="rail-new-button"
            size="small"
            tertiary
            :round="!sessionsCollapsed"
            :circle="sessionsCollapsed"
            :aria-label="sessionsCollapsed ? '新建对话' : undefined"
            @click="newSession"
          >
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            <span v-if="!sessionsCollapsed" class="rail-new-text">新建</span>
          </n-button>
          <n-button
            class="rail-toggle-button"
            quaternary
            circle
            :aria-label="sessionsCollapsed ? '展开对话列表' : '折叠对话列表'"
            :title="sessionsCollapsed ? '展开对话列表' : '折叠对话列表'"
            @click="sessionsCollapsed = !sessionsCollapsed"
          >
            <template #icon>
              <n-icon><component :is="sessionsCollapsed ? ChevronForwardOutline : ChevronBackOutline" /></n-icon>
            </template>
          </n-button>
        </div>
      </div>
      <n-spin v-if="sessionStore.loading" />
      <div v-else class="session-list">
        <div
          v-for="s in sessionStore.sessions"
          :key="s.id"
          :class="['session-row', { active: s.id === chatStore.activeSessionId }]"
        >
          <button class="session-item" type="button" :title="s.title" @click="selectSession(s.id)">
            <span class="session-initial" aria-hidden="true">{{ sessionInitial(s.title) }}</span>
            <span class="session-meta">
              <span class="session-title">{{ s.title }}</span>
              <span class="session-time">{{ s.updated_at?.slice(0, 16) }}</span>
            </span>
          </button>
          <n-popconfirm
            :positive-button-props="{ type: 'error', size: 'tiny' }"
            negative-text="取消"
            positive-text="删除"
            @positive-click="deleteSession(s.id)"
          >
            <template #trigger>
              <n-button
                class="session-delete"
                quaternary
                circle
                size="tiny"
                :aria-label="`删除 ${s.title}`"
                :disabled="chatStore.streaming && s.id === chatStore.activeSessionId"
                title="删除对话"
                @click.stop
              >
                <template #icon>
                  <n-icon><TrashOutline /></n-icon>
                </template>
              </n-button>
            </template>
            删除这个对话？
          </n-popconfirm>
        </div>
      </div>
    </aside>

    <section class="chat-main">
      <header class="chat-topbar">
        <div>
          <div class="chat-title">{{ currentTitle }}</div>
          <div class="chat-subtitle">K8s / ECS 运维助手</div>
        </div>
        <div v-if="chatStore.activeSessionId" class="chat-controls">
          <n-select
            v-model:value="chatStore.llmProviderId"
            :options="llmOptions"
            size="small"
            class="model-select"
            placeholder="选择模型"
            :disabled="!llmOptions.length"
          />
          <div class="tool-context-control">
            <span>工具上下文</span>
            <n-switch v-model:value="chatStore.toolContextEnabled" size="small" />
          </div>
        </div>
      </header>

      <main ref="messageListRef" class="message-scroll">
        <div v-if="!chatStore.activeSessionId" class="empty-state">
          <div class="empty-mark">DR</div>
          <h2>今天要排查什么？</h2>
          <p>新建一个会话，描述集群、服务、日志或 ECS 问题。</p>
          <n-button type="primary" round @click="newSession">开始新对话</n-button>
        </div>
        <template v-else>
          <div class="message-column">
            <MessageBubble v-for="msg in chatStore.messages" :key="msg.id" :message="msg" />
            <div v-if="chatStore.streaming" class="streaming-msg">
              <MessageBubble :message="{ id: 'streaming', role: 'assistant', content: chatStore.streamingContent, tool_calls: chatStore.streamingToolCalls, tool_results: chatStore.streamingToolResults, created_at: '' }" streaming />
              <n-spin size="small" />
            </div>
          </div>
        </template>
      </main>

      <footer class="composer-shell">
        <ChatInput
          :disabled="chatStore.streaming"
          :streaming="chatStore.streaming"
          @send="onSend"
          @stop="stopStream"
        />
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { NButton, NIcon, NPopconfirm, NSelect, NSpin, NSwitch } from 'naive-ui'
import { useSessionStore } from '@/stores/session'
import { useChatStore } from '@/stores/chat'
import { systemApi } from '@/api/client'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import { SSE } from 'sse.js'
import type { LLMConfig } from '@/types'
import { AddOutline, ChevronBackOutline, ChevronForwardOutline, TrashOutline } from '@vicons/ionicons5'

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const messageListRef = ref<HTMLElement>()
const llmConfig = ref<LLMConfig | null>(null)
const activeSse = shallowRef<{ close: () => void } | null>(null)
const sessionsCollapsed = ref(false)

const currentTitle = computed(() => {
  const s = sessionStore.sessions.find((s) => s.id === chatStore.activeSessionId)
  return s?.title || '智能对话'
})

const llmOptions = computed(() =>
  (llmConfig.value?.providers || []).map((provider) => ({
    label: `${provider.name || provider.id} · ${provider.model || '未填写模型'}`,
    value: provider.id,
    disabled: !provider.enabled || !provider.api_key_configured,
  })),
)

onMounted(async () => {
  await Promise.all([sessionStore.fetchSessions(), loadLlmConfig()])
})

onBeforeUnmount(() => {
  if (activeSse.value) {
    activeSse.value.close()
    activeSse.value = null
  }
  if (chatStore.streaming) {
    chatStore.finalizeStream()
  }
})

async function loadLlmConfig() {
  try {
    const config = await systemApi.llmConfig()
    llmConfig.value = config
    const enabledOptions = config.providers.filter((provider) => provider.enabled && provider.api_key_configured)
    const selectedStillValid = enabledOptions.some((provider) => provider.id === chatStore.llmProviderId)
    if (!selectedStillValid) {
      const defaultProvider = enabledOptions.find((provider) => provider.id === config.default_provider)
      chatStore.llmProviderId = defaultProvider?.id || enabledOptions[0]?.id || config.selected_provider_id || ''
    }
  } catch {
    llmConfig.value = null
  }
}

async function newSession() {
  const id = await sessionStore.createSession()
  chatStore.setSession(id)
  return id
}

async function selectSession(id: string) {
  await chatStore.loadMessages(id)
  await nextTick()
  scrollToBottom()
}

async function deleteSession(id: string) {
  if (chatStore.streaming && id === chatStore.activeSessionId) return

  const deletingActive = id === chatStore.activeSessionId
  await sessionStore.deleteSession(id)
  if (!deletingActive) return

  const next = sessionStore.sessions[0]
  if (next) {
    await selectSession(next.id)
  } else {
    chatStore.reset()
  }
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function sessionInitial(title?: string) {
  return (title?.trim().slice(0, 1) || '新').toUpperCase()
}

watch(() => chatStore.messages.length, () => nextTick(scrollToBottom))
watch(() => chatStore.streamingContent, () => nextTick(scrollToBottom))

async function onSend(content: string) {
  if (chatStore.streaming) return
  if (!chatStore.activeSessionId) {
    await newSession()
  }

  chatStore.addMessage({
    id: Date.now().toString(),
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  })
  chatStore.beginStream()

  const sse = new SSE('/api/v2/chat/sessions/' + chatStore.activeSessionId + '/stream', {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
    payload: JSON.stringify({
      content,
      tool_context_enabled: chatStore.toolContextEnabled,
      llm_provider_id: chatStore.llmProviderId || undefined,
    }),
    method: 'POST',
  })
  const currentSse = sse as { close: () => void }
  activeSse.value = currentSse

  sse.addEventListener('token', (e: any) => {
    if (activeSse.value !== currentSse) return
    const data = JSON.parse(e.data)
    chatStore.appendStream(data.content)
    nextTick(scrollToBottom)
  })

  sse.addEventListener('tool_call', (e: any) => {
    if (activeSse.value !== currentSse) return
    const data = JSON.parse(e.data)
    if (data.tool_call) {
      chatStore.addStreamingToolCall(data.tool_call)
      nextTick(scrollToBottom)
    }
  })

  sse.addEventListener('tool_result', (e: any) => {
    if (activeSse.value !== currentSse) return
    const data = JSON.parse(e.data)
    if (data.tool_call_id) {
      chatStore.addStreamingToolResult(data.tool_call_id, data.result)
      nextTick(scrollToBottom)
    }
  })

  sse.addEventListener('done', async () => {
    if (activeSse.value !== currentSse) return
    activeSse.value = null
    const sessionId = chatStore.activeSessionId
    chatStore.finalizeStream()
    if (sessionId) {
      await chatStore.loadMessages(sessionId)
    }
    await sessionStore.fetchSessions()
    nextTick(scrollToBottom)
  })

  sse.addEventListener('error', () => {
    if (activeSse.value !== currentSse) return
    activeSse.value = null
    chatStore.appendStream('\n发生错误\n')
    chatStore.finalizeStream()
  })
}

function stopStream() {
  if (!chatStore.streaming) return
  const currentSse = activeSse.value
  activeSse.value = null
  currentSse?.close()
  chatStore.finalizeStream()
  sessionStore.fetchSessions()
}
</script>

<style scoped>
.chat-workbench {
  height: 100%;
  max-height: 100%;
  min-height: 0;
  display: grid;
  grid-template-columns: 276px minmax(0, 1fr);
  background: var(--dr-bg);
  color: var(--dr-text);
  overflow: hidden;
  transition: grid-template-columns 180ms ease;
}
.chat-workbench.sessions-collapsed {
  grid-template-columns: 72px minmax(0, 1fr);
}
.session-rail {
  min-width: 0;
  min-height: 0;
  border-right: 1px solid var(--dr-border);
  background: var(--dr-sidebar);
  padding: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: padding 180ms ease;
}
.rail-head,
.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.rail-copy {
  min-width: 0;
}
.rail-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}
.rail-new-button,
.rail-toggle-button {
  min-width: 36px;
}
.rail-title {
  font-size: 15px;
  font-weight: 650;
  color: var(--dr-text);
}
.rail-subtitle,
.chat-subtitle,
.session-time {
  color: var(--dr-text-muted);
  font-size: 12px;
}
.session-list {
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.session-row {
  width: 100%;
  min-height: 58px;
  border: 1px solid transparent;
  border-radius: var(--dr-radius);
  background: transparent;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  align-items: center;
  overflow: hidden;
}
.session-row:hover {
  background: var(--dr-surface-hover);
}
.session-row.active {
  background: #faf1ea;
  border-color: rgba(25, 24, 20, 0.06);
}
.session-item {
  min-width: 0;
  height: 100%;
  padding: 10px 4px 10px 12px;
  border: 0;
  background: transparent;
  color: var(--dr-text-soft);
  text-align: left;
  cursor: pointer;
}
.session-initial {
  display: none;
}
.session-meta {
  min-width: 0;
  display: block;
}
.session-delete {
  opacity: 0;
  color: var(--dr-text-muted);
}
.session-row:hover .session-delete,
.session-row.active .session-delete {
  opacity: 1;
}
.session-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  margin-bottom: 5px;
}
.sessions-collapsed .session-rail {
  padding: 12px 8px;
}
.sessions-collapsed .rail-head {
  justify-content: center;
}
.sessions-collapsed .rail-copy,
.sessions-collapsed .rail-new-text,
.sessions-collapsed .session-meta,
.sessions-collapsed .session-delete {
  display: none;
}
.sessions-collapsed .rail-actions {
  flex-direction: column;
  gap: 8px;
}
.sessions-collapsed .session-list {
  align-items: center;
  overflow-x: hidden;
}
.sessions-collapsed .session-row {
  width: 44px;
  min-height: 44px;
  grid-template-columns: 1fr;
  justify-items: center;
}
.sessions-collapsed .session-item {
  width: 44px;
  min-height: 44px;
  padding: 0;
  display: grid;
  place-items: center;
  text-align: center;
}
.sessions-collapsed .session-initial {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 1px solid #d8d0c3;
  border-radius: var(--dr-radius);
  background: #fffdf8;
  color: var(--dr-accent-deep);
  font-size: 12px;
  font-weight: 650;
}
.chat-main {
  position: relative;
  min-width: 0;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  display: grid;
  grid-template-rows: 64px minmax(0, 1fr);
  background: var(--dr-bg);
  overflow: hidden;
}
.chat-topbar {
  position: relative;
  z-index: 2;
  min-height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: rgba(250, 247, 241, 0.86);
  backdrop-filter: blur(12px);
}
.chat-title {
  font-size: 15px;
  font-weight: 650;
  color: var(--dr-text);
}
.chat-controls,
.tool-context-control {
  display: flex;
  align-items: center;
}
.chat-controls {
  gap: 12px;
}
.model-select {
  width: min(280px, 30vw);
}
.tool-context-control {
  gap: 8px;
  color: var(--dr-text-soft);
  font-size: 12px;
  font-weight: 400;
}
.message-scroll {
  min-height: 0;
  height: 100%;
  overflow-x: hidden;
  overflow-y: scroll;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-color: #b9ad9c transparent;
  scrollbar-width: thin;
  scrollbar-gutter: stable;
  padding: 28px 24px 154px;
  box-shadow: inset -1px 0 0 #e3dacc;
}
.message-scroll::-webkit-scrollbar,
.session-list::-webkit-scrollbar {
  width: 10px;
}
.message-scroll::-webkit-scrollbar-track,
.session-list::-webkit-scrollbar-track {
  background: transparent;
}
.message-scroll::-webkit-scrollbar-thumb,
.session-list::-webkit-scrollbar-thumb {
  border: 3px solid transparent;
  border-radius: 999px;
  background: #cfc5b7;
  background-clip: content-box;
}
.message-column {
  width: min(100%, 880px);
  margin: 0 auto;
}
.streaming-msg {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.composer-shell {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 22px;
  z-index: 3;
  padding: 0 24px;
  border: 0;
  background: transparent;
  box-shadow: none;
  pointer-events: none;
}
.composer-shell :deep(.composer) {
  pointer-events: auto;
}
.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: var(--dr-text);
  gap: 12px;
}
.empty-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border: 1px solid #d4cbbd;
  border-radius: var(--dr-radius);
  background: #fffdf8;
  color: var(--dr-accent-deep);
  font-weight: 700;
}
.empty-state h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
}
.empty-state p {
  margin: 0 0 8px;
  color: var(--dr-text-muted);
}
@media (max-width: 820px) {
  .chat-workbench {
    grid-template-columns: 1fr;
  }
  .session-rail {
    display: none;
  }
  .chat-controls {
    gap: 8px;
  }
  .model-select {
    width: 168px;
  }
  .message-scroll {
    padding: 22px 14px 144px;
  }
  .composer-shell {
    bottom: 18px;
    padding: 0 14px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .chat-workbench,
  .session-rail {
    transition: none;
  }
}
</style>
