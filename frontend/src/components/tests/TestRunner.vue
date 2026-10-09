<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { CheckCircle2, ClipboardCheck, Play, RotateCcw, Send, XCircle } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import { useTestsStore } from '@/stores/tests'
import { useEmployeesStore } from '@/stores/employees'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  open: { type: Boolean, default: false },
  resultId: { type: Number, default: null },
})
const emit = defineEmits(['close', 'finished'])

const store = useTestsStore()
const employees = useEmployeesStore()
const toast = useToast()

const result = computed(() => store.results.find((r) => r.id === props.resultId) || null)
const test = computed(() => (result.value ? store.testById(result.value.testId) : null))
const employee = computed(() => (result.value ? employees.findById(result.value.employeeId) : null))
const maxAttempts = computed(() => store.settings?.maxAttempts ?? 3)
const attemptsLeft = computed(() => Math.max(0, maxAttempts.value - (result.value?.attempts.length || 0)))

const step = ref('intro') // intro | questions | done
const answers = reactive({})
const order = ref([]) // [{ question, options: [{ text, index }] }]
const submitting = ref(false)
const outcome = ref(null)
const showReview = ref(false)
const showUnanswered = ref(false)

const shuffle = (arr) => {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function prepare() {
  Object.keys(answers).forEach((k) => delete answers[k])
  const s = store.settings || {}
  const questions = s.shuffleQuestions ? shuffle(test.value.questions) : test.value.questions
  order.value = questions.map((q) => {
    const options = q.options.map((text, index) => ({ text, index }))
    return { question: q, options: s.shuffleOptions ? shuffle(options) : options }
  })
  showUnanswered.value = false
}

watch(
  () => [props.open, props.resultId],
  ([open]) => {
    if (!open) return
    outcome.value = null
    showReview.value = false
    step.value = result.value?.status === 'Kutilmoqda' || !result.value?.attempts.length ? 'intro' : 'done'
    if (step.value === 'done') {
      const last = result.value.attempts.at(-1)
      outcome.value = { ...last }
      Object.keys(answers).forEach((k) => delete answers[k])
      Object.assign(answers, last.answers || {})
      order.value = test.value ? test.value.questions.map((q) => ({ question: q, options: q.options.map((text, index) => ({ text, index })) })) : []
    }
  },
  { immediate: true },
)

function begin() {
  prepare()
  step.value = 'questions'
}

const answered = computed(() => order.value.filter((o) => answers[o.question.id] !== undefined).length)
const total = computed(() => order.value.length)

async function submit() {
  if (answered.value < total.value) {
    showUnanswered.value = true
    toast.error('Barcha savollarga javob bering', `${total.value - answered.value} ta savol javobsiz qoldi`)
    return
  }
  submitting.value = true
  try {
    const res = await store.submit(result.value.id, { ...answers })
    outcome.value = { ...res.attempts.at(-1) }
    step.value = 'done'
    emit('finished', res)
    if (outcome.value.passed) toast.success('Test topshirildi — O‘tdi', `${outcome.value.score}% to‘g‘ri javob`)
    else toast.info('Test topshirildi — O‘tmadi', `${outcome.value.score}% (kerak: ${result.value.passPercent}%)`)
  } catch (e) {
    toast.error('Natijani saqlab bo‘lmadi', e.message)
  } finally {
    submitting.value = false
  }
}

const optionClass = (o, opt) => {
  const selected = answers[o.question.id] === opt.index
  if (step.value === 'done' && showReview.value) {
    if (opt.index === o.question.correctIndex) return 'border-emerald-300 bg-emerald-50 text-emerald-800'
    if (selected) return 'border-red-300 bg-red-50 text-red-800'
    return 'border-line text-slate-500'
  }
  return selected ? 'border-primary-500 bg-primary-50 text-primary-800 ring-1 ring-primary-500' : 'border-line text-ink hover:border-slate-300 hover:bg-slate-50'
}

const persistent = computed(() => step.value === 'questions' || submitting.value)
</script>

<template>
  <Modal :open="open && !!result && !!test" size="lg" :persistent="persistent" @close="!submitting && emit('close')">
    <template #header>
      <div v-if="test" class="flex min-w-0 items-center gap-3">
        <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600"><ClipboardCheck class="h-5 w-5" /></span>
        <div class="min-w-0">
          <h2 class="truncate text-base font-semibold text-ink sm:text-lg">{{ test.title }}</h2>
          <p class="truncate text-sm text-muted">{{ employee?.fullName || 'Xodim' }}</p>
        </div>
      </div>
    </template>

    <template v-if="result && test">
      <!-- Kirish -->
      <div v-if="step === 'intro'" class="py-2">
        <p v-if="test.description" class="text-sm text-slate-600">{{ test.description }}</p>
        <dl class="mt-5 grid grid-cols-3 gap-3">
          <div class="rounded-xl border border-line p-3 text-center">
            <dt class="text-xs text-muted">Savollar</dt>
            <dd class="mt-1 text-xl font-semibold tabular-nums text-ink">{{ test.questions.length }}</dd>
          </div>
          <div class="rounded-xl border border-line p-3 text-center">
            <dt class="text-xs text-muted">O‘tish foizi</dt>
            <dd class="mt-1 text-xl font-semibold tabular-nums text-ink">{{ result.passPercent }}%</dd>
          </div>
          <div class="rounded-xl border border-line p-3 text-center">
            <dt class="text-xs text-muted">Urinishlar</dt>
            <dd class="mt-1 text-xl font-semibold tabular-nums text-ink">{{ attemptsLeft }}/{{ maxAttempts }}</dd>
          </div>
        </dl>
        <p class="mt-5 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Test xodim tomonidan mustaqil topshiriladi. Javoblar yuborilgach natija avtomatik hisoblanadi.
        </p>
      </div>

      <!-- Savollar / tahlil -->
      <div v-else>
        <div v-if="step === 'done' && outcome" :class="['mb-5 flex items-center gap-4 rounded-xl p-4', outcome.passed ? 'bg-emerald-50' : 'bg-red-50']">
          <component :is="outcome.passed ? CheckCircle2 : XCircle" :class="['h-10 w-10 shrink-0', outcome.passed ? 'text-emerald-600' : 'text-red-600']" />
          <div class="min-w-0 flex-1">
            <p :class="['text-lg font-semibold', outcome.passed ? 'text-emerald-800' : 'text-red-800']">{{ outcome.passed ? 'O‘tdi' : 'O‘tmadi' }}</p>
            <p class="text-sm text-slate-700">
              {{ outcome.correct }} / {{ outcome.total }} to‘g‘ri javob · o‘tish chegarasi {{ result.passPercent }}%
            </p>
          </div>
          <p :class="['text-3xl font-semibold tabular-nums', outcome.passed ? 'text-emerald-700' : 'text-red-700']">{{ outcome.score }}%</p>
        </div>

        <div v-if="step === 'questions'" class="sticky -top-5 z-10 -mx-5 -mt-5 mb-4 border-b border-line bg-white/95 px-5 py-3 backdrop-blur sm:-mx-6 sm:px-6">
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted">Javob berildi</span>
            <span class="font-medium tabular-nums text-ink">{{ answered }}/{{ total }}</span>
          </div>
          <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full bg-primary-600 transition-[width] duration-200" :style="{ width: `${total ? (answered / total) * 100 : 0}%` }" />
          </div>
        </div>

        <button v-if="step === 'done'" class="mb-3 text-sm font-medium text-primary-600 hover:underline" @click="showReview = !showReview">
          {{ showReview ? 'Javoblar tahlilini yashirish' : 'Javoblar tahlilini ko‘rish' }}
        </button>

        <ol v-if="step === 'questions' || showReview" class="space-y-4">
          <li
            v-for="(o, qi) in order"
            :key="o.question.id"
            :class="['rounded-xl border p-4', showUnanswered && answers[o.question.id] === undefined ? 'border-red-300 bg-red-50/40' : 'border-line']"
          >
            <p class="text-sm font-medium text-ink"><span class="mr-1 text-muted">{{ qi + 1 }}.</span>{{ o.question.text }}</p>
            <div class="mt-3 grid gap-2" role="radiogroup" :aria-label="o.question.text">
              <label
                v-for="opt in o.options"
                :key="opt.index"
                :class="['flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors', optionClass(o, opt), step === 'done' && 'cursor-default']"
              >
                <input
                  v-model="answers[o.question.id]"
                  type="radio"
                  :name="`q-${o.question.id}`"
                  :value="opt.index"
                  :disabled="step === 'done'"
                  class="h-4 w-4 shrink-0 border-slate-300 text-primary-600 focus:ring-primary-500"
                />
                {{ opt.text }}
              </label>
            </div>
          </li>
        </ol>
      </div>
    </template>

    <template #footer>
      <template v-if="step === 'intro'">
        <Button variant="secondary" @click="emit('close')">Yopish</Button>
        <Button :icon="Play" :disabled="!attemptsLeft" @click="begin">{{ attemptsLeft ? 'Testni boshlash' : 'Urinishlar tugagan' }}</Button>
      </template>
      <template v-else-if="step === 'questions'">
        <Button variant="secondary" :disabled="submitting" @click="step = 'intro'">Ortga</Button>
        <Button :icon="Send" :loading="submitting" @click="submit">Javoblarni yuborish</Button>
      </template>
      <template v-else>
        <Button v-if="outcome && !outcome.passed && attemptsLeft" variant="secondary" :icon="RotateCcw" @click="begin">
          Qayta topshirish ({{ attemptsLeft }} ta urinish qoldi)
        </Button>
        <Button @click="emit('close')">Yopish</Button>
      </template>
    </template>
  </Modal>
</template>
