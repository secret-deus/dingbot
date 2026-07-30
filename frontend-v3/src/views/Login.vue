<template>
  <div class="login-shell">
    <section class="login-card" aria-labelledby="login-title">
      <div class="window-dots" aria-hidden="true" />
      <div class="login-brand">
        <div class="brand-mark">O</div>
        <div>
          <span>Ops Workbench</span>
          <h1 id="login-title">智能运维工作台</h1>
          <p>连接 Kubernetes、MCP 工具链和知识图谱，用低噪声界面组织排障证据。</p>
        </div>
      </div>

      <n-alert v-if="loginError" class="login-error" type="error" :bordered="false">
        {{ loginError }}
      </n-alert>

      <n-form ref="formRef" class="login-form" :model="form" :rules="rules" @submit.prevent="onLogin">
        <n-form-item label="用户名" path="username" :label-props="{ for: 'login-username' }">
          <n-input
            v-model:value="form.username"
            placeholder="admin"
            autofocus
            :disabled="loading"
            :input-props="{ id: 'login-username', name: 'username', autocomplete: 'username' }"
          />
        </n-form-item>
        <n-form-item label="密码" path="password" :label-props="{ for: 'login-password' }">
          <n-input
            v-model:value="form.password"
            type="password"
            placeholder="admin"
            show-password-on="click"
            :disabled="loading"
            :input-props="{ id: 'login-password', name: 'password', autocomplete: 'current-password' }"
          />
        </n-form-item>
        <n-button class="login-submit" type="primary" block :disabled="!canSubmit" :loading="loading" attr-type="submit">登录</n-button>
      </n-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NAlert, NButton, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import type { FormInst } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const loading = ref(false)
const loginError = ref('')
const formRef = ref<FormInst | null>(null)

const form = reactive({ username: '', password: '' })
const rules = {
  username: { required: true, message: '请输入用户名', trigger: ['input', 'blur'] },
  password: { required: true, message: '请输入密码', trigger: ['input', 'blur'] },
}
const hasCredentials = computed(() => Boolean(form.username.trim() && form.password))
const canSubmit = computed(() => Boolean(hasCredentials.value && !loading.value))

async function onLogin() {
  if (loading.value) return
  loginError.value = ''

  loading.value = true
  try {
    await formRef.value?.validate()
  } catch {
    loading.value = false
    return
  }

  try {
    await auth.login(form.username.trim(), form.password)
    message.success('登录成功')
    router.push({ name: 'Dashboard' })
  } catch (e: any) {
    loginError.value = e?.response?.data?.detail || '登录失败'
    message.error(loginError.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 18% 12%, rgba(47, 111, 237, 0.18), transparent 30%),
    linear-gradient(135deg, #111116 0%, #1b1c22 38%, #f4f7fb 38%, #ffffff 100%);
  color: var(--dr-text);
}

.login-card {
  width: min(460px, 100%);
  padding: 20px;
  border: 1px solid rgba(23, 23, 23, 0.08);
  border-radius: var(--dr-radius-lg);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--dr-shadow-lift);
  backdrop-filter: blur(18px);
}

.login-brand {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 12px 0 24px;
}

.login-brand span {
  display: block;
  color: var(--dr-text-muted);
  font-size: var(--dr-text-xs);
  font-weight: 650;
  text-transform: uppercase;
}

.login-brand h1 {
  margin: 4px 0 0;
  color: var(--dr-text);
  font-size: 22px;
  font-weight: 650;
  line-height: 1.14;
}

.login-brand p {
  margin: 10px 0 0;
  color: var(--dr-text-muted);
  line-height: 1.58;
}

.login-error {
  margin-bottom: 14px;
}

.login-form :deep(.n-form-item-label__text) {
  color: var(--dr-text-soft);
  font-weight: 610;
}

.login-form :deep(.n-input) {
  min-height: 44px;
}

.login-submit {
  min-height: 44px;
  margin-top: 4px;
  font-weight: 650;
}
</style>
