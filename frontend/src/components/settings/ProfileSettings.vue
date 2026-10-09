<script setup>
import { computed, reactive, ref } from 'vue'
import { KeyRound, Save, UserRound } from 'lucide-vue-next'
import SettingsSection from './SettingsSection.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import Avatar from '@/components/ui/Avatar.vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { roleLabel } from '@/constants'
import { validatePassword, validateProfile } from '@/utils/validators'
import { formatPhoneInput } from '@/utils/format'

const auth = useAuthStore()
const toast = useToast()

const pick = () => ({ fullName: auth.user?.fullName || '', email: auth.user?.email || '', phone: auth.user?.phone || '+998 ' })
const profile = reactive(pick())
const errors = ref({})
const saving = ref(false)
const dirty = computed(() => JSON.stringify(profile) !== JSON.stringify(pick()))

async function submitProfile() {
  errors.value = validateProfile(profile)
  if (Object.keys(errors.value).length) return toast.error('Formada xatolar bor', 'Belgilangan maydonlarni to‘g‘rilang')
  saving.value = true
  try {
    await auth.updateProfile({ ...profile, fullName: profile.fullName.trim(), email: profile.email.trim() })
    toast.success('Profil saqlandi')
  } catch (e) {
    toast.error('Saqlab bo‘lmadi', e.message)
  } finally {
    saving.value = false
  }
}
function reset() {
  Object.assign(profile, pick())
  errors.value = {}
}

// ---------- Parol ----------
const pw = reactive({ current: '', password: '', confirm: '' })
const pwErrors = ref({})
const pwSaving = ref(false)
async function submitPassword() {
  const e = validatePassword(pw.password, pw.confirm)
  if (!pw.current) e.current = 'Joriy parolni kiriting'
  pwErrors.value = e
  if (Object.keys(e).length) return
  pwSaving.value = true
  try {
    await auth.changePassword(pw.current, pw.password)
    Object.assign(pw, { current: '', password: '', confirm: '' })
    toast.success('Parol o‘zgartirildi', 'Keyingi kirishda yangi paroldan foydalaning')
  } catch (err) {
    pwErrors.value = { current: err.message }
  } finally {
    pwSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <form novalidate @submit.prevent="submitProfile">
      <SettingsSection :icon="UserRound" title="Profil" subtitle="Tizimda ko‘rinadigan shaxsiy ma’lumotlar">
        <div class="p-5">
          <div class="mb-6 flex items-center gap-4">
            <Avatar :name="profile.fullName || auth.user?.fullName" size="lg" />
            <div class="min-w-0">
              <p class="truncate font-medium text-ink">{{ auth.user?.fullName }}</p>
              <p class="text-sm text-muted">Login: <span class="font-medium text-ink">{{ auth.user?.login }}</span> · {{ roleLabel(auth.user?.role) }}</p>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <FormField class="sm:col-span-2" label="F.I.Sh" for="p-name" :error="errors.fullName" required>
              <input id="p-name" v-model="profile.fullName" :class="['form-input', errors.fullName && 'has-error']" autocomplete="name" />
            </FormField>
            <FormField label="Email" for="p-email" :error="errors.email">
              <input id="p-email" v-model="profile.email" type="email" :class="['form-input', errors.email && 'has-error']" autocomplete="email" />
            </FormField>
            <FormField label="Telefon" for="p-phone" :error="errors.phone">
              <input
                id="p-phone"
                :value="profile.phone"
                type="tel"
                inputmode="tel"
                :class="['form-input tabular-nums', errors.phone && 'has-error']"
                placeholder="+998 90 123 45 67"
                @input="profile.phone = formatPhoneInput($event.target.value)"
              />
            </FormField>
          </div>
        </div>
        <template #footer>
          <Button variant="ghost" :disabled="!dirty || saving" @click="reset">Bekor qilish</Button>
          <Button type="submit" :icon="Save" :loading="saving" :disabled="!dirty">Saqlash</Button>
        </template>
      </SettingsSection>
    </form>

    <form novalidate autocomplete="off" @submit.prevent="submitPassword">
      <SettingsSection :icon="KeyRound" title="Parolni o‘zgartirish" subtitle="Kamida 6 belgi. Parolni hech kimga bermang.">
        <div class="grid gap-4 p-5 sm:grid-cols-3">
          <FormField label="Joriy parol" for="pw-cur" :error="pwErrors.current" required>
            <input id="pw-cur" v-model="pw.current" type="password" autocomplete="current-password" :class="['form-input', pwErrors.current && 'has-error']" />
          </FormField>
          <FormField label="Yangi parol" for="pw-new" :error="pwErrors.password" required>
            <input id="pw-new" v-model="pw.password" type="password" autocomplete="new-password" :class="['form-input', pwErrors.password && 'has-error']" />
          </FormField>
          <FormField label="Yangi parolni takrorlang" for="pw-conf" :error="pwErrors.confirm" required>
            <input id="pw-conf" v-model="pw.confirm" type="password" autocomplete="new-password" :class="['form-input', pwErrors.confirm && 'has-error']" />
          </FormField>
        </div>
        <template #footer>
          <Button type="submit" :icon="KeyRound" :loading="pwSaving" :disabled="!pw.current && !pw.password">Parolni yangilash</Button>
        </template>
      </SettingsSection>
    </form>
  </div>
</template>
