<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { AtSign, Briefcase, Building2, ImagePlus, MonitorSmartphone, Phone, Trash2, UserRound, Wallet } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'
import FormField from '@/components/ui/FormField.vue'
import Switch from '@/components/ui/Switch.vue'
import { COMPUTER_SKILLS, EMPLOYEE_STATUSES, GENDERS } from '@/constants'
import { useCatalogStore } from '@/stores/catalog'
import { validateEmployee } from '@/utils/validators'
import { formatNumber, formatPhoneInput, joinName, nameParts, onlyDigits, telegramHandle } from '@/utils/format'
import { todayISO } from '@/utils/date'

const props = defineProps({
  open: { type: Boolean, default: false },
  employee: { type: Object, default: null }, // null -> yangi xodim
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'submit'])
const catalog = useCatalogStore()

const blank = () => ({
  photo: null,
  firstName: '',
  lastName: '',
  middleName: '',
  phone: '+998 ',
  telegram: '',
  previousWork: '',
  computerSkill: '',
  expectedSalary: '',
  gender: '',
  address: '',
  departmentId: '',
  positionId: '',
  hireDate: todayISO(),
  status: 'Yangi',
})
const FIELDS = Object.keys(blank())

const form = reactive(blank())
const errors = ref({})
const submitted = ref(false)
const photoError = ref('')
const formEl = ref(null)
const startTraining = ref(true)
const isEdit = computed(() => !!props.employee)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const e = props.employee
    const source = e ? { ...Object.fromEntries(FIELDS.map((k) => [k, e[k] ?? blank()[k]])), ...nameParts(e) } : blank()
    if (e && (source.expectedSalary === null || source.expectedSalary === undefined)) source.expectedSalary = ''
    Object.assign(form, source)
    errors.value = {}
    submitted.value = false
    photoError.value = ''
    startTraining.value = true
  },
  { immediate: true },
)

// Birinchi saqlash urinishidan keyin xatolar jonli yangilanadi
watch(form, () => {
  if (submitted.value) errors.value = validateEmployee(form)
})

const fullName = computed(() => joinName(form.lastName, form.firstName, form.middleName))
const required = ['firstName', 'lastName', 'phone', 'departmentId', 'positionId', 'hireDate', 'status']
const filled = computed(() => required.filter((k) => (k === 'phone' ? onlyDigits(form.phone).length >= 12 : !!String(form[k] || '').trim())).length)

function onPhoneInput(event) {
  form.phone = formatPhoneInput(event.target.value)
}
// Oylik: yozish paytida 5 000 000 ko‘rinishida
const salaryText = computed(() => (form.expectedSalary === '' ? '' : formatNumber(form.expectedSalary)))
function onSalaryInput(event) {
  const digits = onlyDigits(event.target.value).slice(0, 10)
  form.expectedSalary = digits ? Number(digits) : ''
  event.target.value = salaryText.value
}

function readPhoto(file) {
  photoError.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) return (photoError.value = 'Faqat rasm fayllari (JPG, PNG, WEBP)')
  if (file.size > 2 * 1024 * 1024) return (photoError.value = 'Rasm hajmi 2 MB dan oshmasin')
  const reader = new FileReader()
  reader.onload = () => (form.photo = reader.result)
  reader.readAsDataURL(file)
}
function onPhotoChange(event) {
  readPhoto(event.target.files?.[0])
  event.target.value = ''
}
const dragging = ref(false)
function onPhotoDrop(event) {
  dragging.value = false
  readPhoto(event.dataTransfer?.files?.[0])
}

async function submit() {
  submitted.value = true
  errors.value = validateEmployee(form)
  const first = Object.keys(errors.value)[0]
  if (first) {
    await nextTick()
    const el = formEl.value?.querySelector(`[name="${first}"]`)
    el?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    el?.focus({ preventScroll: true })
    return
  }
  const clean = (v) => String(v || '').trim().replace(/\s+/g, ' ')
  const data = {
    ...form,
    firstName: clean(form.firstName),
    lastName: clean(form.lastName),
    middleName: clean(form.middleName),
    fullName: fullName.value,
    telegram: telegramHandle(form.telegram),
    previousWork: String(form.previousWork || '').trim(),
    address: String(form.address || '').trim(),
    expectedSalary: form.expectedSalary === '' ? null : Number(form.expectedSalary),
    positionId: Number(form.positionId),
    departmentId: Number(form.departmentId),
  }
  emit('submit', data, { startTraining: !isEdit.value && form.status === 'Yangi' && startTraining.value })
}

const maxHire = todayISO().slice(0, 4) * 1 + 1 + '-12-31'
</script>

<template>
  <Modal
    :open="open"
    size="xl"
    :persistent="saving"
    :title="isEdit ? 'Xodim ma’lumotlarini tahrirlash' : 'Yangi xodim qo‘shish'"
    :subtitle="isEdit ? employee.fullName : 'Xodim haqidagi ma’lumotlarni to‘ldiring'"
    @close="!saving && emit('close')"
  >
    <form id="employee-form" ref="formEl" class="emp-form" novalidate @submit.prevent="submit">
      <!-- Yuqori: rasm va qisqa ko‘rinish -->
      <div class="flex flex-col gap-5 rounded-2xl border border-primary-100 bg-gradient-to-br from-primary-50/80 via-white to-white p-4 sm:flex-row sm:items-center sm:p-5">
        <label
          :class="[
            'group relative grid h-24 w-24 shrink-0 cursor-pointer place-items-center self-center overflow-hidden rounded-2xl border-2 border-dashed bg-white transition-all duration-200 sm:self-auto',
            dragging ? 'scale-105 border-primary-500 bg-primary-50' : 'border-primary-200 hover:border-primary-400',
          ]"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onPhotoDrop"
        >
          <img v-if="form.photo" :src="form.photo" alt="Xodim rasmi" class="h-full w-full object-cover" />
          <span v-else class="flex flex-col items-center gap-1 text-primary-600">
            <ImagePlus class="h-6 w-6 transition-transform duration-200 group-hover:scale-110" />
            <span class="text-[11px] font-medium">Rasm</span>
          </span>
          <span v-if="form.photo" class="absolute inset-0 grid place-items-center bg-slate-900/40 text-xs font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">Almashtirish</span>
          <input type="file" accept="image/*" class="sr-only" aria-label="Xodim rasmi" @change="onPhotoChange" />
        </label>
        <div class="min-w-0 flex-1 text-center sm:text-left">
          <p class="text-xs font-medium uppercase tracking-wider text-primary-600">Rasm <span class="normal-case tracking-normal text-muted">— majburiy emas</span></p>
          <p class="mt-1 truncate text-lg font-semibold text-ink">{{ fullName || 'Yangi xodim' }}</p>
          <p :class="['mt-0.5 text-xs', photoError ? 'text-red-600' : 'text-muted']">{{ photoError || 'JPG yoki PNG, 2 MB gacha. Rasmni shu yerga sudrab tashlash ham mumkin.' }}</p>
          <Button v-if="form.photo" class="mt-2" size="sm" variant="ghost" :icon="Trash2" @click="form.photo = null">Rasmni olib tashlash</Button>
        </div>
        <div class="shrink-0 text-center sm:text-right">
          <p class="text-xs text-muted">Majburiy maydonlar</p>
          <p class="mt-0.5 text-lg font-semibold tabular-nums text-ink">{{ filled }}/{{ required.length }}</p>
          <div class="mx-auto mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-slate-100 sm:ml-auto sm:mr-0">
            <div class="h-full rounded-full bg-primary-600 transition-[width] duration-300" :style="{ width: `${(filled / required.length) * 100}%` }" />
          </div>
        </div>
      </div>

      <!-- Shaxsiy ma'lumotlar -->
      <fieldset class="form-section">
        <legend class="form-section-title"><UserRound class="h-4 w-4" /> Shaxsiy ma’lumotlar</legend>
        <div class="grid gap-4 sm:grid-cols-3">
          <FormField label="Ism" for="emp-first" :error="errors.firstName" required>
            <input id="emp-first" v-model="form.firstName" name="firstName" autocomplete="given-name" placeholder="Anvar" :class="['form-input', errors.firstName && 'has-error']" />
          </FormField>
          <FormField label="Familiya" for="emp-last" :error="errors.lastName" required>
            <input id="emp-last" v-model="form.lastName" name="lastName" autocomplete="family-name" placeholder="Aliyev" :class="['form-input', errors.lastName && 'has-error']" />
          </FormField>
          <FormField label="Otasining ismi" for="emp-middle" :error="errors.middleName">
            <input id="emp-middle" v-model="form.middleName" name="middleName" placeholder="Valiyevich" :class="['form-input', errors.middleName && 'has-error']" />
          </FormField>
        </div>
        <div class="mt-4 grid gap-4 sm:grid-cols-[220px_minmax(0,1fr)]">
          <FormField label="Jinsi">
            <div class="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Jinsi">
              <label
                v-for="g in GENDERS"
                :key="g"
                :class="[
                  'flex h-10 cursor-pointer items-center justify-center rounded-lg border text-sm font-medium transition-all duration-150 focus-within:ring-4 focus-within:ring-primary-500/15',
                  form.gender === g ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm' : 'border-line text-slate-600 hover:border-slate-300 hover:bg-slate-50',
                ]"
              >
                <input v-model="form.gender" type="radio" name="gender" :value="g" class="sr-only" />{{ g }}
              </label>
            </div>
          </FormField>
          <FormField label="Yashash manzili" for="emp-address">
            <input id="emp-address" v-model="form.address" name="address" placeholder="Toshkent sh., Chilonzor tumani, ..." class="form-input" />
          </FormField>
        </div>
      </fieldset>

      <!-- Aloqa -->
      <fieldset class="form-section">
        <legend class="form-section-title"><Phone class="h-4 w-4" /> Aloqa</legend>
        <div class="grid gap-4 sm:grid-cols-2">
          <FormField label="Telefon raqami" for="emp-phone" :error="errors.phone" required>
            <input id="emp-phone" :value="form.phone" name="phone" type="tel" inputmode="tel" placeholder="+998 90 123 45 67" :class="['form-input tabular-nums', errors.phone && 'has-error']" @input="onPhoneInput" />
          </FormField>
          <FormField label="Telegram username" for="emp-tg" :error="errors.telegram" hint="Masalan: @anvar_aliyev">
            <div class="relative">
              <AtSign class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              <input
                id="emp-tg"
                :value="form.telegram.replace(/^@/, '')"
                name="telegram"
                autocapitalize="none"
                spellcheck="false"
                placeholder="username"
                :class="['form-input pl-9', errors.telegram && 'has-error']"
                @input="form.telegram = $event.target.value.trim() ? '@' + $event.target.value.trim().replace(/^@+/, '') : ''"
              />
            </div>
          </FormField>
        </div>
      </fieldset>

      <!-- Tajriba va kutuvlar -->
      <fieldset class="form-section">
        <legend class="form-section-title"><Briefcase class="h-4 w-4" /> Tajriba va kutuvlar</legend>
        <FormField label="Qayerda ishlagan" for="emp-work" hint="Oldingi ish joylari, lavozim va muddati">
          <textarea id="emp-work" v-model="form.previousWork" name="previousWork" rows="2" class="form-input" placeholder="Masalan: Uzum Market — operator, 1 yil" />
        </FormField>

        <div class="mt-4">
          <p class="form-label flex items-center gap-1.5"><MonitorSmartphone class="h-4 w-4 text-muted" /> Kompyuter savodxonligi darajasi</p>
          <div class="grid grid-cols-2 gap-2 lg:grid-cols-4" role="radiogroup" aria-label="Kompyuter savodxonligi">
            <label
              v-for="s in COMPUTER_SKILLS"
              :key="s.value"
              :class="[
                'cursor-pointer rounded-xl border p-3 transition-all duration-150 focus-within:ring-4 focus-within:ring-primary-500/15',
                form.computerSkill === s.value ? 'border-primary-500 bg-primary-50 shadow-sm' : 'border-line hover:-translate-y-px hover:border-slate-300 hover:bg-slate-50',
              ]"
            >
              <input v-model="form.computerSkill" type="radio" name="computerSkill" :value="s.value" class="sr-only" />
              <span class="flex gap-1" aria-hidden="true">
                <span v-for="i in 4" :key="i" :class="['h-1.5 flex-1 rounded-full', i <= s.level ? (form.computerSkill === s.value ? 'bg-primary-600' : 'bg-primary-300') : 'bg-slate-200']" />
              </span>
              <span :class="['mt-2 block text-sm font-semibold', form.computerSkill === s.value ? 'text-primary-700' : 'text-ink']">{{ s.value }}</span>
              <span class="block text-[11px] leading-snug text-muted">{{ s.hint }}</span>
            </label>
          </div>
        </div>

        <FormField class="mt-4 sm:max-w-sm" label="Qancha oylik kutyapti" for="emp-salary" :error="errors.expectedSalary">
          <div class="relative">
            <Wallet class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              id="emp-salary"
              :value="salaryText"
              name="expectedSalary"
              inputmode="numeric"
              placeholder="5 000 000"
              :class="['form-input pl-9 pr-14 tabular-nums', errors.expectedSalary && 'has-error']"
              @input="onSalaryInput"
            />
            <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted">so‘m</span>
          </div>
        </FormField>
      </fieldset>

      <!-- Ish ma'lumotlari -->
      <fieldset class="form-section">
        <legend class="form-section-title"><Building2 class="h-4 w-4" /> Ish ma’lumotlari</legend>
        <div class="grid gap-4 sm:grid-cols-2">
          <FormField label="Bo‘lim" for="emp-dept" :error="errors.departmentId" required>
            <Select id="emp-dept" v-model="form.departmentId" name="departmentId" :options="catalog.departmentOptions" placeholder="Bo‘limni tanlang" :error="errors.departmentId" />
          </FormField>
          <FormField label="Lavozim" for="emp-pos" :error="errors.positionId" required>
            <Select id="emp-pos" v-model="form.positionId" name="positionId" :options="catalog.positionOptions" placeholder="Lavozimni tanlang" :error="errors.positionId" />
          </FormField>
          <FormField label="Ishga qabul qilingan sana" for="emp-hire" :error="errors.hireDate" required>
            <input id="emp-hire" v-model="form.hireDate" name="hireDate" type="date" :max="maxHire" :class="['form-input', errors.hireDate && 'has-error']" />
          </FormField>
          <FormField label="Status" :error="errors.status" required>
            <div class="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Status">
              <label
                v-for="st in EMPLOYEE_STATUSES"
                :key="st"
                :class="[
                  'flex h-10 cursor-pointer items-center justify-center rounded-lg border text-[13px] font-medium transition-all duration-150 focus-within:ring-4 focus-within:ring-primary-500/15',
                  form.status === st
                    ? st === 'Faol emas' ? 'border-slate-400 bg-slate-100 text-slate-700' : st === 'Faol' ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-line text-slate-600 hover:bg-slate-50',
                ]"
              >
                <input v-model="form.status" type="radio" name="status" :value="st" class="sr-only" />{{ st }}
              </label>
            </div>
          </FormField>
        </div>

        <div v-if="!isEdit && form.status === 'Yangi'" class="mt-4 flex items-center justify-between gap-4 rounded-xl border border-primary-100 bg-primary-50/50 px-4 py-3">
          <div>
            <p class="text-sm font-medium text-ink">7 kunlik o‘quv dasturini boshlash</p>
            <p class="text-xs text-muted">Xodim “Darslar” bo‘limida ko‘rinadi, 7-kundan so‘ng testga yuboriladi</p>
          </div>
          <Switch v-model="startTraining" label="O‘quv dasturini boshlash" />
        </div>
      </fieldset>

      <p class="mt-5 text-xs text-muted"><span class="text-red-500">*</span> — majburiy maydonlar</p>
    </form>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button type="submit" form="employee-form" :loading="saving">{{ saving ? 'Saqlanmoqda...' : isEdit ? 'O‘zgarishlarni saqlash' : 'Xodimni qo‘shish' }}</Button>
    </template>
  </Modal>
</template>

<style scoped>
.form-section {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid theme('colors.line');
}
/* legend fieldset chegarasida qolmasligi uchun float; keyingi elementlar uning ostidan boshlanadi */
.form-section > :not(legend) {
  clear: both;
}
.form-section-title {
  float: left;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-right: 0.75rem;
  margin-bottom: 1rem;
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: theme('colors.primary.700');
}
</style>
