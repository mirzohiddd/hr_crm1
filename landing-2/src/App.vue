<script setup>
/**
 * Yakuniy bilim testi (7 kunlik darslardan keyin): /test/yakuniy
 * - 1-bosqich: ism, familiya, yosh va tug‘ilgan sana. Backend tekshiradi (POST /public/final-test/register)
 *   va ishtirokchi id + maxfiy kalit qaytaradi. Shundan keyingina savollar ochiladi.
 * - Javob tanlangach keyingi savolga avtomatik o‘tiladi; oldingi savolga qaytib javobni o‘zgartirish mumkin.
 * - 20-savoldan keyin "Testni yakunlash" — javoblar ishtirokchi id/kaliti bilan backendga yuboriladi,
 *   ball faqat backendda hisoblanadi. Natija HR CRM → Testlar → "Yakuniy bilim testi" da ism-familiya bilan.
 * - Sahifa yangilansa: kiritilgan ma'lumotlar, ishtirokchi va tugallanmagan javoblar localStorage dan tiklanadi.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  AlertCircle, ArrowLeft, ArrowRight, Award, BookOpenCheck, Cake, CalendarClock, CalendarDays, Check, CheckCircle2, Clock,
  Flag, GraduationCap, Keyboard, ListChecks, Loader2, RotateCcw, ShieldCheck, Target, UserRound, XCircle,
} from 'lucide-vue-next'
import BrandLogo from '@/components/BrandLogo.vue'
import ChoiceAnswer from '@/components/ChoiceAnswer.vue'
import heroUrl from '@/assets/yakuniy-hero.svg'
import { finalApi } from '@/api'

const LETTERS = 'ABCDEFGH'
const DRAFT_KEY = 'hr-crm:yakuniy:draft'
const RESULT_KEY = 'hr-crm:yakuniy:result'
const FORM_KEY = 'hr-crm:yakuniy:form'
const PARTICIPANT_KEY = 'hr-crm:yakuniy:participant'

// Backend bilan bir xil qoidalar (backend/app/final_test.py → validate_participant)
const AGE_MIN = 16
const AGE_MAX = 70
const NAME_RE = /^\p{L}[\p{L}\p{M}' \-ʻʼ‘’`]*$/u

function newId() {
  try {
    if (crypto?.randomUUID) return crypto.randomUUID()
  } catch {
    /* eski brauzer */
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}
const storage = {
  get(store, key) {
    try {
      return JSON.parse(store.getItem(key) || 'null')
    } catch {
      return null
    }
  },
  set(store, key, value) {
    try {
      store.setItem(key, JSON.stringify(value))
    } catch {
      /* saqlash imkoni yo‘q — muhim emas */
    }
  },
  remove(store, key) {
    try {
      store.removeItem(key)
    } catch {
      /* */
    }
  },
}

// ---------- Sana yordamchilari (mahalliy sana bo‘yicha) ----------
function todayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
/** 'YYYY-MM-DD' → { y, m, d } yoki null (mavjud bo‘lmagan sana — null) */
function parseISO(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''))
  if (!m) return null
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])]
  const dt = new Date(y, mo - 1, d)
  return dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d ? { y, m: mo, d } : null
}
/** Tug‘ilgan sanadan bugungi to‘liq yosh */
function ageFrom(iso) {
  const b = parseISO(iso)
  const t = parseISO(todayISO())
  if (!b || !t) return null
  return t.y - b.y - (t.m < b.m || (t.m === b.m && t.d < b.d) ? 1 : 0)
}
const cleanName = (v) => String(v ?? '').replace(/\s+/g, ' ').trim()
const formatBirth = (iso) => (iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : '')

// ---------- Holat ----------
const loading = ref(true)
const loadError = ref('')
const test = ref(null)
const phase = ref('register') // register | quiz | result

// 1-bosqich: ishtirokchi ma'lumotlari
const form = reactive({ firstName: '', lastName: '', age: '', birthDate: '' })
const errors = ref({})
const participant = ref(null) // { id, key, firstName, lastName, fullName, age, birthDate }
const registering = ref(false)
const registerError = ref('')
const regClientId = ref(newId())
const maxBirth = todayISO()
const answers = reactive({})
const current = ref(0)
const direction = ref(1)
const startedAt = ref(Date.now())
const clientId = ref(newId())
const submitting = ref(false)
const submitError = ref('')
const result = ref(null)

const questions = computed(() => test.value?.questions || [])
const total = computed(() => questions.value.length)
const question = computed(() => questions.value[current.value])
const isLast = computed(() => current.value === total.value - 1)
const isAnswered = (q) => !!q && answers[q.id] !== undefined && answers[q.id] !== null
const answeredCount = computed(() => questions.value.filter(isAnswered).length)
const progress = computed(() => (total.value ? Math.round((answeredCount.value / total.value) * 100) : 0))
const firstUnanswered = computed(() => questions.value.findIndex((q) => !isAnswered(q)))
const allAnswered = computed(() => total.value > 0 && firstUnanswered.value === -1)
// Oldinga faqat javob berilgan savollargacha (va birinchi javobsiz savolga) o‘tish mumkin
const reachable = (i) => allAnswered.value || i <= firstUnanswered.value
const passNeeded = computed(() => Math.ceil(((test.value?.passPercent ?? 80) / 100) * (total.value || 20)))

function saveDraft() {
  if (phase.value === 'quiz' && test.value) {
    storage.set(localStorage, DRAFT_KEY, {
      answers, current: current.value, startedAt: startedAt.value, clientId: clientId.value, participantId: participant.value?.id ?? null,
    })
  }
}
watch([current, () => ({ ...answers })], saveDraft, { deep: true })

// Kiritilgan ma'lumotlar sahifa yangilanganda yo‘qolmasin; ma'lumot o‘zgarsa — yangi ro‘yxatdan o‘tish so‘rovi id si
watch(
  () => ({ ...form }),
  (value, old) => {
    storage.set(localStorage, FORM_KEY, value)
    if (old && ['firstName', 'lastName', 'age', 'birthDate'].some((k) => value[k] !== old[k])) regClientId.value = newId()
  },
)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await finalApi.open()
    test.value = data.test
    document.title = `${data.test.title} — HR+`
    // Sahifa yangilansa — natija, ishtirokchi, kiritilgan ma'lumotlar va tugallanmagan javoblar qayta tiklanadi
    const savedParticipant = storage.get(localStorage, PARTICIPANT_KEY)
    if (savedParticipant?.id && savedParticipant?.key) participant.value = savedParticipant
    const savedForm = storage.get(localStorage, FORM_KEY)
    const src = savedForm || participant.value
    if (src) {
      Object.assign(form, {
        firstName: String(src.firstName ?? ''), lastName: String(src.lastName ?? ''),
        age: src.age === null || src.age === undefined ? '' : String(src.age), birthDate: String(src.birthDate ?? ''),
      })
    }
    const saved = storage.get(sessionStorage, RESULT_KEY)
    if (saved?.result) {
      result.value = saved.result
      phase.value = 'result'
      return
    }
    const draft = storage.get(localStorage, DRAFT_KEY)
    if (draft) {
      const ids = new Set(questions.value.map((q) => String(q.id)))
      Object.entries(draft.answers || {}).forEach(([k, v]) => ids.has(String(k)) && (answers[k] = v))
      current.value = Math.min(Math.max(0, Number(draft.current) || 0), total.value - 1)
      if (!reachable(current.value)) current.value = Math.max(0, firstUnanswered.value)
      startedAt.value = draft.startedAt || Date.now()
      clientId.value = draft.clientId || clientId.value
    }
    // Test boshlangan bo‘lsa (shu ishtirokchi bilan) — to‘g‘ridan-to‘g‘ri savollarga qaytiladi
    if (participant.value && draft && draft.participantId === participant.value.id) phase.value = 'quiz'
  } catch (e) {
    loadError.value = e.message || 'Testni yuklab bo‘lmadi'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// ---------- 1-bosqich: ro‘yxatdan o‘tish ----------
const computedAge = computed(() => {
  const a = ageFrom(form.birthDate)
  return a !== null && a >= 0 && form.birthDate <= maxBirth ? a : null
})
function onBirthInput() {
  clearError('birthDate')
  // Yosh tug‘ilgan sanadan avtomatik hisoblanadi (foydalanuvchi o‘zgartirsa — moslik tekshiriladi)
  if (computedAge.value !== null) {
    form.age = String(computedAge.value)
    clearError('age')
  }
}
function onAgeInput(e) {
  form.age = String(e.target.value || '').replace(/\D/g, '').slice(0, 3)
  e.target.value = form.age
  clearError('age')
}
function clearError(key) {
  registerError.value = ''
  if (errors.value[key]) {
    const next = { ...errors.value }
    delete next[key]
    errors.value = next
  }
}
function nameError(value, label) {
  const v = cleanName(value)
  if (!v) return `${label}ni kiriting`
  if (v.length < 2) return `${label} kamida 2 ta harfdan iborat bo‘lsin`
  if (v.length > 50) return `${label} 50 ta belgidan oshmasin`
  if (!NAME_RE.test(v)) return `${label}da faqat harflar, tutuq belgisi (ʻ) va chiziqcha (-) bo‘lishi mumkin`
  return ''
}
function validateForm() {
  const e = {}
  const first = nameError(form.firstName, 'Ism')
  const last = nameError(form.lastName, 'Familiya')
  if (first) e.firstName = first
  if (last) e.lastName = last

  if (!form.birthDate) e.birthDate = 'Tug‘ilgan sanani tanlang'
  else if (!parseISO(form.birthDate)) e.birthDate = 'Bunday sana mavjud emas'
  else if (form.birthDate > maxBirth) e.birthDate = 'Tug‘ilgan sana kelajakdagi sana bo‘lishi mumkin emas'
  else if (form.birthDate < '1900-01-01') e.birthDate = 'Tug‘ilgan sana noto‘g‘ri'

  const ageText = String(form.age ?? '').trim()
  const age = Number(ageText)
  if (!ageText) e.age = 'Yoshingizni kiriting'
  else if (!/^\d{1,3}$/.test(ageText)) e.age = 'Yosh butun son bo‘lishi kerak'
  else if (age < AGE_MIN || age > AGE_MAX) e.age = `Yosh ${AGE_MIN} dan ${AGE_MAX} gacha bo‘lishi kerak`
  else if (!e.birthDate && computedAge.value !== null && computedAge.value !== age) {
    e.age = `Yosh tug‘ilgan sanaga mos emas: tug‘ilgan sanaga ko‘ra ${computedAge.value} yosh`
  }
  errors.value = e
  return !Object.keys(e).length
}
function focusFirstError() {
  nextTick(() => {
    const first = ['firstName', 'lastName', 'birthDate', 'age'].find((k) => errors.value[k])
    if (first) document.getElementById(`reg-${first}`)?.focus()
  })
}
const normalizedForm = () => ({
  firstName: cleanName(form.firstName),
  lastName: cleanName(form.lastName),
  age: Number(form.age),
  birthDate: form.birthDate,
})
const sameParticipant = (p, f) => !!p && ['firstName', 'lastName', 'age', 'birthDate'].every((k) => p[k] === f[k])

async function startTest() {
  if (registering.value) return
  registerError.value = ''
  if (!validateForm()) return focusFirstError()
  const data = normalizedForm()
  // Ma'lumotlar o‘zgarmagan bo‘lsa — avvalgi ishtirokchi (qayta topshirish — keyingi urinish sifatida saqlanadi)
  if (!sameParticipant(participant.value, data)) {
    registering.value = true
    try {
      const res = await finalApi.register({ ...data, clientId: regClientId.value })
      participant.value = res.participant
      storage.set(localStorage, PARTICIPANT_KEY, res.participant)
      regClientId.value = newId()
    } catch (e) {
      if (e.status === 400) registerError.value = e.message
      else if (e.status === 409) {
        regClientId.value = newId()
        registerError.value = 'Ma’lumotlar o‘zgargan. “Testni boshlash” ni qayta bosing.'
      } else registerError.value = e.message || 'Ma’lumotlarni yuborib bo‘lmadi. Qayta urinib ko‘ring.'
      return
    } finally {
      registering.value = false
    }
  }
  Object.assign(form, { firstName: data.firstName, lastName: data.lastName })
  // Hali birorta savolga javob berilmagan bo‘lsa — vaqt shu daqiqadan hisoblanadi
  if (!answeredCount.value) startedAt.value = Date.now()
  submitError.value = ''
  phase.value = 'quiz'
  saveDraft()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ---------- Navigatsiya ----------
let advanceTimer = null
function go(i) {
  if (i < 0 || i >= total.value || !reachable(i)) return
  clearTimeout(advanceTimer)
  submitError.value = ''
  direction.value = i >= current.value ? 1 : -1
  current.value = i
}
function next() {
  if (!isAnswered(question.value) || isLast.value) return
  go(current.value + 1)
}
function prev() {
  go(current.value - 1)
}
function select(value) {
  const q = question.value
  answers[q.id] = value
  submitError.value = ''
  clearTimeout(advanceTimer)
  // Javob tanlangach keyingi savolga avtomatik o‘tish (20-savolda — "Testni yakunlash" tugmasi chiqadi)
  if (!isLast.value) advanceTimer = setTimeout(() => (question.value?.id === q.id ? next() : null), 420)
}
function onKey(e) {
  if (phase.value !== 'quiz' || !question.value || submitting.value || e.altKey || e.ctrlKey || e.metaKey) return
  const idx = LETTERS.toLowerCase().indexOf(e.key.toLowerCase())
  const num = Number(e.key) - 1
  if (idx > -1 && idx < question.value.options.length) return select(idx)
  if (num >= 0 && num < question.value.options.length) return select(num)
  if (e.key === 'ArrowRight') next()
  else if (e.key === 'ArrowLeft') prev()
}
// Mobil: joriy savol raqami doim ko‘rinib tursin
watch(current, (i) => nextTick(() => document.querySelector(`[data-qdot="${i}"]`)?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })))
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  clearTimeout(advanceTimer)
  clearInterval(ticker)
})

const now = ref(Date.now())
const ticker = setInterval(() => (now.value = Date.now()), 1000)
const elapsed = computed(() => {
  const s = Math.max(0, Math.floor((now.value - startedAt.value) / 1000))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
})

// ---------- Yakunlash ----------
async function finish() {
  submitError.value = ''
  if (!allAnswered.value) {
    submitError.value = `Barcha savollarga javob bering: ${total.value - answeredCount.value} ta savol javobsiz.`
    go(firstUnanswered.value)
    return
  }
  if (!participant.value) {
    phase.value = 'register'
    registerError.value = 'Avval shaxsiy ma’lumotlaringizni kiriting.'
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    const res = await finalApi.submit({
      participantId: participant.value.id,
      participantKey: participant.value.key,
      answers: { ...answers },
      durationSec: Math.round((Date.now() - startedAt.value) / 1000),
      clientId: clientId.value,
    })
    result.value = { ...res.result, fullName: res.result.fullName || participant.value.fullName }
    phase.value = 'result'
    storage.set(sessionStorage, RESULT_KEY, { result: result.value })
    storage.remove(localStorage, DRAFT_KEY)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    if (e.status === 403) {
      // Ishtirokchi serverda topilmadi (masalan, ma'lumotlar tozalangan) — javoblar saqlanadi, ma'lumotlar qayta kiritiladi
      participant.value = null
      storage.remove(localStorage, PARTICIPANT_KEY)
      phase.value = 'register'
      registerError.value = `${e.message} Javoblaringiz saqlanib qoldi.`
    } else {
      submitError.value = e.message || 'Yuborib bo‘lmadi. Qayta urinib ko‘ring.'
    }
  } finally {
    submitting.value = false
  }
}

function restart() {
  storage.remove(sessionStorage, RESULT_KEY)
  storage.remove(localStorage, DRAFT_KEY)
  Object.keys(answers).forEach((k) => delete answers[k])
  result.value = null
  current.value = 0
  direction.value = 1
  startedAt.value = Date.now()
  clientId.value = newId()
  submitError.value = ''
  registerError.value = ''
  errors.value = {}
  // Qayta topshirish ham ma'lumotlarni tasdiqlashdan boshlanadi (o‘zgartirilsa — yangi ishtirokchi)
  phase.value = 'register'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ---------- Natija ----------
const passed = computed(() => result.value?.status === 'O‘tdi')
const R = 64
const C = 2 * Math.PI * R
const ringDash = ref(`0 ${C}`)
watch(
  result,
  (r) => {
    ringDash.value = `0 ${C}`
    if (r) setTimeout(() => (ringDash.value = `${(r.percent / 100) * C} ${C}`), 120)
  },
  { immediate: true },
)
const formatDT = (v) => (v ? `${v.slice(8, 10)}.${v.slice(5, 7)}.${v.slice(0, 4)}, ${v.slice(11, 16)}` : '')
</script>

<template>
  <div class="relative min-h-screen bg-[#F5F8FF] text-ink">
    <div class="pointer-events-none fixed inset-0" aria-hidden="true">
      <div class="grid-bg absolute inset-0" />
      <div class="glow glow-a" />
    </div>

    <div class="relative z-10 mx-auto grid min-h-screen max-w-[1440px] lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
      <!-- ================= Chap: rasm ================= -->
      <aside class="hero relative overflow-hidden lg:sticky lg:top-0 lg:h-screen lg:p-5">
        <div class="hero-frame relative h-44 overflow-hidden sm:h-64 lg:h-full lg:rounded-[32px]">
          <img :src="heroUrl" alt="Ofisda xodimlarni o‘qitish" class="hero-img absolute inset-0 h-full w-full object-cover object-[50%_40%]" />
          <div class="absolute inset-0 bg-gradient-to-t from-[#0B1E4D]/85 via-[#0B1E4D]/20 to-transparent" />
          <div class="absolute left-4 top-4 rounded-2xl bg-white/90 px-2.5 py-1.5 shadow-lg backdrop-blur lg:left-7 lg:top-7"><BrandLogo size="sm" :text="false" /></div>

          <div class="absolute inset-x-0 bottom-0 p-4 text-white sm:p-7 lg:p-9">
            <span class="hidden items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider ring-1 ring-white/25 backdrop-blur sm:inline-flex">
              <GraduationCap class="h-3.5 w-3.5" /> HR+ o‘quv markazi
            </span>
            <h2 class="max-w-md text-xl font-bold leading-tight tracking-tight sm:mt-3 sm:text-3xl lg:text-[34px]">7 kunlik dasturni tugatdingiz — endi bilimlaringizni tasdiqlang</h2>
            <ul class="mt-5 hidden gap-2 sm:flex sm:flex-wrap">
              <li class="hero-chip"><BookOpenCheck class="h-4 w-4" /> 7 kun · 7 mavzu</li>
              <li class="hero-chip"><ListChecks class="h-4 w-4" /> {{ total || 20 }} ta savol</li>
              <li class="hero-chip"><Target class="h-4 w-4" /> O‘tish: {{ passNeeded }} ta to‘g‘ri</li>
            </ul>
          </div>
        </div>
      </aside>

      <!-- ================= O‘ng: test ================= -->
      <main class="flex min-w-0 flex-col px-4 pb-12 pt-5 sm:px-8 lg:px-12 lg:pt-10 xl:px-16">
        <header class="flex items-center justify-between gap-4">
          <div class="min-w-0">
            <p class="text-xs font-semibold uppercase tracking-wider text-primary-600">Yakuniy bilim testi</p>
            <p class="truncate text-sm text-muted">{{ test?.subtitle || '7 kunlik o‘quv dasturi bo‘yicha' }}</p>
          </div>
          <div v-if="phase === 'quiz' && test" class="flex shrink-0 items-center gap-2 text-xs font-medium">
            <span class="hidden items-center gap-1.5 rounded-full bg-white px-2.5 py-1 tabular-nums text-slate-600 shadow-sm ring-1 ring-line sm:inline-flex"><Clock class="h-3.5 w-3.5" />{{ elapsed }}</span>
            <span class="counter" aria-live="polite"><b>{{ current + 1 }}</b>/{{ total }} savol</span>
          </div>
        </header>

        <div v-if="phase === 'quiz' && test" class="mt-4">
          <p v-if="participant" class="mb-3 inline-flex max-w-full items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 shadow-sm ring-1 ring-line">
            <UserRound class="h-3.5 w-3.5 shrink-0 text-primary-600" />
            <span class="truncate">{{ participant.fullName }} · {{ participant.age }} yosh</span>
          </p>
          <div class="h-2 overflow-hidden rounded-full bg-primary-100/70" role="progressbar" :aria-valuenow="answeredCount" aria-valuemin="0" :aria-valuemax="total" :aria-label="`${answeredCount} / ${total} savolga javob berildi`">
            <div class="progress-fill h-full rounded-full" :style="{ width: `${progress}%` }" />
          </div>
          <p class="mt-1.5 flex justify-between text-[11px] text-muted">
            <span><CheckCircle2 class="mr-1 inline h-3 w-3 -translate-y-px text-primary-600" />{{ answeredCount }} ta javob berildi</span>
            <span class="tabular-nums">{{ progress }}%</span>
          </p>
        </div>

        <div class="mt-5 flex-1">
          <!-- Yuklanmoqda -->
          <div v-if="loading" class="grid min-h-[40vh] place-items-center">
            <div class="flex items-center gap-3 text-sm text-muted"><Loader2 class="h-5 w-5 animate-spin text-primary-600" /> Savollar yuklanmoqda...</div>
          </div>

          <!-- Server bilan aloqa yo‘q -->
          <div v-else-if="loadError" class="panel reveal mx-auto max-w-lg p-8 text-center">
            <span class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-red-50 text-red-600"><AlertCircle class="h-7 w-7" /></span>
            <h1 class="mt-5 text-xl font-semibold tracking-tight">Savollarni yuklab bo‘lmadi</h1>
            <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ loadError }}</p>
            <button type="button" class="btn-primary mt-6" @click="load"><RotateCcw class="h-4 w-4" /> Qayta urinish</button>
          </div>

          <Transition v-else name="phase" mode="out-in">
            <!-- ================= 1-bosqich: shaxsiy ma'lumotlar ================= -->
            <section v-if="phase === 'register'" key="register" class="reveal">
              <form class="panel mx-auto max-w-2xl p-5 sm:p-8" novalidate @submit.prevent="startTest">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-wider text-primary-600">1-bosqich</p>
                    <h1 class="mt-1 text-xl font-semibold tracking-tight sm:text-2xl">Shaxsiy ma’lumotlar</h1>
                    <p class="mt-1.5 text-sm leading-relaxed text-slate-600">Test natijasi shu ma’lumotlar bilan HR bo‘limiga yuboriladi. Barcha maydonlar majburiy.</p>
                  </div>
                  <span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-600/25"><UserRound class="h-6 w-6" /></span>
                </div>

                <div class="mt-6 grid gap-4 sm:grid-cols-2">
                  <div class="field">
                    <label class="form-label" for="reg-firstName">Ism <span class="text-red-500">*</span></label>
                    <div class="input-wrap">
                      <UserRound class="input-icon" />
                      <input id="reg-firstName" v-model="form.firstName" class="form-input has-icon" :class="{ 'has-error': errors.firstName }" placeholder="Masalan: Aziz" autocomplete="given-name" maxlength="50" :aria-invalid="!!errors.firstName" aria-describedby="err-firstName" @input="clearError('firstName')" />
                    </div>
                    <p v-if="errors.firstName" id="err-firstName" class="form-error">{{ errors.firstName }}</p>
                  </div>
                  <div class="field">
                    <label class="form-label" for="reg-lastName">Familiya <span class="text-red-500">*</span></label>
                    <div class="input-wrap">
                      <UserRound class="input-icon" />
                      <input id="reg-lastName" v-model="form.lastName" class="form-input has-icon" :class="{ 'has-error': errors.lastName }" placeholder="Masalan: Karimov" autocomplete="family-name" maxlength="50" :aria-invalid="!!errors.lastName" aria-describedby="err-lastName" @input="clearError('lastName')" />
                    </div>
                    <p v-if="errors.lastName" id="err-lastName" class="form-error">{{ errors.lastName }}</p>
                  </div>
                  <div class="field">
                    <label class="form-label" for="reg-birthDate">Tug‘ilgan sana <span class="text-red-500">*</span></label>
                    <div class="input-wrap">
                      <CalendarDays class="input-icon" />
                      <input id="reg-birthDate" v-model="form.birthDate" class="form-input has-icon" :class="{ 'has-error': errors.birthDate }" type="date" min="1900-01-01" :max="maxBirth" autocomplete="bday" :aria-invalid="!!errors.birthDate" aria-describedby="err-birthDate" @input="onBirthInput" @change="onBirthInput" />
                    </div>
                    <p v-if="errors.birthDate" id="err-birthDate" class="form-error">{{ errors.birthDate }}</p>
                  </div>
                  <div class="field">
                    <label class="form-label" for="reg-age">Yosh <span class="text-red-500">*</span></label>
                    <div class="input-wrap">
                      <Cake class="input-icon" />
                      <input id="reg-age" :value="form.age" class="form-input has-icon" :class="{ 'has-error': errors.age }" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="3" placeholder="25" :aria-invalid="!!errors.age" aria-describedby="err-age" @input="onAgeInput" />
                    </div>
                    <p v-if="errors.age" id="err-age" class="form-error">{{ errors.age }}</p>
                    <p v-else-if="computedAge !== null" class="mt-1.5 text-xs text-muted">Tug‘ilgan sanadan avtomatik hisoblandi</p>
                  </div>
                </div>

                <p v-if="registerError" class="mt-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
                  <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> {{ registerError }}
                </p>

                <ul class="mt-6 grid gap-2 rounded-2xl bg-primary-50/60 p-3 text-[13px] text-slate-600 sm:grid-cols-3">
                  <li class="flex items-center gap-2"><ListChecks class="h-4 w-4 shrink-0 text-primary-600" /> {{ total || 20 }} ta savol</li>
                  <li class="flex items-center gap-2"><Target class="h-4 w-4 shrink-0 text-primary-600" /> O‘tish: {{ passNeeded }} ta to‘g‘ri</li>
                  <li class="flex items-center gap-2"><Clock class="h-4 w-4 shrink-0 text-primary-600" /> Vaqt boshlashdan hisoblanadi</li>
                </ul>

                <button type="submit" class="btn-primary btn-lg group mt-6 w-full" :disabled="registering">
                  <Loader2 v-if="registering" class="h-4 w-4 animate-spin" />
                  {{ registering ? 'Tekshirilmoqda...' : answeredCount ? 'Testni davom ettirish' : 'Testni boshlash' }}
                  <ArrowRight v-if="!registering" class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </button>
                <p class="mt-3 flex items-center justify-center gap-1.5 text-xs text-muted"><ShieldCheck class="h-3.5 w-3.5" /> Ma’lumotlaringiz faqat HR bo‘limiga ko‘rinadi</p>
              </form>
            </section>

            <!-- ================= Savollar ================= -->
            <section v-else-if="phase === 'quiz'" key="quiz">
              <!-- Savollar raqamlari: javob berilganlar belgilangan, oldingilarga qaytish mumkin -->
              <div class="-mx-4 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0">
                <div class="grid w-max grid-flow-col gap-1.5 sm:w-full sm:grid-flow-row sm:grid-cols-10">
                  <button
                    v-for="(q, i) in questions"
                    :key="q.id"
                    type="button"
                    :data-qdot="i"
                    :disabled="!reachable(i) || submitting"
                    :aria-label="`${i + 1}-savol${isAnswered(q) ? ', javob berilgan' : ''}`"
                    :aria-current="i === current ? 'step' : undefined"
                    :class="['q-dot', isAnswered(q) && 'is-done', i === current && 'is-current']"
                    @click="go(i)"
                  >
                    {{ i + 1 }}
                    <span v-if="isAnswered(q) && i !== current" class="q-tick"><Check class="h-2.5 w-2.5" stroke-width="3.5" /></span>
                  </button>
                </div>
              </div>

              <div class="panel mt-4 overflow-hidden p-5 sm:mt-5 sm:p-8">
                <Transition :name="direction > 0 ? 'q-next' : 'q-prev'" mode="out-in">
                  <div :key="question.id">
                    <div class="flex items-start gap-4 sm:gap-5">
                      <span class="q-number" aria-hidden="true">{{ String(current + 1).padStart(2, '0') }}</span>
                      <div class="min-w-0 flex-1 pt-1">
                        <p class="text-xs font-medium text-muted">{{ current + 1 }}/{{ total }} savol · bitta javobni tanlang</p>
                        <h1 class="mt-1.5 text-xl font-semibold leading-snug tracking-tight sm:text-[22px]">{{ question.text }}</h1>
                      </div>
                    </div>
                    <div class="mt-6 sm:mt-7">
                      <ChoiceAnswer :model-value="answers[question.id] ?? null" :options="question.options" :name="question.text" @update:model-value="select" />
                    </div>
                  </div>
                </Transition>

                <p v-if="submitError" class="mt-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
                  <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> {{ submitError }}
                </p>

                <div class="mt-7 flex items-center justify-between gap-3 border-t border-line pt-5">
                  <button type="button" class="btn-ghost" :disabled="current === 0 || submitting" @click="prev"><ArrowLeft class="h-4 w-4" /> Oldingi</button>
                  <span class="hidden items-center gap-1.5 text-xs text-muted md:inline-flex"><Keyboard class="h-3.5 w-3.5" /> A–D yoki 1–4</span>
                  <Transition name="fade" mode="out-in">
                    <button v-if="isLast" key="finish" type="button" class="btn-primary btn-finish" :disabled="!isAnswered(question) || submitting" @click="finish">
                      <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
                      <Flag v-else class="h-4 w-4" />
                      Testni yakunlash
                    </button>
                    <button v-else key="next" type="button" class="btn-primary" :disabled="!isAnswered(question)" @click="next">Keyingi <ArrowRight class="h-4 w-4" /></button>
                  </Transition>
                </div>
              </div>
            </section>

            <!-- ================= Natija ================= -->
            <section v-else key="result" class="reveal">
              <div class="panel relative overflow-hidden p-6 text-center sm:p-10">
                <div :class="['absolute inset-x-0 top-0 h-1.5', passed ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-gradient-to-r from-red-500 to-orange-400']" />
                <div class="relative mx-auto h-40 w-40">
                  <svg viewBox="0 0 160 160" class="h-full w-full -rotate-90" aria-hidden="true">
                    <circle cx="80" cy="80" :r="R" fill="none" stroke-width="14" class="stroke-slate-100" />
                    <circle cx="80" cy="80" :r="R" fill="none" stroke-width="14" stroke-linecap="round" :stroke-dasharray="ringDash" :class="['ring-arc', passed ? 'stroke-emerald-500' : 'stroke-red-500']" />
                  </svg>
                  <div class="absolute inset-0 grid place-items-center">
                    <div>
                      <p class="text-4xl font-bold tabular-nums tracking-tight">{{ result.correct }}<span class="text-xl text-muted">/{{ result.total }}</span></p>
                      <p class="text-xs text-muted">ball · {{ result.percent }}%</p>
                    </div>
                  </div>
                </div>
                <span :class="['mt-5 inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-semibold ring-1 ring-inset', passed ? 'bg-emerald-50 text-emerald-700 ring-emerald-600/20' : 'bg-red-50 text-red-700 ring-red-600/20']">
                  <Award v-if="passed" class="h-4 w-4" /><XCircle v-else class="h-4 w-4" />
                  {{ passed ? 'Testdan o‘tdi' : 'Testdan o‘tmadi' }}
                </span>
                <h1 class="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">{{ passed ? 'Tabriklaymiz!' : 'Bu safar yetmadi' }}</h1>
                <p v-if="result.fullName" class="mt-1 text-sm font-medium text-ink">{{ result.fullName }}</p>
                <p class="mx-auto mt-2 max-w-md text-sm leading-relaxed text-slate-600">
                  <template v-if="passed">Siz yakuniy bilim testidan muvaffaqiyatli o‘tdingiz. Natija HR bo‘limiga yuborildi.</template>
                  <template v-else>O‘tish uchun kamida {{ Math.ceil((result.passPercent / 100) * result.total) }} ta to‘g‘ri javob kerak. Natija HR bo‘limiga yuborildi — mavzularni takrorlab, qayta topshirishingiz mumkin.</template>
                </p>

                <dl class="mx-auto mt-7 grid max-w-lg grid-cols-2 gap-3 sm:grid-cols-4">
                  <div class="res-cell"><dt>To‘g‘ri</dt><dd class="text-emerald-600">{{ result.correct }}</dd></div>
                  <div class="res-cell"><dt>Xato</dt><dd class="text-red-600">{{ result.wrong }}</dd></div>
                  <div class="res-cell"><dt>Ball</dt><dd>{{ result.correct }}/{{ result.total }}</dd></div>
                  <div class="res-cell"><dt>Foiz</dt><dd>{{ result.percent }}%</dd></div>
                </dl>
                <p class="mt-6 inline-flex items-center gap-1.5 text-xs text-muted"><CalendarClock class="h-3.5 w-3.5" /> Topshirildi: {{ formatDT(result.submittedAt) }}</p>
              </div>
              <div class="mt-5 text-center">
                <button type="button" class="btn-ghost" @click="restart"><RotateCcw class="h-4 w-4" /> Testni qayta boshlash</button>
              </div>
            </section>
          </Transition>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.grid-bg {
  background-image: linear-gradient(rgba(37, 99, 235, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 99, 235, 0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 70% 60% at 80% 0%, #000 30%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 80% 0%, #000 30%, transparent 100%);
}
.glow {
  @apply absolute rounded-full blur-3xl;
}
.glow-a {
  width: 560px;
  height: 560px;
  top: -200px;
  right: -160px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.25), transparent 65%);
  animation: drift 18s ease-in-out infinite alternate;
}
@keyframes drift {
  to {
    transform: translate(-50px, 40px) scale(1.06);
  }
}
.hero-frame {
  @apply shadow-[0_40px_80px_-40px_rgba(30,64,175,0.55)];
}
.hero-img {
  animation: hero-zoom 1.4s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
@keyframes hero-zoom {
  from {
    transform: scale(1.06);
    opacity: 0;
  }
}
.hero-chip {
  @apply inline-flex items-center gap-1.5 rounded-xl bg-white/15 px-3 py-1.5 text-[13px] font-medium ring-1 ring-white/20 backdrop-blur transition-colors hover:bg-white/25;
}
.counter {
  @apply inline-flex items-center rounded-full bg-primary-50 px-3 py-1 text-[13px] tabular-nums text-primary-700 ring-1 ring-primary-100;
}
.counter b {
  @apply font-bold;
}
.progress-fill {
  @apply bg-gradient-to-r from-primary-600 via-primary-500 to-sky-400 transition-[width] duration-500 ease-out;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
}
.panel {
  @apply rounded-[24px] border border-white bg-white/90 shadow-[0_24px_60px_-34px_rgba(30,64,175,0.45),0_2px_6px_-2px_rgba(15,23,42,0.06)] backdrop-blur-xl;
}
.q-number {
  @apply select-none text-5xl font-bold leading-none tabular-nums tracking-tighter sm:text-6xl;
  color: transparent;
  -webkit-text-stroke: 1.5px rgba(37, 99, 235, 0.45);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.12), transparent);
  -webkit-background-clip: text;
  background-clip: text;
}
.q-dot {
  @apply relative grid h-9 w-9 place-items-center rounded-lg border border-line bg-white text-xs font-semibold tabular-nums text-slate-500 transition-all duration-150 sm:w-auto;
  @apply hover:-translate-y-0.5 hover:border-primary-300 hover:text-primary-700 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0;
}
.q-dot.is-done {
  @apply border-primary-100 bg-primary-50 text-primary-700;
}
.q-dot.is-current {
  @apply border-transparent bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/30;
}
.q-tick {
  @apply absolute -right-1 -top-1 grid h-3.5 w-3.5 place-items-center rounded-full bg-emerald-500 text-white ring-2 ring-white;
}
.res-cell {
  @apply rounded-2xl bg-slate-50 px-3 py-3;
}
.res-cell dt {
  @apply text-[11px] font-medium uppercase tracking-wider text-muted;
}
.res-cell dd {
  @apply mt-0.5 text-2xl font-bold tabular-nums;
}
.ring-arc {
  transition: stroke-dasharray 1.1s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.btn-primary {
  @apply inline-flex h-11 select-none items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-5 text-sm font-semibold text-white shadow-lg shadow-primary-600/25 transition-all duration-200;
  @apply hover:-translate-y-0.5 hover:shadow-xl hover:shadow-primary-600/30 active:translate-y-0 active:scale-[0.98];
  @apply focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/25 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none;
}
.btn-lg {
  @apply h-12 text-[15px];
}
.input-wrap {
  @apply relative;
}
.input-icon {
  @apply pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400;
}
.form-input.has-icon {
  @apply h-11 rounded-xl pl-9;
}
.btn-finish {
  @apply from-emerald-600 to-emerald-500 shadow-emerald-600/25 hover:shadow-emerald-600/30;
}
.btn-ghost {
  @apply inline-flex h-11 items-center gap-2 rounded-xl px-4 text-sm font-medium text-slate-600 transition-colors hover:bg-white hover:text-ink hover:shadow-sm disabled:pointer-events-none disabled:opacity-40;
  @apply focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/15;
}
.reveal {
  animation: fade-up 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.96);
}
.phase-enter-active,
.phase-leave-active {
  transition: opacity 0.3s ease, transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.phase-enter-from {
  opacity: 0;
  transform: translateY(16px);
}
.phase-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.q-next-enter-active,
.q-next-leave-active,
.q-prev-enter-active,
.q-prev-leave-active {
  transition: opacity 0.2s ease, transform 0.26s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.q-next-enter-from,
.q-prev-leave-to {
  opacity: 0;
  transform: translateX(28px);
}
.q-next-leave-to,
.q-prev-enter-from {
  opacity: 0;
  transform: translateX(-28px);
}
@media (prefers-reduced-motion: reduce) {
  .glow,
  .hero-img,
  .reveal {
    animation: none !important;
  }
}
</style>