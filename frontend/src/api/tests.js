import { ApiError, USE_MOCK, mockResponse, request } from './client'
import { createResource } from './resource'
import { table } from './mockDb'
import { nowLocal } from '@/utils/date'
import { DEFAULT_PASS_PERCENT } from '@/constants'

export const testsApi = createResource('/tests', 'tests')

/** Test natijasini hisoblash: to‘g‘ri javoblar foizi va o‘tish chegarasi (standart 80%) */
export function gradeTest(test, answers, passPercent = DEFAULT_PASS_PERCENT) {
  const total = test.questions.length
  const correct = test.questions.reduce((sum, q) => sum + (Number(answers[q.id]) === q.correctIndex ? 1 : 0), 0)
  const score = total ? Math.round((correct / total) * 100) : 0
  return { total, correct, score, passed: score >= passPercent }
}

/** Xodim lavozimiga mos testni tanlash: avval lavozimga xos, keyin umumiy test */
export function pickTestFor(employee, tests) {
  const active = tests.filter((t) => t.active !== false && t.questions?.length)
  return (
    active.find((t) => t.positionIds?.includes(employee.positionId)) ||
    active.find((t) => !t.positionIds?.length) ||
    null
  )
}

/** Mock: xodimga test biriktirish (darslar tugaganda yoki qo‘lda) */
export function assignTestMock(employeeId, { testId = null, trainingId = null } = {}) {
  const employee = table('employees').find(employeeId)
  if (!employee) throw new ApiError('Xodim topilmadi', 404)
  const test = testId ? table('tests').find(testId) : pickTestFor(employee, table('tests').all())
  if (!test) throw new ApiError('Mos test topilmadi. Testlar bo‘limida test yarating.', 400)
  return table('testResults').insert({
    employeeId,
    testId: test.id,
    trainingId,
    passPercent: getSettings()?.passPercent ?? DEFAULT_PASS_PERCENT,
    assignedAt: nowLocal(),
    status: 'Kutilmoqda',
    score: null,
    correct: null,
    total: test.questions.length,
    completedAt: null,
    attempts: [],
  })
}

const getSettings = () => table('settings').all()[0]

export const testResultsApi = {
  /** GET /test-results */
  list() {
    if (!USE_MOCK) return request('/test-results')
    return mockResponse(table('testResults').all())
  },

  /** POST /test-results { employeeId, testId? } — testni qo‘lda yuborish */
  assign(employeeId, testId = null) {
    if (!USE_MOCK) return request('/test-results', { method: 'POST', body: { employeeId, testId } })
    const open = table('testResults').where((r) => r.employeeId === employeeId && r.status === 'Kutilmoqda')
    if (open.length) return Promise.reject(new ApiError('Bu xodimda topshirilmagan test bor', 409))
    try {
      return mockResponse(assignTestMock(employeeId, { testId }))
    } catch (e) {
      return Promise.reject(e)
    }
  },

  /**
   * POST /test-results/{id}/submit { answers: { [questionId]: optionIndex } }
   * Natija serverda hisoblanadi: { result, employee }
   */
  submit(id, answers) {
    if (!USE_MOCK) return request(`/test-results/${id}/submit`, { method: 'POST', body: { answers } })
    const results = table('testResults')
    const row = results.find(id)
    if (!row) return Promise.reject(new ApiError('Natija topilmadi', 404))
    const test = table('tests').find(row.testId)
    if (!test) return Promise.reject(new ApiError('Test o‘chirilgan', 404))
    const settings = getSettings()
    if (row.status === 'O‘tdi') return Promise.reject(new ApiError('Test allaqachon topshirilgan', 409))
    if (row.attempts.length >= settings.maxAttempts) {
      return Promise.reject(new ApiError(`Urinishlar soni tugagan (${settings.maxAttempts} ta)`, 409))
    }
    const passPercent = settings.passPercent ?? DEFAULT_PASS_PERCENT
    const grade = gradeTest(test, answers, passPercent)
    const at = nowLocal()
    // Savollar nusxasi: test keyinchalik tahrirlansa ham javoblar tahlili to‘g‘ri ko‘rinadi
    const questions = test.questions.map(({ id, text, options, correctIndex }) => ({ id, text, options: [...options], correctIndex }))
    const updated = results.patch(id, {
      status: grade.passed ? 'O‘tdi' : 'O‘tmadi',
      score: grade.score,
      correct: grade.correct,
      total: grade.total,
      completedAt: at,
      passPercent,
      attempts: [...row.attempts, { at, ...grade, answers, questions }],
    })
    let employee = null
    if (grade.passed && settings.activateOnPass) {
      const e = table('employees').find(row.employeeId)
      if (e && e.status === 'Yangi') employee = table('employees').patch(e.id, { status: 'Faol' })
    }
    return mockResponse({ result: updated, employee })
  },

  /** DELETE /test-results/{id} */
  remove(id) {
    if (!USE_MOCK) return request(`/test-results/${id}`, { method: 'DELETE' })
    table('testResults').remove(id)
    table('trainings')
      .where((t) => t.testResultId === id)
      .forEach((t) => table('trainings').patch(t.id, { testResultId: null }))
    return mockResponse(null)
  },
}

export const testSettingsApi = {
  /** GET /settings/tests */
  get() {
    if (!USE_MOCK) return request('/settings/tests')
    return mockResponse(getSettings(), 150)
  },
  /** PUT /settings/tests */
  update(data) {
    if (!USE_MOCK) return request('/settings/tests', { method: 'PUT', body: data })
    return mockResponse(table('settings').patch(getSettings().id, data))
  },
}
