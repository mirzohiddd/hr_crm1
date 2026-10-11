import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

function noTrailingSlash() {
  const rewrite = (req, _res, next) => {
    if (/^\/test\/yakuniy(\?|$)/.test(req.url || '')) {
      req.url = req.url.replace(
        '/test/yakuniy',
        '/test/yakuniy/'
      )
    }
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
  const backend =
    env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

  return {
    base: '/',
    plugins: [noTrailingSlash(), vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5175,
      proxy: {
        '/api': {
          target: backend,
          changeOrigin: true,
        },
      },
    },
    preview: {
      port: 4175,
      proxy: {
        '/api': {
          target: backend,
          changeOrigin: true,
        },
      },
    },
  }
})
