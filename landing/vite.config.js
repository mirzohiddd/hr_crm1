import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

/**
 * Landing /test/ manzilida ishlaydi: /test/sotuv
 * - Ishlab chiqishda: http://localhost:5174/test/sotuv
 * - Vercel'da: asosiy / manzilida ishlaydi
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

  return {
    base: process.env.VERCEL ? '/' : '/test/',
    plugins: [vue()],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: 5174,
      proxy: { '/api': { target: backend, changeOrigin: true } },
    },
    preview: {
      port: 4174,
      proxy: { '/api': { target: backend, changeOrigin: true } },
    },
  }
}) 