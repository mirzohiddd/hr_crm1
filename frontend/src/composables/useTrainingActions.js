import { ref } from 'vue'
import { useTrainingsStore } from '@/stores/trainings'
import { useTestsStore } from '@/stores/tests'
import { useToast } from './useToast'
import { TRAINING_DAYS } from '@/constants'

/** Darslar sahifasi va xodim profilida umumiy: kunni belgilash, bekor qilish, testga yuborish */
export function useTrainingActions() {
  const trainings = useTrainingsStore()
  const tests = useTestsStore()
  const toast = useToast()
  const busyDay = ref(null)
  const assigning = ref(false)

  async function complete(training, day) {
    busyDay.value = day
    try {
      const res = await trainings.completeDay(training.id, day)
      if (day === TRAINING_DAYS) {
        if (res.testResult) {
          const test = tests.testById(res.testResult.testId)
          toast.success('O‘quv dasturi yakunlandi', `Xodim testga yuborildi${test ? `: “${test.title}”` : ''}`)
        } else {
          toast.info('O‘quv dasturi yakunlandi', 'Testni “Testga yuborish” tugmasi orqali qo‘lda yuboring')
        }
      } else {
        toast.success(`${day}-kun bajarildi`, `Progress saqlandi: ${day}/${TRAINING_DAYS}`)
      }
      return res
    } catch (e) {
      toast.error('Saqlab bo‘lmadi', e.message)
    } finally {
      busyDay.value = null
    }
  }

  async function undo(training, day) {
    busyDay.value = day
    try {
      await trainings.undoDay(training.id, day)
      toast.info(`${day}-kun belgisi bekor qilindi`)
    } catch (e) {
      toast.error('Bekor qilib bo‘lmadi', e.message)
    } finally {
      busyDay.value = null
    }
  }

  async function assignTest(employeeId, testId = null) {
    assigning.value = true
    try {
      const result = await tests.assign(employeeId, testId)
      const test = tests.testById(result.testId)
      toast.success('Test yuborildi', test?.title || '')
      return result
    } catch (e) {
      toast.error('Testni yuborib bo‘lmadi', e.message)
    } finally {
      assigning.value = false
    }
  }

  return { busyDay, assigning, complete, undo, assignTest }
}
