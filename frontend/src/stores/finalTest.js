import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { finalTestApi } from '@/api/finalTest'

/** Ishtirokchi nomi: ro‘yxatdan o‘tgan bo‘lsa — "Familiya Ism", eski (ismsiz) yozuvlarda — "Ishtirokchi #N" */
export const participantName = (r) => r?.fullName || `Ishtirokchi #${r?.participantNo ?? r?.id ?? '—'}`

/** Holat nomlari (eski yozuvlardagi "Yiqildi" ham "Testdan o‘tmadi" deb ko‘rsatiladi) */
export const FINAL_RESULT_LABELS = { 'O‘tdi': 'Testdan o‘tdi', 'O‘tmadi': 'Testdan o‘tmadi', Yiqildi: 'Testdan o‘tmadi' }
export const isPassed = (r) => r?.status === 'O‘tdi'

/**
 * Bir kishining urinishlarini guruhlash kaliti: xodim (employeeId) yoki ro‘yxatdan o‘tgan ishtirokchi (participantId).
 * Ikkalasi ham bo‘lmasa (eski yozuvlar) — har bir topshirish alohida.
 */
const personKey = (r) => (r?.employeeId ? `e${r.employeeId}` : r?.participantId ? `p${r.participantId}` : null)

/** Yakuniy bilim testi: barcha topshirishlar (backend/data/final_results.json) */
export const useFinalTestStore = defineStore('finalTest', () => {
  const results = ref([])
  const info = ref(null)
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const [r, i] = await Promise.all([finalTestApi.results(), finalTestApi.info()])
      results.value = r
      info.value = i
      loaded.value = true
    } catch (e) {
      error.value = e.message || 'Yakuniy test natijalarini yuklab bo‘lmadi'
    } finally {
      loading.value = false
    }
  }

  async function remove(id) {
    await finalTestApi.remove(id)
    results.value = results.value.filter((r) => r.id !== id)
  }

  /** Bitta kishining (xodim yoki ishtirokchi) barcha urinishlari; eski ismsiz yozuvda — faqat shu yozuvning o‘zi */
  function attemptsFor(resultId) {
    const row = results.value.find((r) => r.id === resultId)
    if (!row) return []
    const key = personKey(row)
    if (!key) return [row]
    return results.value.filter((r) => personKey(r) === key).sort((a, b) => a.attemptNo - b.attemptNo || a.id - b.id)
  }

  /** Ro‘yxat: har bir kishi — bitta qator (oxirgi urinishi, urinishlar soni bilan); eski ismsiz yozuvlar — alohida */
  const rows = computed(() => {
    const seen = new Set()
    const out = []
    for (const r of [...results.value].sort((a, b) => (b.submittedAt || '').localeCompare(a.submittedAt || '') || b.id - a.id)) {
      const key = personKey(r)
      if (key) {
        if (seen.has(key)) continue
        seen.add(key)
        out.push({ ...r, name: participantName(r), attempts: results.value.filter((x) => personKey(x) === key).length })
      } else {
        out.push({ ...r, name: participantName(r), attempts: 1 })
      }
    }
    return out
  })

  const stats = computed(() => {
    const list = rows.value
    const passed = list.filter(isPassed).length
    return {
      total: list.length,
      passed,
      failed: list.length - passed,
      avg: list.length ? Math.round(list.reduce((s, r) => s + r.percent, 0) / list.length) : 0,
    }
  })

  return { results, info, loading, loaded, error, fetchAll, remove, attemptsFor, rows, stats }
})