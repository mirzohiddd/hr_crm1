import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '@/api/auth'

const KEY = 'hr-crm:session'
const SESSION_HOURS = 12
const MAX_ATTEMPTS = 5
const LOCK_SECONDS = 60

function readSession() {
  for (const storage of [sessionStorage, localStorage]) {
    try {
      const raw = storage.getItem(KEY)
      if (!raw) continue
      const s = JSON.parse(raw)
      if (s.expiresAt && s.expiresAt > Date.now()) return s
      storage.removeItem(KEY)
    } catch {
      /* storage mavjud emas */
    }
  }
  return null
}

function writeSession(session, remember) {
  try {
    sessionStorage.removeItem(KEY)
    localStorage.removeItem(KEY)
    if (session) (remember ? localStorage : sessionStorage).setItem(KEY, JSON.stringify(session))
  } catch {
    /* e'tiborsiz */
  }
}

export const useAuthStore = defineStore('auth', () => {
  const saved = readSession()
  const token = ref(saved?.token || null)
  const user = ref(saved?.user || null)
  const remember = ref(saved?.remember ?? true)
  const verified = ref(false)

  // Ketma-ket noto‘g‘ri urinishlardan himoya
  const failed = ref(0)
  const lockedUntil = ref(0)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function persist() {
    writeSession(
      token.value ? { token: token.value, user: user.value, remember: remember.value, expiresAt: Date.now() + SESSION_HOURS * 3600 * 1000 } : null,
      remember.value,
    )
  }

  async function login(login, password, rememberMe = true) {
    const wait = Math.ceil((lockedUntil.value - Date.now()) / 1000)
    if (wait > 0) throw new Error(`Juda ko‘p noto‘g‘ri urinish. ${wait} soniyadan keyin qayta urinib ko‘ring.`)
    try {
      const res = await authApi.login(login, password)
      token.value = res.access_token
      user.value = res.user
      remember.value = rememberMe
      verified.value = true
      failed.value = 0
      persist()
      return res.user
    } catch (e) {
      if (e.status === 401) {
        failed.value++
        if (failed.value >= MAX_ATTEMPTS) {
          lockedUntil.value = Date.now() + LOCK_SECONDS * 1000
          failed.value = 0
        }
      }
      throw e
    }
  }

  function logout() {
    token.value = null
    user.value = null
    verified.value = false
    persist()
  }

  /** Sahifa ochilganda saqlangan sessiyani tekshirish (foydalanuvchi bloklanmaganmi) */
  async function verify() {
    if (!token.value || verified.value) return isAuthenticated.value
    try {
      user.value = await authApi.me(token.value)
      verified.value = true
      persist()
    } catch (e) {
      if (e.status === 401 || e.status === 403) logout()
      else verified.value = true // tarmoq xatosi — sessiyani saqlab qolamiz
    }
    return isAuthenticated.value
  }

  async function updateProfile(data) {
    user.value = await authApi.updateMe(user.value.id, data)
    persist()
  }

  async function changePassword(current, next) {
    await authApi.changePassword(user.value.id, current, next)
  }

  /** Foydalanuvchilar bo‘limida o‘zini tahrirlaganda */
  function syncUser(u) {
    if (u && user.value && u.id === user.value.id) {
      user.value = { ...user.value, ...u }
      persist()
    }
  }

  return { token, user, isAuthenticated, isAdmin, login, logout, verify, updateProfile, changePassword, syncUser }
})
