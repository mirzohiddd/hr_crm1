<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Check, Download, FileText, Loader2, Trash2, X } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import FormField from '@/components/ui/FormField.vue'
import { useDocumentsStore } from '@/stores/documents'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { formatDate } from '@/utils/date'
import { formatBytes } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  document: { type: Object, default: null },
  busy: { type: String, default: '' }, // '' | 'approve' | 'reject'
})
const emit = defineEmits(['close', 'approve', 'reject', 'open-employee', 'download', 'delete'])

const store = useDocumentsStore()
const employees = useEmployeesStore()
const catalog = useCatalogStore()

const comment = ref('')
const commentError = ref('')
const employee = computed(() => (props.document ? employees.findById(props.document.employeeId) : null))
const employeeName = computed(() => employee.value?.fullName || props.document?.employeeName || 'O‘chirilgan xodim')

// ---------- Fayl ko‘rinishi ----------
const previewUrl = ref('')
const previewType = ref('') // image | pdf | other | none
const previewLoading = ref(false)

function revoke() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

async function loadPreview(doc) {
  revoke()
  previewType.value = ''
  if (!doc) return
  previewLoading.value = true
  try {
    const blob = await store.getFile(doc)
    if (!blob) {
      previewType.value = 'none'
      return
    }
    const type = blob.type || doc.mimeType || ''
    previewUrl.value = URL.createObjectURL(blob)
    previewType.value = type.startsWith('image/') ? 'image' : type === 'application/pdf' ? 'pdf' : 'other'
  } catch {
    previewType.value = 'none'
  } finally {
    previewLoading.value = false
  }
}

watch(
  () => [props.open, props.document?.id],
  ([open]) => {
    comment.value = ''
    commentError.value = ''
    if (open && props.document) loadPreview(props.document)
    else revoke()
  },
)
onBeforeUnmount(revoke)

const pending = computed(() => props.document?.status === 'Kutilmoqda')
const ext = computed(() => props.document?.fileName.split('.').pop().toUpperCase())

function reject() {
  if (comment.value.trim().length < 5) {
    commentError.value = 'Rad etish sababini yozing (kamida 5 belgi)'
    return
  }
  emit('reject', comment.value.trim())
}
</script>

<template>
  <Modal :open="open && !!document" size="lg" title="Hujjat" :persistent="!!busy" @close="!busy && emit('close')">
    <template v-if="document">
      <!-- Fayl -->
      <div class="flex items-center gap-4 rounded-xl border border-primary-100 bg-primary-50/60 p-4">
        <span class="relative grid h-14 w-12 shrink-0 place-items-center rounded-md border border-primary-200 bg-white text-primary-600">
          <FileText class="h-6 w-6" />
          <span class="absolute -bottom-1.5 rounded bg-primary-600 px-1 text-[9px] font-semibold leading-4 text-white">{{ ext }}</span>
        </span>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-ink">{{ document.fileName }}</p>
          <p class="mt-0.5 text-xs text-muted">{{ document.type }} · {{ formatBytes(document.fileSize) }}</p>
        </div>
        <Button size="sm" variant="secondary" :icon="Download" :disabled="previewType === 'none'" @click="emit('download', document)">Yuklab olish</Button>
      </div>

      <!-- Ko‘rish -->
      <div class="mt-4 overflow-hidden rounded-xl border border-line bg-slate-50">
        <div v-if="previewLoading" class="grid h-48 place-items-center text-muted"><Loader2 class="h-6 w-6 animate-spin" /></div>
        <img v-else-if="previewType === 'image'" :src="previewUrl" :alt="document.fileName" class="mx-auto max-h-[420px] w-auto object-contain" />
        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" :title="document.fileName" class="h-[420px] w-full bg-white" />
        <p v-else-if="previewType === 'other'" class="px-4 py-8 text-center text-sm text-muted">Bu turdagi faylni brauzerda ko‘rib bo‘lmaydi — yuklab olib oching.</p>
        <p v-else-if="previewType === 'none'" class="px-4 py-8 text-center text-sm text-muted">Namunaviy yozuv: fayl biriktirilmagan.</p>
      </div>

      <dl class="mt-4 divide-y divide-line text-sm">
        <div class="flex items-center justify-between gap-4 py-3">
          <dt class="text-muted">Xodim</dt>
          <dd>
            <button class="flex items-center gap-2 rounded-md text-right font-medium text-ink hover:text-primary-600 disabled:pointer-events-none" :disabled="!employee" @click="emit('open-employee', document)">
              <Avatar :name="employeeName" :src="employee?.photo" size="xs" />{{ employeeName }}
            </button>
          </dd>
        </div>
        <div class="flex justify-between gap-4 py-3">
          <dt class="text-muted">Lavozim</dt>
          <dd class="text-right text-ink">{{ employee ? catalog.positionName(employee.positionId) : '—' }}</dd>
        </div>
        <div class="flex justify-between gap-4 py-3">
          <dt class="text-muted">Yuklangan</dt>
          <dd class="text-right tabular-nums text-ink">
            {{ formatDate(document.uploadedAt) }}
            <span v-if="document.uploadedBy" class="block text-xs text-muted">{{ document.uploadedBy }}</span>
          </dd>
        </div>
        <div class="flex items-center justify-between gap-4 py-3">
          <dt class="text-muted">Holat</dt>
          <dd><StatusBadge :status="document.status" /></dd>
        </div>
        <div v-if="document.reviewedBy" class="flex justify-between gap-4 py-3">
          <dt class="text-muted">Ko‘rib chiqdi</dt>
          <dd class="text-right text-ink">
            {{ document.reviewedBy }}
            <span class="block text-xs tabular-nums text-muted">{{ formatDate(document.reviewedAt) }}</span>
          </dd>
        </div>
      </dl>

      <div v-if="document.comment" :class="['mt-3 rounded-lg p-3 text-sm', document.status === 'Rad etilgan' ? 'bg-red-50 text-red-800' : 'bg-slate-50 text-slate-700']">
        <p class="text-xs font-medium opacity-80">Izoh</p>
        <p class="mt-0.5">{{ document.comment }}</p>
      </div>

      <FormField v-if="pending" class="mt-5" label="Izoh" for="doc-comment" :error="commentError" hint="Rad etishda majburiy, tasdiqlashda ixtiyoriy">
        <textarea
          id="doc-comment"
          v-model="comment"
          rows="3"
          placeholder="Masalan: skan nusxasi sifatsiz, qayta yuklang"
          :class="['form-input', commentError && 'has-error']"
          @input="commentError = ''"
        />
      </FormField>
    </template>

    <template #footer>
      <Button class="sm:mr-auto" variant="danger-outline" :icon="Trash2" :disabled="!!busy" @click="emit('delete', document)">O‘chirish</Button>
      <template v-if="pending">
        <Button variant="danger-outline" :icon="X" :loading="busy === 'reject'" :disabled="!!busy" @click="reject">Rad etish</Button>
        <Button :icon="Check" :loading="busy === 'approve'" :disabled="!!busy" @click="emit('approve', comment.trim())">Tasdiqlash</Button>
      </template>
      <Button v-else variant="secondary" @click="emit('close')">Yopish</Button>
    </template>
  </Modal>
</template>
