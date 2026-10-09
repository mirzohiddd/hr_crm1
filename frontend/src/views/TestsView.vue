<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle2, Download, ClipboardCheck, ClipboardList, Clock, Eye, Pencil, Percent, Play, Plus, RotateCcw, SearchX, Send, Trash2, UserRoundCheck, XCircle } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import Select from '@/components/ui/Select.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import Modal from '@/components/ui/Modal.vue'
import FormField from '@/components/ui/FormField.vue'
import TestRunner from '@/components/tests/TestRunner.vue'
import TestForm from '@/components/tests/TestForm.vue'
import { useTestsStore } from '@/stores/tests'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { useTrainingActions } from '@/composables/useTrainingActions'
import { formatDateTime } from '@/utils/date'
import { downloadCsv, nameParts, normalizeText, onlyDigits } from '@/utils/format'
import { employeeAge } from '@/utils/date'
import { RESULT_LABELS } from '@/constants'
import ResultDetails from '@/components/tests/ResultDetails.vue'
import LandingResults from '@/components/tests/LandingResults.vue'
import FinalResults from '@/components/tests/FinalResults.vue'
import { useFinalTestStore } from '@/stores/finalTest'
import { useLandingStore } from '@/stores/landing'

const route = useRoute()
const router = useRouter()
const store = useTestsStore()
const landing = useLandingStore()
const finalTest = useFinalTestStore()
const employees = useEmployeesStore()
const catalog = useCatalogStore()
const toast = useToast()
const { assigning, assignTest } = useTrainingActions()

const TAB_VALUES = ['results', 'final', 'landing', 'bank']
const tab = ref(TAB_VALUES.includes(route.query.tab) ? route.query.tab : 'results')
const tabs = computed(() => [
  { value: 'results', label: 'Xodimlar natijalari', count: store.results.length },
  { value: 'final', label: 'Yakuniy bilim testi', count: finalTest.stats.total },
  { value: 'landing', label: 'Nomzodlar testi', count: landing.items.length },
  { value: 'bank', label: 'Testlar bazasi', count: store.tests.length },
])
watch(tab, (t) => router.replace({ query: t === 'results' ? {} : { tab: t } }))

onMounted(async () => {
  landing.fetchAll({ force: true })
  finalTest.fetchAll()
  await Promise.all([store.fetchAll(), employees.fetchAll()])
  if (route.query.start) openRunner(Number(route.query.start))
})

const firstLoad = computed(() => !store.loaded && store.loading)
const maxAttempts = computed(() => store.settings?.maxAttempts ?? 3)

// ---------- Natijalar ----------
const search = ref('')
const status = ref('')
const testFilter = ref('')
const statusTabs = computed(() => [
  { value: '', label: 'Barchasi' },
  { value: 'Kutilmoqda', label: 'Kutilmoqda', count: store.stats.pending },
  { value: 'O‘tdi', label: 'Testdan o‘tdi', count: store.stats.passed },
  { value: 'O‘tmadi', label: 'Testdan o‘tmadi', count: store.stats.failed },
])

const rows = computed(() =>
  store.results
    .map((r) => {
      const employee = employees.findById(r.employeeId)
      return { ...r, employee, test: store.testById(r.testId), ...nameParts(employee), age: employeeAge(employee) }
    })
    .sort((a, b) => {
      // Kutilayotganlar yuqorida, keyin eng so‘nggilari
      if ((a.status === 'Kutilmoqda') !== (b.status === 'Kutilmoqda')) return a.status === 'Kutilmoqda' ? -1 : 1
      return (b.completedAt || b.assignedAt || '').localeCompare(a.completedAt || a.assignedAt || '')
    }),
)
const filtered = computed(() => {
  const q = normalizeText(search.value)
  return rows.value.filter(
    (r) =>
      (!status.value || r.status === status.value) &&
      (!testFilter.value || r.testId === testFilter.value) &&
      (!q || normalizeText(r.employee?.fullName).includes(q) || (onlyDigits(search.value).length >= 3 && onlyDigits(r.employee?.phone).includes(onlyDigits(search.value)))),
  )
})
const { page, paged, total, pageSize } = usePagination(filtered, 10, () => [search.value, status.value, testFilter.value])
const testOptions = computed(() => store.tests.map((t) => ({ value: t.id, label: t.title })))

function clearFilters() {
  search.value = ''
  status.value = ''
  testFilter.value = ''
}

const canRetake = (r) => r.status === 'O‘tmadi' && r.attempts.length < maxAttempts.value

// ---------- Batafsil natija ----------
const resultId = ref(null)
function openResult(r) {
  if (!r.attempts.length) return openRunner(r.id)
  resultId.value = r.id
}
function startFromDetails(r) {
  resultId.value = null
  openRunner(r.id)
}

/** Natijalarni Excel (CSV) ga yuklab olish */
function exportCsv() {
  downloadCsv(
    `test-natijalari-${new Date().toISOString().slice(0, 10)}.csv`,
    ['Ism', 'Familiya', 'Telefon', 'Yosh', 'Jinsi', 'Test', 'To‘g‘ri javoblar', 'Jami savollar', 'Foiz', 'Natija', 'Sana'],
    filtered.value.map((r) => [
      r.firstName, r.lastName, r.employee?.phone, r.age ?? '', r.employee?.gender, r.test?.title,
      r.correct ?? '', r.total ?? '', r.score !== null ? `${r.score}%` : '', RESULT_LABELS[r.status], formatDateTime(r.completedAt || r.assignedAt),
    ]),
  )
}

// ---------- Test topshirish ----------
const runnerId = ref(null)
function openRunner(id) {
  if (store.results.some((r) => r.id === id)) runnerId.value = id
}
function closeRunner() {
  runnerId.value = null
  if (route.query.start) router.replace({ query: { ...route.query, start: undefined } })
}

// ---------- Testga yuborish ----------
const assignOpen = ref(false)
const assignForm = ref({ employeeId: '', testId: '' })
const assignError = ref('')
const assignableEmployees = computed(() =>
  employees.items
    .filter((e) => e.status !== 'Faol emas')
    .filter((e) => !store.results.some((r) => r.employeeId === e.id && r.status === 'Kutilmoqda'))
    .sort((a, b) => a.fullName.localeCompare(b.fullName))
    .map((e) => ({ value: e.id, label: `${e.fullName} — ${catalog.positionName(e.positionId)}` })),
)
function openAssign() {
  assignForm.value = { employeeId: '', testId: '' }
  assignError.value = ''
  assignOpen.value = true
}
async function submitAssign() {
  if (!assignForm.value.employeeId) return (assignError.value = 'Xodimni tanlang')
  const res = await assignTest(Number(assignForm.value.employeeId), assignForm.value.testId ? Number(assignForm.value.testId) : null)
  if (res) {
    assignOpen.value = false
    tab.value = 'results'
    status.value = 'Kutilmoqda'
  }
}

// ---------- Testlar bazasi ----------
const formOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)

const resultCount = (testId) => store.results.filter((r) => r.testId === testId).length
const positionsLabel = (ids) => (ids?.length ? ids.map(catalog.positionName).join(', ') : 'Barcha lavozimlar')

function openCreate() {
  editing.value = null
  formOpen.value = true
}
function openEdit(test) {
  editing.value = test
  formOpen.value = true
}
async function handleSubmit(data) {
  saving.value = true
  try {
    if (editing.value) {
      await store.updateTest(editing.value.id, data)
      toast.success('Test saqlandi', data.title)
    } else {
      await store.createTest(data)
      tab.value = 'bank'
      toast.success('Test yaratildi', `${data.title} — ${data.questions.length} ta savol`)
    }
    formOpen.value = false
  } catch (e) {
    toast.error('Saqlab bo‘lmadi', e.message)
  } finally {
    saving.value = false
  }
}
function askDelete(test) {
  if (resultCount(test.id)) {
    toast.error('Testni o‘chirib bo‘lmaydi', 'Bu test bo‘yicha natijalar bor. O‘chirish o‘rniga nofaol qiling.')
    return
  }
  deleteTarget.value = test
}
async function confirmDelete() {
  deleting.value = true
  try {
    await store.removeTest(deleteTarget.value.id)
    toast.success('Test o‘chirildi', deleteTarget.value.title)
    deleteTarget.value = null
  } catch (e) {
    toast.error('O‘chirib bo‘lmadi', e.message)
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Testlar" subtitle="O‘quv dasturidan keyingi yakuniy testlar va natijalar">
      <template #actions>
        <Button variant="secondary" :icon="Send" @click="openAssign">Testga yuborish</Button>
        <Button :icon="Plus" @click="openCreate">Yangi test</Button>
      </template>
    </PageHeader>

    <div v-if="tab === 'final'" class="stagger grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Test topshirganlar" :value="finalTest.stats.total" :icon="UserRoundCheck" :loading="!finalTest.loaded && finalTest.loading" hint="Ochiq test: /test/yakuniy" />
      <StatCard label="Testdan o‘tdi" :value="finalTest.stats.passed" :icon="CheckCircle2" tone="green" :loading="!finalTest.loaded && finalTest.loading" hint="16–20 ball" />
      <StatCard label="Testdan o‘tmadi" :value="finalTest.stats.failed" :icon="XCircle" tone="red" :loading="!finalTest.loaded && finalTest.loading" hint="0–15 ball" />
      <StatCard label="O‘rtacha natija" :value="`${finalTest.stats.avg}%`" :icon="Percent" :loading="!finalTest.loaded && finalTest.loading" hint="Barcha topshirishlar bo‘yicha" />
    </div>
    <div v-else-if="tab === 'landing'" class="stagger grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Test topshirgan nomzodlar" :value="landing.stats.total" :icon="UserRoundCheck" :loading="!landing.loaded && landing.loading" :hint="landing.stats.unseen ? `${landing.stats.unseen} ta yangi natija` : 'Barchasi ko‘rib chiqilgan'" />
      <StatCard label="Testdan o‘tdi" :value="landing.stats.passed" :icon="CheckCircle2" tone="green" :loading="!landing.loaded && landing.loading" hint="80% va undan yuqori" />
      <StatCard label="Testdan yiqildi" :value="landing.stats.failed" :icon="XCircle" tone="red" :loading="!landing.loaded && landing.loading" hint="80% dan past" />
      <StatCard label="O‘rtacha natija" :value="`${landing.stats.avg}%`" :icon="Percent" :loading="!landing.loaded && landing.loading" hint="Barcha nomzodlar bo‘yicha" />
    </div>
    <div v-else class="stagger grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Topshirish kutilmoqda" :value="store.stats.pending" :icon="Clock" tone="amber" :loading="firstLoad" hint="Darsni tugatgan xodimlar" />
      <StatCard label="Testdan o‘tdi" :value="store.stats.passed" :icon="CheckCircle2" tone="green" :loading="firstLoad" :hint="`${store.settings?.passPercent ?? 80}% va undan yuqori`" />
      <StatCard label="Testdan o‘tmadi" :value="store.stats.failed" :icon="XCircle" tone="red" :loading="firstLoad" :hint="`${store.settings?.passPercent ?? 80}% dan past`" />
      <StatCard label="O‘tish ko‘rsatkichi" :value="`${store.stats.passRate}%`" :icon="Percent" :loading="firstLoad" hint="Topshirilgan testlar bo‘yicha" />
    </div>

    <div class="mt-6">
      <SegmentedControl v-model="tab" :options="tabs" aria-label="Bo‘lim" />
    </div>

    <!-- Yakuniy bilim testi (landing-2: /test/yakuniy) -->
    <FinalResults v-if="tab === 'final'" />
    <!-- Nomzodlar testi (landing: /test/sotuv) -->
    <LandingResults v-else-if="tab === 'landing'" />

    <ErrorState v-else-if="store.error" class="card mt-4" :message="store.error" @retry="store.fetchAll({ force: true })" />

    <!-- Natijalar -->
    <section v-else-if="tab === 'results'" class="card mt-4 overflow-hidden">
      <div class="flex flex-col gap-3 border-b border-line p-4 xl:flex-row xl:items-center">
        <SegmentedControl v-model="status" :options="statusTabs" aria-label="Natija holati" />
        <div class="grid flex-1 gap-3 sm:grid-cols-[minmax(0,1fr)_200px_auto] xl:ml-auto xl:max-w-2xl">
          <SearchInput v-model="search" placeholder="Ism yoki telefon..." label="Natijalardan qidirish" />
          <Select v-model="testFilter" :options="testOptions" placeholder="Barcha testlar" aria-label="Test bo‘yicha filtr" />
          <Button variant="secondary" :icon="Download" :disabled="!filtered.length" @click="exportCsv">Excel</Button>
        </div>
      </div>

      <LoadingState v-if="firstLoad" :rows="6" />
      <EmptyState v-else-if="!store.results.length" :icon="ClipboardList" title="Hali natijalar yo‘q" description="7 kunlik darsni tugatgan xodimlar bu yerga avtomatik tushadi.">
        <Button variant="secondary" :icon="Send" @click="openAssign">Testga yuborish</Button>
      </EmptyState>
      <EmptyState v-else-if="!filtered.length" :icon="SearchX" title="Natija topilmadi" description="Filtrlarni o‘zgartirib ko‘ring.">
        <Button variant="secondary" @click="clearFilters">Filtrlarni tozalash</Button>
      </EmptyState>
      <template v-else>
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-full">
            <thead class="border-b border-line bg-slate-50/60">
              <tr>
                <th class="table-th">Ism</th>
                <th class="table-th">Familiya</th>
                <th class="table-th">Telefon</th>
                <th class="table-th text-center">Yosh</th>
                <th class="table-th">Jinsi</th>
                <th class="table-th text-center">To‘g‘ri</th>
                <th class="table-th text-center">Jami</th>
                <th class="table-th">Foiz</th>
                <th class="table-th">Natija</th>
                <th class="table-th">Sana</th>
                <th class="table-th text-right" />
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr
                v-for="r in paged"
                :key="r.id"
                class="group cursor-pointer transition-colors duration-150 hover:bg-primary-50/40"
                tabindex="0"
                :title="r.test?.title"
                @click="openResult(r)"
                @keydown.enter="openResult(r)"
              >
                <td class="table-td">
                  <div class="flex items-center gap-3">
                    <Avatar :name="r.employee?.fullName || '?'" :src="r.employee?.photo" size="sm" />
                    <span class="font-medium text-ink group-hover:text-primary-700">{{ r.firstName || '—' }}</span>
                  </div>
                </td>
                <td class="table-td font-medium text-ink">{{ r.lastName || '—' }}</td>
                <td class="table-td tabular-nums text-slate-600">{{ r.employee?.phone || '—' }}</td>
                <td class="table-td text-center tabular-nums text-slate-600">{{ r.age ?? '—' }}</td>
                <td class="table-td text-slate-600">{{ r.employee?.gender || '—' }}</td>
                <td class="table-td text-center font-semibold tabular-nums text-emerald-600">{{ r.correct ?? '—' }}</td>
                <td class="table-td text-center tabular-nums text-slate-600">{{ r.total ?? '—' }}</td>
                <td class="table-td">
                  <div v-if="r.score !== null" class="flex items-center gap-2">
                    <div class="hidden h-1.5 w-12 overflow-hidden rounded-full bg-slate-100 xl:block">
                      <div :class="['h-full rounded-full transition-[width] duration-500', r.status === 'O‘tdi' ? 'bg-emerald-500' : 'bg-red-500']" :style="{ width: `${r.score}%` }" />
                    </div>
                    <span class="font-semibold tabular-nums">{{ r.score }}%</span>
                  </div>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="table-td"><StatusBadge :status="r.status" :label="RESULT_LABELS[r.status]" /></td>
                <td class="table-td tabular-nums text-slate-600">{{ formatDateTime(r.completedAt || r.assignedAt) }}</td>
                <td class="table-td text-right" @click.stop @keydown.enter.stop>
                  <button
                    v-if="r.status === 'Kutilmoqda'"
                    class="icon-btn h-8 w-8 bg-primary-600 text-white hover:bg-primary-700 hover:text-white"
                    title="Testni boshlash"
                    aria-label="Testni boshlash"
                    :disabled="!r.test"
                    @click="openRunner(r.id)"
                  >
                    <Play class="h-4 w-4" />
                  </button>
                  <button v-else class="icon-btn h-8 w-8 border border-line bg-white hover:border-primary-200 hover:text-primary-600" title="Javoblarni ko‘rish" aria-label="Javoblarni ko‘rish" @click="openResult(r)">
                    <Eye class="h-4 w-4" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ul class="divide-y divide-line md:hidden">
          <li v-for="r in paged" :key="r.id">
            <button class="flex w-full items-start gap-3 px-4 py-3.5 text-left transition-colors active:bg-slate-50" @click="openResult(r)">
              <Avatar :name="r.employee?.fullName || '?'" size="md" />
              <span class="min-w-0 flex-1">
                <span class="flex items-start justify-between gap-2">
                  <span class="truncate font-medium text-ink">{{ r.firstName }} {{ r.lastName }}</span>
                  <StatusBadge :status="r.status" :label="RESULT_LABELS[r.status]" size="sm" />
                </span>
                <span class="mt-0.5 block truncate text-[13px] text-slate-600">{{ r.employee?.phone }} · {{ [r.age ? `${r.age} yosh` : '', r.employee?.gender].filter(Boolean).join(', ') }}</span>
                <span class="mt-1 flex flex-wrap gap-x-4 text-xs tabular-nums text-muted">
                  <span v-if="r.score !== null"><b class="text-ink">{{ r.correct }}/{{ r.total }}</b> · {{ r.score }}%</span>
                  <span v-else class="font-medium text-primary-600">Testni boshlash →</span>
                  <span>{{ formatDateTime(r.completedAt || r.assignedAt) }}</span>
                </span>
              </span>
            </button>
          </li>
        </ul>
        <Pagination v-model:page="page" :total="total" :page-size="pageSize" />
      </template>
    </section>

    <!-- Testlar bazasi -->
    <section v-else class="mt-4">
      <LoadingState v-if="firstLoad" variant="cards" :rows="3" />
      <div v-else-if="!store.tests.length" class="card">
        <EmptyState :icon="ClipboardCheck" title="Hali testlar yo‘q" description="Birinchi testni yarating: savollar, variantlar va o‘tish foizini belgilang.">
          <Button :icon="Plus" @click="openCreate">Yangi test</Button>
        </EmptyState>
      </div>
      <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="t in store.tests" :key="t.id" class="card card-hover flex flex-col p-5">
          <div class="flex items-start justify-between gap-3">
            <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600"><ClipboardCheck class="h-5 w-5" /></span>
            <StatusBadge :status="t.active ? 'Faol' : 'Faol emas'" size="sm" />
          </div>
          <h3 class="mt-4 font-semibold text-ink">{{ t.title }}</h3>
          <p v-if="t.description" class="mt-1 line-clamp-2 text-sm text-muted">{{ t.description }}</p>
          <dl class="mt-4 grid grid-cols-3 gap-2 text-center">
            <div class="rounded-lg bg-slate-50 py-2">
              <dt class="text-[11px] text-muted">Savol</dt>
              <dd class="font-semibold tabular-nums text-ink">{{ t.questions.length }}</dd>
            </div>
            <div class="rounded-lg bg-slate-50 py-2">
              <dt class="text-[11px] text-muted">O‘tish</dt>
              <dd class="font-semibold tabular-nums text-ink">{{ store.settings?.passPercent ?? 80 }}%</dd>
            </div>
            <div class="rounded-lg bg-slate-50 py-2">
              <dt class="text-[11px] text-muted">Natija</dt>
              <dd class="font-semibold tabular-nums text-ink">{{ resultCount(t.id) }}</dd>
            </div>
          </dl>
          <p class="mt-3 text-xs text-muted"><span class="font-medium text-slate-600">Lavozim:</span> {{ positionsLabel(t.positionIds) }}</p>
          <div class="mt-auto flex gap-2 pt-4">
            <Button class="flex-1" variant="secondary" size="sm" :icon="Pencil" @click="openEdit(t)">Tahrirlash</Button>
            <button class="icon-btn h-8 w-8 border border-line hover:border-red-200 hover:bg-red-50 hover:text-red-600" :aria-label="`${t.title}: o‘chirish`" title="O‘chirish" @click="askDelete(t)">
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
        </article>
      </div>
    </section>

    <TestRunner :open="!!runnerId" :result-id="runnerId" @close="closeRunner" />
    <ResultDetails :open="!!resultId" :result-id="resultId" @close="resultId = null" @start="startFromDetails" />
    <TestForm
      :open="formOpen"
      :test="editing"
      :saving="saving"
      :pass-percent="store.settings?.passPercent ?? 80"
      @close="formOpen = false"
      @submit="handleSubmit"
    />

    <Modal :open="assignOpen" size="md" title="Testga yuborish" subtitle="Xodimga testni qo‘lda biriktirish" :persistent="assigning" @close="!assigning && (assignOpen = false)">
      <form id="assign-form" class="space-y-4" novalidate @submit.prevent="submitAssign">
        <FormField label="Xodim" for="as-emp" :error="assignError" required>
          <Select id="as-emp" v-model="assignForm.employeeId" :options="assignableEmployees" placeholder="Xodimni tanlang" :error="assignError" @update:model-value="assignError = ''" />
        </FormField>
        <FormField label="Test" for="as-test" hint="Tanlanmasa — xodim lavozimiga mos test avtomatik tanlanadi">
          <Select id="as-test" v-model="assignForm.testId" :options="testOptions" placeholder="Avtomatik (lavozimga mos)" />
        </FormField>
      </form>
      <template #footer>
        <Button variant="secondary" :disabled="assigning" @click="assignOpen = false">Bekor qilish</Button>
        <Button type="submit" form="assign-form" :icon="Send" :loading="assigning">Yuborish</Button>
      </template>
    </Modal>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Testni o‘chirasizmi?"
      :message="deleteTarget ? `“${deleteTarget.title}” testi va uning ${deleteTarget.questions.length} ta savoli o‘chiriladi.` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </div>
</template>
