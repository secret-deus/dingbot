import { createRouter, createWebHistory } from 'vue-router'

// 路由组件懒加载
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Chat = () => import('@/views/Chat.vue')
const MCPConfig = () => import('@/views/MCPConfig.vue')
const Scheduler = () => import('@/views/Scheduler.vue')
const AccessControl = () => import('@/views/AccessControl.vue')
const AuditLogs = () => import('@/views/AuditLogs.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '仪表板',
      icon: 'Odometer',
      requiresAuth: true,
      permission: 'ops:read'
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: {
      title: '智能对话',
      icon: 'ChatDotSquare',
      requiresAuth: true,
      permission: 'chat:read'
    }
  },
  {
    path: '/mcp-config',
    name: 'MCPConfig',
    component: MCPConfig,
    meta: {
      title: 'MCP配置',
      icon: 'Tools',
      requiresAuth: true,
      permission: 'mcp:read'
    }
  },
  {
    path: '/scheduler',
    name: 'Scheduler',
    component: Scheduler,
    meta: {
      title: '定时任务',
      icon: 'Timer',
      requiresAuth: true,
      permission: 'scheduler:read'
    }
  },
  {
    path: '/access-control',
    name: 'AccessControl',
    component: AccessControl,
    meta: {
      title: '访问控制',
      icon: 'User',
      requiresAuth: true,
      permission: 'users:read'
    }
  },
  {
    path: '/audit-logs',
    name: 'AuditLogs',
    component: AuditLogs,
    meta: {
      title: '操作日志',
      icon: 'Document',
      requiresAuth: true,
      permission: 'audit:read'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 钉钉K8s运维机器人`
  } else {
    document.title = '钉钉K8s运维机器人'
  }

  // 动态导入auth store
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  await authStore.initAuth()

  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    // 默认需要认证，除非明确设置为false
    if (!authStore.isAuthenticated) {
      // 未登录，重定向到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    if (to.meta.permission && !authStore.hasPermission(to.meta.permission)) {
      next({ path: '/dashboard' })
      return
    }
  } else {
    // 不需要认证的页面（如登录页），如果已登录则重定向到首页
    if (to.path === '/login' && authStore.isAuthenticated) {
      next({ path: '/dashboard' })
      return
    }
  }

  next()
})

router.afterEach((to, from) => {
  // 路由切换后的处理
  console.log(`路由切换: ${from.path} -> ${to.path}`)
})

export default router
