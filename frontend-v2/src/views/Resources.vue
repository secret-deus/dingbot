<template>
  <div class="resources-page">
    <div class="page-header">
      <h1 class="page-title">资源管理</h1>
      <p class="page-subtitle">管理K8s集群资源和应用部署</p>
    </div>
    
    <div class="resources-container">
      <div class="resources-placeholder">
        <el-icon class="placeholder-icon"><Box /></el-icon>
        <h3>资源管理</h3>
        <p>Pod、Service、Deployment等资源管理</p>
        <div class="resource-types">
          <div class="resource-type">
            <el-icon><Grid /></el-icon>
            <span>Pods</span>
          </div>
          <div class="resource-type">
            <el-icon><Connection /></el-icon>
            <span>Services</span>
          </div>
          <div class="resource-type">
            <el-icon><Cpu /></el-icon>
            <span>Deployments</span>
          </div>
          <div class="resource-type">
            <el-icon><Files /></el-icon>
            <span>ConfigMaps</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Box, Grid, Connection, Cpu, Files } from '@element-plus/icons-vue'
</script>

<style scoped>
.resources-page {
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

.resources-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.resources-placeholder {
  text-align: center;
  padding: var(--spacing-2xl);
}

.placeholder-icon {
  font-size: 4rem;
  color: var(--primary-color);
  margin-bottom: var(--spacing-lg);
}

.resources-placeholder h3 {
  font-size: 1.5rem;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.resources-placeholder p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.resource-types {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.resource-type {
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

.resource-type:hover {
  background: var(--primary-color);
  color: white;
  transform: translateY(-2px);
}

.resource-type .el-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.resource-type:hover .el-icon {
  color: white;
}
</style>

