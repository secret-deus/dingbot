/**
 * 认证状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const isLoggedIn = ref(false)
  const loginTime = ref(null)
  
  // 常量
  const AUTH_KEY = 'isAuthenticated'
  const LOGIN_TIME_KEY = 'loginTime'
  const LOGIN_EXPIRE_TIME = 24 * 60 * 60 * 1000 // 24小时
  
  // 计算属性
  const isAuthenticated = computed(() => {
    if (!isLoggedIn.value || !loginTime.value) {
      return false
    }
    
    // 检查是否过期
    const now = Date.now()
    if (now - loginTime.value > LOGIN_EXPIRE_TIME) {
      logout()
      return false
    }
    
    return true
  })
  
  // 方法
  const login = (password) => {
    // 这里可以添加密码验证逻辑
    const DEFAULT_PASSWORD = import.meta.env.VITE_ACCESS_PASSWORD || 'ding2024'
    
    if (password === DEFAULT_PASSWORD) {
      const now = Date.now()
      isLoggedIn.value = true
      loginTime.value = now
      
      // 持久化到localStorage
      localStorage.setItem(AUTH_KEY, 'true')
      localStorage.setItem(LOGIN_TIME_KEY, now.toString())
      
      return true
    }
    
    return false
  }
  
  const logout = () => {
    isLoggedIn.value = false
    loginTime.value = null
    
    // 清除localStorage
    localStorage.removeItem(AUTH_KEY)
    localStorage.removeItem(LOGIN_TIME_KEY)
  }
  
  const initAuth = () => {
    // 从localStorage恢复状态
    const authValue = localStorage.getItem(AUTH_KEY)
    const timeValue = localStorage.getItem(LOGIN_TIME_KEY)
    
    if (authValue === 'true' && timeValue) {
      const storedTime = parseInt(timeValue)
      const now = Date.now()
      
      if (now - storedTime <= LOGIN_EXPIRE_TIME) {
        isLoggedIn.value = true
        loginTime.value = storedTime
      } else {
        // 过期了，清除状态
        logout()
      }
    }
  }
  
  const refreshLoginTime = () => {
    if (isLoggedIn.value) {
      const now = Date.now()
      loginTime.value = now
      localStorage.setItem(LOGIN_TIME_KEY, now.toString())
    }
  }
  
  return {
    // 状态
    isLoggedIn,
    loginTime,
    
    // 计算属性
    isAuthenticated,
    
    // 方法
    login,
    logout,
    initAuth,
    refreshLoginTime
  }
})
