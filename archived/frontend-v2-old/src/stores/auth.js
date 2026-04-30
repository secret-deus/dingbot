/**
 * 后端用户系统认证 Store
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api, AUTH_TOKEN_KEY } from '@/api/client'

const AUTH_USER_KEY = 'auth.user'

const readStoredUser = () => {
  try {
    const raw = localStorage.getItem(AUTH_USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(AUTH_TOKEN_KEY) || '')
  const user = ref(readStoredUser())
  const initialized = ref(false)
  const initializing = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const username = computed(() => user.value?.username || '')
  const displayName = computed(() => user.value?.display_name || user.value?.username || '管理员')
  const roles = computed(() => user.value?.roles || [])
  const permissions = computed(() => user.value?.permissions || [])

  const persistSession = (accessToken, nextUser) => {
    token.value = accessToken
    user.value = nextUser
    if (accessToken) {
      localStorage.setItem(AUTH_TOKEN_KEY, accessToken)
    } else {
      localStorage.removeItem(AUTH_TOKEN_KEY)
    }
    if (nextUser) {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(nextUser))
    } else {
      localStorage.removeItem(AUTH_USER_KEY)
    }
  }

  const clearLegacyAuth = () => {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('loginTime')
  }

  const login = async ({ username: nextUsername = 'admin', password }) => {
    const { data } = await api.auth.login({
      username: nextUsername,
      password
    })
    persistSession(data.access_token, data.user)
    clearLegacyAuth()
    initialized.value = true
    return data.user
  }

  const logout = async () => {
    try {
      if (token.value) {
        await api.auth.logout()
      }
    } finally {
      persistSession('', null)
      clearLegacyAuth()
      initialized.value = true
    }
  }

  const clearSession = () => {
    persistSession('', null)
    clearLegacyAuth()
    initialized.value = true
    initializing.value = false
  }

  const initAuth = async () => {
    if (initialized.value || initializing.value) {
      return isAuthenticated.value
    }
    initializing.value = true
    try {
      if (!token.value) {
        persistSession('', null)
        return false
      }
      const { data } = await api.auth.me()
      persistSession(token.value, data.user)
      return true
    } catch {
      clearSession()
      return false
    } finally {
      initialized.value = true
      initializing.value = false
    }
  }

  const hasPermission = (permission) => {
    if (!permission) return true
    return permissions.value.includes('*') || permissions.value.includes(permission)
  }

  const hasAnyPermission = (items = []) => {
    return items.some((item) => hasPermission(item))
  }

  return {
    token,
    user,
    initialized,
    initializing,
    isAuthenticated,
    username,
    displayName,
    roles,
    permissions,
    login,
    logout,
    clearSession,
    initAuth,
    hasPermission,
    hasAnyPermission
  }
})
