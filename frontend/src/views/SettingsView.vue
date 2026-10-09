<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpenCheck, Briefcase, Building2, ClipboardCheck, Database, RotateCcw, ShieldCheck, UserRound } from 'lucide-vue-next'
import PageHeader from '@/components/layout/PageHeader.vue'
import Button from '@/components/ui/Button.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SettingsSection from '@/components/settings/SettingsSection.vue'
import ProfileSettings from '@/components/settings/ProfileSettings.vue'
import CatalogSettings from '@/components/settings/CatalogSettings.vue'
import LessonsSettings from '@/components/settings/LessonsSettings.vue'
import TestSettings from '@/components/settings/TestSettings.vue'
import UsersSettings from '@/components/settings/UsersSettings.vue'
import { useAuthStore } from '@/stores/auth'
import { USE_MOCK } from '@/api/client'
import { resetMockDb } from '@/api/mockDb'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const tabs = computed(() => [
  { value: 'positions', label: 'Lavozimlar', icon: Briefcase },
  { value: 'departments', label: 'Bo‘limlar', icon: Building2 },
  { value: 'lessons', label: 'Darslar', icon: BookOpenCheck },
  { value: 'tests', label: 'Test sozlamalari', icon: ClipboardCheck },
  ...(auth.isAdmin ? [{ value: 'users', label: 'Foydalanuvchilar', icon: ShieldCheck }] : []),
  { value: 'profile', label: 'Profil va parol', icon: UserRound },
  ...(USE_MOCK && auth.isAdmin ? [{ value: 'system', label: 'Tizim', icon: Database }] : []),
])

const pick = (t) => (tabs.value.some((x) => x.value === t) ? t : 'positions')
const tab = ref(pick(route.query.tab))
watch(() => route.query.tab, (t) => (tab.value = pick(t)))
function select(t) {
  tab.value = t
  router.replace({ query: { tab: t } })
}

// ---------- Demo ma'lumotlarni tiklash ----------
const resetOpen = ref(false)
const resetting = ref(false)
async function resetDemo() {
  resetting.value = true
  await resetMockDb()
  auth.logout()
  window.location.href = '/login'
}
</script>

<template>
  <div>
    <PageHeader title="Sozlamalar" subtitle="Lavozimlar, bo‘limlar, darslar, testlar va foydalanuvchilar" />

    <div class="grid gap-6 lg:grid-cols-[220px_minmax(0,1fr)]">
      <!-- Bo‘limlar menyusi -->
      <nav class="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0 lg:overflow-visible" aria-label="Sozlamalar bo‘limlari">
        <ul class="flex gap-1 lg:sticky lg:top-24 lg:flex-col">
          <li v-for="t in tabs" :key="t.value" class="shrink-0">
            <button
              :class="[
                'flex h-10 w-full items-center gap-2.5 whitespace-nowrap rounded-lg px-3 text-sm font-medium transition-colors',
                tab === t.value ? 'bg-primary-50 text-primary-700' : 'text-muted hover:bg-white hover:text-ink',
              ]"
              :aria-current="tab === t.value ? 'page' : undefined"
              @click="select(t.value)"
            >
              <component :is="t.icon" class="h-4 w-4 shrink-0" />{{ t.label }}
            </button>
          </li>
        </ul>
      </nav>

      <div class="min-w-0">
        <CatalogSettings v-if="tab === 'positions'" key="positions" kind="positions" />
        <CatalogSettings v-else-if="tab === 'departments'" key="departments" kind="departments" />
        <LessonsSettings v-else-if="tab === 'lessons'" />
        <TestSettings v-else-if="tab === 'tests'" />
        <UsersSettings v-else-if="tab === 'users'" />
        <ProfileSettings v-else-if="tab === 'profile'" />
        <SettingsSection v-else-if="tab === 'system'" :icon="Database" title="Tizim" subtitle="Demo (mock) rejim ma’lumotlari">
          <div class="space-y-3 p-5 text-sm text-slate-600">
            <p>Backend ulanmagan: barcha ma’lumotlar shu brauzerda saqlanmoqda (localStorage, fayllar — IndexedDB). Boshqa brauzer yoki qurilmada ma’lumotlar ko‘rinmaydi.</p>
            <p>Haqiqiy foydalanish uchun <code class="rounded bg-slate-100 px-1.5 py-0.5 text-xs">.env</code> faylda <code class="rounded bg-slate-100 px-1.5 py-0.5 text-xs">VITE_API_URL</code> ni ko‘rsating.</p>
          </div>
          <template #footer>
            <Button variant="danger-outline" :icon="RotateCcw" @click="resetOpen = true">Demo ma’lumotlarni tiklash</Button>
          </template>
        </SettingsSection>
      </div>
    </div>

    <ConfirmDialog
      :open="resetOpen"
      title="Demo ma’lumotlar tiklansinmi?"
      message="Barcha nomzodlar, xodimlar, darslar progressi, test natijalari, hujjatlar va foydalanuvchilar boshlang‘ich holatga qaytadi. Siz tizimdan chiqasiz."
      confirm-text="Tiklash"
      :loading="resetting"
      @confirm="resetDemo"
      @close="resetOpen = false"
    />
  </div>
</template>
