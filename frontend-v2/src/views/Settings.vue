<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-subtitle">配置系统参数和用户偏好</p>
    </div>
    
    <div class="settings-container">
      <div class="settings-placeholder">
        <el-icon class="placeholder-icon"><Setting /></el-icon>
        <h3>系统设置</h3>
        <p>LLM配置、MCP设置、用户偏好等</p>
        <div class="settings-categories">
          <div class="category-item">
            <el-icon><ChatDotRound /></el-icon>
            <span>LLM配置</span>
          </div>
          <div class="category-item">
            <el-icon><Connection /></el-icon>
            <span>MCP设置</span>
          </div>
          <div class="category-item">
            <el-icon><User /></el-icon>
            <span>用户偏好</span>
          </div>
          <div class="category-item">
            <el-icon><Key /></el-icon>
            <span>安全设置</span>
          </div>
        </div>
        <el-button type="primary" @click="openSettings">
          打开设置面板
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, ChatDotRound, Connection, User, Key } from '@element-plus/icons-vue'

const openSettings = () => {
  ElMessage.info('设置功能正在开发中，敬请期待！')
}
</script>

<style scoped>
.settings-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
}

.settings-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.settings-placeholder {
  text-align: center;
  padding: var(--spacing-2xl);
}

.placeholder-icon {
  font-size: 4rem;
  color: var(--primary-color);
  margin-bottom: var(--spacing-lg);
}

.settings-placeholder h3 {
  font-size: 1.5rem;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.settings-placeholder p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.settings-categories {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  margin: var(--spacing-lg) 0;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 0.875rem;
  transition: all 0.3s ease;
  cursor: pointer;
}

.category-item:hover {
  background: var(--primary-color);
  color: white;
  transform: translateY(-2px);
}

.category-item .el-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.category-item:hover .el-icon {
  color: white;
}
</style>
