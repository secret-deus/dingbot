import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/claude-desktop.css'
import './styles/workbench-pages.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
