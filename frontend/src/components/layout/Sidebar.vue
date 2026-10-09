<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpenCheck, ChevronLeft, ClipboardCheck, FileText, LayoutDashboard, LogOut, Settings, UserRoundSearch, Users, X } from 'lucide-vue-next'
import Avatar from '@/components/ui/Avatar.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import { useAuthStore } from '@/stores/auth'
import { useCandidatesStore } from '@/stores/candidates'
import { useTestsStore } from '@/stores/tests'
import { useUiStore } from '@/stores/ui'
import { roleLabel } from '@/constants'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const candidates = useCandidatesStore()
const tests = useTestsStore()
const ui = useUiStore()

onMounted(() => {
  candidates.fetchAll()
  tests.fetchAll()
})

const menu = computed(() => [
  { to: '/dashboard', label: 'Bosh sahifa', icon: LayoutDashboard },
  { to: '/candidates', label: 'Nomzodlar', icon: UserRoundSearch, badge: candidates.counts['Yangi'] || 0 },
  { to: '/employees', label: 'Xodimlar', icon: Users },
  { to: '/lessons', label: 'Darslar', icon: BookOpenCheck },
  { to: '/tests', label: 'Testlar', icon: ClipboardCheck, badge: tests.stats.pending || 0 },
  { to: '/documents', label: 'Hujjatlar', icon: FileText },
])

const isActive = (to) => route.path === to || route.path.startsWith(`${to}/`) || route.meta.menu === to
const c = computed(() => ui.collapsed)

function logout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <!-- Mobil va planshetda ochilganda fon -->
  <Transition name="fade">
    <div
      v-if="ui.mobileOpen || ui.tabletExpanded"
      class="fixed inset-0 z-40 bg-slate-900/25 lg:hidden"
      aria-hidden="true"
      @click="ui.closeOverlays()"
    />
  </Transition>

  <aside
    :class="[
      'sidebar fixed inset-y-0 left-0 z-50 flex flex-col border-r border-line bg-white transition-[width,transform,box-shadow] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]',
      c ? 'w-[76px]' : 'w-64',
      ui.mobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0',
      ui.tabletExpanded && 'shadow-2xl',
    ]"
    :data-collapsed="c"
    aria-label="Yon menyu"
  >
    <!-- Logo -->
    <div :class="['relative flex h-16 shrink-0 items-center border-b border-line transition-[padding] duration-300', c ? 'justify-center px-0' : 'gap-3 px-5']">
      <RouterLink to="/dashboard" class="flex min-w-0 items-center gap-2.5 rounded-lg transition-transform duration-200 hover:scale-[1.02]" title="HR CRM">
        <BrandLogo size="md" :text="false" />
        <span :class="['sidebar-label text-[17px] font-semibold tracking-tight text-ink', c && 'is-hidden']">HR CRM</span>
      </RouterLink>
      <button class="icon-btn ml-auto md:hidden" aria-label="Menyuni yopish" @click="ui.mobileOpen = false">
        <X class="h-5 w-5" />
      </button>

      <!-- Ochish / yopish tugmasi -->
      <button
        class="absolute -right-3.5 top-1/2 hidden h-7 w-7 -translate-y-1/2 place-items-center rounded-full border border-line bg-white text-muted shadow-sm transition-all duration-200 hover:scale-110 hover:border-primary-300 hover:text-primary-600 hover:shadow-md md:grid"
        :aria-label="c ? 'Menyuni ochish' : 'Menyuni yig‘ish'"
        :title="c ? 'Menyuni ochish' : 'Menyuni yig‘ish'"
        :aria-expanded="!c"
        @click="ui.toggleSidebar()"
      >
        <ChevronLeft :class="['h-4 w-4 transition-transform duration-300', c && 'rotate-180']" />
      </button>
    </div>

    <nav :class="['flex-1 space-y-1 px-3 py-4', c ? 'overflow-visible' : 'overflow-y-auto overflow-x-hidden']" aria-label="Asosiy menyu">
      <p :class="['mb-2 h-4 px-3 text-[11px] font-medium uppercase tracking-wider text-slate-400 transition-opacity duration-200', c && 'opacity-0']">Menyu</p>
      <RouterLink
        v-for="(item, i) in menu"
        :key="item.to"
        :to="item.to"
        :class="['nav-link group relative', c ? 'justify-center gap-0 px-0' : 'gap-3 px-3', isActive(item.to) && 'nav-link-active']"
        :style="{ '--i': i }"
        :aria-current="isActive(item.to) ? 'page' : undefined"
        :aria-label="item.label"
      >
        <component :is="item.icon" class="h-5 w-5 shrink-0 transition-transform duration-200 group-hover:scale-110" />
        <span :class="['sidebar-label flex-1', c && 'is-hidden']">{{ item.label }}</span>
        <span
          v-if="item.badge"
          :class="[
            'rounded-full text-[11px] font-semibold tabular-nums transition-all duration-300',
            isActive(item.to) ? 'bg-white text-primary-700' : 'bg-primary-600 text-white',
            c ? 'absolute right-1.5 top-1 min-w-[18px] px-1 text-center text-[10px] leading-[18px] ring-2 ring-white' : 'px-1.5 leading-5',
          ]"
        >{{ item.badge }}</span>
        <!-- Yopiq holatda nom (tooltip) -->
        <span v-if="c" class="sidebar-tooltip" role="tooltip">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="space-y-1 border-t border-line px-3 py-3">
      <RouterLink
        to="/settings"
        :class="['nav-link group relative', c ? 'justify-center gap-0 px-0' : 'gap-3 px-3', isActive('/settings') && 'nav-link-active']"
        aria-label="Sozlamalar"
      >
        <Settings class="h-5 w-5 shrink-0 transition-transform duration-500 group-hover:rotate-90" />
        <span :class="['sidebar-label', c && 'is-hidden']">Sozlamalar</span>
        <span v-if="c" class="sidebar-tooltip" role="tooltip">Sozlamalar</span>
      </RouterLink>

      <div v-if="auth.user" :class="['flex items-center rounded-xl py-2 transition-all duration-300', c ? 'flex-col gap-2 px-0' : 'gap-3 bg-slate-50 px-2']">
        <Avatar :name="auth.user.fullName" size="sm" />
        <div :class="['sidebar-label min-w-0 flex-1', c && 'is-hidden']">
          <p class="truncate text-sm font-medium text-ink">{{ auth.user.fullName }}</p>
          <p class="truncate text-xs text-muted">{{ roleLabel(auth.user.role) }}</p>
        </div>
        <button class="icon-btn group relative hover:bg-red-50 hover:text-red-600" title="Chiqish" aria-label="Tizimdan chiqish" @click="logout">
          <LogOut class="h-[18px] w-[18px]" />
        </button>
      </div>
    </div>
  </aside>
</template>
