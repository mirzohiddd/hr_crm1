<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarClock, ClipboardCheck, GraduationCap, UserRoundSearch, Users } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import EmployeeStatsChart from '@/components/dashboard/EmployeeStatsChart.vue'
import DepartmentBreakdown from '@/components/dashboard/DepartmentBreakdown.vue'
import EmployeeTable from '@/components/employees/EmployeeTable.vue'
import TrainingProgress from '@/components/lessons/TrainingProgress.vue'
import Avatar from '@/components/ui/Avatar.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { useAuthStore } from '@/stores/auth'
import { useEmployeesStore } from '@/stores/employees'
import { useCandidatesStore } from '@/stores/candidates'
import { useTrainingsStore, trainingProgress } from '@/stores/trainings'
import { useTestsStore } from '@/stores/tests'
import { useCatalogStore } from '@/stores/catalog'
import { CANDIDATE_STAGES } from '@/constants'
import { MONTHS, MONTHS_SHORT, formatDateLong, todayISO, weekdayName } from '@/utils/date'
import { percent } from '@/utils/format'

const router = useRouter()
const auth = useAuthStore()
const employees = useEmployeesStore()
const candidates = useCandidatesStore()
const trainings = useTrainingsStore()
const tests = useTestsStore()
const catalog = useCatalogStore()

const today = todayISO()

onMounted(() => {
  employees.fetchAll()
  candidates.fetchAll()
  trainings.fetchAll()
  tests.fetchAll()
})

const employeesLoading = computed(() => employees.loading && !employees.loaded)
const candidatesLoading = computed(() => candidates.loading && !candidates.loaded)
const trainingLoading = computed(() => !trainings.loaded)
const firstName = computed(() => auth.user?.fullName.split(' ')[1] || auth.user?.fullName || '')

const newThisMonth = computed(() => employees.items.filter((e) => e.hireDate.slice(0, 7) === today.slice(0, 7)).length)

const inTraining = computed(() =>
  trainings.items
    .filter((t) => !trainingProgress(t).finished)
    .map((t) => ({ ...t, employee: employees.findById(t.employeeId), p: trainingProgress(t) }))
    .filter((t) => t.employee)
    .sort((a, b) => a.startDate.localeCompare(b.startDate)),
)
const overdue = computed(() => inTraining.value.filter((t) => t.p.plannedDate(t.p.nextDay) < today).length)

/** So‘nggi 12 oy: qabul qilinganlar, ketganlar va oy oxiridagi jami */
const chartData = computed(() => {
  const list = employees.items
  const [y, m] = today.split('-').map(Number)
  return Array.from({ length: 12 }, (_, i) => {
    const d = new Date(y, m - 1 - (11 - i), 1)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const monthEnd = `${key}-31`
    return {
      key,
      label: MONTHS_SHORT[d.getMonth()],
      fullLabel: `${MONTHS[d.getMonth()]} ${d.getFullYear()}`,
      hired: list.filter((e) => e.hireDate.slice(0, 7) === key).length,
      left: list.filter((e) => e.leftAt && e.leftAt.slice(0, 7) === key).length,
      total: list.filter((e) => e.hireDate <= monthEnd && !(e.leftAt && e.leftAt <= monthEnd)).length,
    }
  })
})

const funnel = computed(() => {
  const total = candidates.items.length
  return CANDIDATE_STAGES.map((s) => ({ ...s, count: candidates.counts[s.value] || 0, pct: percent(candidates.counts[s.value] || 0, total) }))
})
const hireRate = computed(() => {
  const hired = candidates.counts['Ishga qabul qilindi'] || 0
  const closed = hired + (candidates.counts['Rad etildi'] || 0)
  return closed ? percent(hired, closed) : 0
})
const FUNNEL_TONES = { blue: 'bg-primary-600', sky: 'bg-sky-500', orange: 'bg-orange-500', amber: 'bg-amber-500', green: 'bg-emerald-500', red: 'bg-red-400' }

const breakdown = ref('dept')
const recent = computed(() => [...employees.items].sort((a, b) => b.hireDate.localeCompare(a.hireDate)).slice(0, 6))

function openEmployee(e) {
  router.push(`/employees/${e.id}`)
}
</script>

<template>
  <div>
    <PageHeader title="Bosh sahifa">
      <template #subtitle>Xush kelibsiz{{ firstName ? `, ${firstName}` : '' }}! HR bo‘limining bugungi holati.</template>
      <template #actions>
        <p class="text-sm text-muted">
          <span class="font-medium text-ink">{{ formatDateLong(today) }}</span>, {{ weekdayName(today).toLowerCase() }}
        </p>
      </template>
    </PageHeader>

    <div class="stagger grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Jami xodimlar" :value="employees.stats.total" :icon="Users" :loading="employeesLoading">
        <template #hint>
          <span class="font-medium text-primary-600">+{{ newThisMonth }}</span> shu oyda qo‘shildi
        </template>
      </StatCard>
      <StatCard label="Yangi nomzodlar" :value="candidates.counts['Yangi'] || 0" :icon="UserRoundSearch" tone="blue" :loading="candidatesLoading" :hint="`Bugun ${candidates.newToday} ta ariza keldi`" />
      <StatCard label="O‘qiyotganlar" :value="inTraining.length" :icon="GraduationCap" tone="green" :loading="trainingLoading" :hint="overdue ? `${overdue} nafari rejadan ortda` : '7 kunlik dastur jarayonida'" />
      <StatCard label="Testdan o‘tish" :value="`${tests.stats.passRate}%`" :icon="ClipboardCheck" tone="amber" :loading="!tests.loaded" :hint="`${tests.stats.pending} ta test kutilmoqda`" />
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-3">
      <section class="card min-w-0 p-5 sm:p-6 xl:col-span-2">
        <ErrorState v-if="employees.error" :message="employees.error" @retry="employees.fetchAll({ force: true })" />
        <template v-else-if="employeesLoading">
          <div class="h-5 w-48 animate-pulse rounded bg-slate-100" />
          <LoadingState class="mt-6" variant="block" style="height: 320px" />
        </template>
        <EmployeeStatsChart v-else :data="chartData" />
      </section>

      <section class="card p-5 sm:p-6">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-ink">Nomzodlar voronkasi</h2>
            <p class="mt-0.5 text-sm text-muted">Barcha arizalar bosqichlar bo‘yicha</p>
          </div>
          <RouterLink to="/candidates" class="shrink-0 text-sm font-medium text-primary-600 hover:underline">Ochish</RouterLink>
        </div>
        <LoadingState v-if="candidatesLoading" class="mt-5" variant="block" />
        <template v-else>
          <ul class="mt-5 space-y-3.5">
            <li v-for="s in funnel" :key="s.value">
              <div class="flex items-baseline justify-between text-sm">
                <span class="text-ink">{{ s.label }}</span>
                <span class="tabular-nums"><span class="font-medium text-ink">{{ s.count }}</span><span class="ml-2 inline-block w-9 text-right text-muted">{{ s.pct }}%</span></span>
              </div>
              <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                <div :class="['h-full rounded-full transition-[width] duration-500', FUNNEL_TONES[s.tone]]" :style="{ width: `${Math.max(s.pct, s.count ? 3 : 0)}%` }" />
              </div>
            </li>
          </ul>
          <p class="mt-5 rounded-lg bg-primary-50 px-3 py-2.5 text-sm text-primary-800">
            Ko‘rib chiqilgan nomzodlarning <span class="font-semibold">{{ hireRate }}%</span> i ishga qabul qilingan
          </p>
        </template>
      </section>
    </div>

    <div class="mt-6 grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
      <section class="card p-5 sm:p-6">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-ink">Bugungi suhbatlar</h2>
            <p class="mt-0.5 text-sm text-muted">{{ candidates.interviewsToday.length ? `${candidates.interviewsToday.length} ta rejalashtirilgan` : 'Rejalashtirilmagan' }}</p>
          </div>
          <span class="grid h-10 w-10 place-items-center rounded-lg bg-amber-50 text-amber-600"><CalendarClock class="h-5 w-5" /></span>
        </div>
        <ul v-if="candidates.interviewsToday.length" class="mt-4 divide-y divide-line">
          <li v-for="c in candidates.interviewsToday" :key="c.id">
            <RouterLink :to="{ path: '/candidates', query: { id: c.id } }" class="flex items-center gap-3 py-2.5 hover:text-primary-600">
              <span class="w-12 shrink-0 rounded-md bg-amber-50 py-1 text-center text-xs font-semibold tabular-nums text-amber-700">{{ c.interviewAt.slice(11, 16) }}</span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium">{{ c.fullName }}</span>
                <span class="block truncate text-xs text-muted">{{ catalog.positionName(c.positionId) }}</span>
              </span>
            </RouterLink>
          </li>
        </ul>
        <p v-else class="mt-6 text-sm text-muted">Bugun uchun suhbat belgilanmagan. Nomzodlar bo‘limida “Suhbatga chaqirish” orqali qo‘shing.</p>
      </section>

      <section class="card p-5 sm:p-6">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold text-ink">Darsdagi xodimlar</h2>
            <p class="mt-0.5 text-sm text-muted">7 kunlik dastur progressi</p>
          </div>
          <RouterLink to="/lessons" class="shrink-0 text-sm font-medium text-primary-600 hover:underline">Barchasi</RouterLink>
        </div>
        <LoadingState v-if="trainingLoading" class="mt-5" variant="block" />
        <ul v-else-if="inTraining.length" class="mt-4 space-y-4">
          <li v-for="t in inTraining.slice(0, 5)" :key="t.id">
            <RouterLink :to="{ path: '/lessons', query: { employee: t.employeeId } }" class="flex items-center gap-3">
              <Avatar :name="t.employee.fullName" :src="t.employee.photo" size="sm" />
              <span class="min-w-0 flex-1">
                <span class="flex items-baseline justify-between gap-2">
                  <span class="truncate text-sm font-medium text-ink">{{ t.employee.fullName }}</span>
                  <span class="shrink-0 text-xs tabular-nums text-muted">{{ t.p.done }}/7</span>
                </span>
                <TrainingProgress class="mt-1.5" :done="t.p.done" :show-label="false" size="sm" />
              </span>
            </RouterLink>
          </li>
        </ul>
        <p v-else class="mt-6 text-sm text-muted">Hozir hech kim o‘quv dasturida emas.</p>
      </section>

      <section class="card p-5 sm:p-6 lg:col-span-2 xl:col-span-1">
        <LoadingState v-if="employeesLoading" variant="block" />
        <template v-else>
          <SegmentedControl v-model="breakdown" class="mb-4" :options="[{ value: 'dept', label: 'Bo‘limlar' }, { value: 'pos', label: 'Lavozimlar' }]" aria-label="Kesim" />
          <DepartmentBreakdown
            :items="breakdown === 'dept' ? employees.byDepartment : employees.byPosition"
            :title="breakdown === 'dept' ? 'Bo‘limlar kesimida' : 'Lavozimlar kesimida'"
            subtitle="Faol va yangi xodimlar"
          />
        </template>
      </section>
    </div>

    <section class="card mt-6 overflow-hidden">
      <div class="flex items-center justify-between gap-4 px-5 py-4 sm:px-6">
        <div>
          <h2 class="text-base font-semibold text-ink">Yaqinda qo‘shilgan xodimlar</h2>
          <p class="mt-0.5 text-sm text-muted">Oxirgi qabul qilinganlar</p>
        </div>
        <RouterLink to="/employees" class="shrink-0 rounded-md text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline">
          Barchasini ko‘rish
        </RouterLink>
      </div>
      <div class="border-t border-line">
        <ErrorState v-if="employees.error" :message="employees.error" @retry="employees.fetchAll({ force: true })" />
        <LoadingState v-else-if="employeesLoading" :rows="5" />
        <EmployeeTable v-else :rows="recent" compact @view="openEmployee" />
      </div>
    </section>
  </div>
</template>
