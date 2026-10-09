<script setup>
import { computed, ref, watch } from 'vue'
import { CalendarClock, XCircle } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import { todayISO } from '@/utils/date'

/** Suhbat vaqtini belgilash yoki rad etish sababini so‘rash */
const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'interview' }, // interview | reject
  candidate: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'confirm'])

const REASONS = ['Suhbatga kelmadi', 'Telefonga javob bermadi', 'Ish grafigi to‘g‘ri kelmadi', 'Tajribasi yetarli emas', 'Maosh bo‘yicha kelishilmadi', 'O‘zi rad etdi']
const interviewAt = ref('')
const reason = ref('')
const error = ref('')
const isReject = computed(() => props.mode === 'reject')

watch(
  () => props.open,
  (open) => {
    if (!open) return
    error.value = ''
    reason.value = props.candidate?.rejectReason || ''
    interviewAt.value = props.candidate?.interviewAt || `${todayISO()}T10:00`
  },
)

function submit() {
  if (isReject.value) {
    if (reason.value.trim().length < 3) return (error.value = 'Rad etish sababini yozing')
    emit('confirm', { rejectReason: reason.value.trim() })
  } else {
    if (!interviewAt.value) return (error.value = 'Suhbat sanasi va vaqtini tanlang')
    emit('confirm', { interviewAt: interviewAt.value })
  }
}
</script>

<template>
  <Modal :open="open" size="sm" :persistent="saving" @close="!saving && emit('close')">
    <template #header>
      <div class="flex items-center gap-3">
        <span :class="['grid h-10 w-10 place-items-center rounded-full', isReject ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600']">
          <component :is="isReject ? XCircle : CalendarClock" class="h-5 w-5" />
        </span>
        <div class="min-w-0">
          <h2 class="text-base font-semibold text-ink">{{ isReject ? 'Nomzodni rad etish' : 'Suhbatga chaqirish' }}</h2>
          <p class="truncate text-sm text-muted">{{ candidate?.fullName }}</p>
        </div>
      </div>
    </template>

    <form id="stage-form" novalidate @submit.prevent="submit">
      <FormField v-if="!isReject" label="Suhbat sanasi va vaqti" for="st-at" :error="error" required>
        <input id="st-at" v-model="interviewAt" type="datetime-local" class="form-input" :class="error && 'has-error'" @input="error = ''" />
      </FormField>
      <template v-else>
        <div class="mb-3 flex flex-wrap gap-2">
          <button
            v-for="r in REASONS"
            :key="r"
            type="button"
            :class="['rounded-full border px-3 py-1 text-[13px] transition-colors', reason === r ? 'border-red-300 bg-red-50 text-red-700' : 'border-line text-slate-600 hover:bg-slate-50']"
            @click="reason = r; error = ''"
          >
            {{ r }}
          </button>
        </div>
        <FormField label="Sabab" for="st-reason" :error="error" required>
          <textarea id="st-reason" v-model="reason" rows="2" class="form-input" :class="error && 'has-error'" placeholder="Sababni tanlang yoki yozing" @input="error = ''" />
        </FormField>
      </template>
    </form>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button type="submit" form="stage-form" :variant="isReject ? 'danger' : 'primary'" :loading="saving">{{ isReject ? 'Rad etish' : 'Saqlash' }}</Button>
    </template>
  </Modal>
</template>
