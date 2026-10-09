import { defineStore } from 'pinia'
import { usersApi } from '@/api/auth'
import { useCollection } from './helpers'
import { useAuthStore } from './auth'

/** CRM foydalanuvchilari (HR xodimlari) — faqat administrator boshqaradi */
export const useUsersStore = defineStore('users', () => {
  const c = useCollection(usersApi, 'Foydalanuvchilarni yuklab bo‘lmadi')

  async function update(id, payload) {
    const row = await c.update(id, payload)
    useAuthStore().syncUser(row)
    return row
  }

  return { ...c, update }
})
