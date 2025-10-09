<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>钉钉K8s运维机器人</h1>
        <p>请输入访问密码</p>
      </div>
      
      <el-form @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入访问密码"
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
            style="width: 100%"
            @click="handleLogin"
            :loading="loading"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>© 2024 钉钉K8s运维机器人系统</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!password.value.trim()) {
    ElMessage.warning('请输入访问密码')
    return
  }
  
  loading.value = true
  
  try {
    // 模拟登录延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 使用store进行登录
    const success = authStore.login(password.value)
    
    if (success) {
      ElMessage.success('登录成功')
      
      // 跳转到首页或之前访问的页面
      const redirect = router.currentRoute.value.query.redirect || '/dashboard'
      await router.replace(redirect)
    } else {
      ElMessage.error('密码错误，请重新输入')
      password.value = ''
    }
  } catch (error) {
    ElMessage.error('登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.login-header p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 20px;
}

.login-footer {
  text-align: center;
  color: #909399;
  font-size: 12px;
}

.login-footer p {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
    margin: 0 10px;
  }
  
  .login-header h1 {
    font-size: 20px;
  }
}
</style>
