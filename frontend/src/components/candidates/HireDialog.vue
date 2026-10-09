<script setup>
import { reactive, ref, watch } from 'vue'
import { ArrowRight, BadgeCheck } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'
import FormField from '@/components/ui/FormField.vue'
import Switch from '@/components/ui/Switch.vue'
import Avatar from '@/components/ui/Avatar.vue'
import { useCatalogStore } from '@/stores/catalog'
import { todayISO } from '@/utils/date'

const props = defineProps({
  open: { type: Boolean, default: false },
  candidate: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'confirm'])
const catalog = useCatalogStore()

const form = reactive({ positionId: '', departmentId: '', hireDate: todayISO(), startTraining: true })
const errors = ref({})

watch(
  () => props.open,
  (open) => {
    if (!open || !props.candidate) return
    const position = catalog.findPosition(props.candidate.positionId)
    const department = catalog.findDepartment(props.candidate.departmentId)
    Object.assign(form, { positionId: position?.id || '', departmentId: department?.id || '', hireDate: todayISO(), startTraining: true })
    errors.value = {}
  },
)


function submit() {
  const e = {}
  if (!form.positionId) e.positionId = 'Lavozimni tanlang'
  if (!form.departmentId) e.departmentId = 'Bo‘limni tanlang'
  if (!form.hireDate) e.hireDate = 'Sanani tanlang'
  errors.value = e
  if (Object.keys(e).length) return
  emit('confirm', { ...form, positionId: Number(form.positionId), departmentId: Number(form.departmentId) })
}
</script>

<template>
  <Modal :open="open && !!candidate" size="md" title="Ishga qabul qilish" :persistent="saving" @close="!saving && emit('close')">
    <template v-if="candidate">
      <div class="flex items-center gap-3 rounded-xl border border-emerald-100 bg-emerald-50/60 p-3.5">
        <Avatar :name="candidate.fullName" size="md" />
        <div class="min-w-0 flex-1">
          <p class="truncate font-medium text-ink">{{ candidate.fullName }}</p>
          <p class="text-xs text-muted">Nomzod <ArrowRight class="inline h-3 w-3" /> Xodim</p>
        </div>
        <BadgeCheck class="h-6 w-6 shrink-0 text-emerald-600" />
      </div>

      <form id="hire-form" class="mt-5 grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
        <FormField label="Lavozim" for="h-pos" :error="errors.positionId" required>
          <Select id="h-pos" v-model="form.positionId" :options="catalog.positionOptions" placeholder="Lavozimni tanlang" :error="errors.positionId" />
        </FormField>
        <FormField label="Bo‘lim" for="h-dept" :error="errors.departmentId" required>
          <Select id="h-dept" v-model="form.departmentId" :options="catalog.departmentOptions" placeholder="Bo‘limni tanlang" :error="errors.departmentId" />
        </FormField>
        <FormField class="sm:col-span-2" label="Ishga kirgan sana" for="h-date" :error="errors.hireDate" required>
          <input id="h-date" v-model="form.hireDate" type="date" class="form-input" :class="errors.hireDate && 'has-error'" />
        </FormField>
        <div class="flex items-center justify-between gap-4 rounded-lg border border-primary-100 bg-primary-50/50 px-4 py-3 sm:col-span-2">
          <div>
            <p class="text-sm font-medium text-ink">7 kunlik o‘quv dasturini boshlash</p>
            <p class="text-xs text-muted">1-kun ishga kirgan sanaga rejalashtiriladi</p>
          </div>
          <Switch v-model="form.startTraining" label="O‘quv dasturini boshlash" />
        </div>
      </form>
      <p class="mt-4 text-xs text-muted">Tasdiqlangach nomzod avtomatik ravishda “Xodimlar” ro‘yxatiga “Yangi” holatida qo‘shiladi.</p>
    </template>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button type="submit" form="hire-form" :icon="BadgeCheck" :loading="saving">Ishga qabul qilish</Button>
    </template>
  </Modal>
</template>
