import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'
import './assets/css/main.css'
import './assets/css/rounded-theme.css'
import './assets/css/chat-theme.css'

// 创建Vue应用实例
const app = createApp(App)

// 使用Pinia状态管理
app.use(createPinia())

// 使用Vue Router
app.use(router)

// 使用Element Plus UI库
app.use(ElementPlus, {
  // Element Plus配置
  size: 'default',
  zIndex: 3000,
})

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Global Error:', err)
  console.error('Component Info:', info)
}

// 挂载应用
app.mount('#app')

// 隐藏加载屏幕
document.body.classList.add('app-ready')

// 开发环境下的调试信息
if (import.meta.env.DEV) {
  console.log('🚀 钉钉K8s运维机器人前端启动成功')
  console.log('📱 当前环境:', import.meta.env.MODE)
  console.log('🔗 API基地址:', import.meta.env.VITE_API_BASE_URL || '/api')
} 