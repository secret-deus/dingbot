<template>
  <div :class="['chat-workbench', { 'sessions-collapsed': sessionsCollapsed }]" :inert="sessionMutationBusy" :aria-busy="sessionMutationBusy">
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
            :loading="creatingSession"
            :disabled="chatStore.streaming || sessionMutationBusy"
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
          <button class="session-item" type="button" :title="s.title" :disabled="chatStore.streaming || sessionMutationBusy" @click="selectSession(s.id)">
            <span class="session-initial" aria-hidden="true">{{ sessionInitial(s.title) }}</span>
            <span class="session-meta">
              <span class="session-title">{{ s.title }}</span>
              <span class="session-time">{{ s.updated_at?.slice(0, 16) }}</span>
            </span>
          </button>
          <n-popconfirm
            :positive-button-props="{ type: 'error', size: 'tiny', disabled: sessionMutationBusy }"
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
                :disabled="chatStore.streaming || sessionMutationBusy"
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
            :disabled="chatStore.streaming || sessionMutationBusy || !llmOptions.length"
          />
          <div class="tool-context-control">
            <span>工具上下文</span>
            <n-switch v-model:value="chatStore.toolContextEnabled" size="small" :disabled="chatStore.streaming || sessionMutationBusy" />
          </div>
        </div>
      </header>

      <main ref="messageListRef" class="message-scroll">
        <div v-if="showEmptyState" class="empty-state">
          <div class="empty-mark">DR</div>
          <h2>今天要排查什么？</h2>
          <p>选择一个常见入口填入输入框，或直接描述集群、服务、日志、ECS 问题。</p>
          <div class="prompt-grid" aria-label="常用排障提示">
            <button
              v-for="prompt in quickPrompts"
              :key="prompt.title"
              class="prompt-card"
              type="button"
              :disabled="sessionMutationBusy"
              @click="usePrompt(prompt.text)"
            >
              <span>{{ prompt.kicker }}</span>
              <strong>{{ prompt.title }}</strong>
              <small>{{ prompt.text }}</small>
            </button>
          </div>
          <button
            v-if="!chatStore.activeSessionId"
            class="empty-action"
            type="button"
            :disabled="chatStore.streaming || sessionMutationBusy"
            @click="newSession"
          >
            {{ creatingSession ? '正在创建...' : '开始空白对话' }}
          </button>
        </div>
        <template v-else>
          <div class="message-column">
            <MessageBubble
              v-for="msg in chatStore.messages"
              :key="msg.id"
              :message="msg"
              @tool-confirmed="reloadActiveMessages"
            />
            <div v-if="chatStore.streaming" class="streaming-msg">
              <MessageBubble :message="{ id: 'streaming', role: 'assistant', content: chatStore.streamingContent, tool_calls: chatStore.streamingToolCalls, tool_results: chatStore.streamingToolResults, created_at: '' }" streaming />
              <n-spin size="small" />
            </div>
          </div>
        </template>
      </main>

      <footer class="composer-shell">
        <ChatInput
          ref="chatInputRef"
          v-model="promptDraft"
          :disabled="chatStore.streaming || sessionMutationBusy"
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
import { useRoute, useRouter } from 'vue-router'
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
const route = useRoute()
const router = useRouter()
const messageListRef = ref<HTMLElement>()
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null)
const llmConfig = ref<LLMConfig | null>(null)
const activeSse = shallowRef<{ close: () => void } | null>(null)
const sessionsCollapsed = ref(false)
const promptDraft = ref('')
const creatingSession = ref(false)
let pendingSessionPromise: Promise<string> | null = null
const sessionTransitionLoading = ref(false)
const sessionMutationBusy = computed(() => creatingSession.value || sessionStore.mutationLoading || sessionTransitionLoading.value)
const quickPrompts = [
  {
    kicker: 'K8s',
    title: 'Namespace 状态',
    text: '查看 default namespace 当前状态，列出异常 Pod、事件和下一步建议',
  },
  {
    kicker: 'Logs',
    title: '服务日志排查',
    text: '检查 default namespace 中 web 服务最近 30 分钟的错误日志',
  },
  {
    kicker: 'Tools',
    title: '工具可用性',
    text: '验证 ToolSearch 目录恢复情况，并列出当前可用的 Kubernetes 工具',
  },
  {
    kicker: 'ECS',
    title: '主机监控',
    text: '读取 ECS CPU 和内存监控数据，找出需要关注的实例',
  },
]

const currentTitle = computed(() => {
  const s = sessionStore.sessions.find((s) => s.id === chatStore.activeSessionId)
  return s?.title || '智能对话'
})
const showEmptyState = computed(() => !chatStore.activeSessionId || (!chatStore.messages.length && !chatStore.streaming))

const llmOptions = computed(() =>
  (llmConfig.value?.providers || []).map((provider) => ({
    label: `${provider.name || provider.id} · ${provider.model || '未填写模型'}`,
    value: provider.id,
    disabled: !provider.enabled || !provider.api_key_configured,
  })),
)

onMounted(async () => {
  window.addEventListener('beforeunload', preventStreamingUnload)
  await Promise.all([sessionStore.fetchSessions(), loadLlmConfig()])
  await openSessionFromRoute()
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', preventStreamingUnload)
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
  if (chatStore.streaming || sessionTransitionLoading.value || sessionStore.mutationLoading) return chatStore.activeSessionId
  if (pendingSessionPromise) return pendingSessionPromise

  creatingSession.value = true
  pendingSessionPromise = (async () => {
    try {
      const id = await sessionStore.createSession()
      if (!id) return chatStore.activeSessionId
      chatStore.setSession(id)
      await syncSessionQuery(id)
      return id
    } finally {
      creatingSession.value = false
      pendingSessionPromise = null
    }
  })()

  return pendingSessionPromise
}

async function selectSession(id: string) {
  if (chatStore.streaming || sessionMutationBusy.value) return

  await loadSession(id)
}

async function loadSession(id: string) {
  const loaded = await chatStore.loadMessages(id)
  if (!loaded) return false

  await syncSessionQuery(id)
  await nextTick()
  scrollToBottom()
  return true
}

async function openSessionFromRoute() {
  if (chatStore.streaming) {
    if (chatStore.activeSessionId) await syncSessionQuery(chatStore.activeSessionId)
    return
  }

  if (route.query.new === '1') {
    await newSession()
    return
  }

  const sessionId = typeof route.query.session === 'string' ? route.query.session : ''
  if (!sessionId || sessionId === chatStore.activeSessionId) return
  if (!await chatStore.loadMessages(sessionId)) return
  await nextTick()
  scrollToBottom()
}

function preventStreamingUnload(event: BeforeUnloadEvent) {
  if (!chatStore.streaming) return
  event.preventDefault()
  event.returnValue = ''
}

async function reloadActiveMessages() {
  if (!chatStore.activeSessionId) return
  if (!await chatStore.loadMessages(chatStore.activeSessionId)) return
  await nextTick()
  scrollToBottom()
}

async function deleteSession(id: string) {
  if (chatStore.streaming || sessionMutationBusy.value) return

  sessionTransitionLoading.value = true
  try {
    const deletingActive = id === chatStore.activeSessionId
    const deleted = await sessionStore.deleteSession(id)
    if (!deleted || !deletingActive) return

    const next = sessionStore.sessions[0]
    if (next) {
      await loadSession(next.id)
    } else {
      chatStore.reset()
      await syncSessionQuery('')
    }
  } finally {
    sessionTransitionLoading.value = false
  }
}

async function syncSessionQuery(sessionId: string) {
  const current = typeof route.query.session === 'string' ? route.query.session : ''
  if (current === sessionId) return

  const query = { ...route.query }
  delete query.new
  if (sessionId) query.session = sessionId
  else delete query.session
  await router.replace({ name: 'Chat', query })
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function sessionInitial(title?: string) {
  return (title?.trim().slice(0, 1) || '新').toUpperCase()
}

async function usePrompt(text: string) {
  if (creatingSession.value) return
  promptDraft.value = text
  await nextTick()
  chatInputRef.value?.focus()
}

watch(() => chatStore.messages.length, () => nextTick(scrollToBottom))
watch(() => chatStore.streamingContent, () => nextTick(scrollToBottom))
watch([() => route.query.session, () => route.query.new], () => openSessionFromRoute())

async function onSend(content: string) {
  if (chatStore.streaming || sessionMutationBusy.value) return
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
      if (!await chatStore.loadMessages(sessionId)) return
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
  background: #ffffff;
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
  border-right: 1px solid var(--dr-border-soft);
  background: #ffffff;
  backdrop-filter: none;
  padding: 14px 12px;
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
  --n-border: 0 !important;
  --n-border-hover: 0 !important;
  --n-border-pressed: 0 !important;
  --n-border-focus: 0 !important;
  --n-color: transparent !important;
  --n-color-hover: #f8fafc !important;
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
  gap: 2px;
}
.session-row {
  width: 100%;
  min-height: 58px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  align-items: center;
  overflow: hidden;
}
.session-row:hover {
  background: #f8fafc;
}
.session-row.active {
  background: #eef2f7;
  box-shadow: none;
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
.session-item:disabled {
  cursor: not-allowed;
  opacity: 0.58;
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
  border: 0;
  border-radius: var(--dr-radius);
  background: #f8fafc;
  color: var(--dr-text);
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
  background: #ffffff;
  overflow: hidden;
}
.chat-topbar {
  position: relative;
  z-index: 2;
  min-height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--dr-border-soft);
  background: #ffffff;
  backdrop-filter: none;
}

.chat-topbar > div:first-child {
  min-width: 0;
}

.chat-title {
  overflow: hidden;
  font-size: 15px;
  font-weight: 650;
  color: var(--dr-text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-subtitle {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  scrollbar-color: #b7c2d3 transparent;
  scrollbar-width: thin;
  scrollbar-gutter: stable;
  padding: 30px 24px 130px;
  background: #ffffff;
  box-shadow: none;
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
  background: #c1cad8;
  background-clip: content-box;
}
.message-column {
  width: min(100%, 920px);
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
  bottom: 0;
  z-index: 3;
  padding: 14px 24px 16px;
  border-top: 1px solid var(--dr-border-soft);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: none;
  pointer-events: none;
}
.composer-shell :deep(.composer) {
  pointer-events: auto;
  border: 0;
  background: transparent;
  box-shadow: none;
}
.empty-state {
  width: min(100%, 760px);
  margin: 0 auto;
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
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--dr-text);
  font-weight: 700;
}
.empty-state :deep(.n-button--primary-type) {
  --n-border: 0 !important;
  --n-border-hover: 0 !important;
  --n-border-pressed: 0 !important;
  --n-border-focus: 0 !important;
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
.prompt-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 8px;
}
.prompt-card {
  min-width: 0;
  min-height: 102px;
  padding: 13px 14px;
  border: 1px solid var(--dr-border-soft);
  border-radius: 8px;
  background: #f8fafc;
  color: var(--dr-text);
  text-align: left;
  cursor: pointer;
}
.prompt-card:hover {
  border-color: #cbd5e1;
  background: #f1f5f9;
}
.prompt-card:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}
.prompt-card span {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 7px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4f46e5;
  font-size: 11px;
  font-weight: 750;
}
.prompt-card strong {
  display: block;
  margin-top: 9px;
  font-size: 14px;
  line-height: 1.25;
}
.prompt-card small {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: var(--dr-text-muted);
  font-size: 12px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.empty-action {
  min-height: 36px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #111827;
  cursor: pointer;
  font-weight: 650;
}
.empty-action:hover {
  color: var(--dr-accent);
}
@media (max-width: 820px) {
  .chat-workbench {
    grid-template-columns: 1fr;
  }
  .chat-main {
    grid-template-rows: auto minmax(0, 1fr);
  }
  .session-rail {
    display: none;
  }
  .chat-topbar {
    min-height: 0;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 10px;
    padding: 12px 14px;
  }
  .chat-controls {
    width: 100%;
    align-items: stretch;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
  }
  .model-select {
    width: 100%;
    min-width: 0;
    flex: 0 0 auto;
  }
  .tool-context-control {
    width: 100%;
    justify-content: space-between;
    white-space: nowrap;
  }
  .message-scroll {
    padding: 22px 14px 144px;
  }
  .prompt-grid {
    grid-template-columns: 1fr;
  }
  .composer-shell {
    bottom: 0;
    padding: 12px 14px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .chat-workbench,
  .session-rail {
    transition: none;
  }
}
</style>
