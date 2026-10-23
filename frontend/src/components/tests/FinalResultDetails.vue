<script setup>
import { computed, ref, watch } from 'vue'
import { AlertCircle, Briefcase, Cake, CalendarClock, CalendarDays, Check, CheckCircle2, ClipboardList, Clock, Hash, RotateCcw, Trash2, UserRound, X, XCircle } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import { finalTestApi } from '@/api/finalTest'
import { FINAL_RESULT_LABELS, isPassed, participantName, useFinalTestStore } from '@/stores/finalTest'
import { formatDate, formatDateTime } from '@/utils/date'

/** Yakuniy test natijasi: 20 ta savol, A/B/C/D variantlar, tanlangan javob, to‘g‘ri javob va har bir savol natijasi */
const props = defineProps({
  open: { type: Boolean, default: false },
  resultId: { type: Number, default: null },
})
const emit = defineEmits(['close', 'delete'])

const store = useFinalTestStore()
const LETTERS = 'ABCDEFGH'
const attempts = computed(() => (props.resultId ? store.attemptsFor(props.resultId) : []))
const attemptId = ref(null)
const detail = ref(null)
const loading = ref(false)
const error = ref('')
const filter = ref('all')
const cache = new Map()

async function load(id) {
  error.value = ''
  if (!id) {
    detail.value = null
    return
  }
  if (cache.has(id)) {
    detail.value = cache.get(id)
    return
  }
  loading.value = true
  try {
    const d = await finalTestApi.result(id)
    cache.set(id, d)
    if (attemptId.value === id) detail.value = d
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
watch(attemptId, (id) => load(id))
watch(
  () => [props.open, props.resultId],
  ([open, id]) => {
    if (!open) return
    filter.value = 'all'
    if (attemptId.value === id) load(id)
    else attemptId.value = id
  },
  { immediate: true },
)

const attemptTabs = computed(() => attempts.value.map((a) => ({ value: a.id, label: `${a.attemptNo}-urinish`, count: `${a.percent}%` })))
const items = computed(() => detail.value?.items || [])
const wrongItems = computed(() => items.value.filter((i) => !i.isCorrect))
const shown = computed(() => (filter.value === 'wrong' ? wrongItems.value : items.value))
const filterTabs = computed(() => [
  { value: 'all', label: 'Barcha savollar', count: items.value.length },
  { value: 'wrong', label: 'Xato javoblar', count: wrongItems.value.length },
])
const passed = computed(() => isPassed(detail.value))
const title = computed(() => participantName(detail.value || attempts.value.at(-1)))
// Ishtirokchi ma'lumotlari: natijadagi nusxa (topshirish paytidagi), bo‘lmasa — ishtirokchi yozuvi
const person = computed(() => {
  const d = detail.value || {}
  const p = d.participant || {}
  return {
    age: d.age ?? p.age ?? null,
    birthDate: d.birthDate || p.birthDate || '',
  }
})
const duration = computed(() => {
  const s = detail.value?.durationSec
  return s || s === 0 ? `${Math.floor(s / 60)} daq ${s % 60} son` : '—'
})
const optionClass = (q, i) => {
  if (i === q.correctIndex && i === q.answer) return 'border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500/15'
  if (i === q.correctIndex) return 'border-emerald-300 bg-emerald-50/50'
  if (i === q.answer) return 'border-red-400 bg-red-50 ring-2 ring-red-500/10'
  return 'border-line'
}
const letterClass = (q, i) => {
  if (i === q.correctIndex) return 'bg-emerald-500 text-white'
  if (i === q.answer) return 'bg-red-500 text-white'
  return 'bg-slate-100 text-slate-600'
}
</script>

<template>
  <Modal :open="open" size="xl" @close="emit('close')">
    <template #header>
      <div class="flex min-w-0 items-center gap-3">
        <Avatar :name="detail?.fullName || `# ${detail?.participantNo ?? resultId}`" size="lg" />
        <div class="min-w-0">
          <h2 class="truncate text-base font-semibold text-ink sm:text-lg">{{ title }}</h2>
          <p class="mt-0.5 truncate text-sm text-muted">Yakuniy bilim testi{{ attempts.length > 1 ? ` · ${attempts.length} ta urinish` : '' }}</p>
        </div>
      </div>
    </template>

    <div v-if="attempts.length > 1" class="mb-4">
      <SegmentedControl v-model="attemptId" :options="attemptTabs" aria-label="Urinishlar tarixi" />
    </div>

    <LoadingState v-if="loading && !detail" :rows="5" />
    <div v-else-if="error" class="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
      <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> {{ error }}
      <button class="ml-auto inline-flex items-center gap-1 font-medium hover:underline" @click="load(attemptId)"><RotateCcw class="h-3.5 w-3.5" /> Qayta</button>
    </div>

    <template v-else-if="detail">
      <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <dl class="grid grid-cols-2 gap-3 text-sm">
          <div class="info col-span-2"><dt><UserRound class="h-3.5 w-3.5" /> Ism-familiya</dt><dd :title="title">{{ title }}</dd></div>
          <div class="info"><dt><Cake class="h-3.5 w-3.5" /> Yosh</dt><dd>{{ person.age !== null ? `${person.age} yosh` : 'Ko‘rsatilmagan' }}</dd></div>
          <div class="info"><dt><CalendarDays class="h-3.5 w-3.5" /> Tug‘ilgan sana</dt><dd>{{ person.birthDate ? formatDate(person.birthDate) : 'Ko‘rsatilmagan' }}</dd></div>
          <div class="info col-span-2"><dt><ClipboardList class="h-3.5 w-3.5" /> Test nomi</dt><dd :title="detail.testTitle">{{ detail.testTitle || 'Yakuniy bilim testi' }}</dd></div>
          <div class="info"><dt><CalendarClock class="h-3.5 w-3.5" /> Topshirildi</dt><dd>{{ formatDateTime(detail.submittedAt) }}</dd></div>
          <div class="info"><dt><Clock class="h-3.5 w-3.5" /> Sarflangan vaqt</dt><dd>{{ duration }}</dd></div>
          <div class="info"><dt><Hash class="h-3.5 w-3.5" /> Ishtirokchi ID</dt><dd>{{ detail.participantId ? `#${detail.participantId}` : `Natija #${detail.participantNo ?? detail.id}` }}</dd></div>
          <div v-if="detail.position" class="info"><dt><Briefcase class="h-3.5 w-3.5" /> Lavozim</dt><dd>{{ detail.position }}</dd></div>
          <div v-if="detail.candidate" class="info"><dt><UserRound class="h-3.5 w-3.5" /> Nomzod profili</dt><dd><RouterLink :to="{ path: '/candidates', query: { id: detail.candidate.id } }" class="text-primary-700 hover:underline" :title="detail.candidate.fullName">{{ detail.candidate.fullName || `Nomzod #${detail.candidate.id}` }}</RouterLink></dd></div>
          <div v-if="detail.employeeId" class="info"><dt><UserRound class="h-3.5 w-3.5" /> Xodim kartasi</dt><dd><RouterLink :to="`/employees/${detail.employeeId}`" class="text-primary-700 hover:underline">Xodim #{{ detail.employeeId }}</RouterLink></dd></div>
        </dl>
        <div :class="['rounded-2xl border p-4', passed ? 'border-emerald-100 bg-emerald-50/60' : 'border-red-100 bg-red-50/60']">
          <div class="flex items-center justify-between gap-3">
            <p class="text-3xl font-bold tabular-nums tracking-tight text-ink">{{ detail.correct }}<span class="text-lg text-muted">/{{ detail.total }}</span></p>
            <StatusBadge :status="passed ? 'O‘tdi' : 'O‘tmadi'" :label="FINAL_RESULT_LABELS[detail.status]" />
          </div>
          <p class="mt-0.5 text-xs text-muted">{{ detail.percent }}% · o‘tish: 16–20 ball</p>
          <div class="mt-3 grid grid-cols-2 gap-2 text-center">
            <div class="rounded-xl bg-white px-2 py-2"><p class="text-[11px] text-muted">To‘g‘ri</p><p class="text-xl font-bold tabular-nums text-emerald-600">{{ detail.correct }}</p></div>
            <div class="rounded-xl bg-white px-2 py-2"><p class="text-[11px] text-muted">Xato</p><p class="text-xl font-bold tabular-nums text-red-600">{{ detail.wrong }}</p></div>
          </div>
        </div>
      </div>

      <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 class="text-sm font-semibold text-ink">Savollar va javoblar</h3>
        <SegmentedControl v-model="filter" :options="filterTabs" aria-label="Savollar filtri" />
      </div>
      <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-emerald-500" /> To‘g‘ri javob</span>
        <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-red-500" /> Tanlangan xato javob</span>
      </div>

      <ol class="mt-4 space-y-3">
        <li v-for="q in shown" :key="q.id" class="rounded-2xl border border-line p-4 sm:p-5">
          <div class="flex items-start gap-3">
            <span :class="['grid h-8 w-8 shrink-0 place-items-center rounded-lg text-sm font-bold tabular-nums', q.isCorrect ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600']">{{ q.id }}</span>
            <p class="min-w-0 flex-1 pt-1 font-medium leading-snug text-ink">{{ q.text }}</p>
            <span :class="['inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold', q.isCorrect ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700']">
              <CheckCircle2 v-if="q.isCorrect" class="h-3.5 w-3.5" /><XCircle v-else class="h-3.5 w-3.5" />
              {{ q.isCorrect ? 'To‘g‘ri · 1 ball' : 'Xato · 0 ball' }}
            </span>
          </div>
          <ul class="mt-3 space-y-1.5 sm:pl-11">
            <li v-for="(opt, i) in q.options" :key="i" :class="['flex items-start gap-3 rounded-xl border px-3 py-2 text-sm', optionClass(q, i)]">
              <span :class="['grid h-6 w-6 shrink-0 place-items-center rounded-md text-xs font-bold', letterClass(q, i)]">{{ LETTERS[i] }}</span>
              <span class="flex-1 leading-snug text-slate-700">{{ opt }}</span>
              <span v-if="i === q.answer" :class="['inline-flex shrink-0 items-center gap-1 text-xs font-medium', q.isCorrect ? 'text-emerald-700' : 'text-red-600']">
                <Check v-if="q.isCorrect" class="h-3.5 w-3.5" /><X v-else class="h-3.5 w-3.5" /> Tanlangan javob
              </span>
              <span v-else-if="i === q.correctIndex" class="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-emerald-700"><Check class="h-3.5 w-3.5" /> To‘g‘ri javob</span>
            </li>
          </ul>
        </li>
      </ol>
      <p v-if="!shown.length" class="mt-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">Barcha javoblar to‘g‘ri.</p>
    </template>

    <template #footer>
      <Button v-if="detail" variant="danger-outline" :icon="Trash2" class="sm:mr-auto" @click="emit('delete', { ...detail, name: title })">O‘chirish</Button>
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