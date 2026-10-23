<script setup>
import { computed, ref, watch } from 'vue'
import { AlertCircle, Briefcase, CalendarDays, Check, Clock, Phone, RotateCcw, Star, Trash2, User } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ProfileReport from './ProfileReport.vue'
import PersonaReport from './PersonaReport.vue'
import { landingResultsApi } from '@/api/landing'
import { useLandingStore } from '@/stores/landing'
import { LANDING_RESULT_LABELS } from '@/constants'
import { formatDate, formatDateTime } from '@/utils/date'

/**
 * Landing test natijasi.
 * - 40 savolli test (format=profile): batafsil HR hisoboti — ProfileReport.
 * - eski test: barcha savollar, variantlar, tanlangan javob va baholash kaliti.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  resultId: { type: Number, default: null },
})
const emit = defineEmits(['close', 'delete'])

const store = useLandingStore()
const detail = ref(null)
const loading = ref(false)
const error = ref('')
const filter = ref('all')

async function load(id) {
  detail.value = null
  error.value = ''
  filter.value = 'all'
  if (!id) return
  loading.value = true
  try {
    detail.value = await landingResultsApi.get(id)
    store.markViewed(id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
watch(
  () => [props.open, props.resultId],
  ([open, id]) => open && load(id),
  { immediate: true },
)

const passed = computed(() => detail.value?.status === 'O‘tdi')
const isProfile = computed(() => detail.value?.format === 'profile')
// «Ishdagi shaxsiyat 360»: katta foiz kartasi o‘rniga to‘liq hisobot (PersonaReport)
const isPersona = computed(() => detail.value?.format === 'persona')
const items = computed(() => detail.value?.items || [])
const notBest = computed(() => items.value.filter((i) => i.points < i.maxPoints))
const shown = computed(() => (filter.value === 'weak' ? notBest.value : items.value))
const filterOptions = computed(() => [
  { value: 'all', label: 'Barcha savollar', count: items.value.length },
  { value: 'weak', label: 'Eng yaxshi javob emas', count: notBest.value.length },
])
const sectionTitle = (id) => detail.value?.sectionsInfo?.find((s) => s.id === id)?.title || ''
const duration = computed(() => {
  const s = detail.value?.durationSec
  if (!s && s !== 0) return '—'
  return `${Math.floor(s / 60)} daq ${s % 60} son`
})
// Foiz halqasi
const R = 34
const C = 2 * Math.PI * R
const dash = computed(() => `${((detail.value?.percent || 0) / 100) * C} ${C}`)
const pointTone = (i) => (i.points === i.maxPoints ? 'text-emerald-600' : i.points >= i.maxPoints * 0.6 ? 'text-amber-600' : 'text-red-600')
</script>

<template>
  <Modal :open="open" size="xl" @close="emit('close')">
    <template #header>
      <div v-if="detail" class="flex min-w-0 items-center gap-3">
        <Avatar :name="detail.fullName" size="lg" />
        <div class="min-w-0">
          <h2 class="truncate text-base font-semibold text-ink sm:text-lg">{{ detail.fullName }}</h2>
          <p class="mt-0.5 truncate text-sm text-muted">{{ detail.testTitle }}</p>
        </div>
      </div>
      <h2 v-else class="text-lg font-semibold text-ink">Nomzod natijasi</h2>
    </template>

    <LoadingState v-if="loading" :rows="5" />
    <div v-else-if="error" class="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
      <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> {{ error }}
      <button class="ml-auto inline-flex items-center gap-1 font-medium underline-offset-2 hover:underline" @click="load(resultId)"><RotateCcw class="h-3.5 w-3.5" /> Qayta</button>
    </div>

    <template v-else-if="detail">
      <!-- Xulosa -->
      <div :class="['grid gap-4', !isPersona && 'lg:grid-cols-[minmax(0,1fr)_300px]']">
        <dl :class="['grid grid-cols-2 gap-3 text-sm', isPersona ? 'sm:grid-cols-4' : 'sm:grid-cols-3']">
          <div class="info col-span-2"><dt><User class="h-3.5 w-3.5" /> F.I.Sh.</dt><dd>{{ detail.fullName }}</dd></div>
          <div class="info"><dt><Briefcase class="h-3.5 w-3.5" /> Lavozim</dt><dd>{{ detail.position }}</dd></div>
          <div class="info"><dt><User class="h-3.5 w-3.5" /> Yosh</dt><dd>{{ detail.age }}</dd></div>
          <div class="info"><dt><CalendarDays class="h-3.5 w-3.5" /> Sana (nomzod)</dt><dd>{{ formatDate(detail.date) }}</dd></div>
          <div class="info"><dt><Clock class="h-3.5 w-3.5" /> Topshirildi</dt><dd>{{ formatDateTime(detail.submittedAt) }}</dd></div>
          <div class="info"><dt><Phone class="h-3.5 w-3.5" /> Telefon</dt><dd>{{ detail.phone || '—' }}</dd></div>
          <div class="info"><dt><Clock class="h-3.5 w-3.5" /> Sarflangan vaqt</dt><dd>{{ duration }}</dd></div>
          <div v-if="detail.candidate" class="info"><dt><User class="h-3.5 w-3.5" /> Nomzod profili</dt><dd><RouterLink :to="{ path: '/candidates', query: { id: detail.candidate.id } }" class="text-primary-700 hover:underline" :title="detail.candidate.fullName">{{ detail.candidate.fullName || `Nomzod #${detail.candidate.id}` }}</RouterLink></dd></div>
          <div v-if="detail.employeeId" class="info"><dt><User class="h-3.5 w-3.5" /> Xodim kartasi</dt><dd><RouterLink :to="`/employees/${detail.employeeId}`" class="text-primary-700 hover:underline">Xodim #{{ detail.employeeId }}</RouterLink></dd></div>
        </dl>

        <!-- 40 savolli test: umumiy indeks, tavsiya, ishonchlilik, ko‘rsatkichlar -->
        <div v-if="isProfile" class="rounded-2xl border border-primary-100 bg-primary-50/50 p-4">
          <div class="flex items-center justify-between gap-3">
            <p class="text-3xl font-bold tabular-nums tracking-tight text-ink">{{ detail.percent }}%</p>
            <StatusBadge :status="detail.status" :label="LANDING_RESULT_LABELS[detail.status]" />
          </div>
          <p class="mt-0.5 text-xs text-muted">Umumiy profil indeksi · {{ detail.total }} ta savol</p>
          <div class="mt-3 grid grid-cols-2 gap-2 text-center">
            <div class="rounded-xl bg-white px-2 py-2"><p class="text-[11px] text-muted">Ishonchlilik</p><p class="text-xl font-bold tabular-nums text-ink">{{ detail.reliability }}%</p></div>
            <div class="rounded-xl bg-white px-2 py-2"><p class="text-[11px] text-muted">Eng mos lavozim</p><p class="truncate text-sm font-semibold text-ink" :title="detail.bestPosition?.name">{{ detail.bestPosition?.name || '—' }}</p><p class="text-xs tabular-nums text-primary-700">{{ detail.bestPosition?.percent ?? '—' }}%</p></div>
          </div>
          <ul class="mt-3 space-y-2">
            <li v-for="s in detail.report?.scales || []" :key="s.id">
              <div class="flex justify-between text-xs"><span class="text-slate-600">{{ s.title }}</span><b class="tabular-nums text-ink">{{ s.percent }}%</b></div>
              <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-white"><div :class="['h-full rounded-full', s.percent >= 75 ? 'bg-emerald-500' : s.percent >= 50 ? 'bg-amber-500' : 'bg-red-500']" :style="{ width: `${s.percent}%` }" /></div>
            </li>
          </ul>
        </div>

        <div v-else-if="!isPersona" :class="['flex items-center gap-4 rounded-2xl border p-4', passed ? 'border-emerald-100 bg-emerald-50/60' : 'border-red-100 bg-red-50/60']">
          <svg viewBox="0 0 80 80" class="h-20 w-20 shrink-0 -rotate-90" aria-hidden="true">
            <circle cx="40" cy="40" :r="R" fill="none" stroke="currentColor" stroke-width="8" class="text-white" />
            <circle cx="40" cy="40" :r="R" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round" :stroke-dasharray="dash" :class="['transition-all duration-700', passed ? 'text-emerald-500' : 'text-red-500']" />
          </svg>
          <div class="min-w-0">
            <p class="text-3xl font-bold tabular-nums tracking-tight text-ink">{{ detail.percent }}%</p>
            <p class="text-xs text-muted">{{ detail.points }} / {{ detail.maxPoints }} ball · o‘tish {{ detail.passPercent }}%</p>
            <StatusBadge class="mt-2" :status="detail.status" :label="LANDING_RESULT_LABELS[detail.status]" />
          </div>
        </div>
      </div>

      <PersonaReport v-if="isPersona" :key="`p-${detail.id}`" :detail="detail" class="mt-5" />
      <ProfileReport v-else-if="isProfile" :key="detail.id" :detail="detail" class="mt-6" />

      <template v-else>
      <!-- Bo‘limlar -->
      <div class="mt-4 grid gap-3 sm:grid-cols-2">
        <div v-for="s in detail.sections" :key="s.id" class="rounded-xl border border-line px-4 py-3">
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium text-ink">{{ s.title }}</span>
            <span class="tabular-nums text-muted">{{ s.points }} / {{ s.maxPoints }} ball</span>
          </div>
          <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full bg-gradient-to-r from-primary-600 to-sky-400" :style="{ width: `${(s.points / s.maxPoints) * 100}%` }" />
          </div>
        </div>
      </div>

      <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 class="text-sm font-semibold text-ink">Savollar va javoblar</h3>
        <SegmentedControl v-model="filter" :options="filterOptions" aria-label="Savollar filtri" />
      </div>
      <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded border-2 border-primary-600 bg-primary-50" /> Nomzod javobi</span>
        <span class="inline-flex items-center gap-1.5"><Star class="h-3.5 w-3.5 fill-emerald-500 text-emerald-500" /> Kalit: eng yuqori ball</span>
        <span>Raqam/harf ostidagi son — kalit bo‘yicha ball</span>
      </div>

      <ol class="mt-4 space-y-3">
        <li v-for="q in shown" :key="q.id" class="rounded-2xl border border-line p-4 sm:p-5">
          <div class="flex items-start gap-3">
            <span class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary-50 text-sm font-bold tabular-nums text-primary-700">{{ q.id }}</span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-1.5 text-[11px] font-medium">
                <span class="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">{{ sectionTitle(q.section) }}</span>
                <span v-if="q.type === 'scale'" class="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">1–5 ball</span>
                <span v-if="q.key === 'reverse'" class="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700 ring-1 ring-inset ring-amber-600/20">Teskari savol: 1 = 5 ball</span>
              </div>
              <p class="mt-1.5 font-medium leading-snug text-ink">{{ q.text }}</p>
              <p v-if="q.keyNote" class="mt-0.5 text-xs text-muted">Kalit izohi: {{ q.keyNote }}</p>
            </div>
            <span :class="['shrink-0 text-sm font-semibold tabular-nums', pointTone(q)]">{{ q.points }}/{{ q.maxPoints }}</span>
          </div>

          <!-- 1–5 shkala -->
          <div v-if="q.type === 'scale'" class="mt-3 grid grid-cols-5 gap-1.5 sm:pl-11">
            <div
              v-for="c in q.choices"
              :key="c.label"
              :class="['relative rounded-xl border px-1 py-2 text-center', c.label === q.answerLabel ? 'border-primary-600 bg-primary-50 ring-2 ring-primary-600/15' : 'border-line']"
              :title="c.text"
            >
              <Star v-if="c.best" class="absolute right-1 top-1 h-3 w-3 fill-emerald-500 text-emerald-500" />
              <p :class="['text-base font-bold tabular-nums', c.label === q.answerLabel ? 'text-primary-700' : 'text-slate-500']">{{ c.label }}</p>
              <p class="hidden truncate text-[10.5px] text-muted sm:block">{{ c.text }}</p>
              <p class="mt-0.5 text-[11px] font-semibold tabular-nums text-slate-500">{{ c.points }} ball</p>
            </div>
          </div>

          <!-- A/B/C/D -->
          <ul v-else class="mt-3 space-y-1.5 sm:pl-11">
            <li
              v-for="c in q.choices"
              :key="c.label"
              :class="['flex items-start gap-3 rounded-xl border px-3 py-2 text-sm', c.label === q.answerLabel ? 'border-primary-600 bg-primary-50 ring-2 ring-primary-600/15' : 'border-line']"
            >
              <span :class="['grid h-6 w-6 shrink-0 place-items-center rounded-md text-xs font-bold', c.label === q.answerLabel ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-600']">{{ c.label }}</span>
              <span class="flex-1 leading-snug text-slate-700">{{ c.text }}</span>
              <span v-if="c.label === q.answerLabel" class="hidden shrink-0 items-center gap-1 text-xs font-medium text-primary-700 sm:inline-flex"><Check class="h-3.5 w-3.5" /> Nomzod javobi</span>
              <span class="inline-flex shrink-0 items-center gap-1 text-xs font-semibold tabular-nums text-slate-500">
                <Star v-if="c.best" class="h-3.5 w-3.5 fill-emerald-500 text-emerald-500" />{{ c.points }} ball
              </span>
            </li>
          </ul>

          <p class="mt-2.5 text-[13px] sm:pl-11">
            <span class="text-muted">Tanlangan javob:</span>{{ ' ' }}
            <b class="text-ink">{{ q.type === 'scale' ? `${q.answerLabel} — ${q.answerText}` : q.answerLabel !== undefined ? `${q.answerLabel}) ${q.answerText}` : q.options?.[q.answer] ?? '—' }}</b>
          </p>
        </li>
      </ol>
      <p v-if="!shown.length" class="mt-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">Barcha javoblar kalit bo‘yicha eng yuqori ballni oldi.</p>
      </template>
    </template>

    <template #footer>
      <Button v-if="detail" variant="danger-outline" :icon="Trash2" class="sm:mr-auto" @click="emit('delete', detail)">O‘chirish</Button>
      <Button variant="secondary" @click="emit('close')">Yopish</Button>
    </template>
  </Modal>
</template>

<style scoped>
.info {
  @apply min-w-0 rounded-xl bg-slate-50 px-3 py-2;
}
.info dt {
  @apply flex items-center gap-1.5 text-[11px] text-muted;
}
.info dd {
  @apply mt-0.5 truncate font-medium text-ink;
}
</style>