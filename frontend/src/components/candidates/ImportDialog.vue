<script setup>
import { computed, ref, watch } from 'vue'
import { AlertTriangle, CheckCircle2, ClipboardPaste, FileSpreadsheet, Link2, Upload } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'
import FormField from '@/components/ui/FormField.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useCandidatesStore } from '@/stores/candidates'
import { useToast } from '@/composables/useToast'
import { CANDIDATE_SOURCES } from '@/constants'
import { googleSheetCsvUrl, parseCSV, rowsToCandidates } from '@/utils/csv'
import { phoneKey } from '@/utils/format'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close', 'imported'])

const catalog = useCatalogStore()
const store = useCandidatesStore()
const toast = useToast()

const mode = ref('sheet')
const modes = [
  { value: 'sheet', label: 'Google Sheets' },
  { value: 'file', label: 'CSV fayl' },
  { value: 'paste', label: 'Nusxa joylash' },
]
const url = ref('')
const pasted = ref('')
const fileName = ref('')
const table = ref([])
const loading = ref(false)
const error = ref('')
const saving = ref(false)
const defaultSource = ref('Google Sheets')
const defaultPositionId = ref('')

watch(
  () => props.open,
  (open) => {
    if (!open) return
    url.value = ''
    pasted.value = ''
    fileName.value = ''
    table.value = []
    error.value = ''
    defaultSource.value = 'Google Sheets'
    defaultPositionId.value = ''
  },
)
watch(mode, () => {
  error.value = ''
  table.value = []
})

const parsed = computed(() =>
  rowsToCandidates(table.value, catalog.positions, {
    defaultSource: defaultSource.value,
    defaultPositionId: defaultPositionId.value ? Number(defaultPositionId.value) : null,
    departments: catalog.departments,
  }),
)
const existing = computed(() => new Set(store.items.map((c) => phoneKey(c.phone))))
const preview = computed(() => {
  const seen = new Set()
  return parsed.value.rows.map((r) => {
    const key = phoneKey(r.phone)
    const duplicate = !!key && (existing.value.has(key) || seen.has(key))
    if (key) seen.add(key)
    return { ...r, duplicate, ok: !r.errors.length && !duplicate }
  })
})
const ready = computed(() => preview.value.filter((r) => r.ok))
const summary = computed(() => ({
  total: preview.value.length,
  ok: ready.value.length,
  dup: preview.value.filter((r) => r.duplicate).length,
  bad: preview.value.filter((r) => r.errors.length && !r.duplicate).length,
}))
const missingPosition = computed(() => parsed.value.rows.some((r) => !r.positionId))

function load(text) {
  const rows = parseCSV(text)
  if (!rows.length) {
    error.value = 'Ma’lumot topilmadi. Fayl bo‘sh yoki formati noto‘g‘ri.'
    table.value = []
    return
  }
  table.value = rows
  error.value = ''
}

async function fetchSheet() {
  const csvUrl = googleSheetCsvUrl(url.value.trim())
  if (!csvUrl) return (error.value = 'Google Sheets havolasini kiriting: https://docs.google.com/spreadsheets/d/...')
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(csvUrl)
    if (!res.ok) throw new Error(String(res.status))
    const text = await res.text()
    if (/^\s*<!doctype html|<html/i.test(text)) throw new Error('html')
    load(text)
  } catch {
    error.value = 'Jadvalni o‘qib bo‘lmadi. Jadval “Havolaga ega har kim ko‘ra oladi” rejimida ulashilganini tekshiring yoki Fayl → Yuklab olish → CSV orqali yuklang.'
    table.value = []
  } finally {
    loading.value = false
  }
}

function onFile(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  if (!/\.(csv|tsv|txt)$/i.test(file.name)) {
    error.value = 'CSV faylni tanlang. Excel/Google Sheets’da: Fayl → Yuklab olish → CSV'
    return
  }
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => load(String(reader.result || ''))
  reader.onerror = () => (error.value = 'Faylni o‘qib bo‘lmadi')
  reader.readAsText(file, 'utf-8')
}

async function submit() {
  if (!ready.value.length) return
  saving.value = true
  try {
    const rows = ready.value.map(({ fullName, phone, positionId, departmentId, source, age, city, note, createdAt }) => ({
      fullName,
      phone,
      positionId,
      departmentId,
      source,
      age,
      city,
      note,
      ...(createdAt ? { createdAt } : {}),
    }))
    const res = await store.importRows(rows)
    toast.success(`${res.created.length} ta nomzod qo‘shildi`, res.skipped ? `${res.skipped} ta takroriy raqam o‘tkazib yuborildi` : 'Barchasi “Yangi” bosqichida')
    emit('imported', res)
    emit('close')
  } catch (e) {
    toast.error('Import qilib bo‘lmadi', e.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Modal :open="open" size="xl" title="Nomzodlarni import qilish" subtitle="Google Sheets (Instagram/Google Forms arizalari) yoki CSV fayldan" :persistent="saving" @close="!saving && emit('close')">
    <SegmentedControl v-model="mode" :options="modes" aria-label="Import usuli" />

    <div class="mt-4">
      <div v-if="mode === 'sheet'">
        <FormField label="Google Sheets havolasi" for="imp-url" hint="Jadval “Havolaga ega har kim ko‘ra oladi” rejimida ulashilgan bo‘lishi kerak">
          <div class="flex flex-col gap-2 sm:flex-row">
            <div class="relative flex-1">
              <Link2 class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              <input id="imp-url" v-model="url" type="url" class="form-input pl-9" placeholder="https://docs.google.com/spreadsheets/d/..." @keydown.enter.prevent="fetchSheet" />
            </div>
            <Button variant="secondary" :icon="FileSpreadsheet" :loading="loading" @click="fetchSheet">Yuklash</Button>
          </div>
        </FormField>
      </div>

      <div v-else-if="mode === 'file'">
        <label class="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-line px-4 py-8 text-center transition-colors hover:border-primary-300 hover:bg-primary-50/40">
          <span class="grid h-11 w-11 place-items-center rounded-full bg-primary-50 text-primary-600"><Upload class="h-5 w-5" /></span>
          <span class="mt-3 text-sm font-medium text-ink">{{ fileName || 'CSV faylni tanlang' }}</span>
          <span class="mt-1 text-xs text-muted">Google Sheets / Excel: Fayl → Yuklab olish → CSV</span>
          <input type="file" accept=".csv,.tsv,.txt,text/csv" class="sr-only" @change="onFile" />
        </label>
      </div>

      <div v-else>
        <FormField label="Jadvaldan nusxa ko‘chirib joylang" for="imp-paste" hint="Google Sheets’da qatorlarni belgilab Ctrl+C, so‘ng shu yerga Ctrl+V. Birinchi qator — sarlavha.">
          <textarea id="imp-paste" v-model="pasted" rows="5" class="form-input font-mono text-xs" placeholder="F.I.Sh	Telefon	Lavozim&#10;Aliyev Anvar	+998901234567	Call Center" />
        </FormField>
        <Button class="mt-2" size="sm" variant="secondary" :icon="ClipboardPaste" :disabled="!pasted.trim()" @click="load(pasted)">Tahlil qilish</Button>
      </div>

      <p v-if="error" class="mt-3 flex gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700"><AlertTriangle class="mt-0.5 h-4 w-4 shrink-0" />{{ error }}</p>
    </div>

    <template v-if="preview.length">
      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <FormField label="Manba (ustunda ko‘rsatilmagan bo‘lsa)" for="imp-src">
          <Select id="imp-src" v-model="defaultSource" :options="CANDIDATE_SOURCES" />
        </FormField>
        <FormField label="Lavozim (ustunda topilmasa)" for="imp-pos" :hint="missingPosition && !defaultPositionId ? 'Ba’zi qatorlarda lavozim aniqlanmadi' : ''">
          <Select id="imp-pos" v-model="defaultPositionId" :options="catalog.positionOptions" placeholder="Tanlanmagan" />
        </FormField>
      </div>

      <div class="mt-4 flex flex-wrap gap-2 text-xs">
        <span class="rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700">{{ summary.ok }} ta qo‘shiladi</span>
        <span v-if="summary.dup" class="rounded-full bg-amber-50 px-2.5 py-1 font-medium text-amber-700">{{ summary.dup }} ta takroriy</span>
        <span v-if="summary.bad" class="rounded-full bg-red-50 px-2.5 py-1 font-medium text-red-700">{{ summary.bad }} ta xatoli</span>
        <span class="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600">Jami {{ summary.total }} qator</span>
      </div>

      <div class="mt-3 max-h-72 overflow-auto rounded-xl border border-line">
        <table class="min-w-full text-sm">
          <thead class="sticky top-0 border-b border-line bg-slate-50">
            <tr>
              <th class="table-th w-8" />
              <th class="table-th">F.I.Sh</th>
              <th class="table-th">Telefon</th>
              <th class="table-th">Lavozim</th>
              <th class="table-th">Manba</th>
              <th class="table-th">Izoh</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-line">
            <tr v-for="(r, i) in preview" :key="i" :class="!r.ok && 'bg-slate-50/70 text-muted'">
              <td class="px-3 py-2">
                <CheckCircle2 v-if="r.ok" class="h-4 w-4 text-emerald-600" />
                <AlertTriangle v-else :class="['h-4 w-4', r.duplicate ? 'text-amber-500' : 'text-red-500']" />
              </td>
              <td class="whitespace-nowrap px-3 py-2">{{ r.fullName || '—' }}</td>
              <td class="whitespace-nowrap px-3 py-2 tabular-nums">{{ r.phone || '—' }}</td>
              <td class="whitespace-nowrap px-3 py-2">{{ r.positionId ? catalog.positionName(r.positionId) : r.positionText || '—' }}</td>
              <td class="whitespace-nowrap px-3 py-2">{{ r.source }}</td>
              <td class="px-3 py-2 text-xs">
                <span v-if="r.duplicate" class="text-amber-700">Bu raqam bazada bor</span>
                <span v-else-if="r.errors.length" class="text-red-600">{{ r.errors.join(', ') }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-else-if="!error" class="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
      <p class="font-medium text-ink">Qaysi ustunlar o‘qiladi?</p>
      <p class="mt-1">
        <b>F.I.Sh</b> (Ism), <b>Telefon</b>, <b>Lavozim</b> — majburiy. Ixtiyoriy: Manba, Yosh, Shahar, Izoh, Sana (Google Forms “Timestamp”).
        Sarlavha nomlari o‘zbek, rus yoki ingliz tilida bo‘lishi mumkin. Telefon raqami bazada bo‘lsa — takroriy sifatida o‘tkazib yuboriladi.
      </p>
    </div>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button :icon="Upload" :loading="saving" :disabled="!ready.length" @click="submit">{{ ready.length ? `${ready.length} ta nomzodni qo‘shish` : 'Import qilish' }}</Button>
    </template>
  </Modal>
</template>
