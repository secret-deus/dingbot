<template>
  <div class="monitoring-page">
    <div class="page-header">
      <h1 class="page-title">监控中心</h1>
      <p class="page-subtitle">实时监控集群状态和性能指标</p>
    </div>
    
    <div class="monitoring-container">
      <div class="monitoring-placeholder">
        <el-icon class="placeholder-icon"><Monitor /></el-icon>
        <h3>监控中心</h3>
        <p>集群监控、告警管理、性能分析</p>
        <div class="feature-list">
          <div class="feature-item">
            <el-icon><TrendCharts /></el-icon>
            <span>性能监控</span>
          </div>
          <div class="feature-item">
            <el-icon><Bell /></el-icon>
            <span>告警管理</span>
          </div>
          <div class="feature-item">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据分析</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Monitor, TrendCharts, Bell, DataAnalysis } from '@element-plus/icons-vue'
</script>

<style scoped>
.monitoring-page {
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

.monitoring-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.monitoring-placeholder {
  text-align: center;
  padding: var(--spacing-2xl);
}

.placeholder-icon {
  font-size: 4rem;
  color: var(--primary-color);
  margin-bottom: var(--spacing-lg);
}

.monitoring-placeholder h3 {
  font-size: 1.5rem;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.monitoring-placeholder p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.feature-list {
  display: flex;
  justify-content: center;
  gap: var(--spacing-xl);
  margin-top: var(--spacing-lg);
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.feature-item .el-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
}
</style>

