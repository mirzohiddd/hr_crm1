import { defineStore } from 'pinia'
import { computed } from 'vue'
import { landingResultsApi } from '@/api/landing'
import { useCollection } from './helpers'
import { isLandingPositive, isLandingUnreliable } from '@/constants'

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
    // Ijobiy: eski testda "O‘tdi", 40 savolli testda "Tavsiya etiladi"
    const passed = items.filter(isLandingPositive).length
    const withReliability = items.filter((r) => typeof r.reliability === 'number')
    return {
      total: items.length,
      passed,
      failed: items.length - passed,
      unseen: items.filter((r) => !r.viewed).length,
      avg: items.length ? Math.round(items.reduce((s, r) => s + (r.percent || 0), 0) / items.length) : 0,
      unreliable: items.filter(isLandingUnreliable).length,
      avgReliability: withReliability.length ? Math.round(withReliability.reduce((s, r) => s + r.reliability, 0) / withReliability.length) : null,
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