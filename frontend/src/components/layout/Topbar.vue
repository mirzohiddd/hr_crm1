<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, BookOpenCheck, CalendarClock, CheckCheck, ChevronDown, ClipboardCheck, FileText, LogOut, Menu, PhoneMissed, Search, Settings, UserRoundSearch } from 'lucide-vue-next'
import Avatar from '@/components/ui/Avatar.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useAuthStore } from '@/stores/auth'
import { useCandidatesStore } from '@/stores/candidates'
import { useEmployeesStore } from '@/stores/employees'
import { useTestsStore } from '@/stores/tests'
import { useDocumentsStore } from '@/stores/documents'
import { useTrainingsStore, trainingProgress } from '@/stores/trainings'
import { useCatalogStore } from '@/stores/catalog'
import { useClickOutside } from '@/composables/useClickOutside'
import { roleLabel } from '@/constants'
import { normalizeText, onlyDigits } from '@/utils/format'
import { todayISO } from '@/utils/date'

const emit = defineEmits(['toggle-sidebar'])
const router = useRouter()
const auth = useAuthStore()
const candidates = useCandidatesStore()
const employees = useEmployeesStore()
const tests = useTestsStore()
const documents = useDocumentsStore()
const trainings = useTrainingsStore()
const catalog = useCatalogStore()

onMounted(() => {
  employees.fetchAll()
  documents.fetchAll()
  trainings.fetchAll()
})

// ---------- Qidiruv (xodimlar va nomzodlar) ----------
const query = ref('')
const searchInput = ref(null)
const searchRef = ref(null)
const searchOpen = ref(false)

const results = computed(() => {
  const q = normalizeText(query.value)
  if (q.length < 2) return { employees: [], candidates: [] }
  const digits = onlyDigits(query.value)
  const match = (x) => normalizeText(x.fullName).includes(q) || (digits.length >= 3 && onlyDigits(x.phone).includes(digits))
  return {
    employees: employees.items.filter(match).slice(0, 5),
    candidates: candidates.items.filter(match).slice(0, 5),
  }
})
const hasResults = computed(() => results.value.employees.length + results.value.candidates.length > 0)

watch(query, (q) => (searchOpen.value = q.trim().length >= 2))

function go(path) {
  searchOpen.value = false
  query.value = ''
  searchInput.value?.blur()
  router.push(path)
}

function submitSearch() {
  const q = query.value.trim()
  if (results.value.employees.length === 1 && !results.value.candidates.length) return go(`/employees/${results.value.employees[0].id}`)
  go({ path: '/employees', query: q ? { q } : {} })
}

function onKeydown(event) {
  const tag = document.activeElement?.tagName
  if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) {
    event.preventDefault()
    searchInput.value?.focus()
  }
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

// ---------- Bildirishnomalar (jonli ma'lumotlardan) ----------
const today = todayISO()
const notifications = computed(() => {
  const list = []
  const newCount = candidates.counts['Yangi'] || 0
  if (newCount) list.push({ key: `c${newCount}`, icon: UserRoundSearch, tone: 'bg-primary-50 text-primary-600', title: 'Yangi nomzodlar', text: `${newCount} ta nomzod bog‘lanishni kutmoqda`, to: '/candidates' })
  const missed = candidates.counts['Bog‘lanilmadi'] || 0
  if (missed) list.push({ key: `m${missed}`, icon: PhoneMissed, tone: 'bg-orange-50 text-orange-600', title: 'Qayta qo‘ng‘iroq qilish kerak', text: `${missed} ta nomzod bilan bog‘lanib bo‘lmadi`, to: '/candidates' })
  const interviews = candidates.interviewsToday.length
  if (interviews) list.push({ key: `i${interviews}`, icon: CalendarClock, tone: 'bg-amber-50 text-amber-600', title: 'Bugungi suhbatlar', text: `Bugun ${interviews} ta suhbat rejalashtirilgan`, to: '/candidates' })
  const behind = trainings.items.filter((t) => {
    const p = trainingProgress(t)
    return !p.finished && p.plannedDate(p.nextDay) < today
  }).length
  if (behind) list.push({ key: `t${behind}`, icon: BookOpenCheck, tone: 'bg-sky-50 text-sky-600', title: 'Darslar ortda qolmoqda', text: `${behind} ta xodimning darsi rejadan ortda`, to: '/lessons' })
  const pendingTests = tests.stats.pending
  if (pendingTests) list.push({ key: `r${pendingTests}`, icon: ClipboardCheck, tone: 'bg-emerald-50 text-emerald-600', title: 'Test topshirish kutilmoqda', text: `${pendingTests} ta xodim testni hali topshirmagan`, to: '/tests' })
  const pendingDocs = documents.stats.pending
  if (pendingDocs) list.push({ key: `d${pendingDocs}`, icon: FileText, tone: 'bg-amber-50 text-amber-600', title: 'Hujjatlar tekshiruvda', text: `${pendingDocs} ta hujjat tasdiqlanishi kerak`, to: '/documents' })
  return list
})

const SEEN_KEY = 'hr-crm:notif-seen'
const seen = ref('')
try {
  seen.value = localStorage.getItem(SEEN_KEY) || ''
} catch {
  /* e'tiborsiz */
}
const signature = computed(() => notifications.value.map((n) => n.key).join('|'))
const unread = computed(() => (signature.value && signature.value !== seen.value ? notifications.value.length : 0))

function markAllRead() {
  seen.value = signature.value
  try {
    localStorage.setItem(SEEN_KEY, seen.value)
  } catch {
    /* e'tiborsiz */
  }
}

const notifOpen = ref(false)
const notifRef = ref(null)
function openNotification(n) {
  notifOpen.value = false
  router.push(n.to)
}

// ---------- Profil ----------
const profileOpen = ref(false)
const profileRef = ref(null)

useClickOutside(notifRef, () => (notifOpen.value = false))
useClickOutside(profileRef, () => (profileOpen.value = false))
useClickOutside(searchRef, () => (searchOpen.value = false))

function onEscape(event) {
  if (event.key === 'Escape') {
    notifOpen.value = false
    profileOpen.value = false
    searchOpen.value = false
  }
}

function logout() {
  profileOpen.value = false
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <header class="sticky top-0 z-30 h-16 border-b border-line/80 bg-white/90 backdrop-blur-md supports-[backdrop-filter]:bg-white/75" @keydown="onEscape">
    <div class="flex h-full items-center gap-3 px-4 sm:px-6 lg:px-8">
      <button class="icon-btn -ml-1 md:hidden" aria-label="Menyuni ochish" @click="emit('toggle-sidebar')">
        <Menu class="h-5 w-5" />
      </button>

      <RouterLink to="/dashboard" class="text-ink sm:hidden"><BrandLogo size="sm" /></RouterLink>

      <div ref="searchRef" class="relative hidden max-w-md flex-1 sm:block">
        <form role="search" @submit.prevent="submitSearch">
          <label class="relative block">
            <span class="sr-only">Xodim yoki nomzod qidirish</span>
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              ref="searchInput"
              v-model="query"
              type="search"
              placeholder="Xodim yoki nomzod qidirish..."
              autocomplete="off"
              class="form-input border-transparent bg-slate-100/70 pl-9 pr-10 focus:bg-white"
              @focus="searchOpen = query.trim().length >= 2"
            />
            <kbd class="pointer-events-none absolute right-2.5 top-1/2 hidden -translate-y-1/2 rounded border border-line bg-white px-1.5 text-[11px] leading-5 text-muted lg:block">/</kbd>
          </label>
        </form>

        <Transition name="dropdown">
          <div v-if="searchOpen" class="absolute inset-x-0 z-40 mt-2 overflow-hidden rounded-xl border border-line bg-white shadow-pop">
            <p v-if="!hasResults" class="px-4 py-6 text-center text-sm text-muted">Hech narsa topilmadi</p>
            <template v-else>
              <div v-if="results.employees.length" class="py-1.5">
                <p class="px-4 py-1 text-[11px] font-medium uppercase tracking-wider text-slate-400">Xodimlar</p>
                <button v-for="e in results.employees" :key="`e${e.id}`" class="flex w-full items-center gap-3 px-4 py-2 text-left hover:bg-slate-50" @click="go(`/employees/${e.id}`)">
                  <Avatar :name="e.fullName" :src="e.photo" size="xs" />
                  <span class="min-w-0 flex-1 truncate text-sm text-ink">{{ e.fullName }}</span>
                  <span class="text-xs text-muted">{{ catalog.positionName(e.positionId) }}</span>
                </button>
              </div>
              <div v-if="results.candidates.length" class="border-t border-line py-1.5">
                <p class="px-4 py-1 text-[11px] font-medium uppercase tracking-wider text-slate-400">Nomzodlar</p>
                <button v-for="c in results.candidates" :key="`c${c.id}`" class="flex w-full items-center gap-3 px-4 py-2 text-left hover:bg-slate-50" @click="go({ path: '/candidates', query: { id: c.id } })">
                  <Avatar :name="c.fullName" size="xs" />
                  <span class="min-w-0 flex-1 truncate text-sm text-ink">{{ c.fullName }}</span>
                  <StatusBadge :status="c.status" size="sm" />
                </button>
              </div>
            </template>
          </div>
        </Transition>
      </div>

      <div class="ml-auto flex items-center gap-1 sm:gap-2">
        <RouterLink to="/employees" class="icon-btn sm:hidden" aria-label="Xodim qidirish">
          <Search class="h-5 w-5" />
        </RouterLink>

        <!-- Bildirishnomalar -->
        <div ref="notifRef" class="relative">
          <button
            class="icon-btn"
            :aria-expanded="notifOpen"
            aria-haspopup="true"
            :aria-label="`Bildirishnomalar${unread ? `, ${unread} ta yangi` : ''}`"
            @click="notifOpen = !notifOpen; profileOpen = false"
          >
            <Bell class="h-5 w-5" />
            <span v-if="unread" class="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary-600 ring-2 ring-white" />
          </button>

          <Transition name="dropdown">
            <div
              v-if="notifOpen"
              class="absolute right-0 z-40 mt-2 w-[360px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-line bg-white shadow-pop"
              role="menu"
            >
              <div class="flex items-center justify-between border-b border-line px-4 py-3">
                <p class="font-semibold text-ink">Bildirishnomalar</p>
                <button
                  v-if="unread"
                  class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-primary-600 hover:bg-primary-50"
                  @click="markAllRead"
                >
                  <CheckCheck class="h-3.5 w-3.5" /> O‘qildi deb belgilash
                </button>
              </div>
              <p v-if="!notifications.length" class="px-4 py-8 text-center text-sm text-muted">Hozircha yangi bildirishnoma yo‘q</p>
              <ul v-else class="max-h-[360px] divide-y divide-line overflow-y-auto">
                <li v-for="n in notifications" :key="n.key">
                  <button class="flex w-full gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50" role="menuitem" @click="openNotification(n)">
                    <span :class="['grid h-9 w-9 shrink-0 place-items-center rounded-lg', n.tone]">
                      <component :is="n.icon" class="h-4 w-4" />
                    </span>
                    <span class="min-w-0 flex-1">
                      <span class="flex items-center gap-2">
                        <span :class="['truncate text-sm', unread ? 'font-medium text-ink' : 'text-slate-600']">{{ n.title }}</span>
                        <span v-if="unread" class="h-1.5 w-1.5 shrink-0 rounded-full bg-primary-600" />
                      </span>
                      <span class="mt-0.5 block text-[13px] leading-snug text-muted">{{ n.text }}</span>
                    </span>
                  </button>
                </li>
              </ul>
            </div>
          </Transition>
        </div>

        <!-- Profil -->
        <div v-if="auth.user" ref="profileRef" class="relative">
          <button
            class="flex items-center gap-2.5 rounded-lg p-1 pr-1.5 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/15"
            :aria-expanded="profileOpen"
            aria-haspopup="true"
            @click="profileOpen = !profileOpen; notifOpen = false"
          >
            <Avatar :name="auth.user.fullName" size="sm" />
            <span class="hidden text-left md:block">
              <span class="block max-w-[160px] truncate text-sm font-medium leading-tight text-ink">{{ auth.user.fullName }}</span>
              <span class="block text-xs leading-tight text-muted">{{ roleLabel(auth.user.role) }}</span>
            </span>
            <ChevronDown class="hidden h-4 w-4 text-muted md:block" />
          </button>

          <Transition name="dropdown">
            <div v-if="profileOpen" class="absolute right-0 z-40 mt-2 w-64 overflow-hidden rounded-xl border border-line bg-white shadow-pop" role="menu">
              <div class="border-b border-line px-4 py-3">
                <p class="truncate font-medium text-ink">{{ auth.user.fullName }}</p>
                <p class="truncate text-xs text-muted">{{ auth.user.login }} · {{ roleLabel(auth.user.role) }}</p>
              </div>
              <div class="p-1.5">
                <RouterLink
                  :to="{ path: '/settings', query: { tab: 'profile' } }"
                  class="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-ink hover:bg-slate-50"
                  role="menuitem"
                  @click="profileOpen = false"
                >
                  <Settings class="h-4 w-4 text-muted" /> Profil va parol
                </RouterLink>
                <button class="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-red-600 hover:bg-red-50" role="menuitem" @click="logout">
                  <LogOut class="h-4 w-4" /> Chiqish
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </header>
</template>
