import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

const KEY = 'hr-crm:sidebar-collapsed'

/** Interfeys holati: sidebar ochiq/yopiq (desktopda eslab qolinadi) */
export const useUiStore = defineStore('ui', () => {
  let saved = false
  try {
    saved = localStorage.getItem(KEY) === '1'
  } catch {
    /* e'tiborsiz */
  }
  const collapsedPref = ref(saved) // desktop (≥1024px) uchun foydalanuvchi tanlovi
  const tabletExpanded = ref(false) // planshetda vaqtincha ochish (kontent ustidan)
  const mobileOpen = ref(false) // mobil: chiqib keluvchi menyu

  const width = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', () => (width.value = window.innerWidth), { passive: true })
  }
  const isDesktop = computed(() => width.value >= 1024)
  const isTablet = computed(() => width.value >= 768 && width.value < 1024)
  const isMobile = computed(() => width.value < 768)

  /** Sidebar hozir faqat ikonlar ko‘rinishidami */
  const collapsed = computed(() => {
    if (isMobile.value) return false
    if (isTablet.value) return !tabletExpanded.value
    return collapsedPref.value
  })

  watch(collapsedPref, (v) => {
    try {
      localStorage.setItem(KEY, v ? '1' : '0')
    } catch {
      /* e'tiborsiz */
    }
  })

  function toggleSidebar() {
    if (isMobile.value) mobileOpen.value = !mobileOpen.value
    else if (isTablet.value) tabletExpanded.value = !tabletExpanded.value
    else collapsedPref.value = !collapsedPref.value
  }

  function closeOverlays() {
    mobileOpen.value = false
    tabletExpanded.value = false
  }

  return { collapsed, collapsedPref, tabletExpanded, mobileOpen, isDesktop, isTablet, isMobile, toggleSidebar, closeOverlays }
})
