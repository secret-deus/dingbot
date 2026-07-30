<template>
  <section class="llm-panel providers-panel">
    <div class="panel-title-row">
      <div>
        <span class="panel-kicker">Providers</span>
        <div class="panel-title">模型配置</div>
        <div class="panel-subtitle">{{ providers.length }} 个配置，{{ activeProviderCount }} 个可用</div>
      </div>
      <n-button size="small" type="primary" :disabled="readOnly || busy" @click="$emit('create')">新增</n-button>
    </div>

    <div class="provider-list">
      <button
        v-for="provider in providers"
        :key="provider.id"
        :class="['provider-item', { active: provider.id === selectedProviderId }]"
        type="button"
        @click="$emit('select', provider.id)"
      >
        <span :class="['provider-dot', provider.enabled && provider.api_key_configured ? 'green' : 'muted']" />
        <span class="provider-main">
          <span class="provider-name">{{ provider.name || provider.id }}</span>
          <span class="provider-model">{{ provider.model || '未填写模型' }}</span>
          <span class="provider-url">{{ provider.base_url || 'default OpenAI-compatible endpoint' }}</span>
        </span>
        <span class="provider-tags">
          <span v-if="provider.id === defaultProviderId" class="mini-badge blue">默认</span>
          <span :class="['mini-badge', provider.enabled && provider.api_key_configured ? 'green' : 'muted']">
            {{ provider.enabled && provider.api_key_configured ? '可用' : '未就绪' }}
          </span>
        </span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'
import type { LLMProviderConfig } from '@/types'

defineProps<{
  providers: LLMProviderConfig[]
  selectedProviderId: string
  defaultProviderId?: string
  activeProviderCount: number
  readOnly: boolean
  busy: boolean
}>()

defineEmits<{
  create: []
  select: [providerId: string]
}>()
</script>
