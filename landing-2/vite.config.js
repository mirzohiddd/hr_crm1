import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

/**
 * Landing 2 — yakuniy bilim testi: /test/yakuniy?t=<bir martalik token>
 * - Ishlab chiqishda: http://localhost:5175/test/yakuniy/ (CRM dev-serveri ham /test/yakuniy ni shu yerga uzatadi)
 * - Serverda: backend landing-2/dist ni /test/yakuniy da ochadi
 */
// /test/yakuniy?t=... (oxirida "/" siz) → /test/yakuniy/?t=... (dev va preview; production’da backend bajaradi)
function noTrailingSlash() {
  const rewrite = (req, _res, next) => {
    if (/^\/test\/yakuniy(\?|$)/.test(req.url || '')) req.url = req.url.replace('/test/yakuniy', '/test/yakuniy/')
    next()
  }
  return {
    name: 'no-trailing-slash',
    configureServer(server) {
      server.middlewares.use(rewrite)
    },
    configurePreviewServer(server) {
      server.middlewares.use(rewrite)
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

  return {
    base: '/test/yakuniy/',
    plugins: [noTrailingSlash(), vue()],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: 5175,
      proxy: { '/api': { target: backend, changeOrigin: true } },
    },
    preview: {
      port: 4175,
      proxy: { '/api': { target: backend, changeOrigin: true } },
    },
  }
})
