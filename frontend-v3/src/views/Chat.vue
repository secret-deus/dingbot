<template>
  <div class="chat-workbench">
    <aside class="session-rail">
      <div class="rail-head">
        <div>
          <div class="rail-title">对话</div>
          <div class="rail-subtitle">{{ sessionStore.sessions.length }} 个会话</div>
        </div>
        <n-button size="small" tertiary round @click="newSession">新建</n-button>
      </div>
      <n-spin v-if="sessionStore.loading" />
      <div v-else class="session-list">
        <div
          v-for="s in sessionStore.sessions"
          :key="s.id"
          :class="['session-row', { active: s.id === chatStore.activeSessionId }]"
        >
          <button class="session-item" type="button" @click="selectSession(s.id)">
            <span class="session-title">{{ s.title }}</span>
            <span class="session-time">{{ s.updated_at?.slice(0, 16) }}</span>
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
              <MessageBubble :message="{ id: 'streaming', role: 'assistant', content: chatStore.streamingContent, tool_calls: chatStore.streamingToolCalls, tool_results: chatStore.streamingToolResults, created_at: '' }" />
              <n-spin size="small" />
            </div>
          </div>
        </template>
      </main>

      <footer v-if="chatStore.activeSessionId" class="composer-shell">
        <ChatInput :disabled="chatStore.streaming" @send="onSend" />
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { NButton, NIcon, NPopconfirm, NSelect, NSpin, NSwitch } from 'naive-ui'
import { useSessionStore } from '@/stores/session'
import { useChatStore } from '@/stores/chat'
import { systemApi } from '@/api/client'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import { SSE } from 'sse.js'
import type { LLMConfig } from '@/types'
import { TrashOutline } from '@vicons/ionicons5'

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const messageListRef = ref<HTMLElement>()
const llmConfig = ref<LLMConfig | null>(null)

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

watch(() => chatStore.messages.length, () => nextTick(scrollToBottom))

function onSend(content: string) {
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

  sse.addEventListener('token', (e: any) => {
    const data = JSON.parse(e.data)
    chatStore.appendStream(data.content)
    nextTick(scrollToBottom)
  })

  sse.addEventListener('tool_call', (e: any) => {
    const data = JSON.parse(e.data)
    if (data.tool_call) {
      chatStore.addStreamingToolCall(data.tool_call)
      nextTick(scrollToBottom)
    }
  })

  sse.addEventListener('tool_result', (e: any) => {
    const data = JSON.parse(e.data)
    if (data.tool_call_id) {
      chatStore.addStreamingToolResult(data.tool_call_id, data.result)
      nextTick(scrollToBottom)
    }
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
.chat-workbench {
  height: 100%;
  display: grid;
  grid-template-columns: 276px minmax(0, 1fr);
  background: #111113;
}
.session-rail {
  min-width: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  background: #18181b;
  padding: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rail-head,
.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.rail-title {
  font-size: 15px;
  font-weight: 650;
}
.rail-subtitle,
.chat-subtitle,
.session-time {
  color: #8f9299;
  font-size: 12px;
}
.session-list {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.session-row {
  width: 100%;
  min-height: 58px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  align-items: center;
  overflow: hidden;
}
.session-row:hover {
  background: rgba(255, 255, 255, 0.05);
}
.session-row.active {
  background: rgba(70, 88, 116, 0.34);
  border-color: rgba(112, 132, 166, 0.45);
}
.session-item {
  min-width: 0;
  height: 100%;
  padding: 10px 4px 10px 12px;
  border: 0;
  background: transparent;
  color: #e7e7e9;
  text-align: left;
  cursor: pointer;
}
.session-delete {
  opacity: 0;
  color: #aeb3bd;
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
.chat-main {
  min-width: 0;
  height: 100%;
  display: grid;
  grid-template-rows: 64px minmax(0, 1fr) auto;
  background: #111113;
}
.chat-topbar {
  padding: 0 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}
.chat-title {
  font-size: 15px;
  font-weight: 650;
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
  color: #b8bbc2;
  font-size: 12px;
  font-weight: 400;
}
.message-scroll {
  min-height: 0;
  overflow-y: auto;
  padding: 28px 24px 20px;
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
  padding: 12px 24px 20px;
  background: linear-gradient(180deg, rgba(17, 17, 19, 0), #111113 26%);
}
.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: #d9dadd;
  gap: 12px;
}
.empty-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #263244;
  color: #eef2ff;
  font-weight: 700;
}
.empty-state h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 650;
}
.empty-state p {
  margin: 0 0 8px;
  color: #9ca3af;
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
}
</style>
