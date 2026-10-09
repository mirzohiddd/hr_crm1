import { defineStore } from 'pinia'
import { computed } from 'vue'
import { employeesApi } from '@/api/employees'
import { useCollection } from './helpers'
import { useCatalogStore } from './catalog'
import { todayISO } from '@/utils/date'

export const useEmployeesStore = defineStore('employees', () => {
  const c = useCollection(employeesApi, 'Xodimlar ro‘yxatini yuklab bo‘lmadi')
  const catalog = useCatalogStore()

  async function fetchAll(opts) {
    await Promise.all([c.fetchAll(opts), catalog.fetchAll()])
  }

  async function update(id, payload) {
    // Status "Faol emas" ga o‘tganda ketgan sana belgilanadi
    const current = c.findById(id)
    const data = { ...payload }
    if (data.status === 'Faol emas' && current?.status !== 'Faol emas') data.leftAt = data.leftAt || todayISO()
    if (data.status && data.status !== 'Faol emas') data.leftAt = null
    return c.update(id, data)
  }

  const stats = computed(() => {
    const items = c.items.value
    const count = (s) => items.filter((e) => e.status === s).length
    const inactive = count('Faol emas')
    return { total: items.length - inactive, all: items.length, active: count('Faol'), new: count('Yangi'), inactive }
  })

  const groupBy = (key, nameOf) =>
    computed(() => {
      const map = new Map()
      c.items.value
        .filter((e) => e.status !== 'Faol emas')
        .forEach((e) => map.set(e[key], (map.get(e[key]) || 0) + 1))
      return [...map.entries()].map(([id, count]) => ({ id, name: nameOf(id), count })).sort((a, b) => b.count - a.count)
    })

  const byDepartment = groupBy('departmentId', catalog.departmentName)
  const byPosition = groupBy('positionId', catalog.positionName)

  return { ...c, fetchAll, update, stats, byDepartment, byPosition }
})
