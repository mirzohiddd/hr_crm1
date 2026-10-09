import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setTokenProvider, setUnauthorizedHandler } from './api/client'
import { useAuthStore } from './stores/auth'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())

// API so‘rovlariga Bearer token qo‘shiladi; 401 bo‘lsa — login sahifasiga
const auth = useAuthStore()
setTokenProvider(() => auth.token)
setUnauthorizedHandler(() => {
  auth.logout()
  const current = router.currentRoute.value
  if (!current.meta.public) router.replace({ name: 'login', query: { redirect: current.fullPath } })
})

app.use(router)
app.mount('#app')
