<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { FileUp, Upload, X } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import Select from '@/components/ui/Select.vue'
import Switch from '@/components/ui/Switch.vue'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { useDocumentsStore } from '@/stores/documents'
import { useToast } from '@/composables/useToast'
import { DOCUMENT_ACCEPT, DOCUMENT_MAX_SIZE, DOCUMENT_TYPES } from '@/constants'
import { formatBytes } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  employeeId: { type: Number, default: null }, // berilsa — xodim tanlanmaydi (profil sahifasi)
})
const emit = defineEmits(['close', 'uploaded'])

const employees = useEmployeesStore()
const catalog = useCatalogStore()
const store = useDocumentsStore()
const toast = useToast()

const form = reactive({ employeeId: '', type: '', approved: true, comment: '' })
const files = ref([])
const errors = ref({})
const saving = ref(false)
const dragging = ref(false)
const fileInput = ref(null)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    Object.assign(form, { employeeId: props.employeeId || '', type: '', approved: true, comment: '' })
    files.value = []
    errors.value = {}
  },
)

const employeeOptions = computed(() =>
  [...employees.items]
    .sort((a, b) => a.fullName.localeCompare(b.fullName))
    .map((e) => ({ value: e.id, label: `${e.fullName} — ${catalog.positionName(e.positionId)}` })),
)
const allowed = DOCUMENT_ACCEPT.split(',')

function addFiles(list) {
  delete errors.value.file
  for (const file of list) {
    const ext = `.${file.name.split('.').pop().toLowerCase()}`
    if (!allowed.includes(ext)) {
      errors.value.file = `“${file.name}” — bu turdagi fayl qabul qilinmaydi (PDF, rasm, Word, Excel)`
      continue
    }
    if (file.size > DOCUMENT_MAX_SIZE) {
      errors.value.file = `“${file.name}” hajmi ${formatBytes(DOCUMENT_MAX_SIZE)} dan katta`
      continue
    }
    if (!files.value.some((f) => f.name === file.name && f.size === file.size)) files.value.push(file)
  }
}
function onChange(e) {
  addFiles(e.target.files || [])
  e.target.value = ''
}
function onDrop(e) {
  dragging.value = false
  addFiles(e.dataTransfer?.files || [])
}

async function submit() {
  const e = {}
  if (!form.employeeId) e.employeeId = 'Xodimni tanlang'
  if (!form.type) e.type = 'Hujjat turini tanlang'
  if (!files.value.length) e.file = errors.value.file || 'Faylni tanlang'
  errors.value = e
  if (Object.keys(e).length) return

  saving.value = true
  let ok = 0
  try {
    for (const file of files.value) {
      await store.upload({
        employeeId: Number(form.employeeId),
        type: form.type,
        status: form.approved ? 'Tasdiqlangan' : 'Kutilmoqda',
        comment: form.comment.trim(),
        file,
      })
      ok++
    }
    toast.success(ok > 1 ? `${ok} ta hujjat yuklandi` : 'Hujjat yuklandi', employees.findById(Number(form.employeeId))?.fullName)
    emit('uploaded')
    emit('close')
  } catch (err) {
    toast.error('Yuklab bo‘lmadi', err.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Modal :open="open" size="md" title="Hujjat yuklash" subtitle="PDF, rasm, Word yoki Excel — 10 MB gacha" :persistent="saving" @close="!saving && emit('close')">
    <form id="doc-upload" class="space-y-4" novalidate @submit.prevent="submit">
      <FormField v-if="!employeeId" label="Xodim" for="du-emp" :error="errors.employeeId" required>
        <Select id="du-emp" v-model="form.employeeId" :options="employeeOptions" placeholder="Xodimni tanlang" :error="errors.employeeId" />
      </FormField>

      <FormField label="Hujjat turi" for="du-type" :error="errors.type" required>
        <Select id="du-type" v-model="form.type" :options="DOCUMENT_TYPES" placeholder="Turini tanlang" :error="errors.type" />
      </FormField>

      <div>
        <p class="form-label">Fayl<span class="ml-0.5 text-red-500">*</span></p>
        <label
          :class="[
            'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-7 text-center transition-colors',
            dragging ? 'border-primary-500 bg-primary-50' : errors.file ? 'border-red-300 bg-red-50/40' : 'border-line hover:border-primary-300 hover:bg-primary-50/40',
          ]"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <span class="grid h-11 w-11 place-items-center rounded-full bg-primary-50 text-primary-600"><FileUp class="h-5 w-5" /></span>
          <span class="mt-3 text-sm font-medium text-ink">Faylni tanlang yoki shu yerga tashlang</span>
          <span class="mt-1 text-xs text-muted">Bir nechta faylni birdan yuklash mumkin</span>
          <input ref="fileInput" type="file" multiple :accept="DOCUMENT_ACCEPT" class="sr-only" @change="onChange" />
        </label>
        <p v-if="errors.file" class="form-error">{{ errors.file }}</p>
        <ul v-if="files.length" class="mt-3 space-y-2">
          <li v-for="(f, i) in files" :key="f.name + f.size" class="flex items-center gap-3 rounded-lg border border-line px-3 py-2 text-sm">
            <FileUp class="h-4 w-4 shrink-0 text-primary-600" />
            <span class="min-w-0 flex-1 truncate text-ink">{{ f.name }}</span>
            <span class="text-xs tabular-nums text-muted">{{ formatBytes(f.size) }}</span>
            <button type="button" class="icon-btn h-7 w-7" :aria-label="`${f.name}: olib tashlash`" @click="files.splice(i, 1)"><X class="h-4 w-4" /></button>
          </li>
        </ul>
      </div>

      <FormField label="Izoh" for="du-comment">
        <textarea id="du-comment" v-model="form.comment" rows="2" class="form-input" placeholder="Ixtiyoriy" />
      </FormField>

      <div class="flex items-center justify-between gap-4 rounded-lg border border-line px-4 py-3">
        <div>
          <p class="text-sm font-medium text-ink">Darhol tasdiqlash</p>
          <p class="text-xs text-muted">O‘chirilsa — hujjat “Kutilmoqda” holatida tekshiruvga tushadi</p>
        </div>
        <Switch v-model="form.approved" label="Darhol tasdiqlash" />
      </div>
    </form>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button type="submit" form="doc-upload" :icon="Upload" :loading="saving">Yuklash</Button>
    </template>
  </Modal>
</template>
