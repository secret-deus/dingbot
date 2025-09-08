<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 侧边栏 -->
      <el-aside width="260px" class="sidebar">
        <div class="sidebar-header">
          <div class="logo">
            <el-icon class="logo-icon"><Monitor /></el-icon>
            <span class="logo-text">K8s运维助手</span>
          </div>
        </div>
        
        <el-menu
          :default-active="$route.path"
          router
          class="sidebar-menu"
          background-color="transparent"
          text-color="#ffffff"
          active-text-color="#6366f1"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表板</span>
          </el-menu-item>
          
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能对话</span>
          </el-menu-item>
          
          <el-menu-item index="/monitoring">
            <el-icon><Monitor /></el-icon>
            <span>监控中心</span>
          </el-menu-item>
          
          <el-menu-item index="/resources">
            <el-icon><Box /></el-icon>
            <span>资源管理</span>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          
          <el-menu-item index="/api-test">
            <el-icon><Connection /></el-icon>
            <span>API测试</span>
          </el-menu-item>
        </el-menu>
        
        <div class="sidebar-footer">
          <div class="system-status">
            <div class="status-item">
              <span class="status-dot online"></span>
              <span class="status-text">系统正常</span>
            </div>
          </div>
        </div>
      </el-aside>
      
      <!-- 主内容区域 -->
      <el-container class="main-container">
        <!-- 顶部导航栏 -->
        <el-header height="64px" class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-button type="primary" @click="refreshData" :loading="refreshing">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            
            <el-dropdown trigger="click">
              <el-avatar :size="36" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>个人设置</el-dropdown-item>
                  <el-dropdown-item divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 页面内容 -->
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Monitor,
  Odometer,
  ChatDotRound,
  Box,
  Setting,
  Refresh,
  User,
  Connection
} from '@element-plus/icons-vue'

const route = useRoute()
const refreshing = ref(false)

const currentPageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表板',
    '/chat': '智能对话',
    '/monitoring': '监控中心',
    '/resources': '资源管理',
    '/settings': '系统设置'
  }
  return titles[route.path] || '未知页面'
})

const refreshData = async () => {
  refreshing.value = true
  // 模拟刷新操作
  setTimeout(() => {
    refreshing.value = false
  }, 1000)
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
  border-right: 1px solid #333333;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid #333333;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 600;
  color: #ffffff;
}

.sidebar-menu {
  flex: 1;
  border: none;
  padding: var(--spacing-md);
}

.sidebar-menu .el-menu-item {
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xs);
  height: 44px;
  line-height: 44px;
  color: #ffffff;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }
  
  &.is-active {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(99, 102, 241, 0.1) 100%);
    border-left: 3px solid var(--primary-color);
    color: #6366f1;
  }
}

.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid #333333;
}

.system-status {
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-md);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  
  &.online {
    background: var(--success-color);
  }
}

.status-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
}

.main-container {
  background: var(--bg-secondary);
}

.header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.user-avatar {
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
  }
}

.main-content {
  padding: var(--spacing-lg);
  overflow-y: auto;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
