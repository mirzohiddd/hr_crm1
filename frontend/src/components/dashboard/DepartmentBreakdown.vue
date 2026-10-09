<script setup>
import { computed } from 'vue'
import { percent } from '@/utils/format'

const props = defineProps({
  items: { type: Array, default: () => [] }, // [{ name, count }]
  title: { type: String, default: 'Bo‘limlar kesimida' },
  subtitle: { type: String, default: 'Faol xodimlar taqsimoti' },
})
const total = computed(() => props.items.reduce((s, d) => s + d.count, 0))
const max = computed(() => Math.max(1, ...props.items.map((d) => d.count)))
</script>

<template>
  <div>
    <h2 class="text-base font-semibold text-ink">{{ title }}</h2>
    <p class="mt-0.5 text-sm text-muted">{{ subtitle }}</p>
    <ul class="mt-5 space-y-4">
      <li v-for="d in items" :key="d.name">
        <div class="flex items-baseline justify-between gap-3 text-sm">
          <span class="text-ink">{{ d.name }}</span>
          <span class="tabular-nums text-muted">
            <span class="font-medium text-ink">{{ d.count }}</span><span class="ml-2 inline-block w-9 text-right">{{ percent(d.count, total) }}%</span>
          </span>
        </div>
        <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div class="h-full rounded-full bg-primary-600 transition-[width] duration-500" :style="{ width: `${(d.count / max) * 100}%` }" />
        </div>
      </li>
    </ul>
  </div>
</template>
