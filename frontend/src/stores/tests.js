import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { testResultsApi, testSettingsApi, testsApi } from '@/api/tests'
import { useCollection } from './helpers'
import { useEmployeesStore } from './employees'

export const useTestsStore = defineStore('tests', () => {
  const tests = useCollection(testsApi, 'Testlarni yuklab bo‘lmadi')
  const results = useCollection(testResultsApi, 'Test natijalarini yuklab bo‘lmadi')
  const settings = ref(null)

  async function fetchSettings({ force = false } = {}) {
    if (settings.value && !force) return settings.value
    settings.value = await testSettingsApi.get()
    return settings.value
  }

  function fetchAll(opts) {
    return Promise.all([tests.fetchAll(opts), results.fetchAll(opts), fetchSettings(opts)])
  }

  async function saveSettings(data) {
    settings.value = await testSettingsApi.update(data)
    return settings.value
  }

  async function assign(employeeId, testId = null) {
    return results.upsert(await testResultsApi.assign(employeeId, testId))
  }

  /** Javoblarni yuborish — natija serverda (mock: shu yerda) avtomatik hisoblanadi */
  async function submit(resultId, answers) {
    const res = await testResultsApi.submit(resultId, answers)
    results.upsert(res.result)
    if (res.employee) {
      const employees = useEmployeesStore()
      if (employees.loaded) employees.upsert(res.employee)
    }
    return res.result
  }

  const testById = (id) => tests.findById(id)
  const resultsOf = (employeeId) =>
    results.items.value.filter((r) => r.employeeId === Number(employeeId)).sort((a, b) => (b.assignedAt || '').localeCompare(a.assignedAt || ''))

  const stats = computed(() => {
    const list = results.items.value
    const count = (s) => list.filter((r) => r.status === s).length
    const passed = count('O‘tdi')
    const failed = count('O‘tmadi')
    return { total: list.length, pending: count('Kutilmoqda'), passed, failed, passRate: passed + failed ? Math.round((passed / (passed + failed)) * 100) : 0 }
  })

  return {
    tests: tests.items,
    results: results.items,
    settings,
    loading: computed(() => tests.loading.value || results.loading.value),
    loaded: computed(() => tests.loaded.value && results.loaded.value),
    resultsLoaded: results.loaded,
    error: computed(() => tests.error.value || results.error.value),
    fetchAll,
    fetchSettings,
    saveSettings,
    createTest: tests.create,
    updateTest: tests.update,
    removeTest: tests.remove,
    upsertResult: results.upsert,
    removeResult: results.remove,
    assign,
    submit,
    testById,
    resultsOf,
    stats,
  }
})
