<template>
  <div id="app" class="app-container">
    <!-- 导航栏 -->
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
        <div class="logo-container">
          <img src="/src/assets/images/logo.png" alt="Logo" class="logo" v-if="!isCollapse">
          <span class="logo-text" v-if="!isCollapse">钉钉运维机器人</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="true"
          router
          class="sidebar-menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表板</template>
          </el-menu-item>
          
          <el-menu-item index="/chat">
            <el-icon><ChatDotSquare /></el-icon>
            <template #title>智能对话</template>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>配置管理</template>
          </el-menu-item>
          
          <el-menu-item index="/mcp-config">
            <el-icon><Tools /></el-icon>
            <template #title>MCP配置</template>
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
              @click="toggleSidebar"
              class="sidebar-toggle"
            >
              <el-icon><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
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
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Odometer,
  ChatDotSquare,
  Setting,
  Tools,
  Fold,
  Expand,
  User,
  ArrowDown
} from '@element-plus/icons-vue'

// 响应式数据
const isCollapse = ref(false)
const route = useRoute()

// 计算属性
const activeMenu = computed(() => route.path)

const breadcrumbTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表板',
    '/chat': '智能对话',
    '/settings': '配置管理'
  }
  return titles[route.path] || '钉钉K8s运维机器人'
})

// 方法
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      console.log('打开个人设置')
      break
    case 'logout':
      console.log('退出登录')
      break
  }
}

// 监听路由变化
watch(route, (newRoute) => {
  console.log('路由变化:', newRoute.path)
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: #bfcbd9;
  transition: width 0.3s ease;
}

.logo-container {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  background-color: #2b3442;
}

.logo {
  width: 36px;
  height: 36px;
  margin-right: 12px;
  border-radius: 6px;
  object-fit: contain;
}

.logo-text {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
}

.sidebar-menu {
  border: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.sidebar-toggle {
  font-size: 18px;
  margin-right: 20px;
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.user-avatar {
  margin-right: 8px;
}

.username {
  margin-right: 8px;
  color: #303133;
  font-size: 14px;
}

.dropdown-icon {
  color: #909399;
  font-size: 12px;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 路由动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style> 