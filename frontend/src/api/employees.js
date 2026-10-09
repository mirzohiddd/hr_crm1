import { USE_MOCK, mockResponse, request } from './client'
import { createResource } from './resource'
import { table } from './mockDb'
import { fileStore } from '@/utils/fileStore'

const base = createResource('/employees', 'employees')

export const employeesApi = {
  ...base,
  /**
   * DELETE /employees/{id}
   * Backend bog‘liq yozuvlarni (o‘quv dasturi, test natijalari, hujjatlar) o‘zi o‘chiradi.
   * Mock rejimda shu yerda bajariladi.
   */
  async remove(id) {
    if (!USE_MOCK) return request(`/employees/${id}`, { method: 'DELETE' })
    table('trainings').where((t) => t.employeeId === id).forEach((t) => table('trainings').remove(t.id))
    table('testResults').where((r) => r.employeeId === id).forEach((r) => table('testResults').remove(r.id))
    for (const d of table('documents').where((doc) => doc.employeeId === id)) {
      if (d.fileId) await fileStore.remove(d.fileId).catch(() => {})
      table('documents').remove(d.id)
    }
    table('employees').remove(id)
    return mockResponse(null)
  },
}
