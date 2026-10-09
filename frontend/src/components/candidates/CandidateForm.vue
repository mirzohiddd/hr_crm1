<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'
import FormField from '@/components/ui/FormField.vue'
import { CANDIDATE_SOURCES, GENDERS } from '@/constants'
import { useCatalogStore } from '@/stores/catalog'
import { validateCandidate } from '@/utils/validators'
import { formatPhoneInput } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  candidate: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'submit'])
const catalog = useCatalogStore()

const blank = () => ({ fullName: '', phone: '+998 ', positionId: '', departmentId: '', source: 'Instagram', gender: '', age: '', city: '', note: '' })
const form = reactive(blank())
const errors = ref({})
const submitted = ref(false)
const formEl = ref(null)
const isEdit = computed(() => !!props.candidate)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const src = props.candidate
    Object.assign(form, blank(), src ? Object.fromEntries(Object.keys(blank()).map((k) => [k, src[k] ?? blank()[k]])) : {})
    errors.value = {}
    submitted.value = false
  },
  { immediate: true },
)

watch(form, () => {
  if (submitted.value) errors.value = validateCandidate(form)
})

async function submit() {
  submitted.value = true
  errors.value = validateCandidate(form)
  const first = Object.keys(errors.value)[0]
  if (first) {
    await nextTick()
    formEl.value?.querySelector(`[name="${first}"]`)?.focus()
    return
  }
  emit('submit', {
    fullName: form.fullName.trim().replace(/\s+/g, ' '),
    phone: form.phone,
    positionId: Number(form.positionId),
    departmentId: form.departmentId ? Number(form.departmentId) : null,
    source: form.source,
    gender: form.gender,
    age: form.age === '' || form.age === null ? null : Number(form.age),
    city: form.city.trim(),
    note: form.note.trim(),
  })
}
</script>

<template>
  <Modal
    :open="open"
    size="lg"
    :persistent="saving"
    :title="isEdit ? 'Nomzodni tahrirlash' : 'Yangi nomzod'"
    :subtitle="isEdit ? candidate.fullName : 'Instagram, Google Sheets yoki boshqa manbadan kelgan ariza'"
    @close="!saving && emit('close')"
  >
    <form id="candidate-form" ref="formEl" novalidate class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
      <FormField class="sm:col-span-2" label="F.I.Sh" for="c-name" :error="errors.fullName" required>
        <input id="c-name" v-model="form.fullName" name="fullName" class="form-input" :class="errors.fullName && 'has-error'" placeholder="Masalan: Qodirova Sevara" autocomplete="off" />
      </FormField>
      <FormField label="Telefon" for="c-phone" :error="errors.phone" required>
        <input
          id="c-phone"
          :value="form.phone"
          name="phone"
          type="tel"
          inputmode="tel"
          class="form-input tabular-nums"
          :class="errors.phone && 'has-error'"
          placeholder="+998 90 123 45 67"
          @input="form.phone = formatPhoneInput($event.target.value)"
        />
      </FormField>
      <FormField label="Lavozim" for="c-pos" :error="errors.positionId" required>
        <Select id="c-pos" v-model="form.positionId" name="positionId" :options="catalog.positionOptions" placeholder="Lavozimni tanlang" :error="errors.positionId" />
      </FormField>
      <FormField label="Bo‘lim" for="c-dept" hint="Ixtiyoriy — ishga olishda tanlash mumkin">
        <Select id="c-dept" v-model="form.departmentId" :options="catalog.departmentOptions" placeholder="Tanlanmagan" />
      </FormField>
      <FormField label="Manba" :error="errors.source" required>
        <div class="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Manba">
          <label
            v-for="s in CANDIDATE_SOURCES"
            :key="s"
            :class="[
              'flex h-10 cursor-pointer items-center justify-center rounded-lg border text-sm font-medium transition-colors focus-within:ring-4 focus-within:ring-primary-500/15',
              form.source === s ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-line text-slate-600 hover:bg-slate-50',
            ]"
          >
            <input v-model="form.source" type="radio" name="source" :value="s" class="sr-only" />{{ s }}
          </label>
        </div>
      </FormField>
      <div class="grid grid-cols-2 gap-4">
        <FormField label="Yosh" for="c-age" :error="errors.age">
          <input id="c-age" v-model="form.age" name="age" type="number" min="16" max="70" class="form-input tabular-nums" :class="errors.age && 'has-error'" placeholder="25" />
        </FormField>
        <FormField label="Jinsi" for="c-gender">
          <Select id="c-gender" v-model="form.gender" :options="GENDERS" placeholder="—" />
        </FormField>
      </div>
      <FormField class="sm:col-span-2" label="Shahar / tuman" for="c-city">
        <input id="c-city" v-model="form.city" class="form-input" placeholder="Masalan: Toshkent, Chilonzor" />
      </FormField>
      <FormField class="sm:col-span-2" label="Izoh" for="c-note">
        <textarea id="c-note" v-model="form.note" rows="3" class="form-input" placeholder="Tajribasi, ish grafigi, suhbatdagi taassurot..." />
      </FormField>
    </form>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button type="submit" form="candidate-form" :loading="saving">Saqlash</Button>
    </template>
  </Modal>
</template>
