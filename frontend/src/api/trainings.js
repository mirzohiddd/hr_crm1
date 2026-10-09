import { ApiError, USE_MOCK, mockResponse, request } from './client'
import { table } from './mockDb'
import { assignTestMock } from './tests'
import { TRAINING_DAYS } from '@/constants'
import { nowLocal, todayISO } from '@/utils/date'

export const lessonsApi = {
  /** GET /lessons — 7 kunlik dastur */
  list() {
    if (!USE_MOCK) return request('/lessons')
    return mockResponse([...table('lessons').all()].sort((a, b) => a.day - b.day))
  },
  /** PUT /lessons/{id} */
  update(id, data) {
    if (!USE_MOCK) return request(`/lessons/${id}`, { method: 'PUT', body: data })
    return mockResponse(table('lessons').patch(id, data))
  },
}

const notFound = () => Promise.reject(new ApiError('O‘quv dasturi topilmadi', 404))

export const trainingsApi = {
  /** GET /trainings */
  list() {
    if (!USE_MOCK) return request('/trainings')
    return mockResponse(table('trainings').all())
  },

  /** POST /trainings { employeeId, startDate } — xodimni 7 kunlik dasturga qo‘shish */
  start(employeeId, startDate = todayISO()) {
    if (!USE_MOCK) return request('/trainings', { method: 'POST', body: { employeeId, startDate } })
    if (table('trainings').where((t) => t.employeeId === employeeId).length) {
      return Promise.reject(new ApiError('Bu xodim allaqachon o‘quv dasturiga qo‘shilgan', 409))
    }
    return mockResponse(
      table('trainings').insert({ employeeId, startDate, completedDays: [], status: 'Jarayonda', finishedAt: null, testResultId: null }),
    )
  },

  /**
   * POST /trainings/{id}/days/{day}/complete
   * Kunni bajarildi deb belgilaydi. 7-kun tugasa — test avtomatik yuboriladi.
   * Javob: { training, testResult }
   */
  completeDay(id, day, by) {
    if (!USE_MOCK) return request(`/trainings/${id}/days/${day}/complete`, { method: 'POST' })
    const trainings = table('trainings')
    const t = trainings.find(id)
    if (!t) return notFound()
    const done = t.completedDays.map((d) => d.day)
    if (done.includes(day)) return Promise.reject(new ApiError(`${day}-kun allaqachon bajarilgan`, 409))
    if (day !== done.length + 1) return Promise.reject(new ApiError(`Avval ${done.length + 1}-kunni yakunlang`, 400))

    const at = nowLocal()
    const completedDays = [...t.completedDays, { day, at, by }]
    const finished = completedDays.length >= TRAINING_DAYS
    let testResult = null
    let patch = { completedDays }
    if (finished) {
      patch = { ...patch, status: 'Yakunlandi', finishedAt: at }
      const settings = table('settings').all()[0]
      if (settings.autoAssign && !t.testResultId) {
        try {
          testResult = assignTestMock(t.employeeId, { trainingId: t.id })
          patch.testResultId = testResult.id
        } catch {
          /* mos test yo‘q — HR keyin qo‘lda yuboradi */
        }
      }
    }
    return mockResponse({ training: trainings.patch(id, patch), testResult })
  },

  /** DELETE /trainings/{id}/days/{day} — oxirgi belgilangan kunni bekor qilish */
  undoDay(id, day) {
    if (!USE_MOCK) return request(`/trainings/${id}/days/${day}`, { method: 'DELETE' })
    const trainings = table('trainings')
    const t = trainings.find(id)
    if (!t) return notFound()
    if (t.status === 'Yakunlandi') return Promise.reject(new ApiError('Dastur yakunlangan, kunlarni bekor qilib bo‘lmaydi', 409))
    const last = t.completedDays.at(-1)
    if (!last || last.day !== day) return Promise.reject(new ApiError('Faqat oxirgi bajarilgan kunni bekor qilish mumkin', 400))
    return mockResponse(trainings.patch(id, { completedDays: t.completedDays.slice(0, -1) }))
  },

  /** DELETE /trainings/{id} */
  remove(id) {
    if (!USE_MOCK) return request(`/trainings/${id}`, { method: 'DELETE' })
    table('trainings').remove(id)
    return mockResponse(null)
  },
}
