import { defineStore } from 'pinia'
import { computed } from 'vue'
import { lessonsApi, trainingsApi } from '@/api/trainings'
import { useCollection } from './helpers'
import { useAuthStore } from './auth'
import { useTestsStore } from './tests'
import { TRAINING_DAYS } from '@/constants'
import { addDays, todayISO } from '@/utils/date'

/** 7 kunlik o‘quv dasturi: darslar (kontent) va xodimlar progressi */
export const useTrainingsStore = defineStore('trainings', () => {
  const lessons = useCollection(lessonsApi, 'Darslarni yuklab bo‘lmadi')
  const t = useCollection(trainingsApi, 'O‘quv dasturlarini yuklab bo‘lmadi')
  const auth = useAuthStore()

  function fetchAll(opts) {
    return Promise.all([t.fetchAll(opts), lessons.fetchAll(opts)])
  }

  const sortedLessons = computed(() => [...lessons.items.value].sort((a, b) => a.day - b.day))
  const lessonOf = (day) => sortedLessons.value.find((l) => l.day === day) || null

  const byEmployee = (employeeId) => t.items.value.find((x) => x.employeeId === Number(employeeId)) || null

  async function start(employeeId, startDate = todayISO()) {
    return t.upsert(await trainingsApi.start(employeeId, startDate))
  }

  async function completeDay(trainingId, day) {
    const res = await trainingsApi.completeDay(trainingId, day, auth.user?.fullName || '')
    t.upsert(res.training)
    if (res.testResult) {
      const tests = useTestsStore()
      if (tests.resultsLoaded) tests.upsertResult(res.testResult)
    }
    return res
  }

  async function undoDay(trainingId, day) {
    return t.upsert(await trainingsApi.undoDay(trainingId, day))
  }

  async function updateLesson(id, data) {
    return lessons.upsert(await lessonsApi.update(id, data))
  }

  return {
    items: t.items,
    loading: computed(() => t.loading.value || lessons.loading.value),
    loaded: computed(() => t.loaded.value && lessons.loaded.value),
    error: computed(() => t.error.value || lessons.error.value),
    upsert: t.upsert,
    drop: t.drop,
    remove: t.remove,
    fetchAll,
    lessons: sortedLessons,
    lessonOf,
    byEmployee,
    start,
    completeDay,
    undoDay,
    updateLesson,
  }
})

/** Progress ma'lumotlari (UI uchun) */
export function trainingProgress(training) {
  if (!training) return { done: 0, percent: 0, nextDay: 1, finished: false }
  const done = training.completedDays.length
  return {
    done,
    percent: Math.round((done / TRAINING_DAYS) * 100),
    nextDay: done < TRAINING_DAYS ? done + 1 : null,
    finished: done >= TRAINING_DAYS,
    plannedDate: (day) => addDays(training.startDate, day - 1),
    completedAt: (day) => training.completedDays.find((d) => d.day === day)?.at || null,
  }
}

/**
 * Dastur holati (UI uchun): Jarayonda → Testga yuborildi → O‘tdi / O‘tmadi
 * @param training o‘quv dasturi yozuvi (yoki null)
 * @param result shu dasturga bog‘langan test natijasi (yoki null)
 */
export function trainingState(training, result) {
  if (!training) return 'Boshlanmagan'
  if (training.completedDays.length < TRAINING_DAYS) return 'Jarayonda'
  if (!result) return 'Yakunlandi'
  if (result.status === 'Kutilmoqda') return 'Testga yuborildi'
  return result.status
}
