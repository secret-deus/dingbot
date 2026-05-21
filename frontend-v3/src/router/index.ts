import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录', requiresAuth: false },
    },
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '运维概览', icon: 'speedometer-outline', requiresAuth: true, fullBleed: true },
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/Chat.vue'),
      meta: { title: '智能对话', icon: 'chatbubbles-outline', requiresAuth: true, fullBleed: true },
    },
    {
      path: '/mcp-config',
      name: 'MCPConfig',
      component: () => import('@/views/MCPConfig.vue'),
      meta: { title: 'MCP 工具', icon: 'construct-outline', requiresAuth: true },
    },
    {
      path: '/knowledge-graph',
      name: 'KnowledgeGraph',
      component: () => import('@/views/KnowledgeGraph.vue'),
      meta: { title: '知识图谱', icon: 'git-network-outline', requiresAuth: true },
    },
    {
      path: '/llm-config',
      name: 'LLMConfig',
      component: () => import('@/views/LLMConfig.vue'),
      meta: { title: 'LLM 配置', icon: 'settings-outline', requiresAuth: true },
    },
    {
      path: '/scheduler',
      name: 'Scheduler',
      component: () => import('@/views/Scheduler.vue'),
      meta: { title: '定时任务', icon: 'time-outline', requiresAuth: true, permission: 'operator' },
    },
    {
      path: '/access-control',
      name: 'AccessControl',
      component: () => import('@/views/AccessControl.vue'),
      meta: { title: '权限管理', icon: 'shield-outline', requiresAuth: true, permission: 'admin' },
    },
    {
      path: '/audit-logs',
      name: 'AuditLogs',
      component: () => import('@/views/AccessControl.vue'),
      meta: { title: '审计日志', icon: 'document-text-outline', requiresAuth: true, permission: 'admin' },
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title || '运维机器人'} - 钉钉K8s`

  const auth = useAuthStore()
  if (auth.isLoggedIn && !auth.username) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth !== false && !auth.isLoggedIn) {
    return next({ name: 'Login' })
  }

  if (to.meta.permission === 'admin' && !auth.isAdmin) {
    return next({ name: 'Dashboard' })
  }
  if (to.meta.permission === 'operator' && !auth.isOperator) {
    return next({ name: 'Dashboard' })
  }

  next()
})

export default router
