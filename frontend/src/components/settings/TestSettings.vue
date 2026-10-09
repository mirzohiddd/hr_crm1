<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ClipboardCheck, Save } from 'lucide-vue-next'
import SettingsSection from './SettingsSection.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import Switch from '@/components/ui/Switch.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import { useTestsStore } from '@/stores/tests'
import { useToast } from '@/composables/useToast'

const store = useTestsStore()
const toast = useToast()

const form = reactive({})
const errors = ref({})
const saving = ref(false)
const ready = ref(false)

onMounted(async () => {
  await store.fetchAll()
  reset()
  ready.value = true
})

function reset() {
  Object.assign(form, JSON.parse(JSON.stringify(store.settings || {})))
  errors.value = {}
}
const dirty = computed(() => ready.value && JSON.stringify(form) !== JSON.stringify(store.settings))

const toggles = [
  { key: 'autoAssign', title: 'Testni avtomatik yuborish', text: '7-kun bajarilganda xodim lavozimiga mos test avtomatik yuboriladi' },
  { key: 'activateOnPass', title: 'O‘tganda “Faol” holatiga o‘tkazish', text: 'Testdan o‘tgan “Yangi” xodimning holati avtomatik “Faol” bo‘ladi' },
  { key: 'shuffleQuestions', title: 'Savollarni aralashtirish', text: 'Har bir urinishda savollar tartibi o‘zgaradi' },
  { key: 'shuffleOptions', title: 'Variantlarni aralashtirish', text: 'Javob variantlari tartibi o‘zgaradi' },
]

async function save() {
  const e = {}
  const p = Number(form.passPercent)
  if (!Number.isInteger(p) || p < 1 || p > 100) e.passPercent = '1 dan 100 gacha'
  const a = Number(form.maxAttempts)
  if (!Number.isInteger(a) || a < 1 || a > 10) e.maxAttempts = '1 dan 10 gacha'
  errors.value = e
  if (Object.keys(e).length) return
  saving.value = true
  try {
    await store.saveSettings({ ...form, passPercent: p, maxAttempts: a })
    reset()
    toast.success('Test sozlamalari saqlandi')
  } catch (err) {
    toast.error('Saqlab bo‘lmadi', err.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form novalidate @submit.prevent="save">
    <SettingsSection :icon="ClipboardCheck" title="Test sozlamalari" subtitle="O‘tish foizi, urinishlar soni va avtomatik yuborish">
      <template #actions>
        <RouterLink :to="{ path: '/tests', query: { tab: 'bank' } }" class="text-sm font-medium text-primary-600 hover:underline">Testlar bazasi →</RouterLink>
      </template>

      <LoadingState v-if="!ready" variant="block" class="m-5" />
      <template v-else>
        <div class="grid gap-4 p-5 sm:grid-cols-2">
          <FormField label="O‘tish chegarasi" for="ts-pass" :error="errors.passPercent" hint="Shu foiz va undan yuqori — “Testdan o‘tdi”, past — “Testdan o‘tmadi”. Barcha testlarga qo‘llanadi.">
            <div class="relative">
              <input id="ts-pass" v-model.number="form.passPercent" type="number" min="1" max="100" class="form-input pr-8 tabular-nums" :class="errors.passPercent && 'has-error'" />
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted">%</span>
            </div>
          </FormField>
          <FormField label="Urinishlar soni" for="ts-att" :error="errors.maxAttempts" hint="O‘tmagan xodim necha marta qayta topshira oladi (jami)">
            <input id="ts-att" v-model.number="form.maxAttempts" type="number" min="1" max="10" class="form-input tabular-nums" :class="errors.maxAttempts && 'has-error'" />
          </FormField>
        </div>
        <ul class="divide-y divide-line border-t border-line">
          <li v-for="t in toggles" :key="t.key" class="flex items-center justify-between gap-4 px-5 py-3.5">
            <div class="min-w-0">
              <p class="text-sm font-medium text-ink">{{ t.title }}</p>
              <p class="text-sm text-muted">{{ t.text }}</p>
            </div>
            <Switch v-model="form[t.key]" :label="t.title" />
          </li>
        </ul>
      </template>

      <template #footer>
        <Button variant="ghost" :disabled="!dirty || saving" @click="reset">Bekor qilish</Button>
        <Button type="submit" :icon="Save" :loading="saving" :disabled="!dirty">Saqlash</Button>
      </template>
    </SettingsSection>
  </form>
</template>
