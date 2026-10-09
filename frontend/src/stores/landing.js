import { defineStore } from 'pinia'
import { computed } from 'vue'
import { landingResultsApi } from '@/api/landing'
import { useCollection } from './helpers'

/** Landing (ochiq) test orqali kelgan nomzodlar natijalari — data/landing_results.json */
export const useLandingStore = defineStore('landing', () => {
  const results = useCollection(
    { list: landingResultsApi.list, remove: landingResultsApi.remove },
    'Nomzodlar testi natijalarini yuklab bo‘lmadi',
  )

  async function markViewed(id) {
    const row = results.findById(id)
    if (!row || row.viewed) return
    try {
      results.upsert(await landingResultsApi.markViewed(id))
    } catch {
      /* belgi muhim emas */
    }
  }

  const stats = computed(() => {
    const items = results.items.value
    const passed = items.filter((r) => r.status === 'O‘tdi').length
    return {
      total: items.length,
      passed,
      failed: items.length - passed,
      unseen: items.filter((r) => !r.viewed).length,
      avg: items.length ? Math.round(items.reduce((s, r) => s + (r.percent || 0), 0) / items.length) : 0,
    }
  })

  return {
    items: results.items,
    loading: results.loading,
    error: results.error,
    loaded: results.loaded,
    fetchAll: results.fetchAll,
    findById: results.findById,
    remove: results.remove,
    markViewed,
    stats,
  }
})
