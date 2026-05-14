import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8002'

  return {
    plugins: [
      vue(),
    ],
    server: {
      proxy: {
        '/auth': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path
        },
        '/admin': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path
        }
      }
    }
  }
})
