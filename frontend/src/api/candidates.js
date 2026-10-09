import { ApiError, USE_MOCK, mockResponse, request } from './client'
import { createResource } from './resource'
import { table } from './mockDb'
import { nowLocal } from '@/utils/date'
import { phoneKey } from '@/utils/format'

const base = createResource('/candidates', 'candidates', {
  onCreate: (data) => ({
    status: 'Yangi',
    interviewAt: null,
    rejectReason: '',
    employeeId: null,
    contactAttempts: 0,
    createdAt: nowLocal(),
    ...data,
    history: [{ status: data.status || 'Yangi', at: nowLocal(), by: data.createdBy || '' }],
  }),
})

const notFound = () => Promise.reject(new ApiError('Nomzod topilmadi', 404))

export const candidatesApi = {
  ...base,

  /**
   * PATCH /candidates/{id}/status { status, interviewAt?, rejectReason? }
   * Bosqichni o‘zgartirish (Yangi → Bog‘lanildi / Bog‘lanilmadi → Suhbat → Rad etildi).
   * "Ishga qabul qilindi" uchun hire() ishlatiladi.
   */
  setStatus(id, status, { interviewAt, rejectReason, by = '' } = {}) {
    const body = { status, interviewAt, rejectReason }
    if (!USE_MOCK) return request(`/candidates/${id}/status`, { method: 'PATCH', body })
    const t = table('candidates')
    const c = t.find(id)
    if (!c) return notFound()
    if (c.status === 'Ishga qabul qilindi') return Promise.reject(new ApiError('Nomzod allaqachon ishga qabul qilingan', 409))
    const patch = { status, history: [...(c.history || []), { status, at: nowLocal(), by }] }
    if (interviewAt !== undefined) patch.interviewAt = interviewAt
    // Bog‘lanib bo‘lmagan urinishlar soni
    if (status === 'Bog‘lanilmadi') patch.contactAttempts = (c.contactAttempts || 0) + 1
    if (status === 'Rad etildi') patch.rejectReason = rejectReason || ''
    else patch.rejectReason = ''
    return mockResponse(t.patch(id, patch))
  },

  /**
   * POST /candidates/{id}/hire { hireDate, positionId, departmentId, startTraining }
   * Nomzodni xodimga aylantiradi va (ixtiyoriy) 7 kunlik o‘quv dasturini boshlaydi.
   * Javob: { candidate, employee, training }
   */
  hire(id, { hireDate, positionId, departmentId, startTraining = true, by = '' }) {
    const body = { hireDate, positionId, departmentId, startTraining }
    if (!USE_MOCK) return request(`/candidates/${id}/hire`, { method: 'POST', body })
    const t = table('candidates')
    const c = t.find(id)
    if (!c) return notFound()
    if (c.employeeId && table('employees').find(c.employeeId)) {
      return Promise.reject(new ApiError('Bu nomzod allaqachon xodimlar ro‘yxatida', 409))
    }
    const employee = table('employees').insert({
      fullName: c.fullName,
      gender: c.gender || '',
      birthDate: '',
      phone: c.phone,
      email: c.email || '',
      address: c.city || '',
      age: c.age || null,
      departmentId,
      positionId,
      hireDate,
      status: 'Yangi',
      leftAt: null,
      candidateId: c.id,
      photo: null,
    })
    let training = null
    if (startTraining) {
      training = table('trainings').insert({
        employeeId: employee.id,
        startDate: hireDate,
        completedDays: [],
        status: 'Jarayonda',
        finishedAt: null,
        testResultId: null,
      })
    }
    const status = 'Ishga qabul qilindi'
    const candidate = t.patch(id, {
      status,
      positionId,
      departmentId,
      employeeId: employee.id,
      rejectReason: '',
      history: [...(c.history || []), { status, at: nowLocal(), by }],
    })
    return mockResponse({ candidate, employee, training })
  },

  /**
   * POST /candidates/import { rows: [...] }
   * Google Sheets / CSV dan kelgan qatorlar. Telefon raqami bo‘yicha takrorlar o‘tkazib yuboriladi.
   * Javob: { created: [...], skipped: number }
   */
  import(rows, by = '') {
    if (!USE_MOCK) return request('/candidates/import', { method: 'POST', body: { rows } })
    const t = table('candidates')
    const seen = new Set(t.all().map((c) => phoneKey(c.phone)).filter(Boolean))
    const created = []
    let skipped = 0
    rows.forEach((row) => {
      const key = phoneKey(row.phone)
      if (key && seen.has(key)) {
        skipped++
        return
      }
      if (key) seen.add(key)
      const at = row.createdAt || nowLocal()
      created.push(
        t.insert({
          status: 'Yangi',
          interviewAt: null,
          rejectReason: '',
          employeeId: null,
          gender: '',
          age: null,
          city: '',
          note: '',
          ...row,
          createdAt: at,
          history: [{ status: 'Yangi', at, by: by || `${row.source || 'Fayl'} importi` }],
        }),
      )
    })
    return mockResponse({ created, skipped })
  },
}
