<script setup>
import { computed } from 'vue'
import { TRAINING_DAYS } from '@/constants'

const props = defineProps({
  done: { type: Number, default: 0 },
  showLabel: { type: Boolean, default: true },
  size: { type: String, default: 'md' }, // sm | md
})
const percent = computed(() => Math.round((props.done / TRAINING_DAYS) * 100))
</script>

<template>
  <div>
    <div v-if="showLabel" class="mb-1.5 flex items-baseline justify-between text-xs">
      <span class="text-muted">Progress</span>
      <span class="font-medium tabular-nums text-ink">{{ done }}/{{ TRAINING_DAYS }} kun</span>
    </div>
    <div class="flex gap-1" role="progressbar" :aria-valuenow="percent" aria-valuemin="0" aria-valuemax="100" :aria-label="`${done} / ${TRAINING_DAYS} kun bajarilgan`">
      <span
        v-for="d in TRAINING_DAYS"
        :key="d"
        :class="['flex-1 rounded-full transition-colors', size === 'sm' ? 'h-1.5' : 'h-2', d <= done ? 'bg-primary-600' : 'bg-slate-100']"
      />
    </div>
  </div>
</template>
