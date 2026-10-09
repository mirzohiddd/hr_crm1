<script setup>
import { computed, ref, watch } from 'vue'
import { Check, ChevronDown, Clock, ExternalLink, Lock, RotateCcw } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useTrainingsStore, trainingProgress } from '@/stores/trainings'
import { TRAINING_DAYS } from '@/constants'
import { formatDate, formatDateTime, todayISO } from '@/utils/date'
import { toLines } from '@/utils/format'

const props = defineProps({
  training: { type: Object, required: true },
  busyDay: { type: Number, default: null },
})
const emit = defineEmits(['complete', 'undo'])

const store = useTrainingsStore()
const today = todayISO()
const progress = computed(() => trainingProgress(props.training))

// Keyingi bajariladigan kun avtomatik ochiladi
const expanded = ref(null)
watch(
  () => [props.training.id, progress.value.nextDay],
  () => (expanded.value = progress.value.nextDay),
  { immediate: true },
)

const days = computed(() =>
  Array.from({ length: TRAINING_DAYS }, (_, i) => {
    const day = i + 1
    const done = props.training.completedDays.find((d) => d.day === day)
    const isNext = progress.value.nextDay === day
    const planned = progress.value.plannedDate(day)
    return {
      day,
      lesson: store.lessonOf(day),
      done,
      isNext,
      locked: !done && !isNext,
      planned,
      overdue: isNext && planned < today,
      canUndo: !!done && !progress.value.finished && day === progress.value.done,
    }
  }),
)

const toggle = (day) => (expanded.value = expanded.value === day ? null : day)
</script>

<template>
  <ol class="relative space-y-2">
    <li v-for="d in days" :key="d.day" class="relative">
      <div
        :class="[
          'rounded-xl border transition-colors',
          d.done ? 'border-line bg-white' : d.isNext ? 'border-primary-200 bg-primary-50/40 ring-1 ring-primary-100' : 'border-line bg-slate-50/50',
        ]"
      >
        <button type="button" class="flex w-full items-center gap-3 px-3.5 py-3 text-left sm:px-4" :aria-expanded="expanded === d.day" @click="toggle(d.day)">
          <span
            :class="[
              'grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-semibold',
              d.done ? 'bg-primary-600 text-white' : d.isNext ? 'bg-white text-primary-600 ring-2 ring-primary-500' : 'bg-white text-slate-400 ring-1 ring-line',
            ]"
          >
            <Check v-if="d.done" class="h-4 w-4" />
            <span v-else>{{ d.day }}</span>
          </span>
          <span class="min-w-0 flex-1">
            <span class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
              <span class="text-xs font-medium text-muted">{{ d.day }}-kun</span>
              <span v-if="d.overdue" class="rounded bg-amber-50 px-1.5 text-[11px] font-medium text-amber-700">Rejadan ortda</span>
              <span v-else-if="d.isNext" class="rounded bg-primary-100 px-1.5 text-[11px] font-medium text-primary-700">Navbatdagi</span>
            </span>
            <span :class="['block truncate text-sm font-medium', d.locked ? 'text-slate-500' : 'text-ink']">{{ d.lesson?.title || 'Dars belgilanmagan' }}</span>
            <span class="mt-0.5 block text-xs text-muted">
              <template v-if="d.done">Bajarildi: {{ formatDateTime(d.done.at) }}<template v-if="d.done.by"> · {{ d.done.by }}</template></template>
              <template v-else>Reja: {{ formatDate(d.planned) }}<template v-if="d.lesson?.duration"> · {{ d.lesson.duration }} daqiqa</template></template>
            </span>
          </span>
          <Lock v-if="d.locked" class="h-4 w-4 shrink-0 text-slate-300" />
          <ChevronDown :class="['h-4 w-4 shrink-0 text-muted transition-transform', expanded === d.day && 'rotate-180']" />
        </button>

        <div v-if="expanded === d.day" class="border-t border-line/70 px-4 pb-4 pt-3 sm:pl-[60px]">
          <p v-if="d.lesson?.description" class="text-sm text-slate-600">{{ d.lesson.description }}</p>
          <ul v-if="d.lesson?.content" class="mt-2.5 space-y-1.5">
            <li v-for="(line, i) in toLines(d.lesson.content)" :key="i" class="flex gap-2 text-sm text-ink">
              <span class="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary-500" />{{ line }}
            </li>
          </ul>
          <a v-if="d.lesson?.link" :href="d.lesson.link" target="_blank" rel="noopener" class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:underline">
            <ExternalLink class="h-4 w-4" /> Dars materiali
          </a>

          <div class="mt-4 flex flex-wrap items-center gap-2">
            <Button v-if="d.isNext" size="sm" :icon="Check" :loading="busyDay === d.day" :disabled="!!busyDay" @click="emit('complete', d.day)">
              {{ d.day === TRAINING_DAYS ? 'Bajarildi — testga yuborish' : 'Bajarildi deb belgilash' }}
            </Button>
            <Button v-if="d.canUndo" size="sm" variant="ghost" :icon="RotateCcw" :disabled="!!busyDay" @click="emit('undo', d.day)">Bekor qilish</Button>
            <p v-if="d.locked" class="inline-flex items-center gap-1.5 text-xs text-muted">
              <Clock class="h-3.5 w-3.5" /> Avval {{ progress.nextDay }}-kunni yakunlang
            </p>
          </div>
        </div>
      </div>
    </li>
  </ol>
</template>
