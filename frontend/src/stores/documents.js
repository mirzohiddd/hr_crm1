import { defineStore } from 'pinia'
import { computed } from 'vue'
import { documentsApi } from '@/api/documents'
import { useCollection } from './helpers'
import { useAuthStore } from './auth'

export const useDocumentsStore = defineStore('documents', () => {
  const c = useCollection(documentsApi, 'Hujjatlarni yuklab bo‘lmadi')
  const auth = useAuthStore()

  async function setStatus(id, status, { comment = '' } = {}) {
    return c.upsert(await documentsApi.updateStatus(id, { status, comment, reviewedBy: auth.user?.fullName || '' }))
  }

  async function upload(payload) {
    return c.upsert(await documentsApi.upload({ ...payload, uploadedBy: auth.user?.fullName || '' }))
  }

  const getFile = (doc) => documentsApi.getFile(doc)

  const ofEmployee = (employeeId) => c.items.value.filter((d) => d.employeeId === Number(employeeId))

  const stats = computed(() => {
    const count = (s) => c.items.value.filter((d) => d.status === s).length
    return {
      total: c.items.value.length,
      approved: count('Tasdiqlangan'),
      pending: count('Kutilmoqda'),
      rejected: count('Rad etilgan'),
    }
  })

  return { ...c, setStatus, upload, getFile, ofEmployee, stats }
})
