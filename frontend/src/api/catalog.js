import { ApiError, USE_MOCK } from './client'
import { createResource } from './resource'
import { table } from './mockDb'

const inUse = (msg) => Promise.reject(new ApiError(msg, 409))

const departmentsBase = createResource('/departments', 'departments')
const positionsBase = createResource('/positions', 'positions')

export const departmentsApi = {
  ...departmentsBase,
  /** DELETE /departments/{id} — bog‘langan lavozim/xodim bo‘lsa, server 409 qaytaradi */
  remove(id) {
    if (USE_MOCK) {
      const employees = table('employees').where((e) => e.departmentId === id).length
      const candidates = table('candidates').where((c) => c.departmentId === id).length
      if (employees || candidates) {
        return inUse(`Bo‘limga ${employees} ta xodim va ${candidates} ta nomzod bog‘langan. Avval ularni boshqa bo‘limga o‘tkazing.`)
      }
    }
    return departmentsBase.remove(id)
  },
}

export const positionsApi = {
  ...positionsBase,
  /** DELETE /positions/{id} */
  remove(id) {
    if (USE_MOCK) {
      const employees = table('employees').where((e) => e.positionId === id).length
      const candidates = table('candidates').where((c) => c.positionId === id).length
      if (employees || candidates) {
        return inUse(`Lavozimga ${employees} ta xodim va ${candidates} ta nomzod bog‘langan. O‘chirish o‘rniga nomini o‘zgartiring.`)
      }
    }
    return positionsBase.remove(id)
  },
}
