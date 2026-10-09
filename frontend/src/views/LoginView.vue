<script setup>
import { nextTick, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertCircle, BookOpenCheck, CheckCircle2, ClipboardCheck, Eye, EyeOff, LockKeyhole, LogIn, ShieldCheck, UserRound, Users } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import { useAuthStore } from '@/stores/auth'
import { USE_MOCK } from '@/api/client'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({ login: '', password: '', remember: true })
const errors = ref({})
const serverError = ref('')
const loading = ref(false)
const showPassword = ref(false)
const loginInput = ref(null)
const passwordInput = ref(null)

const features = [
  { icon: Users, title: 'Nomzodlar voronkasi', text: 'Instagram va Google Sheets’dan kelgan arizalar bitta joyda' },
  { icon: BookOpenCheck, title: '7 kunlik o‘quv dasturi', text: 'Har kunlik progress avtomatik saqlanadi' },
  { icon: ClipboardCheck, title: 'Avtomatik testlar', text: 'Natija darhol hisoblanadi: o‘tdi yoki o‘tmadi' },
]
const year = new Date().getFullYear()

async function submit() {
  serverError.value = ''
  errors.value = {}
  if (!form.login.trim()) errors.value.login = 'Loginni kiriting'
  if (!form.password) errors.value.password = 'Parolni kiriting'
  if (errors.value.login) return loginInput.value?.focus()
  if (errors.value.password) return passwordInput.value?.focus()

  loading.value = true
  try {
    await auth.login(form.login.trim(), form.password, form.remember)
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : '/dashboard'
    router.replace(redirect)
  } catch (e) {
    serverError.value = e.message || 'Kirishda xatolik yuz berdi'
    form.password = ''
    await nextTick()
    passwordInput.value?.focus()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page relative grid min-h-screen bg-white lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
    <!-- ================= Chap: CRM imkoniyatlari ================= -->
    <aside class="brand-panel relative hidden overflow-hidden px-12 py-10 text-white lg:flex lg:flex-col xl:px-16">
      <!-- Fon: harakatlanuvchi yorug‘lik dog‘lari va to‘r -->
      <div class="orb orb-a" aria-hidden="true" />
      <div class="orb orb-b" aria-hidden="true" />
      <div class="orb orb-c" aria-hidden="true" />
      <div class="grid-overlay" aria-hidden="true" />

      <div class="relative fade-in" style="--d: 0ms">
        <BrandLogo size="lg" framed class="text-white">HR CRM</BrandLogo>
      </div>

      <div class="relative my-auto max-w-xl py-10">
        <p class="fade-in inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-primary-50 ring-1 ring-white/20 backdrop-blur" style="--d: 80ms">
          <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-300" /> HR bo‘limi uchun yagona tizim
        </p>
        <h1 class="fade-in mt-5 text-[38px] font-semibold leading-[1.15] tracking-tight xl:text-[44px]" style="--d: 140ms">
          Nomzoddan tayyor xodimgacha —<br />
          <span class="bg-gradient-to-r from-white to-sky-200 bg-clip-text text-transparent">bitta tizimda</span>
        </h1>
        <p class="fade-in mt-4 max-w-md text-[15px] leading-relaxed text-primary-100" style="--d: 200ms">
          Arizalarni qabul qiling, suhbat o‘tkazing, ishga oling va yangi xodimni 7 kunlik dastur hamda test orqali tayyorlang.
        </p>

        <ul class="mt-9 space-y-3.5">
          <li
            v-for="(f, i) in features"
            :key="f.title"
            class="feature-card fade-in group flex items-start gap-4 rounded-2xl bg-white/[0.08] p-4 ring-1 ring-white/15 backdrop-blur-md"
            :style="{ '--d': `${280 + i * 110}ms` }"
          >
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white text-primary-600 shadow-lg shadow-primary-900/20 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110">
              <component :is="f.icon" class="h-5 w-5" />
            </span>
            <span class="min-w-0">
              <span class="block text-[15px] font-semibold">{{ f.title }}</span>
              <span class="mt-0.5 block text-sm leading-snug text-primary-100">{{ f.text }}</span>
            </span>
          </li>
        </ul>

        <!-- Kichik “jonli” ko‘rinish -->
        <div class="fade-in mt-8 flex flex-wrap gap-3" style="--d: 640ms" aria-hidden="true">
          <span class="float-chip inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-xs font-medium text-ink shadow-xl shadow-primary-900/20">
            <span class="grid h-6 w-6 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><CheckCircle2 class="h-3.5 w-3.5" /></span>
            Testdan o‘tdi · 90%
          </span>
          <span class="float-chip inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-xs font-medium text-ink shadow-xl shadow-primary-900/20" style="animation-delay: -2s">
            <span class="grid h-6 w-6 place-items-center rounded-lg bg-primary-50 text-primary-600"><BookOpenCheck class="h-3.5 w-3.5" /></span>
            5/7 kun bajarildi
          </span>
        </div>
      </div>

      <p class="relative text-xs text-primary-200">© {{ year }} HR CRM · Ichki foydalanish uchun</p>
    </aside>

    <!-- ================= O‘ng: kirish formasi ================= -->
    <main class="relative flex items-center justify-center overflow-hidden px-5 py-10 sm:px-8">
      <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(600px_300px_at_80%_0%,rgba(37,99,235,0.08),transparent_70%)] lg:hidden" aria-hidden="true" />

      <div class="login-card relative w-full max-w-[420px]">
        <div class="mb-8 flex justify-center lg:hidden">
          <BrandLogo size="xl" :text="false" />
        </div>

        <div class="fade-in" style="--d: 60ms">
          <h2 class="text-center text-[26px] font-semibold tracking-tight text-ink lg:text-left">Xush kelibsiz</h2>
          <p class="mt-1.5 text-center text-sm text-muted lg:text-left">Davom etish uchun login va parolingizni kiriting</p>
        </div>

        <Transition name="shake">
          <div v-if="serverError" :key="serverError" class="mt-6 flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-3.5 py-3 text-sm text-red-700" role="alert">
            <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" />
            <span>{{ serverError }}</span>
          </div>
        </Transition>

        <form class="fade-in mt-7 space-y-4" style="--d: 140ms" novalidate @submit.prevent="submit">
          <div>
            <label for="login" class="form-label">Login</label>
            <div class="input-wrap relative">
              <UserRound class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted transition-colors" />
              <input
                id="login"
                ref="loginInput"
                v-model="form.login"
                type="text"
                autocomplete="username"
                autocapitalize="none"
                spellcheck="false"
                placeholder="Loginingiz"
                :class="['form-input h-12 rounded-xl pl-10', errors.login && 'has-error']"
                autofocus
                @input="errors.login = ''"
              />
            </div>
            <p v-if="errors.login" class="form-error">{{ errors.login }}</p>
          </div>

          <div>
            <label for="password" class="form-label">Parol</label>
            <div class="input-wrap relative">
              <LockKeyhole class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted transition-colors" />
              <input
                id="password"
                ref="passwordInput"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                :class="['form-input h-12 rounded-xl pl-10 pr-12', errors.password && 'has-error']"
                @input="errors.password = ''"
              />
              <button
                type="button"
                class="absolute right-2 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-lg text-muted transition-colors hover:bg-slate-100 hover:text-ink"
                :aria-label="showPassword ? 'Parolni yashirish' : 'Parolni ko‘rsatish'"
                @click="showPassword = !showPassword"
              >
                <component :is="showPassword ? EyeOff : Eye" class="h-4 w-4" />
              </button>
            </div>
            <p v-if="errors.password" class="form-error">{{ errors.password }}</p>
          </div>

          <label class="flex cursor-pointer select-none items-center gap-2.5 text-sm text-slate-600">
            <input v-model="form.remember" type="checkbox" class="h-4 w-4 rounded border-line text-primary-600 focus:ring-primary-500" />
            Meni eslab qol
          </label>

          <Button type="submit" block class="login-btn h-12 rounded-xl text-[15px]" :icon="LogIn" :loading="loading">
            {{ loading ? 'Tekshirilmoqda...' : 'Tizimga kirish' }}
          </Button>
        </form>

        <p class="fade-in mt-6 flex items-center justify-center gap-1.5 text-xs text-muted" style="--d: 220ms">
          <ShieldCheck class="h-3.5 w-3.5 text-emerald-600" /> Faqat ruxsat berilgan xodimlar uchun
        </p>

        <div v-if="USE_MOCK" class="mt-6 rounded-xl border border-primary-100 bg-primary-50/60 px-4 py-3 text-[13px] text-slate-600">
          <p class="font-medium text-ink">Demo rejim</p>
          <p class="mt-1">
            Administrator: <code class="rounded bg-white px-1.5 py-0.5 text-primary-700 ring-1 ring-primary-100">admin</code> /
            <code class="rounded bg-white px-1.5 py-0.5 text-primary-700 ring-1 ring-primary-100">admin123</code>
          </p>
        </div>

        <!-- Mobil: qisqa imkoniyatlar -->
        <ul class="mt-10 grid gap-2.5 lg:hidden">
          <li v-for="f in features" :key="f.title" class="flex items-center gap-3 rounded-xl border border-line bg-white p-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600"><component :is="f.icon" class="h-4 w-4" /></span>
            <span class="min-w-0">
              <span class="block text-sm font-medium text-ink">{{ f.title }}</span>
              <span class="block text-xs text-muted">{{ f.text }}</span>
            </span>
          </li>
        </ul>
      </div>
    </main>
  </div>
</template>

<style scoped>
.brand-panel {
  background: linear-gradient(145deg, #1e40af 0%, #2563eb 45%, #0ea5e9 120%);
}
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse at 30% 40%, black 30%, transparent 75%);
}
.orb {
  position: absolute;
  border-radius: 9999px;
  filter: blur(60px);
  opacity: 0.55;
  animation: drift 16s ease-in-out infinite alternate;
}
.orb-a { width: 420px; height: 420px; top: -120px; right: -100px; background: #38bdf8; }
.orb-b { width: 360px; height: 360px; bottom: -140px; left: -80px; background: #1d4ed8; animation-delay: -5s; }
.orb-c { width: 240px; height: 240px; top: 45%; left: 55%; background: #93c5fd; opacity: 0.35; animation-delay: -9s; }
@keyframes drift {
  to { transform: translate3d(40px, 30px, 0) scale(1.12); }
}

.fade-in {
  animation: fade-up 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  animation-delay: var(--d, 0ms);
}
.feature-card {
  transition: transform 0.25s ease, background-color 0.25s ease, box-shadow 0.25s ease;
}
.feature-card:hover {
  transform: translateX(6px);
  background-color: rgba(255, 255, 255, 0.14);
  box-shadow: 0 16px 40px -18px rgba(15, 23, 42, 0.5);
}
.float-chip {
  animation: float 6s ease-in-out infinite;
}
@keyframes float {
  50% { transform: translateY(-6px); }
}

.login-card { animation: fade-up 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
.input-wrap:focus-within svg { color: theme('colors.primary.600'); }
.login-btn {
  background-image: linear-gradient(90deg, #2563eb, #1d4ed8);
  box-shadow: 0 10px 24px -10px rgba(37, 99, 235, 0.6);
}
.login-btn:hover { box-shadow: 0 14px 30px -10px rgba(37, 99, 235, 0.7); }

.shake-enter-active { animation: shake 0.4s ease; }
@keyframes shake {
  20%, 60% { transform: translateX(-6px); }
  40%, 80% { transform: translateX(6px); }
}
@media (prefers-reduced-motion: reduce) {
  .orb, .float-chip, .fade-in, .login-card { animation: none; }
}
</style>
