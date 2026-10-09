import { computed, ref, unref, watch } from 'vue'

/**
 * @param source ro'yxat (ref/computed)
 * @param pageSize sahifadagi elementlar soni
 * @param resetOn o'zgarganda 1-sahifaga qaytish uchun getter (masalan, filtrlar)
 */
export function usePagination(source, pageSize = 10, resetOn) {
  const page = ref(1)
  const total = computed(() => unref(source).length)
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
  const paged = computed(() => unref(source).slice((page.value - 1) * pageSize, page.value * pageSize))

  watch(totalPages, (n) => {
    if (page.value > n) page.value = n
  })
  if (resetOn) watch(resetOn, () => (page.value = 1), { deep: true })

  return { page, paged, total, totalPages, pageSize }
}
