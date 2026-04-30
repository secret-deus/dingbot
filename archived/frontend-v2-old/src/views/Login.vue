<template>
  <div class="login-container">
    <section class="login-stage">
      <div class="brand-panel">
        <div class="brand-mark">DO</div>
        <p class="eyebrow">DINGOPS COPILOT</p>
        <h1>云原生运维指挥台</h1>
        <p class="subtitle">统一登录、权限控制、操作留痕和只读诊断入口。</p>

        <div class="signal-grid">
          <div>
            <span class="signal-dot"></span>
            <strong>IAM</strong>
            <small>角色权限</small>
          </div>
          <div>
            <span class="signal-dot success"></span>
            <strong>AUDIT</strong>
            <small>全链路日志</small>
          </div>
          <div>
            <span class="signal-dot cyan"></span>
            <strong>MCP</strong>
            <small>本地工具</small>
          </div>
        </div>
      </div>

      <div class="login-card">
        <div class="login-header">
          <p>SECURE ACCESS</p>
          <h2>登录控制台</h2>
        </div>

        <el-form @submit.prevent="handleLogin" class="login-form">
          <el-form-item>
            <el-input
              v-model="username"
              placeholder="用户名"
              size="large"
              :disabled="loading"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-input
              v-model="password"
              type="password"
              placeholder="访问密码"
              size="large"
              show-password
              @keyup.enter="handleLogin"
              :disabled="loading"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-button"
              @click="handleLogin"
              :loading="loading"
            >
              进入指挥台
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <span>默认管理员：admin</span>
          <span>本地签名会话</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('admin')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!password.value.trim()) {
    ElMessage.warning('请输入访问密码')
    return
  }

  loading.value = true
  try {
    await authStore.login({
      username: username.value.trim(),
      password: password.value
    })
    ElMessage.success('登录成功')
    const redirect = router.currentRoute.value.query.redirect || '/dashboard'
    await router.replace(redirect)
  } catch (error) {
    const message = error?.response?.data?.error?.message || error?.response?.data?.detail || error?.message
    ElMessage.error(message || '登录失败，请检查用户名和密码')
    password.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--ops-bg);
  color: var(--ops-text);
}

.login-stage {
  width: min(1040px, 100%);
  min-height: 560px;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  overflow: hidden;
  background: color-mix(in srgb, var(--ops-surface) 88%, transparent);
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
}

.brand-panel {
  padding: 52px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-right: 1px solid rgba(148, 163, 184, 0.18);
  background: var(--ops-surface);
}

.brand-mark {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  border: 1px solid var(--ops-accent-border);
  border-radius: 8px;
  color: var(--ops-accent-strong);
  font-weight: 900;
  background: var(--ops-surface-selected);
  box-shadow: none;
}

.eyebrow,
.login-header p {
  margin: 28px 0 10px;
  color: var(--ops-muted);
  font-size: 12px;
  font-weight: 900;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  max-width: 540px;
  font-size: 48px;
  line-height: 1.05;
  font-weight: 900;
}

.subtitle {
  max-width: 460px;
  margin-top: 18px;
  color: var(--ops-text-soft);
  font-size: 16px;
  line-height: 1.8;
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 44px;
}

.signal-grid div {
  min-height: 96px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 8px;
  background: var(--ops-surface-raised);
}

.signal-dot {
  width: 9px;
  height: 9px;
  display: block;
  margin-bottom: 14px;
  border-radius: 999px;
  background: #f59e0b;
}

.signal-dot.success {
  background: var(--ops-success);
}

.signal-dot.cyan {
  background: var(--ops-accent);
}

.signal-grid strong,
.signal-grid small {
  display: block;
}

.signal-grid strong {
  font-size: 18px;
}

.signal-grid small {
  margin-top: 6px;
  color: var(--ops-muted);
}

.login-card {
  padding: 52px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(8, 12, 20, 0.82);
}

.login-header {
  margin-bottom: 28px;
}

.login-header p {
  margin-top: 0;
}

.login-header h2 {
  font-size: 28px;
  font-weight: 900;
}

.login-form :deep(.el-input__wrapper) {
  height: 46px;
  border: 1px solid #25324a;
  border-radius: 8px;
  background: #08111f;
  box-shadow: none;
}

.login-form :deep(.el-input__inner) {
  color: #e6edf7;
}

.login-button {
  width: 100%;
  height: 46px;
  border-radius: 8px;
  border-color: var(--ops-accent-border);
  background: var(--ops-accent-soft);
  color: var(--ops-accent-strong);
  font-weight: 900;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  color: #607089;
  font-size: 12px;
}

@media (max-width: 820px) {
  .login-stage {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    padding: 32px;
    border-right: none;
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  }

  h1 {
    font-size: 34px;
  }

  .signal-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .login-container {
    padding: 12px;
  }

  .login-card {
    padding: 28px 20px;
  }
}
</style>
