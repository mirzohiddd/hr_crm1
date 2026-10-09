<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { ArrowDown, ArrowUp, Check, Plus, Trash2, X } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import Switch from '@/components/ui/Switch.vue'
import { useCatalogStore } from '@/stores/catalog'

const props = defineProps({
  open: { type: Boolean, default: false },
  test: { type: Object, default: null }, // null → yangi test
  saving: { type: Boolean, default: false },
  passPercent: { type: Number, default: 80 }, // barcha testlar uchun umumiy (Sozlamalar)
})
const emit = defineEmits(['close', 'submit'])
const catalog = useCatalogStore()

let uid = 0
const newQuestion = () => ({ id: `n${++uid}`, text: '', options: ['', '', '', ''], correctIndex: null })

const form = reactive({ title: '', description: '', positionIds: [], passPercent: 70, active: true, questions: [] })
const errors = ref({})
const qErrors = ref({})
const formEl = ref(null)
const isEdit = computed(() => !!props.test)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const t = props.test
    Object.assign(form, {
      title: t?.title || '',
      description: t?.description || '',
      positionIds: [...(t?.positionIds || [])],
      passPercent: props.passPercent,
      active: t?.active ?? true,
      questions: t ? t.questions.map((q) => ({ ...q, options: [...q.options] })) : [newQuestion()],
    })
    errors.value = {}
    qErrors.value = {}
  },
  { immediate: true },
)

function togglePosition(id) {
  const i = form.positionIds.indexOf(id)
  if (i === -1) form.positionIds.push(id)
  else form.positionIds.splice(i, 1)
}

async function addQuestion() {
  form.questions.push(newQuestion())
  await nextTick()
  formEl.value?.querySelector(`[data-q="${form.questions.length - 1}"]`)?.focus()
}
function removeQuestion(i) {
  form.questions.splice(i, 1)
}
function move(i, dir) {
  const j = i + dir
  if (j < 0 || j >= form.questions.length) return
  const [q] = form.questions.splice(i, 1)
  form.questions.splice(j, 0, q)
}
function addOption(q) {
  if (q.options.length < 6) q.options.push('')
}
function removeOption(q, oi) {
  if (q.options.length <= 2) return
  q.options.splice(oi, 1)
  if (q.correctIndex === oi) q.correctIndex = null
  else if (q.correctIndex > oi) q.correctIndex--
}

function validate() {
  const e = {}
  const qe = {}
  if (!form.title.trim()) e.title = 'Test nomini kiriting'
  if (!form.questions.length) e.questions = 'Kamida bitta savol qo‘shing'
  form.questions.forEach((q, i) => {
    const filled = q.options.filter((o) => o.trim()).length
    if (!q.text.trim()) qe[i] = 'Savol matnini yozing'
    else if (filled < 2) qe[i] = 'Kamida 2 ta variant yozing'
    else if (q.correctIndex === null || !q.options[q.correctIndex]?.trim()) qe[i] = 'To‘g‘ri javobni belgilang (✓)'
  })
  errors.value = e
  qErrors.value = qe
  return !Object.keys(e).length && !Object.keys(qe).length
}

async function submit() {
  if (!validate()) {
    await nextTick()
    formEl.value?.querySelector('.form-error')?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    return
  }
  // Bo‘sh variantlar olib tashlanadi, to‘g‘ri javob indeksi qayta hisoblanadi
  let nextId = Math.max(0, ...form.questions.map((q) => (typeof q.id === 'number' ? q.id : 0)))
  const questions = form.questions.map((q) => {
    const kept = q.options.map((text, index) => ({ text: text.trim(), index })).filter((o) => o.text)
    return {
      id: typeof q.id === 'number' ? q.id : ++nextId,
      text: q.text.trim(),
      options: kept.map((o) => o.text),
      correctIndex: kept.findIndex((o) => o.index === q.correctIndex),
    }
  })
  emit('submit', {
    title: form.title.trim(),
    description: form.description.trim(),
    positionIds: [...form.positionIds],
    passPercent: Number(form.passPercent),
    active: form.active,
    questions,
  })
}

const letters = 'ABCDEF'
</script>

<template>
  <Modal
    :open="open"
    size="xl"
    :persistent="saving"
    :title="isEdit ? 'Testni tahrirlash' : 'Yangi test'"
    subtitle="Savollar, variantlar, to‘g‘ri javob va o‘tish foizi"
    @close="!saving && emit('close')"
  >
    <form id="test-form" ref="formEl" novalidate @submit.prevent="submit">
      <div class="grid gap-4 sm:grid-cols-[minmax(0,1fr)_160px]">
        <FormField label="Test nomi" for="t-title" :error="errors.title" required>
          <input id="t-title" v-model="form.title" class="form-input" :class="errors.title && 'has-error'" placeholder="Masalan: Call Center yakuniy testi" />
        </FormField>
        <div>
          <p class="form-label">O‘tish chegarasi</p>
          <p class="flex h-10 items-center rounded-lg border border-primary-100 bg-primary-50/60 px-3 text-sm font-semibold text-primary-700">{{ passPercent }}% va yuqori</p>
        </div>
        <FormField class="sm:col-span-2" label="Tavsif" for="t-desc">
          <textarea id="t-desc" v-model="form.description" rows="2" class="form-input" placeholder="Test haqida qisqacha" />
        </FormField>
      </div>

      <div class="mt-4">
        <p class="form-label">Lavozimlar</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="p in catalog.positionOptions"
            :key="p.value"
            type="button"
            :aria-pressed="form.positionIds.includes(p.value)"
            :class="[
              'inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-[13px] font-medium transition-colors',
              form.positionIds.includes(p.value) ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-line text-slate-600 hover:bg-slate-50',
            ]"
            @click="togglePosition(p.value)"
          >
            <Check v-if="form.positionIds.includes(p.value)" class="h-3.5 w-3.5" />{{ p.label }}
          </button>
        </div>
        <p class="form-hint">{{ form.positionIds.length ? 'Test faqat tanlangan lavozimlarga yuboriladi' : 'Hech biri tanlanmasa — test barcha lavozimlar uchun umumiy' }}</p>
      </div>

      <div class="mt-4 flex items-center justify-between gap-4 rounded-lg border border-line px-4 py-3">
        <div>
          <p class="text-sm font-medium text-ink">Faol</p>
          <p class="text-xs text-muted">Faol bo‘lmagan test xodimlarga avtomatik yuborilmaydi</p>
        </div>
        <Switch v-model="form.active" label="Test faol" />
      </div>

      <div class="mt-6 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-ink">Savollar <span class="font-normal text-muted">({{ form.questions.length }})</span></h3>
      </div>
      <p v-if="errors.questions" class="form-error">{{ errors.questions }}</p>

      <ol class="mt-3 space-y-3">
        <li v-for="(q, i) in form.questions" :key="q.id" :class="['rounded-xl border p-4', qErrors[i] ? 'border-red-200 bg-red-50/30' : 'border-line bg-slate-50/40']">
          <div class="flex items-start gap-2">
            <span class="mt-2.5 w-6 shrink-0 text-sm font-semibold tabular-nums text-muted">{{ i + 1 }}.</span>
            <textarea
              v-model="q.text"
              :data-q="i"
              rows="2"
              class="form-input flex-1"
              placeholder="Savol matni"
              @input="delete qErrors[i]"
            />
            <div class="flex shrink-0 flex-col gap-0.5 sm:flex-row">
              <button type="button" class="icon-btn h-8 w-8" :disabled="i === 0" aria-label="Yuqoriga" title="Yuqoriga" @click="move(i, -1)"><ArrowUp class="h-4 w-4" /></button>
              <button type="button" class="icon-btn h-8 w-8" :disabled="i === form.questions.length - 1" aria-label="Pastga" title="Pastga" @click="move(i, 1)"><ArrowDown class="h-4 w-4" /></button>
              <button type="button" class="icon-btn h-8 w-8 hover:bg-red-50 hover:text-red-600" aria-label="Savolni o‘chirish" title="O‘chirish" @click="removeQuestion(i)"><Trash2 class="h-4 w-4" /></button>
            </div>
          </div>

          <div class="mt-3 space-y-2 sm:pl-8">
            <div v-for="(opt, oi) in q.options" :key="oi" class="flex items-center gap-2">
              <button
                type="button"
                :class="[
                  'grid h-9 w-9 shrink-0 place-items-center rounded-lg border text-xs font-semibold transition-colors',
                  q.correctIndex === oi ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-line bg-white text-muted hover:border-emerald-400 hover:text-emerald-600',
                ]"
                :aria-label="`${letters[oi]} variantni to‘g‘ri javob deb belgilash`"
                :aria-pressed="q.correctIndex === oi"
                :title="q.correctIndex === oi ? 'To‘g‘ri javob' : 'To‘g‘ri javob deb belgilash'"
                @click="q.correctIndex = oi; delete qErrors[i]"
              >
                <Check v-if="q.correctIndex === oi" class="h-4 w-4" />
                <span v-else>{{ letters[oi] }}</span>
              </button>
              <input v-model="q.options[oi]" class="form-input h-9" :placeholder="`${letters[oi]} variant`" @input="delete qErrors[i]" />
              <button type="button" class="icon-btn h-8 w-8" :disabled="q.options.length <= 2" aria-label="Variantni olib tashlash" @click="removeOption(q, oi)">
                <X class="h-4 w-4" />
              </button>
            </div>
            <div class="flex items-center justify-between gap-3">
              <button v-if="q.options.length < 6" type="button" class="text-[13px] font-medium text-primary-600 hover:underline" @click="addOption(q)">+ Variant qo‘shish</button>
              <span v-else />
              <p v-if="qErrors[i]" class="form-error !mt-0">{{ qErrors[i] }}</p>
              <p v-else class="text-xs text-muted">✓ — to‘g‘ri javob</p>
            </div>
          </div>
        </li>
      </ol>

      <Button class="mt-3" variant="secondary" :icon="Plus" block @click="addQuestion">Savol qo‘shish</Button>
    </form>

    <template #footer>
      <Button variant="secondary" :disabled="saving" @click="emit('close')">Bekor qilish</Button>
      <Button type="submit" form="test-form" :loading="saving">Saqlash</Button>
    </template>
  </Modal>
</template>
