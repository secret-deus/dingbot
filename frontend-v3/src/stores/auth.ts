import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref('')
  const role = ref('viewer')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isOperator = computed(() => role.value === 'operator' || role.value === 'admin')

  async function login(user: string, password: string) {
    const res = await authApi.login(user, password)
    token.value = res.access_token
    username.value = res.username
    role.value = res.role
    localStorage.setItem('token', res.access_token)
  }

  async function fetchMe() {
    try {
      const res = await authApi.me()
      username.value = res.username
      role.value = res.role
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = 'viewer'
    localStorage.removeItem('token')
  }

  return { token, username, role, isLoggedIn, isAdmin, isOperator, login, fetchMe, logout }
})
