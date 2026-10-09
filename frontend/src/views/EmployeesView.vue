<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, SearchX, UserPlus } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import Button from '@/components/ui/Button.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import Select from '@/components/ui/Select.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmployeeTable from '@/components/employees/EmployeeTable.vue'
import EmployeeForm from '@/components/employees/EmployeeForm.vue'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { useTrainingsStore } from '@/stores/trainings'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { EMPLOYEE_STATUSES } from '@/constants'
import { normalizeText, onlyDigits } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useEmployeesStore()
const catalog = useCatalogStore()
const trainings = useTrainingsStore()
const toast = useToast()

// ---------- Filtrlar ----------
const search = ref(String(route.query.q || ''))
const department = ref('')
const position = ref('')
const status = ref('')

watch(
  () => route.query.q,
  (q) => {
    if (q !== undefined) search.value = String(q)
  },
)

const positionOptions = computed(() => catalog.positionOptions)
// Lavozim / bo‘lim filtri boshqa sahifadan (?position= / ?department=) kelishi mumkin
if (route.query.position) position.value = Number(route.query.position)
if (route.query.department) department.value = Number(route.query.department)

/** Bo‘limlar bo‘yicha tezkor filtr (ishdan ketganlarsiz soni bilan) */
const departmentTabs = computed(() => {
  const active = store.items.filter((e) => e.status !== 'Faol emas')
  return [
    { value: '', label: 'Barcha bo‘limlar', count: active.length },
    ...catalog.departments.map((d) => ({ value: d.id, label: d.name, count: active.filter((e) => e.departmentId === d.id).length })),
  ]
})

const filtered = computed(() => {
  const q = normalizeText(search.value)
  const qDigits = onlyDigits(search.value)
  return store.items.filter((e) => {
    if (department.value && e.departmentId !== department.value) return false
    if (position.value && e.positionId !== position.value) return false
    if (status.value && e.status !== status.value) return false
    if (!q) return true
    return (
      normalizeText(e.fullName).includes(q) ||
      normalizeText(e.email).includes(q) ||
      normalizeText(catalog.positionName(e.positionId)).includes(q) ||
      (qDigits.length >= 3 && onlyDigits(e.phone).includes(qDigits))
    )
  })
})

const hasFilters = computed(() => !!(search.value || department.value || position.value || status.value))
function clearFilters() {
  search.value = ''
  department.value = ''
  position.value = ''
  status.value = ''
  if (route.query.q || route.query.position || route.query.department) router.replace({ query: {} })
}

const { page, paged, total, pageSize } = usePagination(filtered, 10, () => [search.value, department.value, position.value, status.value])

// ---------- Ommaviy bo‘limga o‘tkazish ----------
const selected = ref([])
const bulkDept = ref('')
const bulkSaving = ref(false)
async function applyBulkDept() {
  const dept = Number(bulkDept.value)
  const ids = [...selected.value]
  bulkSaving.value = true
  try {
    for (const id of ids) {
      const e = store.findById(id)
      if (e && e.departmentId !== dept) await store.update(id, { departmentId: dept })
    }
    toast.success(`${ids.length} ta xodim “${catalog.departmentName(dept)}” bo‘limiga o‘tkazildi`)
    selected.value = []
    bulkDept.value = ''
  } catch (e) {
    toast.error('Bo‘limni o‘zgartirib bo‘lmadi', e.message)
  } finally {
    bulkSaving.value = false
  }
}

// ---------- Modallar ----------
const formOpen = ref(false)
const editing = ref(null)
const saving = ref(false)

const deleteTarget = ref(null)
const deleting = ref(false)

onMounted(async () => {
  // Eski havolalar (?id=) xodim profiliga yo‘naltiriladi
  if (route.query.id) return router.replace(`/employees/${Number(route.query.id)}`)
  await store.fetchAll()
})

function openProfile(employee) {
  router.push(`/employees/${employee.id}`)
}

function openCreate() {
  editing.value = null
  formOpen.value = true
}

function openEdit(employee) {
  editing.value = employee
  formOpen.value = true
}

async function handleSubmit(data, { startTraining } = {}) {
  saving.value = true
  try {
    if (editing.value) {
      await store.update(editing.value.id, data)
      toast.success('O‘zgarishlar saqlandi', `${data.fullName} ma’lumotlari yangilandi`)
    } else {
      const created = await store.create(data)
      if (startTraining) await trainings.start(created.id, created.hireDate)
      clearFilters()
      toast.success('Xodim qo‘shildi', startTraining ? `${data.fullName} 7 kunlik o‘quv dasturiga qo‘shildi` : `${data.fullName} xodimlar ro‘yxatiga qo‘shildi`)
    }
    formOpen.value = false
  } catch (e) {
    toast.error('Saqlab bo‘lmadi', e.message)
  } finally {
    saving.value = false
  }
}

function askDelete(employee) {
  deleteTarget.value = employee
}

async function confirmDelete() {
  const target = deleteTarget.value
  deleting.value = true
  try {
    await store.remove(target.id)
    toast.success('Xodim o‘chirildi', `${target.fullName} ro‘yxatdan olib tashlandi`)
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
    <PageHeader title="Xodimlar">
      <template #subtitle>
        <template v-if="store.loaded">{{ store.stats.total }} ta xodim: {{ store.stats.active }} faol, {{ store.stats.new }} yangi (o‘qishda)</template>
        <template v-else>Kompaniya xodimlari ro‘yxati</template>
      </template>
      <template #actions>
        <Button :icon="Plus" @click="openCreate">Xodim qo‘shish</Button>
      </template>
    </PageHeader>

    <!-- Bo‘limlar bo‘yicha tezkor filtr -->
    <div class="-mx-4 mb-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0" role="tablist" aria-label="Bo‘lim bo‘yicha filtr">
      <button
        v-for="d in departmentTabs"
        :key="d.value"
        role="tab"
        :aria-selected="department === d.value"
        :class="[
          'inline-flex h-9 shrink-0 items-center gap-2 rounded-full border px-3.5 text-[13px] font-medium transition-all duration-200',
          department === d.value
            ? 'border-primary-600 bg-primary-600 text-white shadow-md shadow-primary-600/25'
            : 'border-line bg-white text-slate-600 hover:-translate-y-px hover:border-primary-200 hover:text-primary-700 hover:shadow-sm',
        ]"
        @click="department = d.value"
      >
        {{ d.label }}
        <span :class="['rounded-full px-1.5 text-[11px] tabular-nums', department === d.value ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500']">{{ d.count }}</span>
      </button>
    </div>

    <section class="card overflow-hidden">
      <div class="grid gap-3 border-b border-line p-4 sm:grid-cols-2 lg:grid-cols-[minmax(0,1.6fr)_repeat(3,minmax(0,1fr))_auto]">
        <SearchInput v-model="search" class="sm:col-span-2 lg:col-span-1" placeholder="Xodim qidirish..." label="Xodim qidirish" />
        <Select v-model="position" :options="positionOptions" placeholder="Barcha lavozimlar" aria-label="Lavozim bo‘yicha filtr" />
        <Select v-model="department" :options="catalog.departmentOptions" placeholder="Barcha bo‘limlar" aria-label="Bo‘lim bo‘yicha filtr" />
        <Select v-model="status" :options="EMPLOYEE_STATUSES" placeholder="Barcha holatlar" aria-label="Holat bo‘yicha filtr" />
        <Button v-if="hasFilters" variant="ghost" @click="clearFilters">Tozalash</Button>
      </div>

      <ErrorState v-if="store.error" :message="store.error" @retry="store.fetchAll({ force: true })" />
      <LoadingState v-else-if="store.loading && !store.loaded" :rows="8" />
      <EmptyState
        v-else-if="!store.items.length"
        :icon="UserPlus"
        title="Hali xodimlar yo‘q"
        description="Birinchi xodimni qo‘shing, u shu ro‘yxatda paydo bo‘ladi."
      >
        <Button :icon="Plus" @click="openCreate">Xodim qo‘shish</Button>
      </EmptyState>
      <EmptyState
        v-else-if="!filtered.length"
        :icon="SearchX"
        title="Xodim topilmadi"
        description="Qidiruv so‘zini o‘zgartiring yoki filtrlarni tozalang."
      >
        <Button variant="secondary" @click="clearFilters">Filtrlarni tozalash</Button>
      </EmptyState>
      <template v-else>
        <!-- Ommaviy amal: tanlanganlarni bo‘limga o‘tkazish -->
        <Transition name="dropdown">
          <div v-if="selected.length" class="flex flex-wrap items-center gap-3 border-b border-primary-100 bg-primary-50/70 px-4 py-2.5">
            <span class="text-sm font-medium text-primary-800">{{ selected.length }} ta xodim tanlandi</span>
            <div class="flex flex-1 flex-wrap items-center gap-2 sm:justify-end">
              <Select v-model="bulkDept" class="w-48" :options="catalog.departmentOptions" placeholder="Bo‘limni tanlang" aria-label="Yangi bo‘lim" />
              <Button size="sm" :loading="bulkSaving" :disabled="!bulkDept" @click="applyBulkDept">Bo‘limga o‘tkazish</Button>
              <Button size="sm" variant="ghost" :disabled="bulkSaving" @click="selected = []">Bekor qilish</Button>
            </div>
          </div>
        </Transition>
        <EmployeeTable v-model:selected="selected" selectable :rows="paged" @view="openProfile" @edit="openEdit" @delete="askDelete" />
        <Pagination v-model:page="page" :total="total" :page-size="pageSize" />
      </template>
    </section>

    <EmployeeForm :open="formOpen" :employee="editing" :saving="saving" @close="formOpen = false" @submit="handleSubmit" />
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Xodimni o‘chirasizmi?"
      :message="deleteTarget ? `${deleteTarget.fullName} ro‘yxatdan butunlay o‘chiriladi (darslar progressi, test natijalari va hujjatlari bilan). Bu amalni qaytarib bo‘lmaydi.` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </div>
</template>
