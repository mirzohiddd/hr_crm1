<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Pencil, Plus, ShieldCheck, Trash2 } from 'lucide-vue-next'
import SettingsSection from './SettingsSection.vue'
import Button from '@/components/ui/Button.vue'
import Modal from '@/components/ui/Modal.vue'
import FormField from '@/components/ui/FormField.vue'
import Select from '@/components/ui/Select.vue'
import Switch from '@/components/ui/Switch.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { USER_ROLES, roleLabel } from '@/constants'
import { validateUser } from '@/utils/validators'
import { formatPhoneInput } from '@/utils/format'
import { formatDateTime } from '@/utils/date'

const store = useUsersStore()
const auth = useAuthStore()
const toast = useToast()

onMounted(() => store.fetchAll())

const rows = computed(() => [...store.items].sort((a, b) => a.fullName.localeCompare(b.fullName)))
const activeAdmins = computed(() => store.items.filter((u) => u.role === 'admin' && u.active).length)
const isSelf = (u) => u?.id === auth.user?.id

// ---------- Forma ----------
const formOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = reactive({})
const errors = ref({})

function openForm(u = null) {
  editing.value = u
  Object.assign(form, {
    fullName: u?.fullName || '',
    login: u?.login || '',
    password: '',
    role: u?.role || 'hr',
    email: u?.email || '',
    phone: u?.phone || '+998 ',
    active: u?.active ?? true,
  })
  errors.value = {}
  formOpen.value = true
}

// Oxirgi faol administratorni bloklash yoki rolini tushirishga yo‘l qo‘ymaymiz
const lastAdmin = computed(() => editing.value?.role === 'admin' && editing.value?.active && activeAdmins.value <= 1)

async function submit() {
  errors.value = validateUser(form, { isNew: !editing.value })
  if (Object.keys(errors.value).length) return
  if (lastAdmin.value && (form.role !== 'admin' || !form.active)) {
    return toast.error('Saqlab bo‘lmaydi', 'Tizimda kamida bitta faol administrator qolishi kerak')
  }
  const payload = { ...form, fullName: form.fullName.trim(), login: form.login.trim(), email: form.email.trim() }
  if (!payload.password) delete payload.password
  saving.value = true
  try {
    if (editing.value) await store.update(editing.value.id, payload)
    else await store.create(payload)
    toast.success(editing.value ? 'Foydalanuvchi saqlandi' : 'Foydalanuvchi qo‘shildi', `${payload.fullName} (${payload.login})`)
    formOpen.value = false
  } catch (err) {
    if (err.status === 409) errors.value = { login: err.message }
    else toast.error('Saqlab bo‘lmadi', err.message)
  } finally {
    saving.value = false
  }
}

// ---------- O‘chirish ----------
const deleteTarget = ref(null)
const deleting = ref(false)
function askDelete(u) {
  if (isSelf(u)) return toast.error('O‘zingizni o‘chira olmaysiz')
  if (u.role === 'admin' && u.active && activeAdmins.value <= 1) return toast.error('Oxirgi administratorni o‘chirib bo‘lmaydi')
  deleteTarget.value = u
}
async function confirmDelete() {
  deleting.value = true
  try {
    await store.remove(deleteTarget.value.id)
    toast.success('Foydalanuvchi o‘chirildi', deleteTarget.value.fullName)
    deleteTarget.value = null
  } catch (err) {
    toast.error('O‘chirib bo‘lmadi', err.message)
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <SettingsSection :icon="ShieldCheck" title="Foydalanuvchilar" subtitle="CRM’ga login va parol bilan kiradigan xodimlar">
    <template #actions>
      <Button size="sm" :icon="Plus" @click="openForm()">Foydalanuvchi qo‘shish</Button>
    </template>

    <ErrorState v-if="store.error" :message="store.error" @retry="store.fetchAll({ force: true })" />
    <LoadingState v-else-if="!store.loaded" :rows="3" />
    <ul v-else class="divide-y divide-line">
      <li v-for="u in rows" :key="u.id" class="flex items-center gap-3 px-5 py-3.5">
        <Avatar :name="u.fullName" size="md" />
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <p class="truncate font-medium text-ink">{{ u.fullName }}</p>
            <span v-if="isSelf(u)" class="rounded bg-primary-50 px-1.5 text-[11px] font-medium text-primary-700">Siz</span>
            <StatusBadge v-if="!u.active" status="Bloklangan" size="sm" />
          </div>
          <p class="truncate text-sm text-muted">
            <span class="font-medium text-slate-600">{{ u.login }}</span> · {{ roleLabel(u.role) }}
            <span class="hidden sm:inline"> · oxirgi kirish: {{ u.lastLoginAt ? formatDateTime(u.lastLoginAt) : 'hali kirmagan' }}</span>
          </p>
        </div>
        <div class="flex shrink-0 gap-0.5">
          <button class="icon-btn h-8 w-8" :aria-label="`${u.fullName}: tahrirlash`" title="Tahrirlash" @click="openForm(u)"><Pencil class="h-4 w-4" /></button>
          <button class="icon-btn h-8 w-8 hover:bg-red-50 hover:text-red-600 disabled:opacity-40" :disabled="isSelf(u)" :aria-label="`${u.fullName}: o‘chirish`" title="O‘chirish" @click="askDelete(u)">
            <Trash2 class="h-4 w-4" />
          </button>
        </div>
      </li>
    </ul>

    <Modal :open="formOpen" size="lg" :title="editing ? 'Foydalanuvchini tahrirlash' : 'Yangi foydalanuvchi'" :persistent="saving" @close="!saving && (formOpen = false)">
      <form id="user-form" class="grid gap-4 sm:grid-cols-2" novalidate autocomplete="off" @submit.prevent="submit">
        <FormField class="sm:col-span-2" label="F.I.Sh" for="u-name" :error="errors.fullName" required>
          <input id="u-name" v-model="form.fullName" class="form-input" :class="errors.fullName && 'has-error'" />
        </FormField>
        <FormField label="Login" for="u-login" :error="errors.login" required>
          <input id="u-login" v-model="form.login" class="form-input" :class="errors.login && 'has-error'" autocapitalize="none" spellcheck="false" autocomplete="off" placeholder="masalan: m.karimova" />
        </FormField>
        <FormField :label="editing ? 'Yangi parol' : 'Parol'" for="u-pass" :error="errors.password" :hint="editing ? 'O‘zgartirmaslik uchun bo‘sh qoldiring' : 'Kamida 6 belgi'" :required="!editing">
          <input id="u-pass" v-model="form.password" type="password" autocomplete="new-password" class="form-input" :class="errors.password && 'has-error'" />
        </FormField>
        <FormField label="Rol" for="u-role" :error="errors.role" :hint="form.role === 'admin' ? 'Foydalanuvchilarni boshqara oladi' : 'Foydalanuvchilar bo‘limidan tashqari hamma narsa'" required>
          <Select id="u-role" v-model="form.role" :options="USER_ROLES" :disabled="lastAdmin" />
        </FormField>
        <FormField label="Email" for="u-email" :error="errors.email">
          <input id="u-email" v-model="form.email" type="email" class="form-input" :class="errors.email && 'has-error'" />
        </FormField>
        <FormField label="Telefon" for="u-phone">
          <input id="u-phone" :value="form.phone" type="tel" class="form-input tabular-nums" @input="form.phone = formatPhoneInput($event.target.value)" />
        </FormField>
        <div class="flex items-center justify-between gap-4 rounded-lg border border-line px-4 py-3 sm:col-span-2">
          <div>
            <p class="text-sm font-medium text-ink">Kirishga ruxsat</p>
            <p class="text-xs text-muted">O‘chirilsa, foydalanuvchi tizimga kira olmaydi</p>
          </div>
          <Switch v-model="form.active" label="Kirishga ruxsat" :disabled="isSelf(editing) || lastAdmin" />
        </div>
      </form>
      <template #footer>
        <Button variant="secondary" :disabled="saving" @click="formOpen = false">Bekor qilish</Button>
        <Button type="submit" form="user-form" :loading="saving">Saqlash</Button>
      </template>
    </Modal>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Foydalanuvchini o‘chirasizmi?"
      :message="deleteTarget ? `${deleteTarget.fullName} (${deleteTarget.login}) endi tizimga kira olmaydi.` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </SettingsSection>
</template>
