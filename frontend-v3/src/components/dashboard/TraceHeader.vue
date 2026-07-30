<template>
  <header class="trace-titlebar">
    <div class="trace-title">
      <h1>{{ title }}</h1>
      <span class="trace-label">
        <span class="label-icon" aria-hidden="true">◇</span>
        live-summary
      </span>
    </div>
    <button class="trace-refresh" type="button" :disabled="refreshing" @click="$emit('refresh')">
      <n-icon><RefreshOutline /></n-icon>
      {{ refreshing ? 'Refreshing' : 'Refresh' }}
    </button>
  </header>
</template>

<script setup lang="ts">
import { NIcon } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'

defineProps<{
  title: string
  refreshing: boolean
}>()

defineEmits<{
  refresh: []
}>()
</script>
