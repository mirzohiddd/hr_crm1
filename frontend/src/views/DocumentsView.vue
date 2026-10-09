<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle2, ChevronRight, Clock, FileText, FolderOpen, SearchX, Upload, Users, X, XCircle } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import Button from '@/components/ui/Button.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import Select from '@/components/ui/Select.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import DocumentTable from '@/components/documents/DocumentTable.vue'
import DocumentDetails from '@/components/documents/DocumentDetails.vue'
import DocumentUpload from '@/components/documents/DocumentUpload.vue'
import EmployeeDocsPanel from '@/components/documents/EmployeeDocsPanel.vue'
import Avatar from '@/components/ui/Avatar.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useDocumentsStore } from '@/stores/documents'
import { useEmployeesStore } from '@/stores/employees'
import { usePagination } from '@/composables/usePagination'
import { useDocumentActions } from '@/composables/useDocumentActions'
import { DOCUMENT_TYPES } from '@/constants'
import { normalizeText, percent } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useDocumentsStore()
const employees = useEmployeesStore()
const catalog = useCatalogStore()
const { detailId, busy, deleteTarget, deleting, uploadOpen, download, askDelete, confirmDelete, review } = useDocumentActions()

// ---------- Ko‘rinish: xodimlar bo‘yicha (standart) yoki barcha hujjatlar ----------
const mode = ref(route.query.view === 'all' ? 'all' : 'employees')
const modes = computed(() => [
  { value: 'employees', label: 'Xodimlar bo‘yicha', count: employees.items.length },
  { value: 'all', label: 'Barcha hujjatlar', count: store.items.length },
])
function setMode(m) {
  mode.value = m
  router.replace({ query: m === 'all' ? { view: 'all' } : employeeId.value ? { employee: employeeId.value } : {} })
}

// Xodimlar ro‘yxati (chap panel)
const empSearch = ref('')
const empDept = ref('')
const docCount = (id) => store.items.filter((d) => d.employeeId === id).length
const pendingCount = (id) => store.items.filter((d) => d.employeeId === id && d.status === 'Kutilmoqda').length
const employeeList = computed(() => {
  const q = normalizeText(empSearch.value)
  return [...employees.items]
    .filter((e) => (!empDept.value || e.departmentId === empDept.value) && (!q || normalizeText(e.fullName).includes(q) || String(e.phone || '').includes(empSearch.value.trim())))
    .sort((a, b) => (a.status === 'Faol emas') - (b.status === 'Faol emas') || a.fullName.localeCompare(b.fullName))
})
const selectedEmployee = computed(() => (employeeId.value ? employees.findById(employeeId.value) : null))
function selectEmployee(e) {
  router.replace({ query: { employee: e.id } })
}
function backToList() {
  router.replace({ query: {} })
}

onMounted(async () => {
  await Promise.all([store.fetchAll(), employees.fetchAll()])
  // Katta ekranda o‘ng panel bo‘sh turmasligi uchun birinchi xodim avtomatik tanlanadi
  if (mode.value === 'employees' && !employeeId.value && window.innerWidth >= 1024 && employeeList.value.length) {
    selectEmployee(employeeList.value[0])
  }
})

// ---------- Filtrlar ----------
const search = ref('')
const type = ref('')
const status = ref('')
const employeeId = computed(() => (route.query.employee ? Number(route.query.employee) : null))
const employeeName = computed(() => (employeeId.value ? employees.findById(employeeId.value)?.fullName || 'Tanlangan xodim' : ''))

const statusTabs = computed(() => [
  { value: '', label: 'Barchasi' },
  { value: 'Kutilmoqda', label: 'Kutilmoqda', count: store.stats.pending },
  { value: 'Tasdiqlangan', label: 'Tasdiqlangan' },
  { value: 'Rad etilgan', label: 'Rad etilgan' },
])

const nameOf = (d) => employees.findById(d.employeeId)?.fullName || d.employeeName || ''

const filtered = computed(() => {
  const q = normalizeText(search.value)
  return store.items.filter(
    (d) =>
      (!employeeId.value || d.employeeId === employeeId.value) &&
      (!type.value || d.type === type.value) &&
      (!status.value || d.status === status.value) &&
      (!q || normalizeText(nameOf(d)).includes(q) || normalizeText(d.fileName).includes(q)),
  )
})

const { page, paged, total, pageSize } = usePagination(filtered, 10, () => [search.value, type.value, status.value, employeeId.value])

function clearEmployee() {
  router.replace({ query: {} })
}
function clearFilters() {
  search.value = ''
  type.value = ''
  status.value = ''
  clearEmployee()
}

const selected = computed(() => store.items.find((d) => d.id === detailId.value) || null)

function openEmployee(doc) {
  router.push(`/employees/${doc.employeeId}`)
}

const statsLoading = computed(() => store.loading && !store.loaded)
</script>

<template>
  <div>
    <PageHeader title="Hujjatlar" subtitle="Har bir xodimning ma’lumotlari va hujjatlari: yuklash, ko‘rish, yuklab olish, o‘chirish">
      <template #actions>
        <Button :icon="Upload" @click="uploadOpen = true">Hujjat yuklash</Button>
      </template>
    </PageHeader>

    <div class="stagger grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Jami hujjatlar" :value="store.stats.total" :icon="FileText" :loading="statsLoading" hint="Barcha yuklangan fayllar" />
      <StatCard label="Tasdiqlangan" :value="store.stats.approved" :icon="CheckCircle2" tone="green" :loading="statsLoading" :hint="`${percent(store.stats.approved, store.stats.total)}% hujjatlar`" />
      <StatCard label="Kutilmoqda" :value="store.stats.pending" :icon="Clock" tone="amber" :loading="statsLoading" hint="Ko‘rib chiqish kerak" />
      <StatCard label="Rad etilgan" :value="store.stats.rejected" :icon="XCircle" tone="red" :loading="statsLoading" hint="Qayta topshirish kutilmoqda" />
    </div>

    <div class="mt-6">
      <SegmentedControl :model-value="mode" :options="modes" aria-label="Ko‘rinish" @update:model-value="setMode" />
    </div>

    <!-- ================= Xodimlar bo‘yicha ================= -->
    <div v-if="mode === 'employees'" class="mt-4 grid gap-5 lg:grid-cols-[340px_minmax(0,1fr)]">
      <!-- Xodimlar ro‘yxati -->
      <aside :class="['card flex flex-col overflow-hidden lg:sticky lg:top-24 lg:max-h-[calc(100vh-7.5rem)]', selectedEmployee && 'hidden lg:flex']">
        <div class="space-y-2.5 border-b border-line p-3">
          <SearchInput v-model="empSearch" placeholder="Xodim ismi yoki telefon..." label="Xodim qidirish" />
          <Select v-model="empDept" :options="catalog.departmentOptions" placeholder="Barcha bo‘limlar" aria-label="Bo‘lim bo‘yicha filtr" />
        </div>
        <LoadingState v-if="employees.loading && !employees.loaded" :rows="6" />
        <EmptyState v-else-if="!employeeList.length" compact :icon="Users" title="Xodim topilmadi" />
        <ul v-else class="flex-1 divide-y divide-line overflow-y-auto">
          <li v-for="e in employeeList" :key="e.id">
            <button
              :class="[
                'group flex w-full items-center gap-3 px-3.5 py-3 text-left transition-colors duration-150',
                selectedEmployee?.id === e.id ? 'bg-primary-50/80' : 'hover:bg-slate-50',
              ]"
              :aria-current="selectedEmployee?.id === e.id ? 'true' : undefined"
              @click="selectEmployee(e)"
            >
              <span :class="['h-9 w-1 shrink-0 rounded-full transition-colors', selectedEmployee?.id === e.id ? 'bg-primary-600' : 'bg-transparent']" />
              <Avatar :name="e.fullName" :src="e.photo" size="sm" />
              <span class="min-w-0 flex-1">
                <span :class="['block truncate text-sm font-medium', selectedEmployee?.id === e.id ? 'text-primary-700' : 'text-ink', e.status === 'Faol emas' && 'opacity-60']">{{ e.fullName }}</span>
                <span class="block truncate text-xs text-muted">{{ catalog.departmentName(e.departmentId) }} · {{ catalog.positionName(e.positionId) }}</span>
              </span>
              <span class="flex shrink-0 items-center gap-1.5">
                <span v-if="pendingCount(e.id)" class="h-2 w-2 rounded-full bg-amber-500" title="Tekshiruv kutilmoqda" />
                <span :class="['rounded-full px-2 text-xs font-semibold tabular-nums leading-5', docCount(e.id) ? 'bg-primary-100 text-primary-700' : 'bg-slate-100 text-slate-400']">{{ docCount(e.id) }}</span>
                <ChevronRight class="h-4 w-4 text-slate-300 transition-transform group-hover:translate-x-0.5 lg:hidden" />
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <!-- Tanlangan xodim -->
      <div :class="['min-w-0', !selectedEmployee && 'hidden lg:block']">
        <Transition name="page" mode="out-in">
          <EmployeeDocsPanel
            v-if="selectedEmployee"
            :key="selectedEmployee.id"
            :employee="selectedEmployee"
            @back="backToList"
            @upload="uploadOpen = true"
            @view="(d) => (detailId = d.id)"
            @download="download"
            @delete="askDelete"
          />
          <div v-else class="card grid min-h-[420px] place-items-center">
            <EmptyState :icon="FolderOpen" title="Xodimni tanlang" description="Chap tomondagi ro‘yxatdan xodimni tanlang — uning ma’lumotlari va hujjatlari shu yerda ko‘rinadi." />
          </div>
        </Transition>
      </div>
    </div>

    <!-- ================= Barcha hujjatlar ================= -->
    <section v-else class="card mt-4 overflow-hidden">
      <div class="flex flex-col gap-3 border-b border-line p-4 xl:flex-row xl:items-center">
        <SegmentedControl v-model="status" :options="statusTabs" aria-label="Hujjat holati" />
        <div class="grid flex-1 gap-3 sm:grid-cols-[minmax(0,1fr)_200px] xl:ml-auto xl:max-w-lg">
          <SearchInput v-model="search" placeholder="Xodim yoki fayl nomi..." label="Hujjat qidirish" />
          <Select v-model="type" :options="DOCUMENT_TYPES" placeholder="Barcha turlar" aria-label="Hujjat turi bo‘yicha filtr" />
        </div>
      </div>

      <div v-if="employeeId" class="flex items-center gap-2 border-b border-line bg-primary-50/50 px-4 py-2.5 text-sm">
        <span class="text-muted">Xodim:</span>
        <span class="inline-flex items-center gap-1 rounded-full bg-white py-0.5 pl-3 pr-1 font-medium text-ink ring-1 ring-primary-200">
          {{ employeeName }}
          <button class="grid h-5 w-5 place-items-center rounded-full text-muted hover:bg-slate-100 hover:text-ink" aria-label="Xodim filtrini olib tashlash" @click="clearEmployee">
            <X class="h-3.5 w-3.5" />
          </button>
        </span>
      </div>

      <ErrorState v-if="store.error" :message="store.error" @retry="store.fetchAll({ force: true })" />
      <LoadingState v-else-if="statsLoading" :rows="8" />
      <EmptyState
        v-else-if="!filtered.length && employeeId && !search && !type && !status"
        :icon="FolderOpen"
        title="Bu xodimning hujjatlari hali yuklanmagan"
        description="“Hujjat yuklash” tugmasi orqali birinchi hujjatni qo‘shing."
      >
        <Button :icon="Upload" @click="uploadOpen = true">Hujjat yuklash</Button>
        <Button variant="secondary" @click="clearEmployee">Barcha hujjatlar</Button>
      </EmptyState>
      <EmptyState v-else-if="!store.items.length" :icon="FolderOpen" title="Hali hujjatlar yo‘q" description="Xodimlarning pasport, shartnoma va boshqa hujjatlarini yuklang.">
        <Button :icon="Upload" @click="uploadOpen = true">Hujjat yuklash</Button>
      </EmptyState>
      <EmptyState v-else-if="!filtered.length" :icon="SearchX" title="Hujjat topilmadi" description="Qidiruv yoki filtrlarni o‘zgartirib ko‘ring.">
        <Button variant="secondary" @click="clearFilters">Filtrlarni tozalash</Button>
      </EmptyState>
      <template v-else>
        <DocumentTable :rows="paged" @view="(d) => (detailId = d.id)" @download="download" @delete="askDelete" />
        <Pagination v-model:page="page" :total="total" :page-size="pageSize" />
      </template>
    </section>

    <DocumentDetails
      :open="!!selected"
      :document="selected"
      :busy="busy"
      @close="detailId = null"
      @approve="(c) => review(selected, 'Tasdiqlangan', c)"
      @reject="(c) => review(selected, 'Rad etilgan', c)"
      @open-employee="openEmployee"
      @download="download"
      @delete="askDelete"
    />
    <DocumentUpload :open="uploadOpen" :employee-id="mode === 'employees' ? selectedEmployee?.id ?? null : employeeId" @close="uploadOpen = false" />
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Hujjatni o‘chirasizmi?"
      :message="deleteTarget ? `“${deleteTarget.fileName}” butunlay o‘chiriladi. Bu amalni qaytarib bo‘lmaydi.` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </div>
</template>
