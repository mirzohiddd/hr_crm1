<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, BadgeCheck, Briefcase, Building2, MonitorSmartphone, UserRound, Users, Wallet, Cake, CalendarCheck, ClipboardCheck, Eye, FileText, GraduationCap, Mail, MapPin,
  Pencil, Phone, Play, RotateCcw, Send, Trash2, Upload, User, UserRoundSearch, UserX,
} from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmployeeForm from '@/components/employees/EmployeeForm.vue'
import TrainingProgress from '@/components/lessons/TrainingProgress.vue'
import TrainingTimeline from '@/components/lessons/TrainingTimeline.vue'
import TestRunner from '@/components/tests/TestRunner.vue'
import ResultDetails from '@/components/tests/ResultDetails.vue'
import { RESULT_LABELS } from '@/constants'
import DocumentTable from '@/components/documents/DocumentTable.vue'
import DocumentDetails from '@/components/documents/DocumentDetails.vue'
import DocumentUpload from '@/components/documents/DocumentUpload.vue'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { useTrainingsStore, trainingProgress, trainingState } from '@/stores/trainings'
import { useTestsStore } from '@/stores/tests'
import { useDocumentsStore } from '@/stores/documents'
import { useCandidatesStore } from '@/stores/candidates'
import { useToast } from '@/composables/useToast'
import { useTrainingActions } from '@/composables/useTrainingActions'
import { useDocumentActions } from '@/composables/useDocumentActions'
import { ageFrom, formatDate, formatDateTime, tenure, todayISO } from '@/utils/date'
import { formatMoney, nameParts, telegramHandle, telegramLink } from '@/utils/format'
import { COMPUTER_SKILLS } from '@/constants'

const route = useRoute()
const router = useRouter()
const employees = useEmployeesStore()
const catalog = useCatalogStore()
const trainings = useTrainingsStore()
const tests = useTestsStore()
const documents = useDocumentsStore()
const candidates = useCandidatesStore()
const toast = useToast()
const { busyDay, assigning, complete, undo, assignTest } = useTrainingActions()
const docs = useDocumentActions()

const id = computed(() => Number(route.params.id))
const loading = ref(true)

onMounted(async () => {
  await Promise.all([employees.fetchAll(), trainings.fetchAll(), tests.fetchAll(), documents.fetchAll(), candidates.fetchAll()])
  loading.value = false
})

const employee = computed(() => employees.findById(id.value))
const training = computed(() => trainings.byEmployee(id.value))
const results = computed(() => tests.resultsOf(id.value))
const latestResult = computed(() => (training.value?.testResultId && tests.results.find((r) => r.id === training.value.testResultId)) || results.value[0] || null)
const state = computed(() => trainingState(training.value, latestResult.value))
const progress = computed(() => trainingProgress(training.value))
const employeeDocs = computed(() => documents.ofEmployee(id.value).sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt)))
const candidate = computed(() => (employee.value?.candidateId ? candidates.findById(employee.value.candidateId) : null))
const maxAttempts = computed(() => tests.settings?.maxAttempts ?? 3)

watch(employee, (e) => {
  if (e) document.title = `${e.fullName} — HR CRM`
})

// ---------- Tablar ----------
const TABS = ['overview', 'training', 'tests', 'documents']
const tab = ref(TABS.includes(route.query.tab) ? route.query.tab : 'overview')
watch(tab, (t) => router.replace({ query: t === 'overview' ? {} : { tab: t } }))
const tabs = computed(() => [
  { value: 'overview', label: 'Umumiy' },
  { value: 'training', label: 'Darslar', count: training.value ? `${progress.value.done}/7` : undefined },
  { value: 'tests', label: 'Testlar', count: results.value.length || undefined },
  { value: 'documents', label: 'Hujjatlar', count: employeeDocs.value.length },
])

const parts = computed(() => nameParts(employee.value))
const skill = computed(() => COMPUTER_SKILLS.find((x) => x.value === employee.value?.computerSkill) || null)

/** Profil bo‘limlari: har biri alohida karta */
const sections = computed(() => {
  const e = employee.value
  if (!e) return []
  const tg = telegramHandle(e.telegram)
  const personal = [
    { icon: User, label: 'Ism', value: parts.value.firstName || '—' },
    { icon: User, label: 'Familiya', value: parts.value.lastName || '—' },
    { icon: User, label: 'Otasining ismi', value: parts.value.middleName || '—' },
    { icon: Users, label: 'Jinsi', value: e.gender || '—' },
    { icon: Phone, label: 'Telefon', value: e.phone || '—', href: e.phone ? `tel:${e.phone.replace(/\s/g, '')}` : null },
    { icon: Send, label: 'Telegram', value: tg || '—', href: telegramLink(e.telegram), external: true },
    ...(e.email ? [{ icon: Mail, label: 'Email', value: e.email, href: `mailto:${e.email}` }] : []),
    ...(e.birthDate ? [{ icon: Cake, label: 'Tug‘ilgan sana', value: formatDate(e.birthDate), extra: `${ageFrom(e.birthDate)} yosh` }] : e.age ? [{ icon: Cake, label: 'Yosh', value: `${e.age} yosh` }] : []),
    { icon: MapPin, label: 'Yashash manzili', value: e.address || '—', wide: true },
  ]
  const work = [
    { icon: Building2, label: 'Bo‘lim', value: catalog.departmentName(e.departmentId), accent: true },
    { icon: Briefcase, label: 'Lavozim', value: catalog.positionName(e.positionId), accent: true },
    { icon: CalendarCheck, label: 'Ishga qabul qilingan sana', value: formatDate(e.hireDate), extra: `Staj: ${tenure(e.hireDate)}` },
    { icon: BadgeCheck, label: 'Status', status: e.status },
    ...(e.status === 'Faol emas' && e.leftAt ? [{ icon: UserX, label: 'Ishdan ketgan sana', value: formatDate(e.leftAt) }] : []),
  ]
  return [
    { key: 'personal', title: 'Shaxsiy ma’lumotlar', icon: UserRound, rows: personal },
    { key: 'work', title: 'Ish ma’lumotlari', icon: Building2, rows: work },
  ]
})
const recentDocs = computed(() => employeeDocs.value.slice(0, 3))

// ---------- Tahrirlash / o‘chirish ----------
const formOpen = ref(false)
const saving = ref(false)
async function handleSubmit(data) {
  saving.value = true
  try {
    await employees.update(employee.value.id, data)
    toast.success('O‘zgarishlar saqlandi', data.fullName)
    formOpen.value = false
  } catch (e) {
    toast.error('Saqlab bo‘lmadi', e.message)
  } finally {
    saving.value = false
  }
}

const deleteOpen = ref(false)
const deleting = ref(false)
async function confirmDelete() {
  deleting.value = true
  const name = employee.value.fullName
  try {
    await employees.remove(employee.value.id)
    // Bog‘liq yozuvlar serverda o‘chiriladi — store’larni yangilaymiz
    trainings.fetchAll({ force: true })
    tests.fetchAll({ force: true })
    documents.fetchAll({ force: true })
    toast.success('Xodim o‘chirildi', name)
    router.replace('/employees')
  } catch (e) {
    toast.error('O‘chirib bo‘lmadi', e.message)
  } finally {
    deleting.value = false
  }
}

// ---------- Darslar ----------
const starting = ref(false)
async function startTraining() {
  starting.value = true
  try {
    await trainings.start(employee.value.id, todayISO())
    toast.success('O‘quv dasturi boshlandi', '1-kun bugunga rejalashtirildi')
  } catch (e) {
    toast.error('Boshlab bo‘lmadi', e.message)
  } finally {
    starting.value = false
  }
}
async function onComplete(day) {
  const res = await complete(training.value, day)
  if (res?.testResult) tab.value = 'tests'
}

// ---------- Testlar ----------
const runnerId = ref(null)
const detailsId = ref(null)
function openResult(r) {
  if (!r.attempts.length) runnerId.value = r.id
  else detailsId.value = r.id
}
const hasPending = computed(() => results.value.some((r) => r.status === 'Kutilmoqda'))
const hasPassed = computed(() => results.value.some((r) => r.status === 'O‘tdi'))
const canRetake = (r) => r.status === 'O‘tmadi' && r.attempts.length < maxAttempts.value
async function sendTest() {
  const r = await assignTest(employee.value.id)
  if (r) tab.value = 'tests'
}

const selectedDoc = computed(() => documents.items.find((d) => d.id === docs.detailId.value) || null)
</script>

<template>
  <div>
    <RouterLink to="/employees" class="mb-4 inline-flex items-center gap-1.5 rounded-md text-sm font-medium text-muted hover:text-primary-600">
      <ArrowLeft class="h-4 w-4" /> Xodimlar
    </RouterLink>

    <div v-if="loading && !employee" class="card p-6">
      <LoadingState variant="block" />
    </div>

    <div v-else-if="!employee" class="card">
      <EmptyState :icon="UserX" title="Xodim topilmadi" description="Xodim o‘chirilgan yoki havola noto‘g‘ri.">
        <Button variant="secondary" @click="router.push('/employees')">Xodimlar ro‘yxati</Button>
      </EmptyState>
    </div>

    <template v-else>
      <!-- Sarlavha -->
      <section class="card overflow-hidden">
        <div class="h-20 bg-gradient-to-r from-primary-600 to-primary-500 sm:h-24" />
        <div class="px-5 pb-5 sm:px-6">
          <div class="-mt-10 flex flex-col gap-4 sm:-mt-12 sm:flex-row sm:items-start">
            <Avatar :name="employee.fullName" :src="employee.photo" size="xl" class="ring-4 ring-white sm:h-24 sm:w-24 sm:text-2xl" />
            <!-- Matn banner ostida boshlanadi (avatar banner ustiga chiqadi) -->
            <div class="min-w-0 flex-1 sm:pt-14">
              <div class="flex flex-wrap items-center gap-2">
                <h1 class="truncate text-xl font-semibold tracking-tight text-ink sm:text-2xl">{{ employee.fullName }}</h1>
                <StatusBadge :status="employee.status" />
              </div>
              <div class="mt-2 flex flex-wrap items-center gap-2 text-sm">
                <span class="inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-2.5 py-1 font-medium text-primary-700 ring-1 ring-primary-100">
                  <Building2 class="h-3.5 w-3.5" />{{ catalog.departmentName(employee.departmentId) }}
                </span>
                <span class="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700">
                  <Briefcase class="h-3.5 w-3.5" />{{ catalog.positionName(employee.positionId) }}
                </span>
              </div>
            </div>
            <div class="flex shrink-0 gap-2 sm:pt-14">
              <Button variant="secondary" :icon="Pencil" @click="formOpen = true">Tahrirlash</Button>
              <button class="icon-btn h-10 w-10 border border-line hover:border-red-200 hover:bg-red-50 hover:text-red-600" aria-label="Xodimni o‘chirish" title="O‘chirish" @click="deleteOpen = true">
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div class="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            <a :href="`tel:${employee.phone.replace(/\s/g, '')}`" class="inline-flex items-center gap-1.5 text-slate-600 hover:text-primary-600">
              <Phone class="h-4 w-4 text-muted" /><span class="tabular-nums">{{ employee.phone }}</span>
            </a>
            <a v-if="employee.telegram" :href="telegramLink(employee.telegram)" target="_blank" rel="noopener" class="inline-flex items-center gap-1.5 text-slate-600 hover:text-primary-600">
              <Send class="h-4 w-4 text-muted" />{{ telegramHandle(employee.telegram) }}
            </a>
            <span class="inline-flex items-center gap-1.5 text-slate-600"><CalendarCheck class="h-4 w-4 text-muted" />{{ formatDate(employee.hireDate) }} dan · {{ tenure(employee.hireDate) }}</span>
            <span class="inline-flex items-center gap-1.5 text-slate-600"><GraduationCap class="h-4 w-4 text-muted" />O‘quv dasturi: <StatusBadge :status="state" size="sm" /></span>
          </div>
        </div>
      </section>

      <div class="mt-6">
        <SegmentedControl v-model="tab" :options="tabs" aria-label="Profil bo‘limlari" />
      </div>

      <!-- Umumiy -->
      <div v-if="tab === 'overview'" class="mt-4 grid gap-6 lg:grid-cols-3">
        <div class="stagger space-y-6 lg:col-span-2">
          <section v-for="sec in sections" :key="sec.key" class="card p-5 sm:p-6">
            <h2 class="flex items-center gap-2 text-base font-semibold text-ink">
              <span class="grid h-8 w-8 place-items-center rounded-lg bg-primary-50 text-primary-600"><component :is="sec.icon" class="h-4 w-4" /></span>
              {{ sec.title }}
            </h2>
            <dl class="mt-5 grid gap-x-6 gap-y-5 sm:grid-cols-2 xl:grid-cols-3">
              <div v-for="r in sec.rows" :key="r.label" :class="['flex gap-3', r.wide && 'sm:col-span-2 xl:col-span-3']">
                <span :class="['grid h-9 w-9 shrink-0 place-items-center rounded-lg', r.accent ? 'bg-primary-50 text-primary-600' : 'bg-slate-50 text-muted']">
                  <component :is="r.icon" class="h-4 w-4" />
                </span>
                <div class="min-w-0">
                  <dt class="text-xs text-muted">{{ r.label }}</dt>
                  <dd class="mt-0.5 text-sm font-medium text-ink">
                    <StatusBadge v-if="r.status" :status="r.status" />
                    <a v-else-if="r.href" :href="r.href" :target="r.external ? '_blank' : undefined" rel="noopener" class="break-all text-primary-700 hover:underline">{{ r.value }}</a>
                    <span v-else class="break-words">{{ r.value }}</span>
                    <span v-if="r.extra" class="mt-0.5 block text-xs font-normal text-muted">{{ r.extra }}</span>
                  </dd>
                </div>
              </div>
            </dl>
          </section>

          <!-- Ish tajribasi va oylik kutuvi -->
          <section class="card p-5 sm:p-6">
            <h2 class="flex items-center gap-2 text-base font-semibold text-ink">
              <span class="grid h-8 w-8 place-items-center rounded-lg bg-primary-50 text-primary-600"><Briefcase class="h-4 w-4" /></span>
              Ish tajribasi va kutuvlar
            </h2>
            <div class="mt-5 grid gap-4 md:grid-cols-3">
              <div class="rounded-xl border border-line p-4 md:col-span-3">
                <p class="text-xs text-muted">Qayerda ishlagan</p>
                <p class="mt-1 whitespace-pre-line text-sm font-medium text-ink">{{ employee.previousWork || 'Ko‘rsatilmagan' }}</p>
              </div>
              <div class="rounded-xl border border-line p-4">
                <p class="flex items-center gap-1.5 text-xs text-muted"><MonitorSmartphone class="h-3.5 w-3.5" /> Kompyuter savodxonligi</p>
                <template v-if="skill">
                  <p class="mt-1 text-sm font-semibold text-ink">{{ skill.value }}</p>
                  <div class="mt-2 flex gap-1">
                    <span v-for="i in 4" :key="i" :class="['h-1.5 flex-1 rounded-full', i <= skill.level ? 'bg-primary-600' : 'bg-slate-200']" />
                  </div>
                </template>
                <p v-else class="mt-1 text-sm font-medium text-muted">Ko‘rsatilmagan</p>
              </div>
              <div class="rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 p-4 text-white shadow-md shadow-primary-600/20 md:col-span-2">
                <p class="flex items-center gap-1.5 text-xs text-primary-100"><Wallet class="h-3.5 w-3.5" /> Oylik kutuvi</p>
                <p class="mt-1 text-2xl font-semibold tabular-nums">{{ employee.expectedSalary ? formatMoney(employee.expectedSalary) : '—' }}</p>
                <p class="mt-0.5 text-xs text-primary-100">Xodim kutayotgan oylik maosh</p>
              </div>
            </div>
          </section>
        </div>

        <div class="space-y-6">
          <section class="card p-5">
            <div class="flex items-center justify-between">
              <h2 class="text-base font-semibold text-ink">O‘quv dasturi</h2>
              <button class="text-sm font-medium text-primary-600 hover:underline" @click="tab = 'training'">Ochish</button>
            </div>
            <template v-if="training">
              <TrainingProgress class="mt-4" :done="progress.done" />
              <p class="mt-3 text-sm text-muted">
                <template v-if="progress.nextDay">Navbatdagi: {{ progress.nextDay }}-kun — {{ trainings.lessonOf(progress.nextDay)?.title }}</template>
                <template v-else>7 kun yakunlangan</template>
              </p>
            </template>
            <p v-else class="mt-3 text-sm text-muted">Xodim o‘quv dasturiga qo‘shilmagan.</p>
          </section>

          <section class="card p-5">
            <div class="flex items-center justify-between">
              <h2 class="text-base font-semibold text-ink">So‘nggi test</h2>
              <button class="text-sm font-medium text-primary-600 hover:underline" @click="tab = 'tests'">Barchasi</button>
            </div>
            <div v-if="latestResult" class="mt-4 flex items-center gap-3">
              <span :class="['grid h-12 w-12 place-items-center rounded-full text-sm font-semibold tabular-nums', latestResult.status === 'O‘tdi' ? 'bg-emerald-50 text-emerald-700' : latestResult.status === 'O‘tmadi' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700']">
                {{ latestResult.score !== null ? `${latestResult.score}%` : '—' }}
              </span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-ink">{{ tests.testById(latestResult.testId)?.title || 'Test' }}</p>
                <StatusBadge class="mt-1" :status="latestResult.status" size="sm" />
              </div>
            </div>
            <p v-else class="mt-3 text-sm text-muted">Test hali yuborilmagan.</p>
          </section>

          <section class="card p-5">
            <div class="flex items-center justify-between">
              <h2 class="text-base font-semibold text-ink">Hujjatlar <span class="text-sm font-normal text-muted">({{ employeeDocs.length }})</span></h2>
              <button class="text-sm font-medium text-primary-600 hover:underline" @click="tab = 'documents'">Barchasi</button>
            </div>
            <ul v-if="recentDocs.length" class="mt-3 divide-y divide-line">
              <li v-for="d in recentDocs" :key="d.id">
                <button class="flex w-full items-center gap-3 py-2.5 text-left hover:text-primary-600" @click="docs.detailId.value = d.id">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600"><FileText class="h-4 w-4" /></span>
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-sm font-medium">{{ d.type }}</span>
                    <span class="block truncate text-xs text-muted">{{ d.fileName }}</span>
                  </span>
                  <StatusBadge :status="d.status" size="sm" />
                </button>
              </li>
            </ul>
            <p v-else class="mt-3 text-sm text-muted">Hujjatlar yuklanmagan.</p>
            <Button class="mt-3" size="sm" variant="secondary" block :icon="Upload" @click="docs.uploadOpen.value = true">Hujjat yuklash</Button>
          </section>

          <section v-if="candidate" class="card p-5">
            <h2 class="flex items-center gap-2 text-base font-semibold text-ink"><UserRoundSearch class="h-4 w-4 text-muted" /> Nomzodlik tarixi</h2>
            <dl class="mt-3 space-y-2 text-sm">
              <div class="flex justify-between gap-3"><dt class="text-muted">Manba</dt><dd class="font-medium text-ink">{{ candidate.source }}</dd></div>
              <div class="flex justify-between gap-3"><dt class="text-muted">Ariza sanasi</dt><dd class="tabular-nums text-ink">{{ formatDate(candidate.createdAt) }}</dd></div>
            </dl>
            <RouterLink :to="{ path: '/candidates', query: { id: candidate.id } }" class="mt-3 inline-block text-sm font-medium text-primary-600 hover:underline">Nomzod kartasini ochish</RouterLink>
          </section>
        </div>
      </div>

      <!-- Darslar -->
      <section v-else-if="tab === 'training'" class="card mt-4 p-5 sm:p-6">
        <template v-if="training">
          <div class="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center">
            <div class="flex-1">
              <h2 class="text-base font-semibold text-ink">7 kunlik o‘quv dasturi</h2>
              <p class="text-sm text-muted">Boshlangan: {{ formatDate(training.startDate) }}<template v-if="training.finishedAt"> · Yakunlangan: {{ formatDateTime(training.finishedAt) }}</template></p>
            </div>
            <StatusBadge class="self-start sm:self-auto" :status="state" />
          </div>
          <TrainingProgress class="mb-5" :done="progress.done" />
          <TrainingTimeline :training="training" :busy-day="busyDay" @complete="onComplete" @undo="(d) => undo(training, d)" />
          <div v-if="state === 'Yakunlandi'" class="mt-5 flex flex-col gap-3 rounded-xl bg-primary-50 p-4 sm:flex-row sm:items-center">
            <p class="flex-1 text-sm text-primary-800">Dastur yakunlandi, lekin test yuborilmagan.</p>
            <Button :icon="Send" :loading="assigning" @click="sendTest">Testga yuborish</Button>
          </div>
        </template>
        <EmptyState v-else :icon="GraduationCap" title="O‘quv dasturi boshlanmagan" description="Xodimni 7 kunlik dasturga qo‘shing — har kuni progress saqlanadi, oxirida test yuboriladi.">
          <Button :icon="Play" :loading="starting" @click="startTraining">Dasturni boshlash</Button>
        </EmptyState>
      </section>

      <!-- Testlar -->
      <section v-else-if="tab === 'tests'" class="card mt-4 overflow-hidden">
        <div class="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <h2 class="text-base font-semibold text-ink">Test natijalari</h2>
          <Button v-if="!hasPending && !hasPassed && employee.status !== 'Faol emas'" size="sm" variant="secondary" :icon="Send" :loading="assigning" @click="sendTest">Testga yuborish</Button>
        </div>
        <EmptyState v-if="!results.length" compact :icon="ClipboardCheck" title="Natijalar yo‘q" description="7 kunlik dars tugagach test avtomatik yuboriladi." />
        <ul v-else class="divide-y divide-line">
          <li v-for="r in results" :key="r.id" class="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="font-medium text-ink">{{ tests.testById(r.testId)?.title || 'O‘chirilgan test' }}</p>
                <StatusBadge :status="r.status" :label="RESULT_LABELS[r.status]" size="sm" />
              </div>
              <p class="mt-1 text-xs text-muted">
                Yuborilgan: {{ formatDateTime(r.assignedAt) }}
                <template v-if="r.completedAt"> · Topshirilgan: {{ formatDateTime(r.completedAt) }}</template>
                · Urinish: {{ r.attempts.length }}/{{ maxAttempts }}
              </p>
            </div>
            <div class="flex items-center gap-4">
              <p v-if="r.score !== null" class="text-right">
                <span :class="['text-lg font-semibold tabular-nums', r.status === 'O‘tdi' ? 'text-emerald-700' : 'text-red-700']">{{ r.score }}%</span>
                <span class="block text-xs text-muted">{{ r.correct }}/{{ r.total }} · kerak {{ r.passPercent }}%</span>
              </p>
              <Button v-if="r.status === 'Kutilmoqda'" size="sm" :icon="Play" @click="runnerId = r.id">Boshlash</Button>
              <template v-else>
                <Button v-if="canRetake(r)" size="sm" variant="ghost" :icon="RotateCcw" @click="runnerId = r.id">Qayta</Button>
                <Button size="sm" variant="secondary" :icon="Eye" @click="openResult(r)">Javoblar</Button>
              </template>
            </div>
          </li>
        </ul>
      </section>

      <!-- Hujjatlar -->
      <section v-else class="card mt-4 overflow-hidden">
        <div class="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <h2 class="text-base font-semibold text-ink">Hujjatlar</h2>
          <Button size="sm" :icon="Upload" @click="docs.uploadOpen.value = true">Yuklash</Button>
        </div>
        <EmptyState v-if="!employeeDocs.length" compact :icon="FileText" title="Hujjatlar yo‘q" description="Pasport, mehnat shartnomasi va boshqa hujjatlarni yuklang.">
          <Button :icon="Upload" @click="docs.uploadOpen.value = true">Hujjat yuklash</Button>
        </EmptyState>
        <DocumentTable v-else :rows="employeeDocs" hide-employee @view="(d) => (docs.detailId.value = d.id)" @download="docs.download" @delete="docs.askDelete" />
      </section>

      <EmployeeForm :open="formOpen" :employee="employee" :saving="saving" @close="formOpen = false" @submit="handleSubmit" />
      <TestRunner :open="!!runnerId" :result-id="runnerId" @close="runnerId = null" />
      <ResultDetails :open="!!detailsId" :result-id="detailsId" @close="detailsId = null" @start="(r) => { detailsId = null; runnerId = r.id }" />
      <DocumentDetails
        :open="!!selectedDoc"
        :document="selectedDoc"
        :busy="docs.busy.value"
        @close="docs.detailId.value = null"
        @approve="(c) => docs.review(selectedDoc, 'Tasdiqlangan', c)"
        @reject="(c) => docs.review(selectedDoc, 'Rad etilgan', c)"
        @download="docs.download"
        @delete="docs.askDelete"
      />
      <DocumentUpload :open="docs.uploadOpen.value" :employee-id="employee.id" @close="docs.uploadOpen.value = false" />
      <ConfirmDialog
        :open="!!docs.deleteTarget.value"
        title="Hujjatni o‘chirasizmi?"
        :message="docs.deleteTarget.value ? `“${docs.deleteTarget.value.fileName}” butunlay o‘chiriladi.` : ''"
        confirm-text="O‘chirish"
        :loading="docs.deleting.value"
        @confirm="docs.confirmDelete"
        @close="docs.deleteTarget.value = null"
      />
      <ConfirmDialog
        :open="deleteOpen"
        title="Xodimni o‘chirasizmi?"
        :message="`${employee.fullName} ro‘yxatdan butunlay o‘chiriladi (darslar progressi, test natijalari va hujjatlari bilan). Bu amalni qaytarib bo‘lmaydi.`"
        confirm-text="O‘chirish"
        :loading="deleting"
        @confirm="confirmDelete"
        @close="deleteOpen = false"
      />
    </template>
  </div>
</template>
