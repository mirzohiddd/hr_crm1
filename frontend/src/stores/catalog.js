import { defineStore } from 'pinia'
import { computed } from 'vue'
import { departmentsApi, positionsApi } from '@/api/catalog'
import { useCollection } from './helpers'

/** Bo‘limlar va lavozimlar — nomzodlar va xodimlar shu ro‘yxatlarga id orqali bog‘lanadi */
export const useCatalogStore = defineStore('catalog', () => {
  const departments = useCollection(departmentsApi, 'Bo‘limlarni yuklab bo‘lmadi')
  const positions = useCollection(positionsApi, 'Lavozimlarni yuklab bo‘lmadi')

  const loaded = computed(() => departments.loaded.value && positions.loaded.value)
  const loading = computed(() => departments.loading.value || positions.loading.value)

  function fetchAll(opts) {
    return Promise.all([departments.fetchAll(opts), positions.fetchAll(opts)])
  }

  const positionName = (id) => positions.findById(id)?.name || '—'
  const departmentName = (id) => departments.findById(id)?.name || '—'

  const positionOptions = computed(() =>
    [...positions.items.value].sort((a, b) => a.name.localeCompare(b.name)).map((p) => ({ value: p.id, label: p.name })),
  )
  const departmentOptions = computed(() =>
    [...departments.items.value].sort((a, b) => a.name.localeCompare(b.name)).map((d) => ({ value: d.id, label: d.name })),
  )
  const positionsOf = (departmentId) => positions.items.value.filter((p) => p.departmentId === departmentId)

  return {
    departments: departments.items,
    positions: positions.items,
    loaded,
    loading,
    fetchAll,
    positionName,
    departmentName,
    positionOptions,
    departmentOptions,
    positionsOf,
    findPosition: positions.findById,
    findDepartment: departments.findById,
    createDepartment: departments.create,
    updateDepartment: departments.update,
    removeDepartment: departments.remove,
    createPosition: positions.create,
    updatePosition: positions.update,
    removePosition: positions.remove,
    error: computed(() => departments.error.value || positions.error.value),
  }
})
