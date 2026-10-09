<script setup>
import { onMounted, reactive, ref } from 'vue'
import { BookOpenCheck, ChevronDown, Save } from 'lucide-vue-next'
import SettingsSection from './SettingsSection.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import { useTrainingsStore } from '@/stores/trainings'
import { useToast } from '@/composables/useToast'

const store = useTrainingsStore()
const toast = useToast()

const open = ref(null)
const drafts = reactive({})
const errors = reactive({})
const saving = ref(null)

onMounted(() => store.fetchAll())

function toggle(lesson) {
  if (open.value === lesson.id) return (open.value = null)
  open.value = lesson.id
  drafts[lesson.id] = { title: lesson.title, duration: lesson.duration, description: lesson.description, content: lesson.content, link: lesson.link || '' }
  errors[lesson.id] = {}
}

async function save(lesson) {
  const d = drafts[lesson.id]
  const e = {}
  if (!d.title.trim()) e.title = 'Mavzuni kiriting'
  const minutes = Number(d.duration)
  if (!Number.isInteger(minutes) || minutes < 5 || minutes > 600) e.duration = '5–600 daqiqa'
  if (d.link && !/^https?:\/\//i.test(d.link.trim())) e.link = 'Havola http:// yoki https:// bilan boshlansin'
  errors[lesson.id] = e
  if (Object.keys(e).length) return
  saving.value = lesson.id
  try {
    await store.updateLesson(lesson.id, { ...d, title: d.title.trim(), duration: minutes, description: d.description.trim(), content: d.content.trim(), link: d.link.trim() })
    toast.success(`${lesson.day}-kun darsi saqlandi`)
    open.value = null
  } catch (err) {
    toast.error('Saqlab bo‘lmadi', err.message)
  } finally {
    saving.value = null
  }
}
</script>

<template>
  <SettingsSection :icon="BookOpenCheck" title="Darslar" subtitle="7 kunlik o‘quv dasturi: har bir kun mavzusi va mazmuni">
    <LoadingState v-if="!store.lessons.length && store.loading" :rows="7" />
    <ol v-else class="divide-y divide-line">
      <li v-for="l in store.lessons" :key="l.id">
        <button class="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-slate-50/70" :aria-expanded="open === l.id" @click="toggle(l)">
          <span class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary-50 text-sm font-semibold text-primary-700">{{ l.day }}</span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-medium text-ink">{{ l.title }}</span>
            <span class="block truncate text-xs text-muted">{{ l.duration }} daqiqa · {{ l.description }}</span>
          </span>
          <ChevronDown :class="['h-4 w-4 shrink-0 text-muted transition-transform', open === l.id && 'rotate-180']" />
        </button>

        <form v-if="open === l.id && drafts[l.id]" class="grid gap-4 border-t border-line bg-slate-50/50 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_140px]" novalidate @submit.prevent="save(l)">
          <FormField label="Mavzu" :for="`l-title-${l.id}`" :error="errors[l.id]?.title" required>
            <input :id="`l-title-${l.id}`" v-model="drafts[l.id].title" class="form-input" :class="errors[l.id]?.title && 'has-error'" />
          </FormField>
          <FormField label="Davomiyligi" :for="`l-dur-${l.id}`" :error="errors[l.id]?.duration">
            <div class="relative">
              <input :id="`l-dur-${l.id}`" v-model.number="drafts[l.id].duration" type="number" min="5" class="form-input pr-14 tabular-nums" />
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted">daqiqa</span>
            </div>
          </FormField>
          <FormField class="sm:col-span-2" label="Qisqacha tavsif" :for="`l-desc-${l.id}`">
            <input :id="`l-desc-${l.id}`" v-model="drafts[l.id].description" class="form-input" />
          </FormField>
          <FormField class="sm:col-span-2" label="Dars rejasi" :for="`l-content-${l.id}`" hint="Har bir bandni yangi qatorda yozing">
            <textarea :id="`l-content-${l.id}`" v-model="drafts[l.id].content" rows="5" class="form-input" />
          </FormField>
          <FormField class="sm:col-span-2" label="Material havolasi (video, hujjat)" :for="`l-link-${l.id}`" :error="errors[l.id]?.link">
            <input :id="`l-link-${l.id}`" v-model="drafts[l.id].link" type="url" class="form-input" placeholder="https://..." />
          </FormField>
          <div class="flex justify-end gap-2 sm:col-span-2">
            <Button variant="ghost" :disabled="saving === l.id" @click="open = null">Bekor qilish</Button>
            <Button type="submit" :icon="Save" :loading="saving === l.id">Saqlash</Button>
          </div>
        </form>
      </li>
    </ol>
  </SettingsSection>
</template>
