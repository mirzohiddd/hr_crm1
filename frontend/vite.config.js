import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Ishlab chiqishda /api so‘rovlari backendga uzatiladi (CORS sozlash shart emas)
  const backend = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
  // Ochiq test sahifalari — ishlab chiqishda shu dev-serverlarga uzatiladi
  const landing = env.VITE_LANDING_DEV_URL || 'http://127.0.0.1:5174' // landing/   → /test/sotuv
  const landing2 = env.VITE_LANDING2_DEV_URL || 'http://127.0.0.1:5175' // landing-2/ → /test/yakuniy

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': { target: backend, changeOrigin: true },
        '^/test/yakuniy(/|\\?|$)': { target: landing2, changeOrigin: true, ws: true },
        '^/test(/|$)': { target: landing, changeOrigin: true, ws: true },
      },
    },
    preview: {
      port: 4173,
      proxy: { '/api': { target: backend, changeOrigin: true } },
    },
  }
})
