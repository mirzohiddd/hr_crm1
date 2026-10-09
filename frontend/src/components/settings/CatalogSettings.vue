<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Briefcase, Building2, Pencil, Plus, Trash2 } from 'lucide-vue-next'
import SettingsSection from './SettingsSection.vue'
import Button from '@/components/ui/Button.vue'
import Modal from '@/components/ui/Modal.vue'
import FormField from '@/components/ui/FormField.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useEmployeesStore } from '@/stores/employees'
import { useCandidatesStore } from '@/stores/candidates'
import { useToast } from '@/composables/useToast'
import { normalizeText } from '@/utils/format'
import { CANDIDATE_OPEN_STATUSES } from '@/constants'

/** Lavozimlar yoki bo‘limlar ro‘yxatini boshqarish */
const props = defineProps({ kind: { type: String, default: 'positions' } }) // positions | departments

const router = useRouter()
const catalog = useCatalogStore()
const employees = useEmployeesStore()
const candidates = useCandidatesStore()
const toast = useToast()

onMounted(() => Promise.all([catalog.fetchAll(), employees.fetchAll(), candidates.fetchAll()]))

const isPositions = computed(() => props.kind === 'positions')
const text = computed(() =>
  isPositions.value
    ? { title: 'Lavozimlar', subtitle: 'Nomzodlar va xodimlar shu lavozimlarga bog‘lanadi', one: 'lavozim', add: 'Lavozim qo‘shish', edit: 'Lavozimni tahrirlash', icon: Briefcase }
    : { title: 'Bo‘limlar', subtitle: 'Dermolife, Gepomer, Halila va boshqa yo‘nalishlar', one: 'bo‘lim', add: 'Bo‘lim qo‘shish', edit: 'Bo‘limni tahrirlash', icon: Building2 },
)

const activeEmployees = computed(() => employees.items.filter((e) => e.status !== 'Faol emas'))
const rows = computed(() => {
  const list = isPositions.value ? catalog.positions : catalog.departments
  return [...list]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((x) =>
      isPositions.value
        ? {
            ...x,
            employees: activeEmployees.value.filter((e) => e.positionId === x.id).length,
            candidates: candidates.items.filter((c) => c.positionId === x.id && CANDIDATE_OPEN_STATUSES.includes(c.status)).length,
          }
        : {
            ...x,
            employees: activeEmployees.value.filter((e) => e.departmentId === x.id).length,
            candidates: candidates.items.filter((c) => c.departmentId === x.id && CANDIDATE_OPEN_STATUSES.includes(c.status)).length,
          },
    )
})

// ---------- Forma ----------
const formOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = reactive({ name: '', departmentId: '', description: '' })
const errors = ref({})

function openForm(row = null) {
  editing.value = row
  Object.assign(form, { name: row?.name || '', departmentId: row?.departmentId || '', description: row?.description || '' })
  errors.value = {}
  formOpen.value = true
}

async function submit() {
  const e = {}
  const name = form.name.trim().replace(/\s+/g, ' ')
  const list = isPositions.value ? catalog.positions : catalog.departments
  if (!name) e.name = 'Nomini kiriting'
  else if (list.some((x) => x.id !== editing.value?.id && normalizeText(x.name) === normalizeText(name))) e.name = `Bunday ${text.value.one} mavjud`
  errors.value = e
  if (Object.keys(e).length) return

  const payload = { name, description: form.description.trim() }
  saving.value = true
  try {
    if (isPositions.value) {
      if (editing.value) await catalog.updatePosition(editing.value.id, payload)
      else await catalog.createPosition(payload)
    } else if (editing.value) await catalog.updateDepartment(editing.value.id, payload)
    else await catalog.createDepartment(payload)
    toast.success(editing.value ? 'Saqlandi' : `${name} qo‘shildi`)
    formOpen.value = false
  } catch (err) {
    toast.error('Saqlab bo‘lmadi', err.message)
  } finally {
    saving.value = false
  }
}

// ---------- O‘chirish ----------
const deleteTarget = ref(null)
const deleting = ref(false)
async function confirmDelete() {
  deleting.value = true
  try {
    if (isPositions.value) await catalog.removePosition(deleteTarget.value.id)
    else await catalog.removeDepartment(deleteTarget.value.id)
    toast.success(`${deleteTarget.value.name} o‘chirildi`)
    deleteTarget.value = null
  } catch (err) {
    toast.error('O‘chirib bo‘lmadi', err.message)
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <SettingsSection :icon="text.icon" :title="text.title" :subtitle="text.subtitle">
    <template #actions>
      <Button size="sm" :icon="Plus" @click="openForm()">{{ text.add }}</Button>
    </template>

    <LoadingState v-if="!catalog.loaded" :rows="5" />
    <EmptyState v-else-if="!rows.length" compact :icon="text.icon" :title="`Hali ${text.one}lar yo‘q`" />
    <ul v-else class="divide-y divide-line">
      <li v-for="r in rows" :key="r.id" class="flex items-center gap-4 px-5 py-3.5">
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
            <p class="font-medium text-ink">{{ r.name }}</p>
          </div>
          <p v-if="r.description" class="mt-0.5 truncate text-sm text-muted">{{ r.description }}</p>
          <p class="mt-1 flex flex-wrap gap-x-4 text-xs text-muted">
            <template v-if="isPositions">
              <button class="hover:text-primary-600 hover:underline" @click="router.push({ path: '/employees', query: { position: r.id } })">{{ r.employees }} ta xodim</button>
              <span>{{ r.candidates }} ta faol nomzod</span>
            </template>
            <template v-else>
              <button class="hover:text-primary-600 hover:underline" @click="router.push({ path: '/employees', query: { department: r.id } })">{{ r.employees }} ta xodim</button>
              <span>{{ r.candidates }} ta faol nomzod</span>
            </template>
          </p>
        </div>
        <div class="flex shrink-0 gap-0.5">
          <button class="icon-btn h-8 w-8" :aria-label="`${r.name}: tahrirlash`" title="Tahrirlash" @click="openForm(r)"><Pencil class="h-4 w-4" /></button>
          <button class="icon-btn h-8 w-8 hover:bg-red-50 hover:text-red-600" :aria-label="`${r.name}: o‘chirish`" title="O‘chirish" @click="deleteTarget = r"><Trash2 class="h-4 w-4" /></button>
        </div>
      </li>
    </ul>

    <Modal :open="formOpen" size="md" :title="editing ? text.edit : text.add" :persistent="saving" @close="!saving && (formOpen = false)">
      <form :id="`catalog-${kind}`" class="space-y-4" novalidate @submit.prevent="submit">
        <FormField label="Nomi" :for="`cat-name-${kind}`" :error="errors.name" required>
          <input :id="`cat-name-${kind}`" v-model="form.name" class="form-input" :class="errors.name && 'has-error'" :placeholder="isPositions ? 'Masalan: Call Center' : 'Masalan: Dermolife'" />
        </FormField>
        <FormField label="Tavsif" :for="`cat-desc-${kind}`">
          <textarea :id="`cat-desc-${kind}`" v-model="form.description" rows="2" class="form-input" placeholder="Ixtiyoriy" />
        </FormField>
        <p v-if="editing && isPositions && editing.employees" class="text-xs text-muted">Nom o‘zgarsa, {{ editing.employees }} ta xodim va nomzodlarda avtomatik yangilanadi.</p>
      </form>
      <template #footer>
        <Button variant="secondary" :disabled="saving" @click="formOpen = false">Bekor qilish</Button>
        <Button type="submit" :form="`catalog-${kind}`" :loading="saving">Saqlash</Button>
      </template>
    </Modal>

    <ConfirmDialog
      :open="!!deleteTarget"
      :title="`${deleteTarget?.name || ''} — o‘chirilsinmi?`"
      :message="`Bog‘langan xodim yoki nomzod bo‘lsa, o‘chirishga ruxsat berilmaydi.`"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </SettingsSection>
</template>
