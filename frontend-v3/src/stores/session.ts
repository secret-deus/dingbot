import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Session } from '@/types'
import { sessionApi } from '@/api/client'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const loading = ref(false)

  async function fetchSessions() {
    loading.value = true
    try {
      sessions.value = await sessionApi.list()
    } finally {
      loading.value = false
    }
  }

  async function createSession(title = '新对话', skillId?: string) {
    const res = await sessionApi.create(title, skillId)
    await fetchSessions()
    return res.id
  }

  async function deleteSession(id: string) {
    await sessionApi.delete(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
  }

  return { sessions, loading, fetchSessions, createSession, deleteSession }
})
