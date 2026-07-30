import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Session } from '@/types'
import { sessionApi } from '@/api/client'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const loading = ref(false)
  const mutationLoading = ref(false)
  let fetchVersion = 0

  function invalidateSessionFetches() {
    fetchVersion += 1
    loading.value = false
  }

  async function fetchSessions(force = false) {
    if (mutationLoading.value && !force) return

    const version = ++fetchVersion
    loading.value = true
    try {
      const next = await sessionApi.list()
      if (version === fetchVersion) sessions.value = next
    } finally {
      if (version === fetchVersion) loading.value = false
    }
  }

  async function createSession(title = '新对话', skillId?: string) {
    if (mutationLoading.value) return ''

    mutationLoading.value = true
    invalidateSessionFetches()
    try {
      const res = await sessionApi.create(title, skillId)
      await fetchSessions(true)
      return res.id
    } finally {
      mutationLoading.value = false
    }
  }

  async function deleteSession(id: string) {
    if (mutationLoading.value) return false

    mutationLoading.value = true
    invalidateSessionFetches()
    try {
      await sessionApi.delete(id)
      sessions.value = sessions.value.filter((s) => s.id !== id)
      invalidateSessionFetches()
      return true
    } finally {
      mutationLoading.value = false
    }
  }

  return { sessions, loading, mutationLoading, fetchSessions, createSession, deleteSession }
})
