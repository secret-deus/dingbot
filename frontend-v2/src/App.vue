<template>
  <div id="app" class="app-container">
    <!-- 只有登录后才显示主布局 -->
    <div v-if="showMainLayout">
      <!-- 导航栏 -->
      <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside 
        :width="sidebarWidth" 
        class="sidebar"
        :class="{ 'sidebar-hidden': sidebarState === 'hidden' }"
      >
        <div class="logo-container">
          <img 
            src="/src/assets/images/logo.png" 
            alt="Logo" 
            class="logo"
            :class="{ 'logo-hidden': sidebarState === 'hidden' }"
          >
          <span 
            class="logo-text"
            :class="{ 'logo-text-hidden': sidebarState === 'hidden' }"
          >钉钉运维机器人</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :collapse="false"
          :unique-opened="true"
          router
          class="sidebar-menu"
          :class="{ 'sidebar-menu-hidden': sidebarState === 'hidden' }"
          background-color="#1E293B"
          text-color="rgba(255, 255, 255, 0.8)"
          active-text-color="#FFFFFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表板</template>
          </el-menu-item>
          
          <el-menu-item index="/chat">
            <el-icon><ChatDotSquare /></el-icon>
            <template #title>智能对话</template>
          </el-menu-item>
          
          <el-menu-item index="/mcp-config">
            <el-icon><Tools /></el-icon>
            <template #title>MCP配置</template>
          </el-menu-item>
          
          <el-menu-item index="/scheduler">
            <el-icon><Timer /></el-icon>
            <template #title>定时任务</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 头部 -->
        <el-header class="header">
          <div class="header-left">
            <el-button
              type="text"
              @click="toggleGlobalSidebar"
              class="sidebar-toggle"
            >
              <el-icon><Fold v-if="sidebarState === 'expanded'" /><Expand v-else /></el-icon>
            </el-button>
            
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item>{{ breadcrumbTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-dropdown @command="handleUserCommand">
              <span class="user-dropdown">
                <el-avatar :size="32" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="username">管理员</span>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 主体内容 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
    </div>
    
    <!-- 隐藏侧边栏时的浮动按钮 -->
    <el-button
      v-if="showMainLayout && sidebarState === 'hidden'"
      class="float-sidebar-toggle"
      type="primary"
      circle
      @click="toggleGlobalSidebar"
      title="展开侧边栏"
    >
      <el-icon><Expand /></el-icon>
    </el-button>

    <!-- 未登录时显示路由视图（登录页） -->
    <div v-else>
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer,
  ChatDotSquare,
  Setting,
  Tools,
  Timer,
  Fold,
  Expand,
  User,
  ArrowDown
} from '@element-plus/icons-vue'

// 响应式数据
const sidebarState = ref('expanded') // 'expanded' 或 'hidden'
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 计算属性
const activeMenu = computed(() => route.path)

const showMainLayout = computed(() => {
  return authStore.isAuthenticated && route.path !== '/login'
})

const breadcrumbTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表板',
    '/chat': '智能对话',
    '/mcp-config': 'MCP配置',
    '/scheduler': '定时任务'
  }
  return titles[route.path] || '钉钉K8s运维机器人'
})

const sidebarWidth = computed(() => {
  return sidebarState.value === 'expanded' ? '200px' : '0px'
})

// 方法
const toggleGlobalSidebar = () => {
  console.log('切换侧边栏状态，当前:', sidebarState.value)
  sidebarState.value = sidebarState.value === 'expanded' ? 'hidden' : 'expanded'
  console.log('切换后状态:', sidebarState.value)
  localStorage.setItem('layout.sidebarState', sidebarState.value)
}

const loadSidebarState = () => {
  const saved = localStorage.getItem('layout.sidebarState')
  // 兼容旧的两态值（collapsed/expanded），转换为新的两态（hidden/expanded）
  if (saved === 'expanded' || saved === 'collapsed' || saved === null) {
    sidebarState.value = saved === 'collapsed' ? 'hidden' : 'expanded'
  } else if (saved === 'hidden') {
    sidebarState.value = 'hidden'
  } else {
    sidebarState.value = 'expanded'
  }
  localStorage.setItem('layout.sidebarState', sidebarState.value)
}

const handleUserCommand = async (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人设置功能开发中...')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '退出确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        // 执行退出登录
        authStore.logout()
        ElMessage.success('已退出登录')
        
        // 跳转到登录页
        router.push('/login')
      } catch {
        // 用户取消退出
      }
      break
  }
}

// 监听路由变化
watch(route, (newRoute) => {
  console.log('路由变化:', newRoute.path)
})

// 组件挂载时初始化认证状态
onMounted(() => {
  authStore.initAuth()
  loadSidebarState()
})
</script>

<style scoped>
/* === 极简黑白设计 === */
.app-container {
  height: 100vh;
  overflow: hidden;
  background: var(--background-page);
}

.layout-container {
  height: 100vh;
}

/* === 侧边栏 - 深色主题 === */
.sidebar {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  color: var(--sidebar-text);
  box-shadow: none;
  position: relative;
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /* 使用更平滑的缓动函数和更长的过渡时间 */
  transition: width 0.6s cubic-bezier(0.23, 1, 0.32, 1), 
              opacity 0.5s cubic-bezier(0.23, 1, 0.32, 1),
              transform 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  will-change: width, opacity, transform;
}

.sidebar-hidden {
  opacity: 0;
  pointer-events: none;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
  overflow: hidden;
  transition: opacity 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.1s;
}

.logo {
  width: 32px;
  height: 32px;
  margin-right: 10px;
  border-radius: var(--border-radius-small);
  object-fit: contain;
  transition: opacity 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.15s,
              transform 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.15s,
              margin-right 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

.logo-hidden {
  opacity: 0;
  transform: translateX(-15px);
  margin-right: 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--sidebar-text);
  letter-spacing: -0.2px;
  white-space: nowrap;
  transition: opacity 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.2s,
              transform 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.2s,
              width 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.2s,
              margin 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.2s;
  overflow: hidden;
}

.logo-text-hidden {
  opacity: 0;
  transform: translateX(-20px);
  width: 0;
  margin: 0;
}

.sidebar-menu {
  border: none;
  background: transparent;
  padding: 12px 0;
  flex-grow: 1;
  overflow-y: auto;
  overflow-x: hidden;
  transition: opacity 0.4s cubic-bezier(0.23, 1, 0.32, 1) 0.25s;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.sidebar-menu-hidden {
  opacity: 0;
}

.sidebar-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  color: var(--sidebar-text);
  font-size: 14px;
  padding: 0 20px !important;
  margin: 4px 8px;
  border-radius: var(--border-radius-base);
  width: calc(100% - 16px);
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  position: relative;
  overflow: hidden;
  opacity: 1;
  transform: translateX(0);
}

.sidebar-hidden .sidebar-menu .el-menu-item {
  opacity: 0;
  transform: translateX(-25px);
  transition-delay: 0s;
}

.sidebar-menu .el-menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 100%;
  background: var(--sidebar-active);
  transform: scaleY(0);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center;
}

.sidebar-menu .el-menu-item.is-active::before {
  transform: scaleY(1);
}

.sidebar-menu .el-menu-item.is-active {
  background-color: var(--sidebar-active) !important;
  color: var(--text-white) !important;
  font-weight: 500;
  transform: translateX(2px);
}

.sidebar-menu .el-menu-item:hover {
  background-color: var(--sidebar-hover) !important;
  color: var(--sidebar-text) !important;
  transform: translateX(2px);
}

.sidebar-menu .el-menu-item.is-active:hover {
  color: var(--text-white) !important;
}

.sidebar-menu .el-menu-item .el-icon {
  color: var(--sidebar-text-secondary);
  font-size: 18px;
  margin-right: 8px;
  transition: color 0.25s ease, transform 0.25s ease;
}

.sidebar-menu .el-menu-item:hover .el-icon {
  transform: scale(1.1);
}

.sidebar-menu .el-menu-item.is-active .el-icon {
  color: var(--text-white);
}

/* === 顶部导航栏 - 极简设计 === */
.header {
  background: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: var(--header-shadow);
  position: relative;
  z-index: 99;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sidebar-toggle {
  font-size: 18px;
  color: var(--text-secondary);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 8px;
  border-radius: var(--border-radius-small);
  cursor: pointer;
  position: relative;
}

.sidebar-toggle::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--border-radius-small);
  background: var(--background-hover);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.sidebar-toggle:hover {
  background: var(--background-hover);
  color: var(--text-primary);
  transform: scale(1.05);
}

.sidebar-toggle:active {
  transform: scale(0.95);
}

.breadcrumb {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--border-radius-base);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border-base);
  background: var(--background-base);
}

.user-dropdown:hover {
  background: var(--background-hover);
  border-color: var(--border-dark);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.user-dropdown:active {
  transform: translateY(0);
}

.user-avatar {
  margin-right: 8px;
}

.username {
  margin-right: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
}

.dropdown-icon {
  color: var(--text-secondary);
  font-size: 12px;
  transition: transform 0.2s ease;
}

.user-dropdown:hover .dropdown-icon {
  transform: translateY(2px);
}

/* === 主内容区 - 极简设计 === */
.main-content {
  background: var(--background-page);
  padding: 24px;
  overflow-y: auto;
}

/* === 路由过渡动画 - 丝滑 === */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 浮动按钮样式 */
.float-sidebar-toggle {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 101;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  box-shadow: var(--shadow-md);
  background-color: var(--primary-color);
  color: var(--text-white);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: floatIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: scale(0.8) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.float-sidebar-toggle:hover {
  transform: scale(1.1) translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.float-sidebar-toggle:active {
  transform: scale(0.95) translateY(0);
}

/* === 响应式优化 === */
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }

  .main-content {
    padding: 16px;
  }

  .username {
    display: none;
  }
}
</style> 