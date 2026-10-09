<script setup>
import { computed, ref, watch } from 'vue'
import { Briefcase, Building2, CalendarDays, Check, CircleSlash, Phone, Play, RotateCcw, User, X } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import { useTestsStore } from '@/stores/tests'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { RESULT_LABELS } from '@/constants'
import { employeeAge, formatDateTime } from '@/utils/date'
import { nameParts } from "@/utils/format"

/** Test topshirgan xodim: shaxsiy ma'lumotlar va har bir savol bo‘yicha javoblari */
const props = defineProps({
  open: { type: Boolean, default: false },
  resultId: { type: Number, default: null },
})
const emit = defineEmits(['close', 'start'])

const tests = useTestsStore()
const employees = useEmployeesStore()
const catalog = useCatalogStore()

const result = computed(() => tests.results.find((r) => r.id === props.resultId) || null)
const test = computed(() => (result.value ? tests.testById(result.value.testId) : null))
const employee = computed(() => (result.value ? employees.findById(result.value.employeeId) : null))
const name = computed(() => nameParts(employee.value))
const maxAttempts = computed(() => tests.settings?.maxAttempts ?? 3)
const canRetake = computed(() => result.value?.status === 'O‘tmadi' && result.value.attempts.length < maxAttempts.value)

// Urinishlar (oxirgisi tanlangan)
const attemptIndex = ref(0)
watch(
  () => [props.open, props.resultId, result.value?.attempts.length],
  () => (attemptIndex.value = Math.max(0, (result.value?.attempts.length || 1) - 1)),
  { immediate: true },
)
const attempt = computed(() => result.value?.attempts[attemptIndex.value] || null)
const attemptTabs = computed(() =>
  (result.value?.attempts || []).map((a, i) => ({ value: i, label: `${i + 1}-urinish`, count: `${a.score}%` })),
)

// Savollar: topshirilgan paytdagi nusxa, bo‘lmasa joriy test savollari
const rows = computed(() => {
  const a = attempt.value
  if (!a) return []
  const questions = a.questions || test.value?.questions || []
  return questions.map((q, i) => {
    const given = a.answers?.[q.id]
    const answered = given !== undefined && given !== null && given !== ''
    return {
      n: i + 1,
      text: q.text,
      given: answered ? q.options[Number(given)] : null,
      correct: q.options[q.correctIndex],
      ok: answered && Number(given) === q.correctIndex,
    }
  })
})
const filter = ref('all')
watch(() => props.resultId, () => (filter.value = 'all'))
const visible = computed(() => (filter.value === 'wrong' ? rows.value.filter((r) => !r.ok) : rows.value))
const wrongCount = computed(() => rows.value.filter((r) => !r.ok).length)

const info = computed(() => {
  const e = employee.value
  if (!e) return []
  const age = employeeAge(e)
  return [
    { icon: Phone, label: 'Telefon', value: e.phone, href: `tel:${e.phone.replace(/\s/g, '')}` },
    { icon: User, label: 'Yosh / jinsi', value: [age ? `${age} yosh` : '', e.gender].filter(Boolean).join(', ') || '—' },
    { icon: Briefcase, label: 'Lavozim', value: catalog.positionName(e.positionId) },
    { icon: Building2, label: 'Bo‘lim', value: catalog.departmentName(e.departmentId) },
  ]
})
</script>

<template>
  <Modal :open="open && !!result" size="xl" @close="emit('close')">
    <template #header>
      <div v-if="result" class="flex min-w-0 items-center gap-4">
        <Avatar :name="employee?.fullName || '?'" :src="employee?.photo" size="lg" />
        <div class="min-w-0">
          <p class="text-xs text-muted">{{ test?.title || 'Test' }}</p>
          <h2 class="truncate text-lg font-semibold text-ink">
            <RouterLink v-if="employee" :to="`/employees/${employee.id}`" class="hover:text-primary-600" @click="emit('close')">
              {{ name.firstName }} {{ name.lastName }}
            </RouterLink>
            <span v-else>O‘chirilgan xodim</span>
          </h2>
          <div class="mt-1.5"><StatusBadge :status="result.status" :label="RESULT_LABELS[result.status]" /></div>
        </div>
      </div>
    </template>

    <template v-if="result">
      <!-- Shaxsiy ma'lumotlar -->
      <dl class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div v-for="r in info" :key="r.label" class="flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-2.5">
          <component :is="r.icon" class="h-4 w-4 shrink-0 text-muted" />
          <div class="min-w-0">
            <dt class="text-[11px] text-muted">{{ r.label }}</dt>
            <dd class="truncate text-sm font-medium text-ink">
              <a v-if="r.href" :href="r.href" class="tabular-nums hover:text-primary-600">{{ r.value }}</a>
              <template v-else>{{ r.value }}</template>
            </dd>
          </div>
        </div>
      </dl>

      <p v-if="!result.attempts.length" class="mt-6 rounded-xl bg-amber-50 px-4 py-6 text-center text-sm text-amber-800">
        Xodim testni hali topshirmagan.
      </p>

      <template v-else-if="attempt">
        <div v-if="attemptTabs.length > 1" class="mt-5">
          <SegmentedControl v-model="attemptIndex" :options="attemptTabs" aria-label="Urinishlar" />
        </div>

        <!-- Xulosa -->
        <div class="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div class="rounded-xl border border-line p-3">
            <p class="text-xs text-muted">To‘g‘ri javoblar</p>
            <p class="mt-1 text-xl font-semibold tabular-nums text-emerald-600">{{ attempt.correct }}</p>
          </div>
          <div class="rounded-xl border border-line p-3">
            <p class="text-xs text-muted">Jami savollar</p>
            <p class="mt-1 text-xl font-semibold tabular-nums text-ink">{{ attempt.total }}</p>
          </div>
          <div :class="['rounded-xl p-3', attempt.passed ? 'bg-emerald-50' : 'bg-red-50']">
            <p class="text-xs text-muted">Foiz (kerak {{ result.passPercent }}%)</p>
            <p :class="['mt-1 text-xl font-semibold tabular-nums', attempt.passed ? 'text-emerald-700' : 'text-red-700']">{{ attempt.score }}%</p>
          </div>
          <div class="rounded-xl border border-line p-3">
            <p class="flex items-center gap-1.5 text-xs text-muted"><CalendarDays class="h-3.5 w-3.5" />Sana</p>
            <p class="mt-1 text-sm font-semibold tabular-nums text-ink">{{ formatDateTime(attempt.at) }}</p>
          </div>
        </div>

        <!-- Savollar -->
        <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-ink">Savollar va javoblar</h3>
          <SegmentedControl
            v-model="filter"
            :options="[{ value: 'all', label: 'Barchasi', count: rows.length }, { value: 'wrong', label: 'Noto‘g‘rilar', count: wrongCount }]"
            aria-label="Savollar filtri"
          />
        </div>

        <ol class="stagger mt-3 space-y-2.5">
          <li v-for="r in visible" :key="r.n" :class="['rounded-xl border p-4 transition-colors', r.ok ? 'border-emerald-100 bg-emerald-50/30' : 'border-red-100 bg-red-50/30']">
            <div class="flex items-start gap-3">
              <span :class="['grid h-7 w-7 shrink-0 place-items-center rounded-full text-white', r.ok ? 'bg-emerald-500' : 'bg-red-500']">
                <Check v-if="r.ok" class="h-4 w-4" />
                <X v-else class="h-4 w-4" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-start justify-between gap-2">
                  <p class="text-sm font-medium text-ink"><span class="text-muted">{{ r.n }}.</span> {{ r.text }}</p>
                  <span :class="['shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold', r.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700']">
                    {{ r.ok ? 'To‘g‘ri' : 'Noto‘g‘ri' }}
                  </span>
                </div>
                <dl class="mt-2.5 grid gap-2 text-sm sm:grid-cols-2">
                  <div class="rounded-lg bg-white px-3 py-2 ring-1 ring-line">
                    <dt class="text-[11px] text-muted">Xodim javobi</dt>
                    <dd :class="['mt-0.5 font-medium', r.ok ? 'text-emerald-700' : 'text-red-700']">
                      <span v-if="r.given">{{ r.given }}</span>
                      <span v-else class="inline-flex items-center gap-1 text-muted"><CircleSlash class="h-3.5 w-3.5" />Javob berilmagan</span>
                    </dd>
                  </div>
                  <div class="rounded-lg bg-white px-3 py-2 ring-1 ring-line">
                    <dt class="text-[11px] text-muted">To‘g‘ri javob</dt>
                    <dd class="mt-0.5 font-medium text-emerald-700">{{ r.correct }}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </li>
        </ol>
        <p v-if="!visible.length" class="mt-3 rounded-xl bg-emerald-50 px-4 py-6 text-center text-sm text-emerald-800">Barcha javoblar to‘g‘ri</p>
      </template>
    </template>

    <template #footer>
      <Button v-if="result?.status === 'Kutilmoqda'" :icon="Play" @click="emit('start', result)">Testni boshlash</Button>
      <Button v-else-if="canRetake" variant="secondary" :icon="RotateCcw" @click="emit('start', result)">Qayta topshirish</Button>
      <Button variant="secondary" @click="emit('close')">Yopish</Button>
    </template>
  </Modal>
</template>
