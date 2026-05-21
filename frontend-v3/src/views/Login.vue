<template>
  <div class="login-shell">
    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-brand">
        <img :src="botCoreIcon" alt="">
        <div>
          <span>Ding Robot</span>
          <h1 id="login-title">ChatOps 运维控制台</h1>
          <p>连接 Kubernetes、MCP 工具链和知识图谱。</p>
        </div>
      </div>

      <n-form ref="formRef" class="login-form" :model="form" :rules="rules" @submit.prevent="onLogin">
        <n-form-item label="用户名" path="username" :label-props="{ for: 'login-username' }">
          <n-input
            v-model:value="form.username"
            placeholder="请输入用户名"
            :input-props="{ id: 'login-username', name: 'username', autocomplete: 'username' }"
          />
        </n-form-item>
        <n-form-item label="密码" path="password" :label-props="{ for: 'login-password' }">
          <n-input
            v-model:value="form.password"
            type="password"
            placeholder="请输入密码"
            show-password-on="click"
            :input-props="{ id: 'login-password', name: 'password', autocomplete: 'current-password' }"
          />
        </n-form-item>
        <n-button class="login-submit" type="primary" block :loading="loading" attr-type="submit">登录</n-button>
      </n-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import botCoreIcon from '@/assets/generated/bot-core.svg'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
}

async function onLogin() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    message.success('登录成功')
    router.push({ name: 'Dashboard' })
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '登录失败')
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
  background: #070a0f;
  color: #f8fafc;
}

.login-panel {
  width: min(420px, 100%);
  padding: 22px;
  border: 1px solid #2a3648;
  border-radius: 8px;
  background: #0d1420;
}

.login-brand {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 22px;
}

.login-brand img {
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  border: 1px solid #2a3648;
  border-radius: 8px;
  background: #111827;
}

.login-brand span {
  display: block;
  color: #9aa8bd;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.login-brand h1 {
  margin: 3px 0 0;
  color: #f8fafc;
  font-size: 24px;
  line-height: 1.2;
  letter-spacing: 0;
}

.login-brand p {
  margin: 8px 0 0;
  color: #9aa8bd;
  line-height: 1.6;
}

.login-form :deep(.n-form-item-label__text) {
  color: #d7deea;
  font-weight: 700;
}

.login-form :deep(.n-input) {
  min-height: 44px;
}

.login-submit {
  min-height: 44px;
  font-weight: 700;
}
</style>
