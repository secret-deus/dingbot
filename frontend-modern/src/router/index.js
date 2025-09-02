import { createRouter, createWebHistory } from 'vue-router'

// 路由组件懒加载
const Dashboard = () => import('@/views/Dashboard.vue')
const DashboardModern = () => import('@/views/DashboardModern.vue')
const Chat = () => import('@/views/Chat.vue')
const ChatModern = () => import('@/views/ChatModern.vue')
const Settings = () => import('@/views/Settings.vue')
const SettingsModern = () => import('@/views/SettingsModern.vue')
const MCPConfig = () => import('@/views/MCPConfig.vue')
const Scheduler = () => import('@/views/Scheduler.vue')

const routes = [
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
      icon: 'Odometer'
    }
  },
  {
    path: '/dashboard-modern',
    name: 'DashboardModern',
    component: DashboardModern,
    meta: {
      title: '仪表板 (现代版)',
      icon: 'Odometer'
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: {
      title: '智能对话',
      icon: 'ChatDotSquare'
    }
  },
  {
    path: '/chat-modern',
    name: 'ChatModern',
    component: ChatModern,
    meta: {
      title: '智能对话 (现代版)',
      icon: 'ChatDotSquare'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '配置管理',
      icon: 'Setting'
    }
  },
  {
    path: '/settings-modern',
    name: 'SettingsModern',
    component: SettingsModern,
    meta: {
      title: '配置管理 (现代版)',
      icon: 'Setting'
    }
  },
  {
    path: '/mcp-config',
    name: 'MCPConfig',
    component: MCPConfig,
    meta: {
      title: 'MCP配置',
      icon: 'Tools'
    }
  },
  {
    path: '/scheduler',
    name: 'Scheduler',
    component: Scheduler,
    meta: {
      title: '定时任务',
      icon: 'Timer'
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
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 钉钉K8s运维机器人`
  } else {
    document.title = '钉钉K8s运维机器人'
  }
  
  next()
})

router.afterEach((to, from) => {
  // 路由切换后的处理
  console.log(`路由切换: ${from.path} -> ${to.path}`)
})

export default router 