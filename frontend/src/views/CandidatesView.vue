<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CalendarClock, FileSpreadsheet, Kanban, List, Phone, PhoneMissed, Plus, SearchX, UserRoundSearch } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import Select from '@/components/ui/Select.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import CandidateForm from '@/components/candidates/CandidateForm.vue'
import CandidateDetails from '@/components/candidates/CandidateDetails.vue'
import HireDialog from '@/components/candidates/HireDialog.vue'
import StageDialog from '@/components/candidates/StageDialog.vue'
import ImportDialog from '@/components/candidates/ImportDialog.vue'
import SourceIcon from '@/components/candidates/SourceIcon.vue'
import { useCandidatesStore } from '@/stores/candidates'
import { useCatalogStore } from '@/stores/catalog'
import { useEmployeesStore } from '@/stores/employees'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { CANDIDATE_SOURCES, CANDIDATE_STAGES } from '@/constants'
import { diffDays, formatDate, formatDateTime, todayISO } from '@/utils/date'
import { normalizeText, onlyDigits } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useCandidatesStore()
const catalog = useCatalogStore()
const employees = useEmployeesStore()
const toast = useToast()
const today = todayISO()

onMounted(async () => {
  await Promise.all([store.fetchAll(), catalog.fetchAll(), employees.fetchAll()])
  if (route.query.id) detailId.value = Number(route.query.id)
})
watch(
  () => route.query.id,
  (id) => {
    if (id) detailId.value = Number(id)
  },
)

// ---------- Ko‘rinish va filtrlar ----------
const VIEW_KEY = 'hr-crm:candidates-view'
let savedView = 'board'
try {
  savedView = localStorage.getItem(VIEW_KEY) || 'board'
} catch {
  /* e'tiborsiz */
}
const view = ref(savedView)
watch(view, (v) => {
  try {
    localStorage.setItem(VIEW_KEY, v)
  } catch {
    /* e'tiborsiz */
  }
})

const search = ref('')
const position = ref('')
const source = ref('')
const stage = ref('')

const filtered = computed(() => {
  const q = normalizeText(search.value)
  const digits = onlyDigits(search.value)
  return store.items
    .filter(
      (c) =>
        (!position.value || c.positionId === position.value) &&
        (!source.value || c.source === source.value) &&
        (!q || normalizeText(c.fullName).includes(q) || (digits.length >= 3 && onlyDigits(c.phone).includes(digits))),
    )
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
})
const listRows = computed(() => filtered.value.filter((c) => !stage.value || c.status === stage.value))
const { page, paged, total, pageSize } = usePagination(listRows, 12, () => [search.value, position.value, source.value, stage.value])

const columns = computed(() =>
  CANDIDATE_STAGES.map((s) => {
    let items = filtered.value.filter((c) => c.status === s.value)
    if (s.value === 'Suhbat') items = [...items].sort((a, b) => (a.interviewAt || '').localeCompare(b.interviewAt || ''))
    return { ...s, items }
  }),
)

const hasFilters = computed(() => !!(search.value || position.value || source.value || stage.value))
function clearFilters() {
  search.value = ''
  position.value = ''
  source.value = ''
  stage.value = ''
}
function pickStage(value) {
  stage.value = stage.value === value ? '' : value
  view.value = 'list'
}

const ago = (iso) => {
  const d = diffDays(iso.slice(0, 10), today)
  return d <= 0 ? 'bugun' : d === 1 ? 'kecha' : `${d} kun oldin`
}
const COLUMN_TONES = {
  blue: 'bg-primary-600',
  sky: 'bg-sky-500',
  orange: 'bg-orange-500',
  amber: 'bg-amber-500',
  green: 'bg-emerald-500',
  red: 'bg-red-500',
}

// ---------- Detail va amallar ----------
const detailId = ref(null)
const selected = computed(() => store.items.find((c) => c.id === detailId.value) || null)
const busy = ref(false)

function openDetail(c) {
  detailId.value = c.id
}
function closeDetail() {
  detailId.value = null
  if (route.query.id) router.replace({ query: {} })
}

async function move(c, status, extra = {}) {
  busy.value = true
  try {
    await store.setStatus(c.id, status, extra)
    toast.success(`${c.fullName}: ${status}`, status === 'Suhbat' && extra.interviewAt ? `Suhbat: ${formatDateTime(extra.interviewAt)}` : '')
    return true
  } catch (e) {
    toast.error('Holatni o‘zgartirib bo‘lmadi', e.message)
    return false
  } finally {
    busy.value = false
  }
}

// Suhbat / rad etish
const stageDialog = ref({ open: false, mode: 'interview', candidate: null })
const openStage = (mode, candidate) => (stageDialog.value = { open: true, mode, candidate })
async function confirmStage(extra) {
  const { mode, candidate } = stageDialog.value
  const ok = await move(candidate, mode === 'reject' ? 'Rad etildi' : 'Suhbat', extra)
  if (ok) stageDialog.value.open = false
}

// Ishga qabul qilish
const hireTarget = ref(null)
const hiring = ref(false)
async function confirmHire(payload) {
  const c = hireTarget.value
  hiring.value = true
  try {
    const res = await store.hire(c.id, payload)
    hireTarget.value = null
    toast.success('Ishga qabul qilindi', res.training ? `${c.fullName} xodimlarga qo‘shildi va 7 kunlik darsni boshladi` : `${c.fullName} xodimlarga qo‘shildi`)
  } catch (e) {
    toast.error('Ishga qabul qilib bo‘lmadi', e.message)
  } finally {
    hiring.value = false
  }
}

function openEmployee(e) {
  router.push(`/employees/${e.id}`)
}

// Kanban: sudrab o‘tkazish
const dragId = ref(null)
const dropTarget = ref(null)
function onDragStart(e, c) {
  dragId.value = c.id
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(c.id))
}
function onDragEnd() {
  dragId.value = null
  dropTarget.value = null
}
function onDrop(status) {
  const c = store.findById(dragId.value)
  onDragEnd()
  if (!c || c.status === status) return
  if (c.status === 'Ishga qabul qilindi') return toast.info('Nomzod allaqachon ishga olingan', 'Xodim profilidan boshqaring')
  if (status === 'Ishga qabul qilindi') hireTarget.value = c
  else if (status === 'Rad etildi') openStage('reject', c)
  else if (status === 'Suhbat') openStage('interview', c)
  else move(c, status)
}

// Yaratish / tahrirlash / o‘chirish
const formOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
function openCreate() {
  editing.value = null
  formOpen.value = true
}
function openEdit(c) {
  editing.value = c
  formOpen.value = true
}
async function handleSubmit(data) {
  saving.value = true
  try {
    if (editing.value) {
      await store.update(editing.value.id, data)
      toast.success('Nomzod ma’lumotlari saqlandi', data.fullName)
    } else {
      const created = await store.create(data)
      clearFilters()
      toast.success('Nomzod qo‘shildi', `${created.fullName} — “Yangi” bosqichida`)
    }
    formOpen.value = false
  } catch (e) {
    toast.error('Saqlab bo‘lmadi', e.message)
  } finally {
    saving.value = false
  }
}

const deleteTarget = ref(null)
const deleting = ref(false)
async function confirmDelete() {
  const c = deleteTarget.value
  deleting.value = true
  try {
    await store.remove(c.id)
    if (detailId.value === c.id) closeDetail()
    toast.success('Nomzod o‘chirildi', c.fullName)
    deleteTarget.value = null
  } catch (e) {
    toast.error('O‘chirib bo‘lmadi', e.message)
  } finally {
    deleting.value = false
  }
}

const importOpen = ref(false)
const firstLoad = computed(() => store.loading && !store.loaded)
</script>

<template>
  <div>
    <PageHeader title="Nomzodlar">
      <template #subtitle>
        <template v-if="store.loaded">
          {{ store.items.length }} ta nomzod · bugun {{ store.newToday }} ta yangi ariza<template v-if="store.interviewsToday.length"> · {{ store.interviewsToday.length }} ta suhbat</template>
        </template>
        <template v-else>Instagram va Google Sheets orqali kelgan arizalar</template>
      </template>
      <template #actions>
        <Button variant="secondary" :icon="FileSpreadsheet" @click="importOpen = true">Import</Button>
        <Button :icon="Plus" @click="openCreate">Nomzod qo‘shish</Button>
      </template>
    </PageHeader>

    <!-- Voronka xulosasi -->
    <div class="-mx-4 flex gap-3 overflow-x-auto px-4 pb-1 sm:mx-0 sm:grid sm:grid-cols-3 sm:overflow-visible sm:px-0 sm:pb-0 xl:grid-cols-6">
      <button
        v-for="s in CANDIDATE_STAGES"
        :key="s.value"
        :class="[
          'card card-hover flex min-w-[132px] shrink-0 items-center gap-3 p-3.5 text-left',
          stage === s.value && view === 'list' ? 'border-primary-500 ring-1 ring-primary-500' : '',
        ]"
        :aria-pressed="stage === s.value && view === 'list'"
        @click="pickStage(s.value)"
      >
        <span :class="['h-9 w-1.5 shrink-0 rounded-full', COLUMN_TONES[s.tone]]" />
        <span class="min-w-0">
          <span class="block truncate text-xs text-muted">{{ s.label }}</span>
          <span class="mt-0.5 block text-xl font-semibold tabular-nums text-ink">
            <span v-if="firstLoad" class="inline-block h-5 w-8 animate-pulse rounded bg-slate-100 align-middle" />
            <template v-else>{{ store.counts[s.value] || 0 }}</template>
          </span>
        </span>
      </button>
    </div>

    <!-- Filtrlar -->
    <div class="mt-5 flex flex-col gap-3 lg:flex-row lg:items-center">
      <div class="inline-flex shrink-0 rounded-lg bg-slate-100 p-1" role="tablist" aria-label="Ko‘rinish">
        <button
          v-for="v in [{ value: 'board', label: 'Voronka', icon: Kanban }, { value: 'list', label: 'Ro‘yxat', icon: List }]"
          :key="v.value"
          role="tab"
          :aria-selected="view === v.value"
          :class="['inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-[13px] font-medium transition-colors', view === v.value ? 'bg-white text-ink shadow-sm ring-1 ring-line' : 'text-muted hover:text-ink']"
          @click="view = v.value"
        >
          <component :is="v.icon" class="h-4 w-4" />{{ v.label }}
        </button>
      </div>
      <div class="grid flex-1 gap-3 sm:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_minmax(0,1fr)] lg:ml-auto lg:max-w-3xl">
        <SearchInput v-model="search" placeholder="Ism yoki telefon..." label="Nomzod qidirish" />
        <Select v-model="position" :options="catalog.positionOptions" placeholder="Barcha lavozimlar" aria-label="Lavozim bo‘yicha filtr" />
        <Select v-model="source" :options="CANDIDATE_SOURCES" placeholder="Barcha manbalar" aria-label="Manba bo‘yicha filtr" />
      </div>
    </div>

    <ErrorState v-if="store.error" class="card mt-4" :message="store.error" @retry="store.fetchAll({ force: true })" />
    <LoadingState v-else-if="firstLoad" class="mt-4" variant="cards" :rows="3" />
    <div v-else-if="!store.items.length" class="card mt-4">
      <EmptyState :icon="UserRoundSearch" title="Hali nomzodlar yo‘q" description="Nomzodni qo‘lda qo‘shing yoki Google Sheets’dan import qiling.">
        <Button variant="secondary" :icon="FileSpreadsheet" @click="importOpen = true">Import</Button>
        <Button :icon="Plus" @click="openCreate">Nomzod qo‘shish</Button>
      </EmptyState>
    </div>

    <!-- Voronka (kanban) -->
    <div v-else-if="view === 'board'" class="-mx-4 mt-4 overflow-x-auto px-4 pb-3 sm:-mx-6 sm:px-6 lg:mx-0 lg:px-0">
      <div class="flex snap-x snap-mandatory gap-3 xl:gap-4">
        <section
          v-for="col in columns"
          :key="col.value"
          :class="[
            'flex w-[82vw] max-w-[300px] shrink-0 snap-start flex-col rounded-2xl border bg-slate-50/70 transition-colors duration-200 sm:w-[260px] lg:w-auto lg:min-w-[200px] lg:max-w-none lg:flex-1',
            dropTarget === col.value ? 'border-primary-400 bg-primary-50/60' : 'border-line',
          ]"
          :aria-label="col.label"
          @dragover.prevent="dropTarget = col.value"
          @dragleave="dropTarget === col.value && (dropTarget = null)"
          @drop.prevent="onDrop(col.value)"
        >
          <header class="flex items-center gap-2 px-3.5 py-3">
            <span :class="['h-2 w-2 rounded-full', COLUMN_TONES[col.tone]]" />
            <h2 class="text-sm font-semibold text-ink">{{ col.label }}</h2>
            <span class="ml-auto rounded-full bg-white px-2 text-xs font-medium tabular-nums text-muted ring-1 ring-line">{{ col.items.length }}</span>
          </header>
          <div class="flex max-h-[calc(100vh-330px)] min-h-[160px] flex-1 flex-col gap-2 overflow-y-auto px-2.5 pb-3">
            <article
              v-for="c in col.items"
              :key="c.id"
              :draggable="c.status !== 'Ishga qabul qilindi'"
              :class="[
                'group cursor-pointer rounded-xl border border-line bg-white p-3 shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-[0_8px_20px_-10px_rgba(37,99,235,0.35)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/15 active:cursor-grabbing',
                dragId === c.id && 'opacity-50',
              ]"
              tabindex="0"
              @click="openDetail(c)"
              @keydown.enter="openDetail(c)"
              @dragstart="onDragStart($event, c)"
              @dragend="onDragEnd"
            >
              <div class="flex items-start gap-2.5">
                <Avatar :name="c.fullName" size="sm" />
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-ink">{{ c.fullName }}</p>
                  <p class="truncate text-xs text-muted">{{ catalog.positionName(c.positionId) }}</p>
                </div>
              </div>
              <div v-if="c.status === 'Suhbat' && c.interviewAt" :class="['mt-2.5 flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium', c.interviewAt.slice(0, 10) === today ? 'bg-amber-50 text-amber-700' : 'bg-slate-50 text-slate-600']">
                <CalendarClock class="h-3.5 w-3.5" />{{ c.interviewAt.slice(0, 10) === today ? `Bugun, ${c.interviewAt.slice(11, 16)}` : formatDateTime(c.interviewAt) }}
              </div>
              <p v-if="c.status === 'Rad etildi' && c.rejectReason" class="mt-2 truncate text-xs text-red-600">{{ c.rejectReason }}</p>
              <p v-if="c.status === 'Bog‘lanilmadi'" class="mt-2 inline-flex items-center gap-1 rounded-md bg-orange-50 px-2 py-0.5 text-xs font-medium text-orange-700">
                <PhoneMissed class="h-3.5 w-3.5" />{{ c.contactAttempts || 1 }} marta urinildi
              </p>
              <div class="mt-2.5 flex items-center gap-3 text-xs text-muted">
                <span class="inline-flex min-w-0 items-center gap-1"><SourceIcon :source="c.source" /><span class="truncate">{{ c.source }}</span></span>
                <span class="ml-auto shrink-0 whitespace-nowrap">{{ ago(c.createdAt) }}</span>
              </div>
            </article>
            <p v-if="!col.items.length" class="grid flex-1 place-items-center rounded-lg border border-dashed border-line px-3 py-6 text-center text-xs text-slate-400">
              {{ hasFilters ? 'Mos nomzod yo‘q' : 'Bo‘sh' }}
            </p>
          </div>
        </section>
      </div>
      <p class="mt-2 hidden text-xs text-muted lg:block">Kartani boshqa ustunga sudrab o‘tkazish orqali bosqichni o‘zgartiring.</p>
    </div>

    <!-- Ro‘yxat -->
    <section v-else class="card mt-4 overflow-hidden">
      <div v-if="stage" class="flex items-center gap-2 border-b border-line bg-primary-50/50 px-4 py-2.5 text-sm">
        <span class="text-muted">Bosqich:</span>
        <StatusBadge :status="stage" />
        <button class="ml-1 text-xs font-medium text-primary-600 hover:underline" @click="stage = ''">Barchasi</button>
      </div>
      <EmptyState v-if="!listRows.length" :icon="SearchX" title="Nomzod topilmadi" description="Qidiruv yoki filtrlarni o‘zgartirib ko‘ring.">
        <Button variant="secondary" @click="clearFilters">Filtrlarni tozalash</Button>
      </EmptyState>
      <template v-else>
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-full">
            <thead class="border-b border-line bg-slate-50/60">
              <tr>
                <th class="table-th">Nomzod</th>
                <th class="table-th">Telefon</th>
                <th class="table-th">Lavozim</th>
                <th class="table-th">Manba</th>
                <th class="table-th">Bosqich</th>
                <th class="table-th">Ariza sanasi</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr v-for="c in paged" :key="c.id" class="cursor-pointer transition-colors hover:bg-slate-50/80" tabindex="0" @click="openDetail(c)" @keydown.enter="openDetail(c)">
                <td class="table-td">
                  <div class="flex items-center gap-3">
                    <Avatar :name="c.fullName" size="sm" />
                    <div>
                      <p class="font-medium text-ink">{{ c.fullName }}</p>
                      <p v-if="c.city || c.age" class="text-xs text-muted">{{ [c.city, c.age ? `${c.age} yosh` : ''].filter(Boolean).join(', ') }}</p>
                    </div>
                  </div>
                </td>
                <td class="table-td tabular-nums text-slate-600">{{ c.phone }}</td>
                <td class="table-td">{{ catalog.positionName(c.positionId) }}</td>
                <td class="table-td"><span class="inline-flex items-center gap-1.5 text-slate-600"><SourceIcon :source="c.source" />{{ c.source }}</span></td>
                <td class="table-td">
                  <StatusBadge :status="c.status" />
                  <span v-if="c.status === 'Suhbat' && c.interviewAt" class="mt-1 block text-xs text-muted">{{ formatDateTime(c.interviewAt) }}</span>
                </td>
                <td class="table-td tabular-nums text-slate-600">{{ formatDate(c.createdAt) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <ul class="divide-y divide-line md:hidden">
          <li v-for="c in paged" :key="c.id">
            <button class="flex w-full items-start gap-3 px-4 py-3.5 text-left active:bg-slate-50" @click="openDetail(c)">
              <Avatar :name="c.fullName" size="md" />
              <span class="min-w-0 flex-1">
                <span class="flex items-start justify-between gap-2">
                  <span class="truncate font-medium text-ink">{{ c.fullName }}</span>
                  <StatusBadge :status="c.status" size="sm" />
                </span>
                <span class="mt-0.5 block truncate text-[13px] text-slate-600">{{ catalog.positionName(c.positionId) }}</span>
                <span class="mt-1 flex flex-wrap items-center gap-x-4 text-xs text-muted">
                  <span class="inline-flex items-center gap-1 tabular-nums"><Phone class="h-3 w-3" />{{ c.phone }}</span>
                  <span class="inline-flex items-center gap-1"><SourceIcon :source="c.source" />{{ ago(c.createdAt) }}</span>
                </span>
              </span>
            </button>
          </li>
        </ul>
        <Pagination v-model:page="page" :total="total" :page-size="pageSize" />
      </template>
    </section>

    <CandidateDetails
      :open="!!selected"
      :candidate="selected"
      :busy="busy"
      @close="closeDetail"
      @edit="openEdit"
      @delete="(c) => (deleteTarget = c)"
      @contacted="(c) => move(c, 'Bog‘lanildi')"
      @not-reached="(c) => move(c, 'Bog‘lanilmadi')"
      @interview="(c) => openStage('interview', c)"
      @reject="(c) => openStage('reject', c)"
      @reopen="(c) => move(c, 'Yangi')"
      @hire="(c) => (hireTarget = c)"
      @open-employee="openEmployee"
    />
    <CandidateForm :open="formOpen" :candidate="editing" :saving="saving" @close="formOpen = false" @submit="handleSubmit" />
    <StageDialog :open="stageDialog.open" :mode="stageDialog.mode" :candidate="stageDialog.candidate" :saving="busy" @close="stageDialog.open = false" @confirm="confirmStage" />
    <HireDialog :open="!!hireTarget" :candidate="hireTarget" :saving="hiring" @close="hireTarget = null" @confirm="confirmHire" />
    <ImportDialog :open="importOpen" @close="importOpen = false" />
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Nomzodni o‘chirasizmi?"
      :message="deleteTarget ? `${deleteTarget.fullName} nomzodlar ro‘yxatidan o‘chiriladi.${deleteTarget.employeeId ? ' Xodim yozuvi saqlanib qoladi.' : ''}` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </div>
</template>
