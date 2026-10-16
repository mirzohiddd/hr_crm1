<script setup>
import { computed, ref } from 'vue'
import {
  AlertTriangle, Briefcase, CheckCircle2, ClipboardCopy, Download, Gavel, Info, ListChecks, MessageCircleQuestion,
  ShieldAlert, ShieldCheck, Sparkles, Sprout, ThumbsDown, ThumbsUp, TrendingDown, TrendingUp, UsersRound,
} from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useToast } from '@/composables/useToast'

/**
 * «Ishdagi shaxsiyat 360» (landing /test/sotuv, format=persona) — HR uchun batafsil hisobot.
 * Barcha raqamlar backendda xodimning haqiqiy javoblaridan hisoblangan (backend/app/persona_test.py);
 * bu komponent faqat ko‘rsatadi. "Nusxalash" — backend tuzgan matn (reportText).
 */
const props = defineProps({ detail: { type: Object, required: true } })
const toast = useToast()

const r = computed(() => props.detail.report || {})
const rel = computed(() => r.value.reliability || {})
const traits = computed(() => r.value.traits || [])
const directions = computed(() => r.value.directions || [])
const items = computed(() => props.detail.items || [])

// Yo‘nalish ranglari: yashil/ko‘k — yuqori bo‘lgani yaxshi, sariq/qizil — past bo‘lgani yaxshi
const COLORS = {
  green: { hex: '#059669', soft: 'bg-emerald-50', text: 'text-emerald-700', bar: 'bg-emerald-500', ring: 'ring-emerald-600/15' },
  blue: { hex: '#2563eb', soft: 'bg-primary-50', text: 'text-primary-700', bar: 'bg-primary-600', ring: 'ring-primary-600/15' },
  amber: { hex: '#d97706', soft: 'bg-amber-50', text: 'text-amber-700', bar: 'bg-amber-500', ring: 'ring-amber-600/20' },
  red: { hex: '#dc2626', soft: 'bg-red-50', text: 'text-red-700', bar: 'bg-red-500', ring: 'ring-red-600/15' },
}
const dirById = computed(() => Object.fromEntries(directions.value.map((d) => [d.id, d])))
const colorOf = (trait) => COLORS[dirById.value[trait.direction]?.color] || COLORS.blue
const dirColor = (d) => COLORS[d.color] || COLORS.blue

const REL = {
  yuqori: { label: 'yuqori', icon: ShieldCheck, box: 'border-emerald-100 bg-emerald-50/60', text: 'text-emerald-700' },
  'o‘rtacha': { label: 'o‘rtacha', icon: ShieldAlert, box: 'border-amber-100 bg-amber-50/60', text: 'text-amber-700' },
  past: { label: 'past', icon: ShieldAlert, box: 'border-red-100 bg-red-50/60', text: 'text-red-700' },
}
const relView = computed(() => REL[rel.value.level] || REL['o‘rtacha'])
const PROFILE_TONE = { attention: 'from-amber-500 to-red-500', strong: 'from-emerald-500 to-teal-500', balanced: 'from-primary-600 to-sky-500', develop: 'from-slate-500 to-slate-400' }
const DECISION_TONE = {
  'Ishga olish tavsiya etiladi': 'border-emerald-200 bg-emerald-50 text-emerald-800',
  'Suhbatdan keyin qaror qiling': 'border-amber-200 bg-amber-50 text-amber-800',
  'Ehtiyotkorlik bilan': 'border-orange-200 bg-orange-50 text-orange-800',
  'Natija ishonchsiz': 'border-red-200 bg-red-50 text-red-800',
}

// ---------- Radar ----------
const SIZE = 420
const C = SIZE / 2
const RADIUS = 130
const angle = (i, n) => -Math.PI / 2 + (2 * Math.PI * i) / n
const pt = (i, n, k) => [C + Math.cos(angle(i, n)) * RADIUS * k, C + Math.sin(angle(i, n)) * RADIUS * k]
const rings = [1 / 3, 2 / 3, 1]
const ringPath = (k) => traits.value.map((_, i) => pt(i, traits.value.length, k).join(',')).join(' ')
const shape = computed(() => traits.value.map((t, i) => pt(i, traits.value.length, Math.max(t.percent, 4) / 100).join(',')).join(' '))
const labelPos = (i) => {
  const n = traits.value.length
  const [x, y] = pt(i, n, 1.12)
  const cos = Math.cos(angle(i, n))
  const sin = Math.sin(angle(i, n))
  // Yuqoridagi yagona o‘q — markazda; qolganlari chap/o‘ng tomonga tekislanadi (pastdagilar ustma-ust tushmasin)
  const anchor = Math.abs(cos) < 0.05 ? 'middle' : cos > 0 ? 'start' : 'end'
  return { x, y: y + (sin > 0.5 ? 8 : sin < -0.5 ? -10 : 0), anchor }
}
const hover = ref(null)

// ---------- Javoblar ----------
const showAnswers = ref(false)
const answerFilter = ref('all')
const shownItems = computed(() => {
  if (answerFilter.value === 'reverse') return items.value.filter((i) => i.key === 'reverse')
  if (answerFilter.value === 'attention') return items.value.filter((i) => i.attention)
  return items.value
})

// ---------- Nusxalash ----------
async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    let ok = false
    try {
      ok = document.execCommand('copy')
    } catch {
      ok = false
    }
    ta.remove()
    return ok
  }
}
async function copyReport() {
  if (await copyText(props.detail.reportText || '')) toast.success('Natija nusxalandi', 'Telegram yoki boshqa joyga joylashtiring')
  else toast.error('Nusxalab bo‘lmadi', '“Yuklab olish” tugmasidan foydalaning')
}
function downloadReport() {
  const blob = new Blob([`﻿${props.detail.reportText || ''}`], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ishdagi-shaxsiyat-${(props.detail.fullName || props.detail.id).toString().replace(/[^\p{L}\p{N}]+/gu, '-')}.txt`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<template>
  <div class="space-y-5">
    <!-- Sarlavha: profil -->
    <section class="overflow-hidden rounded-2xl border border-line">
      <div :class="['h-1.5 bg-gradient-to-r', PROFILE_TONE[r.profile?.kind] || PROFILE_TONE.balanced]" />
      <div class="p-4 sm:p-5">
        <p class="text-xs font-semibold uppercase tracking-wider text-muted">{{ (r.name || detail.fullName || '').toUpperCase() }} · ISHDAGI SHAXSIYAT</p>
        <h3 class="mt-1 text-xl font-bold tracking-tight text-ink">{{ r.profile?.title }}</h3>
        <p class="mt-1 text-sm leading-relaxed text-slate-600">{{ r.profile?.text }}</p>
        <div class="mt-4 grid gap-3 sm:grid-cols-3">
          <div class="tile">
            <p class="tile-value text-emerald-600">{{ r.positive }}%</p>
            <p class="tile-label">Yuqori samaradorlik xususiyatlari</p>
          </div>
          <div class="tile">
            <p class="tile-value text-red-600">{{ r.negative }}%</p>
            <p class="tile-label">To‘sqinlik qiluvchi xususiyatlar</p>
          </div>
          <div :class="['tile border', relView.box]">
            <p :class="['tile-value flex items-center gap-1.5', relView.text]"><component :is="relView.icon" class="h-5 w-5" />{{ relView.label }}</p>
            <p class="tile-label">Javoblar ishonchliligi</p>
          </div>
        </div>
        <p v-if="rel.level !== 'yuqori'" :class="['mt-3 flex items-start gap-2 text-sm', relView.text]"><AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" /> {{ rel.text }}</p>
      </div>
    </section>

    <!-- Shaxsiyat profili: radar -->
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h3 class="sec-title"><Sparkles class="h-4 w-4 text-primary-600" /> Shaxsiyat profili</h3>
        <ul class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
          <li v-for="d in directions" :key="d.id" class="inline-flex items-center gap-1.5">
            <span class="h-2.5 w-2.5 rounded-full" :style="{ background: dirColor(d).hex }" />{{ d.title }}
          </li>
        </ul>
      </div>
      <div class="mx-auto mt-2 max-w-[560px]">
        <svg :viewBox="`-130 -10 ${SIZE + 260} ${SIZE + 20}`" class="h-auto w-full" role="img" :aria-label="`Shaxsiyat profili: ${traits.map((t) => `${t.title} ${t.percent}%`).join(', ')}`">
          <polygon v-for="k in rings" :key="k" :points="ringPath(k)" fill="none" stroke="#e2e8f0" stroke-width="1" />
          <line v-for="(t, i) in traits" :key="`ax-${t.id}`" :x1="C" :y1="C" :x2="pt(i, traits.length, 1)[0]" :y2="pt(i, traits.length, 1)[1]" stroke="#e2e8f0" stroke-width="1" />
          <polygon :points="shape" fill="rgba(37, 99, 235, 0.12)" stroke="#2563eb" stroke-width="2" stroke-linejoin="round" />
          <g v-for="(t, i) in traits" :key="`pt-${t.id}`" @mouseenter="hover = t.id" @mouseleave="hover = null">
            <circle :cx="pt(i, traits.length, 1)[0]" :cy="pt(i, traits.length, 1)[1]" r="16" fill="transparent" />
            <circle :cx="pt(i, traits.length, Math.max(t.percent, 4) / 100)[0]" :cy="pt(i, traits.length, Math.max(t.percent, 4) / 100)[1]" :r="hover === t.id ? 6 : 4.5" :fill="colorOf(t).hex" stroke="#fff" stroke-width="2">
              <title>{{ t.title }}: {{ t.percent }}%</title>
            </circle>
            <text :x="labelPos(i).x" :y="labelPos(i).y - 7" :text-anchor="labelPos(i).anchor" class="text-[13px] font-semibold" :fill="colorOf(t).hex">
              {{ t.title }}
              <tspan :x="labelPos(i).x" dy="16" class="fill-slate-500 text-[12px] font-semibold tabular-nums">{{ t.percent }}%</tspan>
            </text>
          </g>
        </svg>
      </div>
      <p class="mt-1 flex items-start gap-1.5 text-xs leading-relaxed text-muted">
        <Info class="mt-0.5 h-3.5 w-3.5 shrink-0" /> Qaysi xususiyat markazdan uzoqroq bo‘lsa, u insonda kuchliroq namoyon bo‘ladi. Yashil va ko‘k yo‘nalishlarda yuqori, sariq va qizil yo‘nalishlarda past ko‘rsatkich yaxshi.
      </p>
    </section>

    <!-- 4 ta yo‘nalish -->
    <section>
      <h3 class="sec-title">{{ directions.length }} ta yo‘nalish</h3>
      <div class="mt-3 grid gap-3 sm:grid-cols-2">
        <div v-for="d in directions" :key="d.id" :class="['rounded-2xl p-4 ring-1 ring-inset', dirColor(d).soft, dirColor(d).ring]">
          <div class="flex items-baseline justify-between gap-2">
            <p :class="['text-xs font-semibold uppercase tracking-wider', dirColor(d).text]">{{ d.title }}</p>
            <p class="text-2xl font-bold tabular-nums text-ink">{{ d.percent }}%</p>
          </div>
          <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-white"><div :class="['h-full rounded-full', dirColor(d).bar]" :style="{ width: `${d.percent}%` }" /></div>
          <p class="mt-2 text-xs leading-relaxed text-slate-600">{{ d.description }}</p>
        </div>
      </div>
    </section>

    <!-- 13 ta xususiyat -->
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <h3 class="sec-title">{{ traits.length }} ta xususiyat</h3>
      <ul class="mt-3 grid gap-x-6 gap-y-2.5 sm:grid-cols-2">
        <li v-for="t in traits" :key="t.id" :title="t.description">
          <div class="flex items-baseline justify-between gap-2 text-sm">
            <span class="inline-flex items-center gap-1.5 text-ink"><span class="h-2 w-2 rounded-full" :style="{ background: colorOf(t).hex }" />{{ t.title }}</span>
            <b class="tabular-nums text-ink">{{ t.percent }}%</b>
          </div>
          <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100"><div :class="['h-full rounded-full', colorOf(t).bar]" :style="{ width: `${t.percent}%` }" /></div>
        </li>
      </ul>
    </section>

    <!-- Kuchli tomonlari / Rivojlanish kerak -->
    <section class="grid gap-4 md:grid-cols-2">
      <div class="rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4 sm:p-5">
        <h3 class="sec-title"><TrendingUp class="h-4 w-4 text-emerald-600" /> Kuchli tomonlari</h3>
        <ul v-if="r.strengths?.length" class="mt-3 space-y-2.5">
          <li v-for="s in r.strengths" :key="s.id" class="text-sm leading-snug">
            <p class="font-medium text-ink">{{ s.title }} <span class="tabular-nums text-emerald-700">· {{ s.percent }}%</span></p>
            <p class="mt-0.5 text-slate-600">{{ s.text }}</p>
          </li>
        </ul>
        <p v-else class="mt-3 text-sm text-slate-600">Yaqqol kuchli tomon aniqlanmadi.</p>
      </div>
      <div class="rounded-2xl border border-amber-100 bg-amber-50/40 p-4 sm:p-5">
        <h3 class="sec-title"><TrendingDown class="h-4 w-4 text-amber-600" /> Rivojlanish kerak</h3>
        <ul v-if="r.development?.length" class="mt-3 space-y-2.5">
          <li v-for="s in r.development" :key="s.id" class="text-sm leading-snug">
            <p class="font-medium text-ink">{{ s.title }} <span class="tabular-nums text-amber-700">· {{ s.percent }}%</span></p>
            <p class="mt-0.5 text-slate-600">{{ s.text }}</p>
          </li>
        </ul>
        <p v-else class="mt-3 flex items-center gap-1.5 text-sm text-slate-600"><CheckCircle2 class="h-4 w-4 text-emerald-600" /> Jiddiy to‘sqinlik qiluvchi xususiyat aniqlanmadi.</p>
      </div>
    </section>

    <!-- Xulq-atvor naqshlari -->
    <section v-if="r.patterns?.length" class="rounded-2xl border border-line p-4 sm:p-5">
      <h3 class="sec-title"><UsersRound class="h-4 w-4 text-primary-600" /> Xulq-atvor naqshlari</h3>
      <ul class="mt-3 grid gap-3 sm:grid-cols-2">
        <li v-for="p in r.patterns" :key="p.title" class="rounded-xl bg-slate-50 px-3.5 py-3">
          <p class="text-sm font-semibold text-ink">{{ p.title }}</p>
          <p class="mt-0.5 text-[13px] leading-relaxed text-slate-600">{{ p.text }}</p>
        </li>
      </ul>
    </section>

    <!-- Ishonchlilik -->
    <section :class="['rounded-2xl border p-4 sm:p-5', relView.box]">
      <h3 class="sec-title"><component :is="relView.icon" :class="['h-4 w-4', relView.text]" /> Javoblar ishonchliligi: {{ relView.label }}</h3>
      <ul class="mt-2 space-y-1.5 text-sm text-slate-700">
        <li v-for="(t, i) in rel.issues?.length ? rel.issues : [rel.text]" :key="i" class="flex gap-2"><Info class="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />{{ t }}</li>
      </ul>
    </section>

    <!-- HR xulosasi -->
    <section :class="['rounded-2xl border p-4 sm:p-5', DECISION_TONE[r.decision?.title] || 'border-line']">
      <p class="sec-title !text-current"><Gavel class="h-4 w-4" /> HR xulosasi: ishga olish bo‘yicha</p>
      <p class="mt-2 text-lg font-bold">{{ r.decision?.title }}</p>
      <p class="mt-1 text-sm leading-relaxed opacity-90">{{ r.decision?.text }}</p>
    </section>

    <section class="grid gap-4 md:grid-cols-2">
      <!-- Eng mos lavozimlar -->
      <div class="rounded-2xl border border-line p-4 sm:p-5">
        <h3 class="sec-title"><Briefcase class="h-4 w-4 text-primary-600" /> Eng mos lavozimlar</h3>
        <ol class="mt-3 space-y-2">
          <li v-for="(p, i) in (r.roles || []).slice(0, 3)" :key="p.name" class="flex items-center gap-3">
            <span class="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-primary-600 text-xs font-bold text-white">{{ i + 1 }}</span>
            <span class="min-w-0 flex-1 truncate text-sm font-medium text-ink">{{ p.name }}</span>
            <span class="text-sm font-bold tabular-nums text-primary-700">{{ p.percent }}%</span>
          </li>
        </ol>
      </div>
      <!-- Rivojlanish tavsiyalari -->
      <div class="rounded-2xl border border-line p-4 sm:p-5">
        <h3 class="sec-title"><Sprout class="h-4 w-4 text-emerald-600" /> Rivojlanish tavsiyalari</h3>
        <ul v-if="r.recommendations?.length" class="mt-3 space-y-2">
          <li v-for="d in r.recommendations" :key="d.title" class="text-sm leading-snug">
            <p class="font-medium text-ink">{{ d.title }}</p>
            <p class="text-slate-600">{{ d.text }}</p>
          </li>
        </ul>
        <p v-else class="mt-3 text-sm text-slate-600">Maxsus tavsiya yo‘q — kuchli tomonlarini rivojlantirishda davom etsin.</p>
      </div>
    </section>

    <!-- Suhbat savollari -->
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <h3 class="sec-title"><MessageCircleQuestion class="h-4 w-4 text-primary-600" /> Suhbatda so‘rash kerak bo‘lgan savollar</h3>
      <ol class="mt-3 space-y-2">
        <li v-for="(q, i) in r.interview" :key="i" class="flex gap-3 text-sm leading-snug text-ink">
          <span class="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-slate-100 text-xs font-bold tabular-nums text-slate-600">{{ i + 1 }}</span>{{ q }}
        </li>
      </ol>
    </section>

    <!-- Natijani nusxalash -->
    <section class="rounded-2xl border border-primary-100 bg-primary-50/40 p-4 sm:p-5">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h3 class="sec-title"><ClipboardCopy class="h-4 w-4 text-primary-600" /> Natija matni</h3>
        <div class="flex flex-wrap gap-2">
          <Button size="sm" :icon="ClipboardCopy" @click="copyReport">Nusxalash</Button>
          <Button size="sm" variant="secondary" :icon="Download" @click="downloadReport">Yuklab olish (.txt)</Button>
        </div>
      </div>
      <p class="mt-1 text-xs text-muted">Matnni nusxalab, Telegram orqali yuborishingiz yoki xodim kartasiga qo‘shishingiz mumkin.</p>
      <pre class="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-white p-3 font-sans text-[13px] leading-relaxed text-slate-700 ring-1 ring-inset ring-line">{{ detail.reportText }}</pre>
    </section>

    <!-- Javoblar -->
    <section class="rounded-2xl border border-line">
      <button type="button" class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left sm:px-5" :aria-expanded="showAnswers" @click="showAnswers = !showAnswers">
        <span class="sec-title"><ListChecks class="h-4 w-4 text-primary-600" /> Xodimning javoblari ({{ items.length }} ta)</span>
        <span class="text-xs font-medium text-primary-700">{{ showAnswers ? 'Yashirish' : 'Ko‘rsatish' }}</span>
      </button>
      <div v-if="showAnswers" class="border-t border-line p-4 sm:p-5">
        <div class="inline-flex rounded-lg bg-slate-100 p-1 text-[13px]">
          <button v-for="o in [['all', 'Barchasi'], ['reverse', 'Teskari savollar'], ['attention', 'Diqqat tekshiruvi']]" :key="o[0]" type="button" :class="['rounded-md px-3 py-1 font-medium', answerFilter === o[0] ? 'bg-white text-ink shadow-sm' : 'text-muted']" @click="answerFilter = o[0]">{{ o[1] }}</button>
        </div>
        <ol class="mt-3 divide-y divide-line">
          <li v-for="q in shownItems" :key="q.id" class="flex flex-col gap-2 py-2.5 sm:flex-row sm:items-center">
            <div class="flex min-w-0 flex-1 items-start gap-3">
              <span :class="['grid h-7 w-7 shrink-0 place-items-center rounded-md text-xs font-bold tabular-nums', q.attention ? (q.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700') : 'bg-slate-100 text-slate-600']">{{ q.id }}</span>
              <div class="min-w-0">
                <p class="text-sm leading-snug text-ink">{{ q.text }}</p>
                <p class="mt-0.5 text-[11px] text-muted">{{ q.traitTitle }}<template v-if="q.key === 'reverse'"> · teskari savol</template><template v-if="q.attention"> · {{ q.ok ? 'to‘g‘ri javob' : 'noto‘g‘ri javob' }}</template></p>
              </div>
            </div>
            <span :class="['inline-flex shrink-0 items-center gap-1 self-start rounded-full px-2 py-0.5 text-xs font-medium sm:self-center', q.answer === 1 ? 'bg-primary-50 text-primary-700' : 'bg-slate-100 text-slate-600']">
              <ThumbsUp v-if="q.answer === 1" class="h-3 w-3" /><ThumbsDown v-else class="h-3 w-3" /> {{ q.options?.[q.answer] }}
            </span>
          </li>
        </ol>
      </div>
    </section>

    <p class="flex items-start gap-2 rounded-xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-600">
      <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0 text-amber-500" /> {{ r.disclaimer }}
    </p>
  </div>
</template>

<style scoped>
.sec-title {
  @apply flex items-center gap-2 text-sm font-semibold text-ink;
}
.tile {
  @apply rounded-xl bg-slate-50 px-3.5 py-3;
}
.tile-value {
  @apply text-2xl font-bold tabular-nums tracking-tight;
}
.tile-label {
  @apply mt-0.5 text-xs text-slate-600;
}
</style>
