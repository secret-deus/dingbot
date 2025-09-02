import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // 代理API请求到后端服务
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // 代理钉钉webhook到后端
      '/dingtalk': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    // 构建输出到backend/static/spa目录
    outDir: '../backend/static/spa',
    emptyOutDir: true,
    // 设置公共基础路径
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          elementplus: ['element-plus']
        }
      }
    },
    // 生成sourcemap用于调试
    sourcemap: false,
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000
  },
  // 设置基础公共路径
  base: '/spa/',
  define: {
    __VUE_PROD_DEVTOOLS__: false,
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
  }
}) 