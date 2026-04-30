/**
 * 认证相关工具函数
 */
import { ref } from 'vue'

// 登录状态key
const AUTH_KEY = 'isAuthenticated'
const LOGIN_TIME_KEY = 'loginTime'

// 登录有效期（24小时）
const LOGIN_EXPIRE_TIME = 24 * 60 * 60 * 1000

// 响应式的登录状态
export const authState = ref(false)

/**
 * 检查是否已登录
 * @returns {boolean}
 */
export function isAuthenticated() {
  const isAuth = localStorage.getItem(AUTH_KEY)
  const loginTime = localStorage.getItem(LOGIN_TIME_KEY)
  
  if (!isAuth || !loginTime) {
    authState.value = false
    return false
  }
  
  // 检查登录是否过期
  const now = Date.now()
  const loginTimestamp = parseInt(loginTime)
  
  if (now - loginTimestamp > LOGIN_EXPIRE_TIME) {
    // 登录已过期，清除状态
    logout()
    return false
  }
  
  const authenticated = isAuth === 'true'
  authState.value = authenticated
  return authenticated
}

/**
 * 设置登录状态
 */
export function setAuthenticated() {
  localStorage.setItem(AUTH_KEY, 'true')
  localStorage.setItem(LOGIN_TIME_KEY, Date.now().toString())
  authState.value = true
}

/**
 * 退出登录
 */
export function logout() {
  localStorage.removeItem(AUTH_KEY)
  localStorage.removeItem(LOGIN_TIME_KEY)
  authState.value = false
}

/**
 * 获取剩余登录时间（毫秒）
 * @returns {number}
 */
export function getRemainingTime() {
  const loginTime = localStorage.getItem(LOGIN_TIME_KEY)
  if (!loginTime) {
    return 0
  }
  
  const now = Date.now()
  const loginTimestamp = parseInt(loginTime)
  const remaining = LOGIN_EXPIRE_TIME - (now - loginTimestamp)
  
  return Math.max(0, remaining)
}

/**
 * 刷新登录时间
 */
export function refreshLoginTime() {
  if (isAuthenticated()) {
    localStorage.setItem(LOGIN_TIME_KEY, Date.now().toString())
  }
}

/**
 * 初始化认证状态
 */
export function initAuthState() {
  // 页面加载时检查登录状态
  isAuthenticated()
}
