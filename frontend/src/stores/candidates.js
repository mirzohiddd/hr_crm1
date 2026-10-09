import { defineStore } from 'pinia'
import { computed } from 'vue'
import { candidatesApi } from '@/api/candidates'
import { useCollection } from './helpers'
import { useAuthStore } from './auth'
import { useEmployeesStore } from './employees'
import { useTrainingsStore } from './trainings'
import { CANDIDATE_STATUSES } from '@/constants'
import { todayISO } from '@/utils/date'

export const useCandidatesStore = defineStore('candidates', () => {
  const c = useCollection(candidatesApi, 'Nomzodlarni yuklab bo‘lmadi')
  const auth = useAuthStore()
  const by = () => auth.user?.fullName || ''

  const create = (payload) => c.create({ ...payload, createdBy: by() })

  async function setStatus(id, status, extra = {}) {
    return c.upsert(await candidatesApi.setStatus(id, status, { ...extra, by: by() }))
  }

  /** Ishga qabul qilish: nomzod → xodim (+ 7 kunlik dastur) */
  async function hire(id, payload) {
    const res = await candidatesApi.hire(id, { ...payload, by: by() })
    c.upsert(res.candidate)
    const employees = useEmployeesStore()
    if (employees.loaded) employees.upsert(res.employee)
    const trainings = useTrainingsStore()
    if (res.training && trainings.loaded) trainings.upsert(res.training)
    return res
  }

  async function importRows(rows) {
    const res = await candidatesApi.import(rows, by())
    res.created.forEach((row) => c.upsert(row))
    return res
  }

  const counts = computed(() => {
    const map = Object.fromEntries(CANDIDATE_STATUSES.map((s) => [s, 0]))
    c.items.value.forEach((x) => (map[x.status] = (map[x.status] || 0) + 1))
    return map
  })

  const today = todayISO()
  const newToday = computed(() => c.items.value.filter((x) => x.createdAt?.slice(0, 10) === today).length)
  const interviewsToday = computed(() =>
    c.items.value
      .filter((x) => x.status === 'Suhbat' && x.interviewAt?.slice(0, 10) === today)
      .sort((a, b) => a.interviewAt.localeCompare(b.interviewAt)),
  )

  return { ...c, create, setStatus, hire, importRows, counts, newToday, interviewsToday }
})
