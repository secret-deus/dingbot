<template>
  <section class="llm-status-strip" aria-label="LLM 运行状态">
    <article class="status-tile">
      <span>Runtime</span>
      <strong>{{ statusText }}</strong>
      <small>{{ active ? 'new chats use active config' : 'configuration needs attention' }}</small>
    </article>
    <article class="status-tile">
      <span>Available providers</span>
      <strong>{{ activeProviderCount }}/{{ providerCount }}</strong>
      <small>{{ activeProviderCount ? 'ready for chat routing' : 'no usable API key' }}</small>
    </article>
    <article class="status-tile wide">
      <span>Default model</span>
      <strong>{{ defaultProviderName }}</strong>
      <small>selected provider for new conversations</small>
    </article>
    <article class="status-tile">
      <span>Config source</span>
      <strong>{{ source || '-' }}</strong>
      <small>local runtime file</small>
    </article>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  statusText: string
  active: boolean
  activeProviderCount: number
  providerCount: number
  defaultProviderName: string
  source?: string
}>()
</script>
