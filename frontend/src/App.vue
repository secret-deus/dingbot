<template>
  <div id="app" class="app-container">
    <!-- 只有登录后才显示主布局 -->
    <div v-if="showMainLayout">
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
const isCollapse = ref(false)
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

// 方法
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
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
  background-color: #1E293B;
  color: rgba(255, 255, 255, 0.8);
  transition: width 0.3s ease;
  border-right: none;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.logo-container {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  background-color: #0F172A;
  border-bottom: 1px solid #334155;
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
  font-weight: 600;
  color: #FFFFFF;
  font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}

.sidebar-menu {
  border: none;
}

.header {
  background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
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
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.user-dropdown:hover {
  background-color: rgba(64, 158, 255, 0.08);
  border-color: rgba(64, 158, 255, 0.2);
  transform: translateY(-1px);
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
  background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
  padding: 24px;
  overflow-y: auto;
  position: relative;
}

.main-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(64, 158, 255, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(103, 194, 58, 0.03) 0%, transparent 50%);
  pointer-events: none;
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