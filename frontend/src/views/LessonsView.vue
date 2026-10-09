<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlarmClock, BookOpenCheck, CalendarDays, CheckCircle2, ClipboardCheck, GraduationCap, Pencil, Play, SearchX, Send, UserPlus } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import Modal from '@/components/ui/Modal.vue'
import FormField from '@/components/ui/FormField.vue'
import Select from '@/components/ui/Select.vue'
import TrainingProgress from '@/components/lessons/TrainingProgress.vue'
import TrainingTimeline from '@/components/lessons/TrainingTimeline.vue'
import { useTrainingsStore, trainingProgress, trainingState } from '@/stores/trainings'
import { useTestsStore } from '@/stores/tests'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { useToast } from '@/composables/useToast'
import { useTrainingActions } from '@/composables/useTrainingActions'
import { TRAINING_DAYS } from '@/constants'
import { formatDate, todayISO } from '@/utils/date'
import { normalizeText, toLines } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useTrainingsStore()
const tests = useTestsStore()
const employees = useEmployeesStore()
const catalog = useCatalogStore()
const toast = useToast()
const { busyDay, assigning, complete, undo, assignTest } = useTrainingActions()
const today = todayISO()

onMounted(async () => {
  await Promise.all([store.fetchAll(), tests.fetchAll(), employees.fetchAll()])
  if (route.query.employee) {
    const t = store.byEmployee(route.query.employee)
    if (t) detailId.value = t.id
  }
})

const firstLoad = computed(() => !store.loaded && store.loading)

/** Xodimning shu dasturga tegishli (yoki eng so‘nggi) test natijasi */
const resultOf = (t) => tests.results.find((r) => r.id === t.testResultId) || tests.resultsOf(t.employeeId)[0] || null

const rows = computed(() =>
  store.items
    .map((t) => {
      const employee = employees.findById(t.employeeId)
      const result = resultOf(t)
      const p = trainingProgress(t)
      return {
        ...t,
        employee,
        result,
        progress: p,
        state: trainingState(t, result),
        nextLesson: p.nextDay ? store.lessonOf(p.nextDay) : null,
        overdue: !p.finished && p.plannedDate(p.nextDay) < today,
      }
    })
    .filter((r) => r.employee)
    .sort((a, b) => b.startDate.localeCompare(a.startDate)),
)

// ---------- Filtrlar ----------
const tab = ref('active')
const search = ref('')
const count = (fn) => rows.value.filter(fn).length
const tabs = computed(() => [
  { value: 'active', label: 'Jarayonda', count: count((r) => r.state === 'Jarayonda') },
  { value: 'test', label: 'Test kutilmoqda', count: count((r) => ['Testga yuborildi', 'Yakunlandi', 'O‘tmadi'].includes(r.state)) },
  { value: 'done', label: 'Yakunlangan', count: count((r) => r.state === 'O‘tdi') },
  { value: 'all', label: 'Barchasi', count: rows.value.length },
])
const filtered = computed(() => {
  const q = normalizeText(search.value)
  return rows.value.filter((r) => {
    if (tab.value === 'active' && r.state !== 'Jarayonda') return false
    if (tab.value === 'test' && !['Testga yuborildi', 'Yakunlandi', 'O‘tmadi'].includes(r.state)) return false
    if (tab.value === 'done' && r.state !== 'O‘tdi') return false
    return !q || normalizeText(r.employee.fullName).includes(q)
  })
})

const stats = computed(() => ({
  active: count((r) => r.state === 'Jarayonda'),
  overdue: count((r) => r.overdue),
  testing: count((r) => r.state === 'Testga yuborildi'),
  passed: count((r) => r.state === 'O‘tdi'),
}))

// ---------- Detail ----------
const detailId = ref(null)
const selected = computed(() => rows.value.find((r) => r.id === detailId.value) || null)
function closeDetail() {
  detailId.value = null
  if (route.query.employee) router.replace({ query: {} })
}

async function onComplete(day) {
  const t = selected.value
  const res = await complete(t, day)
  if (res && day === TRAINING_DAYS) tab.value = 'test'
}

async function sendToTest(row) {
  await assignTest(row.employeeId)
}

function startTest(row) {
  router.push({ path: '/tests', query: { start: row.result.id } })
}

// ---------- Dasturga qo‘shish ----------
const addOpen = ref(false)
const addForm = ref({ employeeId: '', startDate: today })
const addError = ref('')
const adding = ref(false)
const candidatesForTraining = computed(() =>
  employees.items
    .filter((e) => e.status !== 'Faol emas' && !store.byEmployee(e.id))
    .sort((a, b) => b.hireDate.localeCompare(a.hireDate))
    .map((e) => ({ value: e.id, label: `${e.fullName} — ${catalog.positionName(e.positionId)}` })),
)
function openAdd() {
  addForm.value = { employeeId: '', startDate: today }
  addError.value = ''
  addOpen.value = true
}
async function submitAdd() {
  if (!addForm.value.employeeId) return (addError.value = 'Xodimni tanlang')
  adding.value = true
  try {
    const t = await store.start(Number(addForm.value.employeeId), addForm.value.startDate || today)
    toast.success('Xodim o‘quv dasturiga qo‘shildi', employees.findById(t.employeeId)?.fullName)
    addOpen.value = false
    tab.value = 'active'
    detailId.value = t.id
  } catch (e) {
    toast.error('Qo‘shib bo‘lmadi', e.message)
  } finally {
    adding.value = false
  }
}

// ---------- Dastur mazmuni ----------
const programOpen = ref(false)
watch(selected, (s) => {
  if (detailId.value && !s && store.loaded) detailId.value = null
})
</script>

<template>
  <div>
    <PageHeader title="Darslar" subtitle="Yangi xodimlar uchun 7 kunlik o‘quv dasturi">
      <template #actions>
        <Button variant="secondary" :icon="BookOpenCheck" @click="programOpen = true">Dastur mazmuni</Button>
        <Button :icon="UserPlus" @click="openAdd">Xodimni qo‘shish</Button>
      </template>
    </PageHeader>

    <div class="stagger grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="O‘qiyotganlar" :value="stats.active" :icon="GraduationCap" :loading="firstLoad" hint="Dastur jarayonida" />
      <StatCard label="Rejadan ortda" :value="stats.overdue" :icon="AlarmClock" tone="amber" :loading="firstLoad" hint="Navbatdagi kun o‘tib ketgan" />
      <StatCard label="Testga yuborilgan" :value="stats.testing" :icon="ClipboardCheck" tone="slate" :loading="firstLoad" hint="Topshirish kutilmoqda" />
      <StatCard label="Muvaffaqiyatli tugatgan" :value="stats.passed" :icon="CheckCircle2" tone="green" :loading="firstLoad" hint="Testdan o‘tgan" />
    </div>

    <div class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center">
      <SegmentedControl v-model="tab" :options="tabs" aria-label="Dastur holati" />
      <div class="lg:ml-auto lg:w-72">
        <SearchInput v-model="search" placeholder="Xodim ismi..." label="Xodim qidirish" />
      </div>
    </div>

    <ErrorState v-if="store.error" class="card mt-4" :message="store.error" @retry="store.fetchAll({ force: true })" />
    <LoadingState v-else-if="firstLoad" class="mt-4" variant="cards" :rows="6" />
    <div v-else-if="!rows.length" class="card mt-4">
      <EmptyState :icon="GraduationCap" title="Hali hech kim o‘qimayapti" description="Nomzodni ishga qabul qilganda u avtomatik 7 kunlik dasturga qo‘shiladi.">
        <Button :icon="UserPlus" @click="openAdd">Xodimni qo‘shish</Button>
      </EmptyState>
    </div>
    <div v-else-if="!filtered.length" class="card mt-4">
      <EmptyState :icon="SearchX" title="Bu bo‘limda hech kim yo‘q" description="Boshqa holatni tanlang yoki qidiruvni tozalang.">
        <Button variant="secondary" @click="tab = 'all'; search = ''">Barchasini ko‘rsatish</Button>
      </EmptyState>
    </div>

    <div v-else class="stagger mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <article
        v-for="r in filtered"
        :key="r.id"
        class="card card-hover flex cursor-pointer flex-col p-5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/15"
        tabindex="0"
        @click="detailId = r.id"
        @keydown.enter="detailId = r.id"
      >
        <div class="flex items-start gap-3">
          <Avatar :name="r.employee.fullName" :src="r.employee.photo" size="md" />
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium text-ink">{{ r.employee.fullName }}</p>
            <p class="truncate text-[13px] text-muted">{{ catalog.positionName(r.employee.positionId) }}</p>
          </div>
          <StatusBadge :status="r.state" size="sm" />
        </div>

        <TrainingProgress class="mt-4" :done="r.progress.done" />

        <div class="mt-4 flex-1 rounded-lg bg-slate-50 px-3 py-2.5 text-sm">
          <template v-if="r.nextLesson">
            <p class="text-xs text-muted">{{ r.progress.nextDay }}-kun · {{ formatDate(r.progress.plannedDate(r.progress.nextDay)) }}</p>
            <p class="mt-0.5 truncate font-medium text-ink">{{ r.nextLesson.title }}</p>
            <p v-if="r.overdue" class="mt-1 text-xs font-medium text-amber-700">Rejadan ortda qolmoqda</p>
          </template>
          <template v-else-if="r.result && r.result.score !== null">
            <p class="text-xs text-muted">Test natijasi</p>
            <p :class="['mt-0.5 font-medium', r.result.status === 'O‘tdi' ? 'text-emerald-700' : 'text-red-700']">{{ r.result.score }}% — {{ r.result.status }}</p>
          </template>
          <template v-else>
            <p class="text-xs text-muted">7 kun yakunlandi</p>
            <p class="mt-0.5 font-medium text-ink">{{ r.result ? 'Test topshirish kutilmoqda' : 'Testga yuborilmagan' }}</p>
          </template>
        </div>

        <p class="mt-3 flex items-center gap-1.5 text-xs text-muted">
          <CalendarDays class="h-3.5 w-3.5" /> Boshlangan: {{ formatDate(r.startDate) }}
        </p>
      </article>
    </div>

    <!-- Xodim dasturi -->
    <Modal :open="!!selected" size="lg" @close="closeDetail">
      <template #header>
        <div v-if="selected" class="flex min-w-0 items-center gap-3">
          <Avatar :name="selected.employee.fullName" :src="selected.employee.photo" size="md" />
          <div class="min-w-0">
            <RouterLink :to="`/employees/${selected.employee.id}`" class="block truncate text-base font-semibold text-ink hover:text-primary-600 sm:text-lg">
              {{ selected.employee.fullName }}
            </RouterLink>
            <p class="truncate text-sm text-muted">{{ catalog.positionName(selected.employee.positionId) }} · boshlangan {{ formatDate(selected.startDate) }}</p>
          </div>
        </div>
      </template>

      <template v-if="selected">
        <div class="mb-4 flex items-center gap-4">
          <TrainingProgress class="flex-1" :done="selected.progress.done" />
          <StatusBadge :status="selected.state" />
        </div>
        <TrainingTimeline :training="selected" :busy-day="busyDay" @complete="onComplete" @undo="(d) => undo(selected, d)" />
      </template>

      <template #footer>
        <template v-if="selected">
          <Button v-if="selected.state === 'Yakunlandi'" :icon="Send" :loading="assigning" @click="sendToTest(selected)">Testga yuborish</Button>
          <Button v-else-if="selected.state === 'Testga yuborildi'" :icon="Play" @click="startTest(selected)">Testni boshlash</Button>
          <Button v-else-if="selected.state === 'O‘tmadi' || selected.state === 'O‘tdi'" variant="secondary" :icon="ClipboardCheck" @click="startTest(selected)">Test natijasi</Button>
          <Button variant="secondary" @click="closeDetail">Yopish</Button>
        </template>
      </template>
    </Modal>

    <!-- Dastur mazmuni -->
    <Modal :open="programOpen" size="lg" title="7 kunlik dastur" subtitle="Har bir kun uchun dars mavzusi va mazmuni" @close="programOpen = false">
      <ol class="space-y-3">
        <li v-for="l in store.lessons" :key="l.id" class="rounded-xl border border-line p-4">
          <div class="flex items-start gap-3">
            <span class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary-50 text-sm font-semibold text-primary-700">{{ l.day }}</span>
            <div class="min-w-0">
              <p class="font-medium text-ink">{{ l.title }}</p>
              <p class="text-xs text-muted">{{ l.duration }} daqiqa</p>
              <p v-if="l.description" class="mt-1.5 text-sm text-slate-600">{{ l.description }}</p>
              <ul class="mt-2 space-y-1">
                <li v-for="(line, i) in toLines(l.content)" :key="i" class="flex gap-2 text-sm text-ink">
                  <span class="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary-500" />{{ line }}
                </li>
              </ul>
            </div>
          </div>
        </li>
      </ol>
      <template #footer>
        <Button variant="secondary" :icon="Pencil" @click="programOpen = false; router.push({ path: '/settings', query: { tab: 'lessons' } })">Darslarni tahrirlash</Button>
        <Button @click="programOpen = false">Yopish</Button>
      </template>
    </Modal>

    <!-- Dasturga qo‘shish -->
    <Modal :open="addOpen" size="md" title="Xodimni dasturga qo‘shish" subtitle="Dasturda hali qatnashmagan xodimlar" :persistent="adding" @close="!adding && (addOpen = false)">
      <form id="add-training" class="space-y-4" novalidate @submit.prevent="submitAdd">
        <FormField label="Xodim" for="tr-emp" :error="addError" required>
          <Select id="tr-emp" v-model="addForm.employeeId" :options="candidatesForTraining" placeholder="Xodimni tanlang" :error="addError" @update:model-value="addError = ''" />
        </FormField>
        <FormField label="Boshlanish sanasi" for="tr-start" hint="1-kun shu sanaga rejalashtiriladi">
          <input id="tr-start" v-model="addForm.startDate" type="date" class="form-input" />
        </FormField>
      </form>
      <template #footer>
        <Button variant="secondary" :disabled="adding" @click="addOpen = false">Bekor qilish</Button>
        <Button type="submit" form="add-training" :loading="adding">Qo‘shish</Button>
      </template>
    </Modal>
  </div>
</template>
