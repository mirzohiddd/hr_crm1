<script setup>
/**
 * Yangi kelgan xodimlar / nomzodlar uchun ochiq test (landing ilovasi): /test/sotuv
 * Login talab qilinmaydi. Savollar backenddan olinadi (backend/app/landing_tests/<slug>.json),
 * hisoblash serverda, natija HR CRM → Testlar → "Nomzodlar testi" bo‘limiga tushadi.
 *
 * Joriy test (format=persona, «Ishdagi shaxsiyat 360»): 40 ta savol 4 bosqichda (har birida 10 ta),
 * javob — «Qo‘shilmayman» / «Qo‘shilaman».
 *   "Oldinga" — bosqichdagi barcha savollarga javob berilgach; "Orqaga" — oldingi bosqichga (javoblar saqlanadi,
 *   1-bosqichda — ma’lumotlarga); 4-bosqichda "Testni yakunlash". HR uchun batafsil hisobot — backendda.
 *   Oxirgi bosqich — rasmli savollar (test.pictures, 3 ta rasm × 4 variant): nomzod rasmda birinchi bo‘lib
 *   ko‘rgan narsani tanlaydi; javoblar submit da pictures = { rasmId: variant } sifatida yuboriladi.
 * Eski formatdagi savolnomalar (1–5 shkala, A/B/C/D) avvalgidek bitta-bitta savol bilan ishlaydi.
 *
 * Telefon raqami majburiy: "Testni boshlash" bosilganda avval brauzerda formati, so‘ng backendda
 * (POST /public/tests/{slug}/phone-check) bandligi tekshiriladi. Raqam tasdiqlanmaguncha savollar ochilmaydi;
 * topshirishda backend yana tekshiradi (bitta raqam — bitta natija).
 */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  AlertCircle, ArrowLeft, ArrowRight, BadgeCheck, Briefcase, CalendarDays, Check, CheckCircle2, Clock, Flag, Image as ImageIcon,
  Keyboard, Layers, ListChecks, Loader2, Pencil, Phone, RotateCcw, Send, ShieldCheck, Sparkles, Target, UserRound,
} from 'lucide-vue-next'
import BrandLogo from '@/components/BrandLogo.vue'
import ScaleAnswer from '@/components/ScaleAnswer.vue'
import ChoiceAnswer from '@/components/ChoiceAnswer.vue'
import AgreeAnswer from '@/components/AgreeAnswer.vue'
import PictureQuestion from '@/components/PictureQuestion.vue'
import { assetUrl, testApi } from '@/api'
import { formatDate, normalizePhone, phoneError, slugFromPath, todayISO } from '@/utils'

const slug = computed(() => slugFromPath())
// 40 savolli test qoralamasi eski (20 savolli) test qoralamasi bilan aralashmasin
const DRAFT_KEY = computed(() => `hr-crm:landing:${slug.value}${['profile', 'persona'].includes(test.value?.format) ? `:${test.value.format}` : ''}`)
const LETTERS = 'ABCDEFGH'

// ---------- Savolnoma ----------
const test = ref(null)
const loading = ref(true)
const loadError = ref('')
const questions = computed(() => test.value?.questions || [])
const total = computed(() => questions.value.length)
const sections = computed(() =>
  (test.value?.sections || []).map((s) => {
    const items = questions.value.map((q, index) => ({ q, index })).filter((x) => x.q.section === s.id)
    return { ...s, items, from: (items[0]?.index ?? 0) + 1, to: (items.at(-1)?.index ?? 0) + 1 }
  }),
)
const sectionOf = (q) => sections.value.find((s) => s.id === q?.section)
// Bosqichli «Qo‘shilmayman»/«Qo‘shilaman» testi: persona («Ishdagi shaxsiyat 360») yoki profile formati
const isProfile = computed(() => ['profile', 'persona'].includes(test.value?.format))
const agreeOptions = computed(() => test.value?.options || ['Qo‘shilmayman', 'Qo‘shilaman'])

// ---------- Holat ----------
const phase = ref('intro') // intro | quiz | review | done
const form = reactive({ fullName: '', age: '', date: todayISO(), position: '', phone: '' })
const errors = ref({})
const answers = reactive({})
const picAnswers = reactive({}) // rasmli savollar: { rasmId: variant indeksi }
const current = ref(0)
const direction = ref(1)
// Test vaqti: faqat faol vaqt hisoblanadi. Sahifa yopilgan / kompyuter uxlagan / tab uzoq yashirin turgan
// tanaffuslar (IDLE_GAP_MS dan uzun) startedAt ni oldinga surish orqali chiqarib tashlanadi.
// Aks holda nomzod ertasi kuni qaytsa, vaqt 1 sutkadan oshib, backend testni rad etardi (durationSec ≤ 86400).
const MAX_DURATION_SEC = 86400 // backend bilan bir xil (backend/app/schemas.py → MAX_DURATION_SEC)
const IDLE_GAP_MS = 10 * 60 * 1000
const startedAt = ref(null)
const lastActiveAt = ref(null)
const timeUnknown = ref(false) // eski qoralamadan tiklanganda haqiqiy vaqtni bilib bo‘lmasa
const clientId = ref(newId())
const submitting = ref(false)
const submitError = ref('')
const submitDetail = ref('') // asl texnik xato (masalan: "durationSec: Input should be ..."), kichik shriftda
const done = ref(null)
// Telefon: backend tasdiqlagan raqam ('+998 90 123 45 67'); bo‘sh — savollarga o‘tib bo‘lmaydi
const phoneVerified = ref('')
const checkingPhone = ref(false)
const startError = ref('')
const phoneOk = computed(() => !!phoneVerified.value && normalizePhone(form.phone) === phoneVerified.value)

function newId() {
  try {
    if (crypto?.randomUUID) return crypto.randomUUID()
  } catch {
    /* eski brauzer */
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

const question = computed(() => questions.value[current.value])
const isAnswered = (q) => q && answers[q.id] !== undefined && answers[q.id] !== null
const answeredCount = computed(() => questions.value.filter(isAnswered).length)
// Rasmli savollar (faqat bosqichli persona testida)
const pictures = computed(() => (test.value?.format === 'persona' ? test.value?.pictures || [] : []))
const hasPictures = computed(() => pictures.value.length > 0)
const isPicDone = (p) => p && Number.isInteger(picAnswers[p.id])
const picAnsweredCount = computed(() => pictures.value.filter(isPicDone).length)
const allPicturesDone = computed(() => pictures.value.every(isPicDone))
// Umumiy progress: savollar + rasmlar
const doneCount = computed(() => answeredCount.value + picAnsweredCount.value)
const grandTotal = computed(() => total.value + pictures.value.length)
const progress = computed(() => (grandTotal.value ? Math.round((doneCount.value / grandTotal.value) * 100) : 0))
const firstUnanswered = computed(() => questions.value.findIndex((q) => !isAnswered(q)))
const allAnswered = computed(() => total.value > 0 && firstUnanswered.value === -1)
// Savollar xaritasida faqat javob berilganlar va birinchi javobsiz savolgacha o‘tish mumkin
const reachable = (i) => allAnswered.value || i <= firstUnanswered.value
const firstName = computed(() => form.fullName.trim().split(/\s+/)[1] || form.fullName.trim().split(/\s+/)[0] || '')

// ---------- Profil testi: 4 bosqich × 10 savol ----------
const stage = ref(0)
const highlight = ref(false) // "Oldinga" bosilganda javobsiz savollarni ajratib ko‘rsatish
const byId = computed(() => new Map(questions.value.map((q) => [String(q.id), q])))
const stages = computed(() => {
  const list = test.value?.stages
  if (list?.length) return list.map((s) => s.questionIds.map((id) => byId.value.get(String(id))).filter(Boolean))
  const size = test.value?.stageSize || 10
  const out = []
  for (let i = 0; i < questions.value.length; i += size) out.push(questions.value.slice(i, i + size))
  return out
})
// Bosqichlar: savollar bosqichlari + (bo‘lsa) oxirida rasmlar bosqichi
const picStage = computed(() => (hasPictures.value ? stages.value.length : -1))
const stageCount = computed(() => stages.value.length + (hasPictures.value ? 1 : 0))
const isPictureStage = computed(() => stage.value === picStage.value)
const stageQuestions = computed(() => stages.value[stage.value] || [])
const stageOffset = computed(() => stages.value.slice(0, stage.value).reduce((n, s) => n + s.length, 0))
const isLastStage = computed(() => stage.value === stageCount.value - 1)
const stageSize = (i) => (i === picStage.value ? pictures.value.length : (stages.value[i] || []).length)
const stageDone = (i) => (i === picStage.value ? allPicturesDone.value : (stages.value[i] || []).every(isAnswered))
const stageAnswered = (i) => (i === picStage.value ? picAnsweredCount.value : (stages.value[i] || []).filter(isAnswered).length)
const stageRange = (i) => {
  if (i === picStage.value) return 'rasmlar'
  const from = stages.value.slice(0, i).reduce((n, s) => n + s.length, 0)
  return `${from + 1}–${from + (stages.value[i] || []).length}`
}
const firstOpenStage = computed(() => {
  for (let i = 0; i < stageCount.value; i++) if (!stageDone(i)) return i
  return Math.max(0, stageCount.value - 1)
})
const stageReachable = (i) => i <= firstOpenStage.value

function scrollToQuestion(q) {
  nextTick(() => document.getElementById(`q-${q.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
}
function scrollToPicture(p) {
  nextTick(() => document.getElementById(`pic-${p.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}
function goStage(i) {
  if (i < 0 || i >= stageCount.value || !stageReachable(i) || submitting.value) return
  submitError.value = ''
  highlight.value = false
  direction.value = i >= stage.value ? 1 : -1
  stage.value = i
  scrollTop()
}
/** Bosqichdagi birinchi javobsiz savolni ko‘rsatadi; hammasiga javob berilgan bo‘lsa — false */
function showMissing() {
  if (isPictureStage.value) {
    const missingPics = pictures.value.filter((p) => !isPicDone(p))
    if (!missingPics.length) return false
    highlight.value = true
    submitError.value = `${missingPics.length} ta rasmga javob berilmagan. Har bir rasmda birinchi ko‘rgan narsangizni tanlang.`
    scrollToPicture(missingPics[0])
    return true
  }
  const missing = stageQuestions.value.filter((q) => !isAnswered(q))
  if (!missing.length) return false
  highlight.value = true
  submitError.value = `Bu bosqichda ${missing.length} ta savol javobsiz qoldi. Davom etish uchun barcha savollarga javob bering.`
  scrollToQuestion(missing[0])
  return true
}
function nextStage() {
  if (showMissing()) return
  goStage(stage.value + 1)
}
function prevStage() {
  if (stage.value === 0) {
    phase.value = 'intro' // ma'lumotlarga qaytish — javoblar saqlanib qoladi
    scrollTop()
    return
  }
  goStage(stage.value - 1)
}
function selectAgree(q, value) {
  answers[q.id] = value
  if (stageDone(stage.value)) {
    submitError.value = ''
    highlight.value = false
  }
  const list = stageQuestions.value
  const nextQ = list.slice(list.indexOf(q) + 1).find((x) => !isAnswered(x))
  if (nextQ) scrollToQuestion(nextQ)
}
function selectPicture(p, value) {
  picAnswers[p.id] = value
  if (allPicturesDone.value) {
    submitError.value = ''
    highlight.value = false
  }
  const list = pictures.value
  const nextP = list.slice(list.indexOf(p) + 1).find((x) => !isPicDone(x))
  if (nextP) setTimeout(() => scrollToPicture(nextP), 350)
}
async function finishProfile() {
  if (showMissing()) return
  if (!allAnswered.value || !allPicturesDone.value) {
    goStage(firstOpenStage.value)
    nextTick(showMissing)
    return
  }
  await submit()
}

// ---------- Qoralama (sahifa yangilansa javoblar yo‘qolmaydi) ----------
function saveDraft() {
  try {
    localStorage.setItem(
      DRAFT_KEY.value,
      JSON.stringify({
        phase: phase.value, form, answers, pictures: picAnswers, current: current.value, stage: stage.value, startedAt: startedAt.value,
        lastActiveAt: startedAt.value ? Date.now() : null, timeUnknown: timeUnknown.value,
        clientId: clientId.value, done: done.value, phoneVerified: phoneVerified.value,
      }),
    )
  } catch {
    /* saqlash imkoni yo‘q — muhim emas */
  }
}
function loadDraft() {
  try {
    const d = JSON.parse(localStorage.getItem(DRAFT_KEY.value) || 'null')
    if (!d) return
    Object.assign(form, d.form || {})
    Object.entries(d.answers || {}).forEach(([k, v]) => {
      // Profil testida faqat mavjud savollar va 0/1 javoblar tiklanadi
      if (!isProfile.value || (byId.value.has(String(k)) && (v === 0 || v === 1))) answers[k] = v
    })
    // Rasmli savollar: faqat mavjud rasm va to‘g‘ri variant tiklanadi
    Object.entries(d.pictures || {}).forEach(([k, v]) => {
      const p = pictures.value.find((x) => x.id === k)
      if (p && Number.isInteger(v) && v >= 0 && v < p.options.length) picAnswers[k] = v
    })
    restoreTimer(d)
    clientId.value = d.clientId || clientId.value
    done.value = d.done || null
    phoneVerified.value = typeof d.phoneVerified === 'string' ? d.phoneVerified : ''
    const max = Math.max(0, total.value - 1)
    current.value = Math.min(Number(d.current) || 0, max)
    phase.value = ['intro', 'quiz', 'review', 'done'].includes(d.phase) ? d.phase : 'intro'
    if (phase.value === 'done' && !done.value) phase.value = 'intro'
    if (isProfile.value) {
      stage.value = Math.min(Math.max(0, Number(d.stage) || 0), Math.max(0, stageCount.value - 1))
      if (!stageReachable(stage.value)) stage.value = firstOpenStage.value
      if (phase.value === 'review') phase.value = 'quiz'
    }
  } catch {
    /* buzilgan qoralama */
  }
}
/** Qoralamadan vaqtni tiklash: sahifa yopiq turgan vaqt test vaqtiga qo‘shilmaydi */
function restoreTimer(d) {
  const start = Number(d.startedAt) || null
  const last = Number(d.lastActiveAt) || null
  timeUnknown.value = d.timeUnknown === true
  startedAt.value = start
  lastActiveAt.value = start ? Date.now() : null
  if (!start) return
  if (last && last >= start && last <= Date.now()) {
    // Sahifa yopilgan paytdan hozirgacha bo‘lgan tanaffus chiqarib tashlanadi
    startedAt.value = start + (Date.now() - last)
  } else if (Date.now() - start > MAX_DURATION_SEC * 1000 || start > Date.now()) {
    // Eski qoralama (lastActiveAt yo‘q) yoki soat o‘zgargan: haqiqiy vaqtni bilib bo‘lmaydi
    startedAt.value = Date.now()
    timeUnknown.value = true
  }
}
/** Tanaffus (kompyuter uxlagan, tab uzoq yashirin) — vaqtga qo‘shilmaydi */
function markActive() {
  const t = Date.now()
  if (startedAt.value && lastActiveAt.value && t - lastActiveAt.value > IDLE_GAP_MS) {
    startedAt.value += t - lastActiveAt.value
  }
  lastActiveAt.value = startedAt.value ? t : null
}
/** Backendga yuboriladigan vaqt (soniya): noma’lum yoki chegaradan tashqari bo‘lsa — null */
function durationSeconds() {
  if (!startedAt.value || timeUnknown.value) return null
  const s = Math.round((Date.now() - startedAt.value) / 1000)
  return s >= 0 && s <= MAX_DURATION_SEC ? s : null
}
function onVisibility() {
  if (document.visibilityState === 'visible') markActive()
  else saveDraft()
}
onMounted(() => {
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('pagehide', saveDraft)
})
onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('pagehide', saveDraft)
})

function clearDraft() {
  try {
    localStorage.removeItem(DRAFT_KEY.value)
  } catch {
    /* */
  }
}
watch([phase, current, stage, () => ({ ...form }), () => ({ ...answers }), () => ({ ...picAnswers })], saveDraft, { deep: true })

// Telefon tasdiqlanmagan bo‘lsa (masalan, eski qoralama yoki raqam o‘zgartirilgan) — savollar ochilmaydi,
// javoblar saqlanib qoladi va foydalanuvchi ma'lumotlar formasiga qaytariladi
watch(phase, (p) => {
  if ((p === 'quiz' || p === 'review') && !phoneOk.value) {
    phase.value = 'intro'
    if (!errors.value.phone) errors.value = { ...errors.value, phone: phoneError(form.phone) || undefined }
  }
})
watch(
  () => form.phone,
  (v) => {
    if (phoneVerified.value && normalizePhone(v) !== phoneVerified.value) phoneVerified.value = ''
  },
)

onMounted(async () => {
  try {
    test.value = await testApi.get(slug.value)
    document.title = `${test.value.title} — HR+`
    if (test.value.positions?.length === 1) form.position = test.value.positions[0]
    loadDraft()
    // Lavozim ro‘yxati o‘zgargan bo‘lsa
    if (form.position && test.value.positions?.length && !test.value.positions.includes(form.position)) form.position = ''
  } catch (e) {
    loadError.value = e.status === 404 ? 'Bunday test topilmadi. Havolani tekshiring.' : e.message
  } finally {
    loading.value = false
  }
})

// ---------- 1-bosqich: ma’lumotlar ----------
function validateForm() {
  const e = {}
  const name = form.fullName.trim().replace(/\s+/g, ' ')
  if (!name) e.fullName = 'F.I.Sh. ni kiriting'
  else if (name.split(' ').length < 2 || name.length < 5) e.fullName = 'Familiya, ism va otasining ismini to‘liq yozing'
  const age = Number(form.age)
  if (!form.age) e.age = 'Yoshingizni kiriting'
  else if (!Number.isInteger(age) || age < 16 || age > 70) e.age = '16 dan 70 gacha'
  if (!form.date) e.date = 'Sanani tanlang'
  if (!form.position) e.position = 'Lavozimni tanlang'
  const phoneMsg = phoneError(form.phone)
  if (phoneMsg) e.phone = phoneMsg
  errors.value = e
  return !Object.keys(e).length
}
async function focusFirstError() {
  await nextTick()
  document.querySelector('.field-error')?.closest('.field')?.querySelector('input,button')?.focus()
}
function showPhoneError(message) {
  phoneVerified.value = ''
  errors.value = { ...errors.value, phone: message }
  focusFirstError()
}
/** Raqamni backendda tekshiradi: true — bo‘sh va to‘g‘ri (phoneVerified o‘rnatiladi) */
async function verifyPhone() {
  checkingPhone.value = true
  startError.value = ''
  try {
    const res = await testApi.checkPhone(slug.value, normalizePhone(form.phone))
    form.phone = res.phone
    phoneVerified.value = res.phone
    return true
  } catch (e) {
    // 409 — raqam band, 422 — formati noto‘g‘ri: xabar telefon maydoni ostida
    if (e.status === 409 || (e.status === 422 && e.field === 'phone')) showPhoneError(e.message)
    else startError.value = e.message || 'Telefon raqamini tekshirib bo‘lmadi. Qayta urinib ko‘ring.'
    return false
  } finally {
    checkingPhone.value = false
  }
}
async function start() {
  if (checkingPhone.value) return
  startError.value = ''
  if (!validateForm()) return focusFirstError()
  form.fullName = form.fullName.trim().replace(/\s+/g, ' ')
  form.phone = normalizePhone(form.phone)
  if (!(await verifyPhone())) return
  if (!startedAt.value) startedAt.value = Date.now()
  markActive()
  phase.value = 'quiz'
  current.value = allAnswered.value ? 0 : Math.max(0, firstUnanswered.value)
  if (isProfile.value) {
    stage.value = firstOpenStage.value
    highlight.value = false
    submitError.value = ''
  }
  scrollTop()
}
function clearError(field) {
  if (field === 'phone') startError.value = ''
  if (errors.value[field]) errors.value = { ...errors.value, [field]: undefined }
}
/** Maydondan chiqilganda to‘g‘ri raqam yagona ko‘rinishga keltiriladi: +998 90 123 45 67 */
function formatPhoneField() {
  const v = normalizePhone(form.phone)
  if (v) form.phone = v
}

// ---------- 2-bosqich: savollar ----------
let advanceTimer = null
function go(index) {
  if (index < 0 || index >= total.value) return
  clearTimeout(advanceTimer)
  direction.value = index >= current.value ? 1 : -1
  current.value = index
}
function next() {
  if (!isAnswered(question.value)) return
  if (current.value < total.value - 1) go(current.value + 1)
  else openReview()
}
function prev() {
  if (current.value > 0) go(current.value - 1)
  else {
    phase.value = 'intro'
    scrollTop()
  }
}
function select(value) {
  const q = question.value
  const wasEmpty = !isAnswered(q)
  answers[q.id] = value
  clearTimeout(advanceTimer)
  // Birinchi marta javob berilganda keyingi savolga avtomatik o‘tish
  if (wasEmpty) advanceTimer = setTimeout(() => (question.value?.id === q.id ? next() : null), 420)
}
function openReview() {
  clearTimeout(advanceTimer)
  phase.value = 'review'
  scrollTop()
}
function editQuestion(index) {
  phase.value = 'quiz'
  direction.value = 1
  current.value = index
  scrollTop()
}

// Mobil xaritada joriy savol doim ko‘rinib tursin
watch(current, (i) =>
  nextTick(() => document.querySelector(`[data-mdot="${i}"]`)?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })),
)

function onKey(e) {
  if (phase.value !== 'quiz' || !question.value || isProfile.value) return
  if (e.target instanceof HTMLElement && e.target.closest('input, textarea, select')) return
  if (e.altKey || e.ctrlKey || e.metaKey) return
  const q = question.value
  const key = e.key.toLowerCase()
  if (q.type === 'scale') {
    const n = Number(key)
    const lo = test.value.scale?.min ?? 1
    const hi = test.value.scale?.max ?? 5
    if (n >= lo && n <= hi) return select(n)
  } else {
    const idx = LETTERS.toLowerCase().indexOf(key)
    const num = Number(key) - 1
    if (idx > -1 && idx < q.options.length) return select(idx)
    if (num >= 0 && num < q.options.length) return select(num)
  }
  if (e.key === 'ArrowRight' || e.key === 'Enter') next()
  else if (e.key === 'ArrowLeft') prev()
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  clearTimeout(advanceTimer)
  clearInterval(ticker)
})

// Sarflangan vaqt
const now = ref(Date.now())
const ticker = setInterval(() => {
  markActive()
  now.value = Date.now()
}, 1000)
const elapsed = computed(() => {
  if (!startedAt.value) return '00:00'
  const s = Math.max(0, Math.floor((now.value - startedAt.value) / 1000))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
})

const answerText = (q) => {
  if (!isAnswered(q)) return ''
  const v = answers[q.id]
  if (q.type === 'scale') {
    const lo = test.value.scale?.min ?? 1
    return `${v} — ${test.value.scale?.labels?.[v - lo] || ''}`
  }
  return `${LETTERS[v]}) ${q.options[v]}`
}

// ---------- 3-bosqich: topshirish ----------
async function submit() {
  submitError.value = ''
  submitDetail.value = ''
  if (!allAnswered.value) {
    submitError.value = `Barcha savollarga javob bering (${total.value - answeredCount.value} ta javobsiz).`
    return
  }
  if (!allPicturesDone.value) {
    submitError.value = 'Barcha rasmlarga javob bering.'
    return
  }
  if (!validateForm()) {
    phase.value = 'intro'
    return
  }
  submitting.value = true
  try {
    const res = await testApi.submit(slug.value, {
      fullName: form.fullName.trim(),
      age: Number(form.age),
      date: form.date,
      position: form.position,
      phone: normalizePhone(form.phone),
      answers: { ...answers },
      ...(hasPictures.value ? { pictures: { ...picAnswers } } : {}),
      durationSec: durationSeconds(),
      clientId: clientId.value,
    })
    done.value = { name: firstName.value, fullName: form.fullName, position: form.position, submittedAt: res.submittedAt }
    phase.value = 'done'
    scrollTop()
  } catch (e) {
    if (e.status === 409 || (e.status === 422 && e.field === 'phone')) {
      // Raqam band bo‘lib qolgan yoki noto‘g‘ri — javoblar saqlanadi, ma'lumotlar formasida xabar ko‘rsatiladi
      phoneVerified.value = ''
      phase.value = 'intro'
      scrollTop()
      showPhoneError(e.message)
    } else {
      // Tushunarli xabar + asl (texnik) xato — HR ga aytish yoki skrinshot uchun
      submitError.value = e.message || 'Yuborib bo‘lmadi. Qayta urinib ko‘ring.'
      submitDetail.value = e.technical || ''
      if (e.technical) console.warn('Test yuborilmadi:', e.technical, e.raw)
    }
  } finally {
    submitting.value = false
  }
}

function restart() {
  clearDraft()
  Object.keys(answers).forEach((k) => delete answers[k])
  Object.keys(picAnswers).forEach((k) => delete picAnswers[k])
  Object.assign(form, { fullName: '', age: '', date: todayISO(), position: test.value?.positions?.length === 1 ? test.value.positions[0] : '', phone: '' })
  errors.value = {}
  current.value = 0
  stage.value = 0
  highlight.value = false
  startedAt.value = null
  lastActiveAt.value = null
  timeUnknown.value = false
  submitDetail.value = ''
  clientId.value = newId()
  done.value = null
  submitError.value = ''
  phoneVerified.value = ''
  startError.value = ''
  phase.value = 'intro'
  scrollTop()
}

function reload() {
  window.location.reload()
}

function scrollTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const formatSubmitted = (v) => (v ? `${formatDate(v.slice(0, 10))}, ${v.slice(11, 16)}` : '')
const steps = computed(() =>
  isProfile.value
    ? [
        { icon: UserRound, title: 'Ma’lumotlaringiz', text: 'F.I.Sh., yosh, lavozim va telefon' },
        { icon: Layers, title: `${total.value} ta savol · ${stages.value.length} bosqich`, text: '«Qo‘shilmayman» yoki «Qo‘shilaman» — samimiy javob bering' },
        ...(hasPictures.value
          ? [{ icon: ImageIcon, title: `${pictures.value.length} ta rasm`, text: 'Har bir rasmda birinchi ko‘rgan narsangizni tanlang' }]
          : []),
        { icon: BadgeCheck, title: 'HR suhbati', text: 'Natijani HR ko‘rib chiqib siz bilan bog‘lanadi' },
      ]
    : [
        { icon: UserRound, title: 'Ma’lumotlaringiz', text: 'F.I.Sh., yosh, lavozim va telefon' },
        { icon: ListChecks, title: `${total.value} ta savol`, text: 'Shaxsiy sifatlar va savdo vaziyatlari' },
        { icon: BadgeCheck, title: 'HR javobi', text: 'Natijani HR ko‘rib chiqib bog‘lanadi' },
      ],
)
</script>

<template>
  <div class="landing relative min-h-screen overflow-x-hidden bg-[#F5F8FF] text-ink">
    <!-- Fon: to‘r va yorug‘lik -->
    <div class="pointer-events-none fixed inset-0" aria-hidden="true">
      <div class="grid-bg absolute inset-0" />
      <div class="glow glow-a" />
      <div class="glow glow-b" />
    </div>

    <!-- Yuqori panel -->
    <header class="sticky top-0 z-30 border-b border-white/70 bg-white/75 backdrop-blur-xl">
      <div class="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <BrandLogo size="sm" :text="false" />
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-semibold tracking-tight">{{ test?.title || 'Nomzodlar testi' }}</p>
          <p class="hidden truncate text-xs text-muted sm:block">HR+ · Ishga qabul bo‘limi</p>
        </div>
        <div v-if="phase === 'quiz' || phase === 'review'" class="flex items-center gap-2 text-xs font-medium sm:gap-3">
          <span class="hidden items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 tabular-nums text-slate-600 sm:inline-flex"><Clock class="h-3.5 w-3.5" />{{ elapsed }}</span>
          <span class="inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-2.5 py-1 tabular-nums text-primary-700">
            <CheckCircle2 class="h-3.5 w-3.5" />{{ doneCount }}/{{ grandTotal }}
          </span>
        </div>
      </div>
      <!-- Progress bar -->
      <div v-if="phase === 'quiz' || phase === 'review'" class="h-1 w-full bg-primary-100/60" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100" aria-label="Test progressi">
        <div class="progress-fill h-full" :style="{ width: `${progress}%` }" />
      </div>
    </header>

    <main class="relative z-10 mx-auto max-w-6xl px-4 pb-16 pt-8 sm:px-6 lg:pt-12">
      <!-- Yuklanmoqda / xato -->
      <div v-if="loading" class="grid min-h-[60vh] place-items-center">
        <div class="flex items-center gap-3 text-sm text-muted"><Loader2 class="h-5 w-5 animate-spin text-primary-600" /> Test yuklanmoqda...</div>
      </div>
      <div v-else-if="loadError" class="mx-auto mt-10 max-w-md rounded-3xl border border-red-100 bg-white p-8 text-center shadow-pop">
        <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-600"><AlertCircle class="h-6 w-6" /></span>
        <h1 class="mt-4 text-lg font-semibold">Testni ochib bo‘lmadi</h1>
        <p class="mt-2 text-sm text-muted">{{ loadError }}</p>
        <button class="btn-primary mt-6" @click="reload"><RotateCcw class="h-4 w-4" /> Qayta urinish</button>
      </div>

      <Transition v-else name="phase" mode="out-in">
        <!-- ================= 1. Kirish va ma’lumotlar ================= -->
        <section v-if="phase === 'intro'" key="intro" class="grid items-start gap-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:gap-14">
          <div class="reveal">
            <span class="inline-flex items-center gap-2 rounded-full border border-primary-100 bg-white/80 px-3 py-1 text-xs font-semibold text-primary-700 shadow-sm">
              <span class="relative flex h-2 w-2"><span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary-400 opacity-60" /><span class="relative inline-flex h-2 w-2 rounded-full bg-primary-600" /></span>
              {{ isProfile ? 'Yangi xodimlar · HR+' : 'Ochiq vakansiya · Sotuv bo‘limi' }}
            </span>
            <h1 v-if="isProfile" class="mt-5 text-[34px] font-bold leading-[1.08] tracking-tight sm:text-5xl">
              O‘zingiz haqingizda<br class="hidden sm:block" />
              <span class="text-gradient">samimiy</span> javob bering
            </h1>
            <h1 v-else class="mt-5 text-[34px] font-bold leading-[1.08] tracking-tight sm:text-5xl">
              Savdoda kuchli<br class="hidden sm:block" />
              tomonlaringizni <span class="text-gradient">ko‘rsating</span>
            </h1>
            <p v-if="isProfile" class="mt-5 max-w-xl text-[15px] leading-relaxed text-slate-600 sm:text-base">
              {{ test.description }} Javoblaringiz HR bo‘limiga yuboriladi.
            </p>
            <p v-else class="mt-5 max-w-xl text-[15px] leading-relaxed text-slate-600 sm:text-base">
              {{ test.subtitle }}. Javoblaringiz HR bo‘limiga yuboriladi — mos nomzodlar bilan suhbat uchun bog‘lanamiz.
            </p>

            <dl class="mt-8 grid max-w-xl grid-cols-3 gap-3">
              <div class="metric">
                <dt>Savollar</dt>
                <dd>{{ total }}</dd>
              </div>
              <div class="metric">
                <dt>Vaqt</dt>
                <dd>≈{{ isProfile ? 8 : 10 }}<small> daq</small></dd>
              </div>
              <div class="metric">
                <dt>{{ isProfile ? 'Bosqich' : 'Bo‘lim' }}</dt>
                <dd>{{ isProfile ? stageCount : sections.length }}</dd>
              </div>
            </dl>

            <ol class="mt-8 hidden max-w-xl gap-3 sm:grid">
              <li v-for="(s, i) in steps" :key="s.title" class="step-row" :style="{ '--d': `${200 + i * 90}ms` }">
                <span class="step-index">{{ String(i + 1).padStart(2, '0') }}</span>
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-primary-600 shadow-sm ring-1 ring-primary-100"><component :is="s.icon" class="h-5 w-5" /></span>
                <span class="min-w-0">
                  <span class="block text-sm font-semibold">{{ s.title }}</span>
                  <span class="block text-[13px] text-muted">{{ s.text }}</span>
                </span>
              </li>
            </ol>
          </div>

          <!-- Forma -->
          <form class="form-card reveal" style="--d: 120ms" novalidate @submit.prevent="start">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wider text-primary-600">1-bosqich</p>
                <h2 class="mt-1 text-xl font-semibold tracking-tight">Nomzod ma’lumotlari</h2>
              </div>
              <span class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-600/30"><UserRound class="h-5 w-5" /></span>
            </div>

            <div class="mt-6 space-y-4">
              <div class="field">
                <label class="form-label" for="ct-name">F.I.Sh. <span class="text-red-500">*</span></label>
                <div class="input-wrap">
                  <UserRound class="input-icon" />
                  <input id="ct-name" v-model="form.fullName" class="form-input has-icon" :class="{ 'has-error': errors.fullName }" placeholder="Familiya Ism Otasining ismi" autocomplete="name" maxlength="120" @input="clearError('fullName')" />
                </div>
                <p v-if="errors.fullName" class="form-error field-error">{{ errors.fullName }}</p>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="field">
                  <label class="form-label" for="ct-age">Yosh <span class="text-red-500">*</span></label>
                  <div class="input-wrap">
                    <Target class="input-icon" />
                    <input id="ct-age" v-model="form.age" class="form-input has-icon" :class="{ 'has-error': errors.age }" type="number" inputmode="numeric" min="16" max="70" placeholder="25" @input="clearError('age')" />
                  </div>
                  <p v-if="errors.age" class="form-error field-error">{{ errors.age }}</p>
                </div>
                <div class="field">
                  <label class="form-label" for="ct-date">Sana <span class="text-red-500">*</span></label>
                  <div class="input-wrap">
                    <CalendarDays class="input-icon" />
                    <input id="ct-date" v-model="form.date" class="form-input has-icon" :class="{ 'has-error': errors.date }" type="date" @input="clearError('date')" />
                  </div>
                  <p v-if="errors.date" class="form-error field-error">{{ errors.date }}</p>
                </div>
              </div>

              <div class="field">
                <p id="ct-pos-label" class="form-label">Lavozim <span class="text-red-500">*</span></p>
                <div role="radiogroup" aria-labelledby="ct-pos-label" class="grid gap-2">
                  <button
                    v-for="p in test.positions"
                    :key="p"
                    type="button"
                    role="radio"
                    :aria-checked="form.position === p"
                    :class="['pos-option', form.position === p && 'is-active']"
                    @click="form.position = p; clearError('position')"
                  >
                    <Briefcase class="h-4 w-4 shrink-0" />
                    <span class="flex-1">{{ p }}</span>
                    <span class="pos-dot" />
                  </button>
                </div>
                <p v-if="errors.position" class="form-error field-error">{{ errors.position }}</p>
              </div>

              <div class="field">
                <label class="form-label" for="ct-phone">Telefon <span class="text-red-500">*</span> <span class="font-normal text-muted">(majburiy)</span></label>
                <div class="input-wrap">
                  <Phone class="input-icon" />
                  <input
                    id="ct-phone"
                    v-model="form.phone"
                    class="form-input has-icon"
                    :class="{ 'has-error': errors.phone }"
                    type="tel"
                    inputmode="tel"
                    placeholder="+998 90 123 45 67"
                    autocomplete="tel"
                    maxlength="30"
                    required
                    :aria-invalid="!!errors.phone"
                    :aria-describedby="errors.phone ? 'ct-phone-error' : undefined"
                    @input="clearError('phone')"
                    @blur="formatPhoneField"
                  />
                </div>
                <p v-if="errors.phone" id="ct-phone-error" class="form-error field-error" role="alert">{{ errors.phone }}</p>
              </div>
            </div>

            <p v-if="startError" class="mt-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
              <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> {{ startError }}
            </p>

            <button type="submit" class="btn-primary btn-lg group mt-6 w-full" :disabled="checkingPhone">
              <Loader2 v-if="checkingPhone" class="h-4 w-4 animate-spin" />
              {{ checkingPhone ? 'Tekshirilmoqda...' : answeredCount ? 'Testni davom ettirish' : 'Testni boshlash' }}
              <ArrowRight v-if="!checkingPhone" class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </button>
            <p class="mt-4 flex items-center justify-center gap-1.5 text-center text-xs text-muted">
              <ShieldCheck class="h-3.5 w-3.5 text-primary-500" /> Ma’lumotlaringiz faqat HR bo‘limiga ko‘rinadi
            </p>
          </form>
        </section>

        <!-- ================= 2a. Savollar: 4 bosqich × 10 ta (profil testi) ================= -->
        <section v-else-if="phase === 'quiz' && isProfile" key="stages" class="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:gap-8">
          <aside class="hidden lg:block">
            <div class="sticky top-24 space-y-4">
              <div class="side-card">
                <div class="flex items-center gap-3">
                  <span class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-primary-600 to-primary-500 text-sm font-bold text-white shadow-md shadow-primary-600/30">
                    {{ form.fullName.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase() }}
                  </span>
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold">{{ form.fullName }}</p>
                    <p class="truncate text-xs text-muted">{{ form.position }}</p>
                  </div>
                </div>
                <div class="mt-4 space-y-3">
                  <div v-for="i in stageCount" :key="i">
                    <div class="flex items-center justify-between text-xs">
                      <span :class="['font-medium', i - 1 === stage ? 'text-primary-700' : 'text-slate-600']">{{ i }}-bosqich · {{ stageRange(i - 1) }}</span>
                      <span class="tabular-nums text-muted">{{ stageAnswered(i - 1) }}/{{ stageSize(i - 1) }}</span>
                    </div>
                    <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div class="progress-fill h-full rounded-full" :style="{ width: `${(stageAnswered(i - 1) / (stageSize(i - 1) || 1)) * 100}%` }" />
                    </div>
                  </div>
                </div>
              </div>
              <p class="flex items-start gap-2 px-1 text-xs leading-relaxed text-muted">
                <Sparkles class="mt-0.5 h-3.5 w-3.5 shrink-0" />
                To‘g‘ri yoki noto‘g‘ri javob yo‘q — birinchi xayolingizga kelgan, samimiy javobni tanlang.
              </p>
            </div>
          </aside>

          <div class="min-w-0">
            <nav class="grid gap-2" :style="{ gridTemplateColumns: `repeat(${stageCount}, minmax(0, 1fr))` }" aria-label="Test bosqichlari">
              <button
                v-for="n in stageCount"
                :key="n"
                type="button"
                :disabled="!stageReachable(n - 1) || submitting"
                :aria-current="n - 1 === stage ? 'step' : undefined"
                :aria-label="`${n}-bosqich${n - 1 === picStage ? ' (rasmlar)' : ''}: ${stageAnswered(n - 1)}/${stageSize(n - 1)} ta javob`"
                :class="['stage-tab', stageDone(n - 1) && 'is-done', n - 1 === stage && 'is-current']"
                @click="goStage(n - 1)"
              >
                <span class="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide sm:text-xs">
                  <span class="stage-dot"><Check v-if="stageDone(n - 1) && n - 1 !== stage" class="h-3 w-3" stroke-width="3.5" /><ImageIcon v-else-if="n - 1 === picStage" class="h-3 w-3" /><template v-else>{{ n }}</template></span>
                  <span class="hidden sm:inline">{{ n - 1 === picStage ? 'Rasmlar' : `${n}-bosqich` }}</span>
                </span>
                <span class="mt-1 block text-[11px] tabular-nums opacity-80">{{ stageAnswered(n - 1) }}/{{ stageSize(n - 1) }}</span>
              </button>
            </nav>

            <div class="question-card mt-4">
              <div class="flex flex-wrap items-end justify-between gap-2 border-b border-line pb-4">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wider text-primary-600">{{ stage + 1 }}-bosqich / {{ stageCount }}</p>
                  <h2 v-if="isPictureStage" class="mt-1 text-xl font-semibold tracking-tight">Rasmli savollar</h2>
                  <h2 v-else class="mt-1 text-xl font-semibold tracking-tight">{{ stageOffset + 1 }}–{{ stageOffset + stageQuestions.length }}-savollar</h2>
                </div>
                <p v-if="isPictureStage" class="text-xs text-muted">Har bir rasmga qarang va birinchi bo‘lib ko‘rgan narsangizni tanlang</p>
                <p v-else class="text-xs text-muted">Har bir fikrga: «{{ agreeOptions[0] }}» yoki «{{ agreeOptions[1] }}»</p>
              </div>

              <Transition :name="direction > 0 ? 'q-next' : 'q-prev'" mode="out-in">
                <!-- Rasmli savollar (oxirgi bosqich) -->
                <ol v-if="isPictureStage" key="pictures" class="divide-y divide-line">
                  <li v-for="(p, k) in pictures" :id="`pic-${p.id}`" :key="p.id" :class="['q-row scroll-mt-28 !py-6', highlight && !isPicDone(p) && 'is-missing']">
                    <PictureQuestion
                      :picture="p"
                      :src="assetUrl(p.image)"
                      :number="k + 1"
                      :model-value="picAnswers[p.id] ?? null"
                      :invalid="highlight && !isPicDone(p)"
                      @update:model-value="selectPicture(p, $event)"
                    />
                  </li>
                </ol>
                <ol v-else :key="stage" class="divide-y divide-line">
                  <li v-for="(q, k) in stageQuestions" :id="`q-${q.id}`" :key="q.id" :class="['q-row scroll-mt-28', highlight && !isAnswered(q) && 'is-missing']">
                    <div class="flex items-start gap-3">
                      <span :class="['q-badge', isAnswered(q) && 'is-done']" aria-hidden="true">{{ stageOffset + k + 1 }}</span>
                      <p class="min-w-0 flex-1 pt-1 text-[15px] font-medium leading-snug text-ink sm:text-base">{{ q.text }}</p>
                    </div>
                    <div class="mt-3 sm:pl-11">
                      <AgreeAnswer
                        :model-value="answers[q.id] ?? null"
                        :options="q.options || agreeOptions"
                        :name="`${stageOffset + k + 1}-savol: ${q.text}`"
                        :invalid="highlight && !isAnswered(q)"
                        @update:model-value="selectAgree(q, $event)"
                      />
                    </div>
                  </li>
                </ol>
              </Transition>

              <p v-if="submitError" class="mt-4 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
                <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" />
                <span class="min-w-0">{{ submitError }}<span v-if="submitDetail" class="mt-1 block break-words text-xs text-red-500/80">Texnik ma’lumot: {{ submitDetail }}</span></span>
              </p>

              <div class="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5">
                <button type="button" class="btn-ghost" :disabled="submitting" @click="prevStage">
                  <ArrowLeft class="h-4 w-4" /> {{ stage === 0 ? 'Ma’lumotlar' : 'Orqaga' }}
                </button>
                <span class="hidden text-xs tabular-nums text-muted sm:block">{{ stageAnswered(stage) }}/{{ stageSize(stage) }} ta javob · {{ progress }}%</span>
                <button v-if="isLastStage" type="button" class="btn-primary btn-finish" :disabled="submitting" @click="finishProfile">
                  <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
                  <Flag v-else class="h-4 w-4" />
                  {{ submitting ? 'Yuborilmoqda...' : 'Testni yakunlash' }}
                </button>
                <button v-else type="button" class="btn-primary" @click="nextStage">Oldinga <ArrowRight class="h-4 w-4" /></button>
              </div>
            </div>
          </div>
        </section>

        <!-- ================= 2. Savollar (eski format: bitta-bitta) ================= -->
        <section v-else-if="phase === 'quiz'" key="quiz" class="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:gap-8">
          <!-- Chap panel (kompyuter) -->
          <aside class="hidden lg:block">
            <div class="sticky top-24 space-y-4">
              <div class="side-card">
                <div class="flex items-center gap-3">
                  <span class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-primary-600 to-primary-500 text-sm font-bold text-white shadow-md shadow-primary-600/30">
                    {{ form.fullName.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase() }}
                  </span>
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold">{{ form.fullName }}</p>
                    <p class="truncate text-xs text-muted">{{ form.position }}</p>
                  </div>
                </div>
                <div class="mt-4 space-y-3">
                  <div v-for="s in sections" :key="s.id">
                    <div class="flex items-center justify-between text-xs">
                      <span class="font-medium text-slate-600">{{ s.title }}</span>
                      <span class="tabular-nums text-muted">{{ s.items.filter((x) => isAnswered(x.q)).length }}/{{ s.items.length }}</span>
                    </div>
                    <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div class="progress-fill h-full rounded-full" :style="{ width: `${(s.items.filter((x) => isAnswered(x.q)).length / s.items.length) * 100}%` }" />
                    </div>
                  </div>
                </div>
              </div>

              <div class="side-card">
                <p class="text-xs font-semibold uppercase tracking-wider text-muted">Savollar xaritasi</p>
                <div v-for="s in sections" :key="s.id" class="mt-3">
                  <p class="mb-2 text-[11px] font-medium text-slate-500">{{ s.from }}–{{ s.to }} · {{ s.title }}</p>
                  <div class="grid grid-cols-5 gap-1.5">
                    <button
                      v-for="x in s.items"
                      :key="x.q.id"
                      type="button"
                      :disabled="!reachable(x.index)"
                      :aria-label="`${x.index + 1}-savol`"
                      :aria-current="x.index === current ? 'step' : undefined"
                      :class="['map-dot', isAnswered(x.q) && 'is-done', x.index === current && 'is-current']"
                      @click="go(x.index)"
                    >
                      {{ x.index + 1 }}
                    </button>
                  </div>
                </div>
              </div>

              <p class="flex items-start gap-2 px-1 text-xs leading-relaxed text-muted">
                <Keyboard class="mt-0.5 h-3.5 w-3.5 shrink-0" />
                Klaviatura: 1–5 yoki A–D — javob, ← → — savollar orasida
              </p>
            </div>
          </aside>

          <div class="min-w-0">
            <!-- Mobil: savollar xaritasi -->
            <div class="-mx-4 mb-4 overflow-x-auto px-4 pb-1 lg:hidden">
              <div class="flex w-max gap-1.5">
                <button
                  v-for="(q, i) in questions"
                  :key="q.id"
                  type="button"
                  :disabled="!reachable(i)"
                  :aria-label="`${i + 1}-savol`"
                  :data-mdot="i"
                  :class="['map-dot w-9', isAnswered(q) && 'is-done', i === current && 'is-current']"
                  @click="go(i)"
                >
                  {{ i + 1 }}
                </button>
              </div>
            </div>

            <div class="question-card">
              <Transition :name="direction > 0 ? 'q-next' : 'q-prev'" mode="out-in">
                <div :key="question.id">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-700">{{ sectionOf(question)?.title }}</span>
                    <span class="text-xs text-muted">{{ question.type === 'scale' ? '1–5 ballik baho' : 'Bitta variantni tanlang' }}</span>
                  </div>
                  <div class="mt-5 flex items-start gap-4 sm:gap-6">
                    <span class="q-number" aria-hidden="true">{{ String(current + 1).padStart(2, '0') }}</span>
                    <div class="min-w-0 flex-1 pt-1">
                      <p class="text-xs font-medium text-muted">Savol {{ current + 1 }} / {{ total }}</p>
                      <h2 class="mt-1.5 text-xl font-semibold leading-snug tracking-tight sm:text-2xl">{{ question.text }}</h2>
                    </div>
                  </div>
                  <p v-if="current + 1 === sectionOf(question)?.from" class="mt-4 rounded-xl border border-primary-100 bg-primary-50/60 px-4 py-3 text-[13px] leading-relaxed text-primary-800">
                    <Sparkles class="mr-1 inline h-3.5 w-3.5 -translate-y-px" /> {{ sectionOf(question)?.description }}
                  </p>

                  <div class="mt-7">
                    <ScaleAnswer
                      v-if="question.type === 'scale'"
                      :model-value="answers[question.id] ?? null"
                      :min="test.scale?.min ?? 1"
                      :max="test.scale?.max ?? 5"
                      :labels="test.scale?.labels"
                      :name="question.text"
                      @update:model-value="select"
                    />
                    <ChoiceAnswer v-else :model-value="answers[question.id] ?? null" :options="question.options" :name="question.text" @update:model-value="select" />
                  </div>
                </div>
              </Transition>

              <div class="mt-8 flex items-center justify-between gap-3 border-t border-line pt-5">
                <button type="button" class="btn-ghost" @click="prev">
                  <ArrowLeft class="h-4 w-4" /> {{ current === 0 ? 'Ma’lumotlar' : 'Orqaga' }}
                </button>
                <span class="hidden text-xs tabular-nums text-muted sm:block">{{ progress }}% bajarildi</span>
                <button type="button" class="btn-primary" :disabled="!isAnswered(question)" @click="next">
                  {{ current === total - 1 ? 'Yakunlash' : 'Keyingi' }} <ArrowRight class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- ================= 3. Tekshirish va topshirish ================= -->
        <section v-else-if="phase === 'review'" key="review" class="mx-auto max-w-3xl">
          <div class="text-center">
            <span class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-600/30"><ListChecks class="h-7 w-7" /></span>
            <h1 class="mt-5 text-3xl font-bold tracking-tight">Javoblaringizni tekshiring</h1>
            <p class="mt-2 text-sm text-muted">Istalgan javobni o‘zgartirishingiz mumkin. Topshirgandan keyin o‘zgartirib bo‘lmaydi.</p>
          </div>

          <div class="mt-8 grid grid-cols-3 gap-3">
            <div class="metric text-center"><dt>Javob berildi</dt><dd>{{ answeredCount }}<small>/{{ total }}</small></dd></div>
            <div class="metric text-center"><dt>Sarflangan vaqt</dt><dd class="tabular-nums">{{ elapsed }}</dd></div>
            <div class="metric text-center"><dt>Lavozim</dt><dd class="truncate !text-base !leading-9">{{ form.position }}</dd></div>
          </div>

          <div v-for="s in sections" :key="s.id" class="review-card mt-5">
            <h2 class="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5 text-sm font-semibold">
              {{ s.title }} <span class="text-xs font-normal text-muted">{{ s.from }}–{{ s.to }}-savollar</span>
            </h2>
            <ul class="divide-y divide-line">
              <li v-for="x in s.items" :key="x.q.id">
                <button type="button" class="group flex w-full items-start gap-3 px-5 py-3 text-left transition-colors hover:bg-primary-50/50" @click="editQuestion(x.index)">
                  <span :class="['mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-bold tabular-nums', isAnswered(x.q) ? 'bg-primary-50 text-primary-700' : 'bg-red-50 text-red-600']">{{ x.index + 1 }}</span>
                  <span class="min-w-0 flex-1">
                    <span class="block text-sm text-slate-700">{{ x.q.text }}</span>
                    <span v-if="isAnswered(x.q)" class="mt-0.5 block text-[13px] font-medium text-primary-700">{{ answerText(x.q) }}</span>
                    <span v-else class="mt-0.5 block text-[13px] font-medium text-red-600">Javob berilmagan</span>
                  </span>
                  <Pencil class="mt-1 h-4 w-4 shrink-0 text-slate-300 transition-colors group-hover:text-primary-600" />
                </button>
              </li>
            </ul>
          </div>

          <p v-if="submitError" class="mt-5 flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" />
                <span class="min-w-0">{{ submitError }}<span v-if="submitDetail" class="mt-1 block break-words text-xs text-red-500/80">Texnik ma’lumot: {{ submitDetail }}</span></span>
          </p>

          <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
            <button type="button" class="btn-ghost justify-center" @click="editQuestion(allAnswered ? total - 1 : firstUnanswered)">
              <ArrowLeft class="h-4 w-4" /> Savollarga qaytish
            </button>
            <button type="button" class="btn-primary btn-lg" :disabled="!allAnswered || submitting" @click="submit">
              <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
              <Send v-else class="h-4 w-4" />
              Testni topshirish
            </button>
          </div>
          <p v-if="!allAnswered" class="mt-3 text-right text-xs text-red-600">Topshirish uchun barcha {{ total }} ta savolga javob bering</p>
        </section>

        <!-- ================= 4. Yakun ================= -->
        <section v-else key="done" class="mx-auto max-w-xl pt-6 text-center">
          <div class="done-badge mx-auto">
            <span class="ripple" /><span class="ripple ripple-late" />
            <CheckCircle2 class="relative h-12 w-12" />
          </div>
          <h1 class="mt-8 text-3xl font-bold tracking-tight sm:text-4xl">Rahmat{{ done?.name ? `, ${done.name}` : '' }}!</h1>
          <p class="mx-auto mt-3 max-w-md text-[15px] leading-relaxed text-slate-600">
            Javoblaringiz qabul qilindi va HR bo‘limiga yuborildi. Natija ko‘rib chiqilgach, siz bilan bog‘lanamiz.
          </p>
          <dl class="mx-auto mt-8 grid max-w-md gap-px overflow-hidden rounded-2xl border border-line bg-line text-left text-sm shadow-sm">
            <div class="flex justify-between gap-4 bg-white px-5 py-3"><dt class="text-muted">Nomzod</dt><dd class="truncate font-medium">{{ done?.fullName }}</dd></div>
            <div class="flex justify-between gap-4 bg-white px-5 py-3"><dt class="text-muted">Lavozim</dt><dd class="font-medium">{{ done?.position }}</dd></div>
            <div class="flex justify-between gap-4 bg-white px-5 py-3"><dt class="text-muted">Topshirildi</dt><dd class="font-medium tabular-nums">{{ formatSubmitted(done?.submittedAt) }}</dd></div>
          </dl>
          <button type="button" class="btn-ghost mx-auto mt-8" @click="restart"><RotateCcw class="h-4 w-4" /> Boshqa nomzod uchun yangi test</button>
        </section>
      </Transition>
    </main>
  </div>
</template>

<style scoped>
/* ---------- Fon ---------- */
.grid-bg {
  background-image: linear-gradient(rgba(37, 99, 235, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 99, 235, 0.06) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%);
}
.glow {
  @apply absolute rounded-full blur-3xl;
}
.glow-a {
  width: 520px;
  height: 520px;
  top: -180px;
  right: -120px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.28), transparent 65%);
  animation: drift 16s ease-in-out infinite alternate;
}
.glow-b {
  width: 460px;
  height: 460px;
  bottom: -200px;
  left: -160px;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.35), transparent 65%);
  animation: drift 20s ease-in-out infinite alternate-reverse;
}
@keyframes drift {
  to {
    transform: translate(-40px, 40px) scale(1.08);
  }
}
.text-gradient {
  @apply bg-gradient-to-r from-primary-700 via-primary-600 to-sky-500 bg-clip-text text-transparent;
}
.progress-fill {
  @apply bg-gradient-to-r from-primary-600 via-primary-500 to-sky-400 transition-[width] duration-500 ease-out;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.55);
}

/* ---------- Kartalar ---------- */
.metric {
  @apply rounded-2xl border border-white bg-white/80 px-4 py-3 shadow-[0_8px_24px_-16px_rgba(15,23,42,0.25)] backdrop-blur transition-transform duration-200 hover:-translate-y-0.5;
}
.metric dt {
  @apply text-[11px] font-medium uppercase tracking-wider text-muted;
}
.metric dd {
  @apply mt-1 text-2xl font-bold tabular-nums leading-9 tracking-tight text-ink;
}
.metric small {
  @apply text-sm font-medium text-muted;
}
.step-row {
  @apply relative flex items-center gap-4 rounded-2xl border border-transparent p-2 pr-4 transition-all duration-200 hover:border-white hover:bg-white/70 hover:shadow-sm;
  animation: fade-up 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  animation-delay: var(--d);
}
.step-index {
  @apply w-6 text-xs font-bold tabular-nums text-primary-300;
}
.form-card {
  @apply relative rounded-[28px] border border-white bg-white/90 p-6 shadow-[0_30px_80px_-40px_rgba(30,64,175,0.45),0_2px_8px_-2px_rgba(15,23,42,0.06)] backdrop-blur-xl sm:p-8;
}
.form-card::before {
  content: '';
  @apply pointer-events-none absolute inset-x-8 -top-px h-px bg-gradient-to-r from-transparent via-primary-400 to-transparent;
}
.side-card {
  @apply rounded-3xl border border-white bg-white/85 p-5 shadow-[0_16px_40px_-28px_rgba(30,64,175,0.4)] backdrop-blur;
}
.question-card {
  @apply relative overflow-hidden rounded-[28px] border border-white bg-white/90 p-5 shadow-[0_30px_80px_-40px_rgba(30,64,175,0.45),0_2px_8px_-2px_rgba(15,23,42,0.06)] backdrop-blur-xl sm:p-8 lg:p-10;
}
.review-card {
  @apply overflow-hidden rounded-3xl border border-white bg-white/90 shadow-[0_16px_40px_-28px_rgba(30,64,175,0.4)];
}
.q-number {
  @apply select-none text-5xl font-bold leading-none tabular-nums tracking-tighter sm:text-7xl;
  color: transparent;
  -webkit-text-stroke: 1.5px rgba(37, 99, 235, 0.45);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.12), transparent);
  -webkit-background-clip: text;
  background-clip: text;
}

/* ---------- Maydonlar ---------- */
.input-wrap {
  @apply relative;
}
.input-icon {
  @apply pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400;
}
.form-input.has-icon {
  @apply h-11 rounded-xl pl-9;
}
.pos-option {
  @apply flex h-11 w-full items-center gap-3 rounded-xl border border-line bg-white px-3.5 text-left text-sm font-medium text-slate-600 transition-all duration-150;
  @apply hover:border-primary-300 hover:text-ink focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/15;
}
.pos-dot {
  @apply h-4 w-4 rounded-full border-2 border-slate-300 transition-all duration-150;
}
.pos-option.is-active {
  @apply border-primary-500 bg-primary-50/70 text-primary-800 shadow-[0_8px_20px_-14px_rgba(37,99,235,0.7)];
}
.pos-option.is-active .pos-dot {
  @apply border-[5px] border-primary-600;
}

/* ---------- Tugmalar ---------- */
.btn-primary {
  @apply inline-flex h-11 select-none items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-5 text-sm font-semibold text-white shadow-lg shadow-primary-600/25 transition-all duration-200;
  @apply hover:-translate-y-0.5 hover:shadow-xl hover:shadow-primary-600/30 active:translate-y-0 active:scale-[0.98];
  @apply focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/25 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none;
}
.btn-lg {
  @apply h-12 px-6 text-[15px];
}
.btn-ghost {
  @apply inline-flex h-11 items-center gap-2 rounded-xl px-4 text-sm font-medium text-slate-600 transition-colors hover:bg-white hover:text-ink hover:shadow-sm focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/15;
}

/* ---------- Savollar xaritasi ---------- */
.map-dot {
  @apply grid h-9 place-items-center rounded-lg border border-line bg-white text-xs font-semibold tabular-nums text-slate-500 transition-all duration-150;
  @apply hover:border-primary-300 hover:text-primary-700 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-line disabled:hover:text-slate-500;
}
.map-dot.is-done {
  @apply border-primary-100 bg-primary-50 text-primary-700;
}
.map-dot.is-current {
  @apply border-transparent bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/30;
}

/* ---------- Bosqichlar (profil testi) ---------- */
.stage-tab {
  @apply rounded-xl border border-line bg-white px-2 py-2 text-left text-slate-500 transition-all duration-150 sm:px-3;
  @apply hover:-translate-y-0.5 hover:border-primary-300 disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0;
}
.stage-tab.is-done {
  @apply border-emerald-100 bg-emerald-50/70 text-emerald-700;
}
.stage-tab.is-current {
  @apply border-transparent bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/30;
}
.stage-dot {
  @apply grid h-5 w-5 place-items-center rounded-full text-[11px] font-bold tabular-nums;
  border: 1.5px solid currentColor;
}
.q-row {
  @apply -mx-2 rounded-xl px-2 py-4 transition-colors duration-200 sm:-mx-3 sm:px-3;
}
.q-row.is-missing {
  @apply bg-red-50/60;
}
.q-badge {
  @apply grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-xs font-bold tabular-nums text-slate-500 transition-colors;
}
.q-badge.is-done {
  @apply bg-primary-50 text-primary-700;
}
.btn-finish {
  @apply from-emerald-600 to-emerald-500 shadow-emerald-600/25 hover:shadow-emerald-600/30;
}

/* ---------- Yakun ---------- */
.done-badge {
  @apply relative grid h-24 w-24 place-items-center rounded-full bg-gradient-to-br from-primary-600 to-sky-500 text-white shadow-2xl shadow-primary-600/40;
  animation: pop 0.6s cubic-bezier(0.2, 1.4, 0.4, 1) both;
}
.done-badge .ripple {
  @apply absolute inset-0 rounded-full border-2 border-primary-400;
  animation: ripple 2.4s ease-out infinite;
}
.done-badge .ripple-late {
  animation-delay: 1.2s;
}
@keyframes pop {
  from {
    transform: scale(0.4);
    opacity: 0;
  }
}
@keyframes ripple {
  from {
    transform: scale(1);
    opacity: 0.7;
  }
  to {
    transform: scale(1.9);
    opacity: 0;
  }
}

/* ---------- O‘tishlar ---------- */
.reveal {
  animation: fade-up 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  animation-delay: var(--d, 0ms);
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
  transition: opacity 0.22s ease, transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
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
  .reveal,
  .step-row,
  .done-badge,
  .done-badge .ripple {
    animation: none !important;
  }
}
</style>