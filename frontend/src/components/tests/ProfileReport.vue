<script setup>
import { computed, ref } from 'vue'
import {
  AlertTriangle, Brain, Briefcase, CheckCircle2, ClipboardCopy, Download, Gauge, Info, ListChecks, MessageCircleQuestion,
  ShieldAlert, ShieldCheck, Sprout, ThumbsDown, ThumbsUp, TrendingDown, TrendingUp, Zap,
} from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import { useToast } from '@/composables/useToast'

/**
 * Yangi xodimlar testi (landing /test/sotuv, format=profile) — batafsil HR hisoboti.
 * Barcha raqamlar backendda xodimning haqiqiy javoblaridan hisoblangan (backend/app/profile_test.py);
 * bu komponent faqat ko‘rsatadi. "Nusxalash" — backend tuzgan to‘liq matnli hisobot (reportText).
 */
const props = defineProps({
  detail: { type: Object, required: true },
})
const toast = useToast()

const report = computed(() => props.detail.report || {})
const rel = computed(() => report.value.reliability || {})
const scales = computed(() => report.value.scales || [])
const positions = computed(() => report.value.positions || [])
const items = computed(() => props.detail.items || [])

const LEVEL_TONE = {
  Yuqori: { bar: 'bg-emerald-500', text: 'text-emerald-700', chip: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15' },
  'O‘rtacha': { bar: 'bg-amber-500', text: 'text-amber-700', chip: 'bg-amber-50 text-amber-700 ring-amber-600/20' },
  Past: { bar: 'bg-red-500', text: 'text-red-600', chip: 'bg-red-50 text-red-700 ring-red-600/15' },
}
const tone = (level) => LEVEL_TONE[level] || LEVEL_TONE['O‘rtacha']

const answerFilter = ref('all')
const answerTabs = computed(() => [
  { value: 'all', label: 'Barcha javoblar', count: items.value.length },
  { value: 'reverse', label: 'Teskari savollar', count: items.value.filter((i) => i.key === 'reverse' && !i.sincerity).length },
  { value: 'sincerity', label: 'Samimiylik', count: items.value.filter((i) => i.sincerity).length },
])
const shownItems = computed(() => {
  if (answerFilter.value === 'reverse') return items.value.filter((i) => i.key === 'reverse' && !i.sincerity)
  if (answerFilter.value === 'sincerity') return items.value.filter((i) => i.sincerity)
  return items.value
})
const inconsistentIds = computed(() => new Set((rel.value.inconsistencies || []).flatMap((x) => x.ids)))
const showAnswers = ref(false)

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Eski brauzer yoki http — vaqtinchalik textarea orqali
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
  const text = props.detail.reportText || ''
  if (!text) return toast.error('Hisobot matni topilmadi')
  if (await copyText(text)) toast.success('HR hisoboti nusxalandi', 'Matnni xat, Telegram yoki hujjatga joylashtirishingiz mumkin')
  else toast.error('Nusxalab bo‘lmadi', 'Brauzer ruxsat bermadi — “Yuklab olish” tugmasidan foydalaning')
}
function downloadReport() {
  const text = props.detail.reportText || ''
  const blob = new Blob([`﻿${text}`], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const name = (props.detail.fullName || `ishtirokchi-${props.detail.participantNo ?? props.detail.id}`).replace(/[^\p{L}\p{N}]+/gu, '-')
  a.href = url
  a.download = `hr-hisobot-${name}-${String(props.detail.submittedAt || '').slice(0, 10)}.txt`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<template>
  <div class="space-y-5">
    <!-- 1. HR xulosasi va ishonchlilik -->
    <section class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div class="rounded-2xl border border-primary-100 bg-primary-50/40 p-4 sm:p-5">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h3 class="sec-title"><Brain class="h-4 w-4 text-primary-600" /> HR xulosasi</h3>
          <StatusBadge :status="report.recommendation || detail.status" />
        </div>
        <p class="mt-3 text-sm leading-relaxed text-slate-700">{{ report.summary }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button size="sm" :icon="ClipboardCopy" @click="copyReport">HR hisobotini nusxalash</Button>
          <Button size="sm" variant="secondary" :icon="Download" @click="downloadReport">Yuklab olish (.txt)</Button>
        </div>
      </div>
      <div :class="['rounded-2xl border p-4', rel.level === 'Past' ? 'border-red-100 bg-red-50/50' : rel.level === 'O‘rtacha' ? 'border-amber-100 bg-amber-50/50' : 'border-emerald-100 bg-emerald-50/50']">
        <h3 class="sec-title">
          <ShieldCheck v-if="rel.level === 'Yuqori'" class="h-4 w-4 text-emerald-600" />
          <ShieldAlert v-else class="h-4 w-4" :class="rel.level === 'Past' ? 'text-red-600' : 'text-amber-600'" />
          Natija ishonchliligi
        </h3>
        <p class="mt-2 text-3xl font-bold tabular-nums tracking-tight text-ink">{{ rel.percent }}%<span :class="['ml-2 text-sm font-semibold', tone(rel.level).text]">{{ rel.level }}</span></p>
        <dl class="mt-3 grid grid-cols-3 gap-2 text-center">
          <div class="mini"><dt>Samimiylik</dt><dd>{{ rel.sincerity }}%</dd></div>
          <div class="mini"><dt>Ziddiyat</dt><dd>{{ rel.inconsistentPairs }}/{{ rel.pairsTotal }}</dd></div>
          <div class="mini"><dt>«Qo‘shilaman»</dt><dd>{{ rel.agreeRatio }}%</dd></div>
        </dl>
        <ul class="mt-3 space-y-1.5 text-xs leading-relaxed text-slate-600">
          <li v-for="(n, i) in rel.notes" :key="i" class="flex gap-1.5"><Info class="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />{{ n }}</li>
        </ul>
      </div>
    </section>

    <!-- 2. Asosiy ko‘rsatkichlar -->
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h3 class="sec-title"><Gauge class="h-4 w-4 text-primary-600" /> Asosiy ko‘rsatkichlar</h3>
        <p class="text-xs text-muted">Umumiy profil indeksi: <b class="tabular-nums text-ink">{{ report.index }}%</b> ({{ report.indexLevel }})</p>
      </div>
      <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <div v-for="s in scales" :key="s.id" class="rounded-xl bg-slate-50 p-3">
          <div class="flex items-baseline justify-between gap-2">
            <p class="font-medium text-ink">{{ s.title }}</p>
            <p class="tabular-nums"><b :class="['text-lg', tone(s.level).text]">{{ s.percent }}%</b></p>
          </div>
          <div class="mt-2 h-2 overflow-hidden rounded-full bg-white ring-1 ring-inset ring-line" role="meter" :aria-valuenow="s.percent" aria-valuemin="0" aria-valuemax="100" :aria-label="s.title">
            <div :class="['h-full rounded-full transition-[width] duration-700', tone(s.level).bar]" :style="{ width: `${s.percent}%` }" />
          </div>
          <p class="mt-1.5 flex justify-between gap-2 text-[11px] text-muted">
            <span class="truncate" :title="s.description">{{ s.description }}</span>
            <span class="shrink-0 tabular-nums">{{ s.points }}/{{ s.max }} · {{ s.level }}</span>
          </p>
        </div>
      </div>
    </section>

    <!-- 3. Eng mos lavozimlar -->
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <h3 class="sec-title"><Briefcase class="h-4 w-4 text-primary-600" /> Eng mos lavozimlar</h3>
      <ol class="mt-3 space-y-2">
        <li v-for="(p, i) in positions" :key="p.name" :class="['flex items-center gap-3 rounded-xl px-3 py-2', i < 3 ? 'bg-primary-50/50' : '']">
          <span :class="['grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-bold tabular-nums', i < 3 ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-500']">{{ i + 1 }}</span>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-ink">{{ p.name }}</p>
            <p class="truncate text-[11px] text-muted">Asosiy talablar: {{ (p.keyScales || []).join(', ') }}</p>
          </div>
          <div class="hidden h-1.5 w-28 overflow-hidden rounded-full bg-slate-100 sm:block">
            <div :class="['h-full rounded-full', tone(p.level).bar]" :style="{ width: `${p.percent}%` }" />
          </div>
          <span :class="['w-12 shrink-0 text-right text-sm font-bold tabular-nums', tone(p.level).text]">{{ p.percent }}%</span>
        </li>
      </ol>
    </section>

    <!-- 4. Suhbat savollari -->
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <h3 class="sec-title"><MessageCircleQuestion class="h-4 w-4 text-primary-600" /> Suhbatda so‘raladigan savollar</h3>
      <ol class="mt-3 space-y-2.5">
        <li v-for="(q, i) in report.interviewQuestions" :key="i" class="flex gap-3">
          <span class="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-slate-100 text-xs font-bold tabular-nums text-slate-600">{{ i + 1 }}</span>
          <div class="min-w-0">
            <p class="text-sm leading-snug text-ink">{{ q.question }}</p>
            <p class="mt-0.5 text-[11px] text-muted">{{ q.reason }}</p>
          </div>
        </li>
      </ol>
    </section>

    <!-- 5–6. Kuchli va zaif tomonlar -->
    <section class="grid gap-4 md:grid-cols-2">
      <div class="rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4 sm:p-5">
        <h3 class="sec-title"><TrendingUp class="h-4 w-4 text-emerald-600" /> Kuchli tomonlar</h3>
        <ul class="mt-3 space-y-2.5">
          <li v-for="s in report.strengths" :key="s.scale" class="text-sm leading-snug">
            <p class="font-medium text-ink">{{ s.scale }} <span class="tabular-nums text-emerald-700">· {{ s.percent }}%</span></p>
            <p class="mt-0.5 text-slate-600">{{ s.text }}</p>
          </li>
        </ul>
      </div>
      <div class="rounded-2xl border border-amber-100 bg-amber-50/40 p-4 sm:p-5">
        <h3 class="sec-title"><TrendingDown class="h-4 w-4 text-amber-600" /> Zaif tomonlar</h3>
        <ul v-if="report.weaknesses?.length" class="mt-3 space-y-2.5">
          <li v-for="s in report.weaknesses" :key="s.scale" class="text-sm leading-snug">
            <p class="font-medium text-ink">{{ s.scale }} <span class="tabular-nums text-amber-700">· {{ s.percent }}%</span></p>
            <p class="mt-0.5 text-slate-600">{{ s.text }}</p>
          </li>
        </ul>
        <p v-else class="mt-3 flex items-center gap-1.5 text-sm text-slate-600"><CheckCircle2 class="h-4 w-4 text-emerald-600" /> Sezilarli zaif tomon aniqlanmadi.</p>
      </div>
    </section>

    <!-- 7–9. Fikrlash uslubi, qiyin vaziyat, rivojlanish -->
    <section class="grid gap-4 md:grid-cols-2">
      <div class="rounded-2xl border border-line p-4 sm:p-5">
        <h3 class="sec-title"><Brain class="h-4 w-4 text-primary-600" /> Fikrlash uslubi</h3>
        <p class="mt-2 font-medium text-ink">{{ report.thinkingStyle?.title }}</p>
        <p class="mt-1 text-sm leading-relaxed text-slate-600">{{ report.thinkingStyle?.text }}</p>
      </div>
      <div class="rounded-2xl border border-line p-4 sm:p-5">
        <h3 class="sec-title"><Zap class="h-4 w-4 text-primary-600" /> Qiyin vaziyatdagi xulq</h3>
        <p class="mt-2 font-medium text-ink">{{ report.hardSituations?.title }}</p>
        <p class="mt-1 text-sm leading-relaxed text-slate-600">{{ report.hardSituations?.text }}</p>
      </div>
    </section>
    <section class="rounded-2xl border border-line p-4 sm:p-5">
      <h3 class="sec-title"><Sprout class="h-4 w-4 text-emerald-600" /> Rivojlanish tavsiyalari</h3>
      <ul class="mt-3 space-y-2">
        <li v-for="d in report.development" :key="d.scale" class="text-sm leading-snug">
          <span class="font-medium text-ink">{{ d.scale }}:</span> <span class="text-slate-600">{{ d.text }}</span>
        </li>
      </ul>
    </section>

    <p class="flex items-start gap-2 rounded-xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-600">
      <AlertTriangle class="mt-0.5 h-4 w-4 shrink-0 text-amber-500" /> {{ report.disclaimer }}
    </p>

    <!-- Javoblar (tekshirish uchun) -->
    <section class="rounded-2xl border border-line">
      <button type="button" class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left sm:px-5" :aria-expanded="showAnswers" @click="showAnswers = !showAnswers">
        <span class="sec-title"><ListChecks class="h-4 w-4 text-primary-600" /> Xodimning javoblari ({{ items.length }} ta)</span>
        <span class="text-xs font-medium text-primary-700">{{ showAnswers ? 'Yashirish' : 'Ko‘rsatish' }}</span>
      </button>
      <div v-if="showAnswers" class="border-t border-line p-4 sm:p-5">
        <SegmentedControl v-model="answerFilter" :options="answerTabs" aria-label="Javoblar filtri" />
        <ol class="mt-3 divide-y divide-line">
          <li v-for="q in shownItems" :key="q.id" class="flex flex-col gap-2 py-2.5 sm:flex-row sm:items-center">
            <div class="flex min-w-0 flex-1 items-start gap-3">
              <span :class="['grid h-7 w-7 shrink-0 place-items-center rounded-md text-xs font-bold tabular-nums', inconsistentIds.has(q.id) ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600']">{{ q.id }}</span>
              <div class="min-w-0">
                <p class="text-sm leading-snug text-ink">{{ q.text }}</p>
                <p class="mt-0.5 text-[11px] text-muted">
                  {{ q.scaleTitle }}<template v-if="q.key === 'reverse'"> · teskari savol</template><template v-if="inconsistentIds.has(q.id)"> · <span class="text-amber-700">ziddiyatli juftlik</span></template>
                </p>
              </div>
            </div>
            <div class="flex shrink-0 items-center gap-2 sm:pl-3">
              <span :class="['inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium', q.answer === 1 ? 'bg-primary-50 text-primary-700' : 'bg-slate-100 text-slate-600']">
                <ThumbsUp v-if="q.answer === 1" class="h-3 w-3" /><ThumbsDown v-else class="h-3 w-3" /> {{ q.options?.[q.answer] }}
              </span>
              <span :class="['w-14 text-right text-xs font-semibold tabular-nums', q.point ? 'text-emerald-600' : 'text-slate-400']" :title="q.sincerity ? 'Samimiylik: 1 — samimiy javob' : 'Shkala bali'">
                {{ q.sincerity ? (q.point ? 'samimiy' : 'ideal') : `${q.point} ball` }}
              </span>
            </div>
          </li>
        </ol>
      </div>
    </section>
  </div>
</template>

<style scoped>
.sec-title {
  @apply flex items-center gap-2 text-sm font-semibold text-ink;
}
.mini {
  @apply rounded-lg bg-white/80 px-1.5 py-1.5;
}
.mini dt {
  @apply text-[10px] text-muted;
}
.mini dd {
  @apply text-sm font-bold tabular-nums text-ink;
}
</style>
