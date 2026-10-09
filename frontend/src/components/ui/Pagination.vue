<script setup>
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const page = defineModel('page', { type: Number, default: 1 })
const props = defineProps({
  total: { type: Number, required: true },
  pageSize: { type: Number, default: 10 },
})

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const from = computed(() => (props.total ? (page.value - 1) * props.pageSize + 1 : 0))
const to = computed(() => Math.min(page.value * props.pageSize, props.total))

const pages = computed(() => {
  const n = totalPages.value
  const p = page.value
  if (n <= 7) return Array.from({ length: n }, (_, i) => i + 1)
  const list = [1]
  if (p > 3) list.push('…')
  for (let i = Math.max(2, p - 1); i <= Math.min(n - 1, p + 1); i++) list.push(i)
  if (p < n - 2) list.push('…')
  list.push(n)
  return list
})

function go(value) {
  page.value = Math.min(totalPages.value, Math.max(1, value))
}
</script>

<template>
  <div v-if="total > pageSize" class="flex items-center justify-between gap-4 border-t border-line px-4 py-3">
    <p class="text-[13px] text-muted">
      <span class="tabular-nums text-ink">{{ from }}–{{ to }}</span> / <span class="tabular-nums">{{ total }}</span>
    </p>
    <nav class="flex items-center gap-1" aria-label="Sahifalar">
      <button class="icon-btn h-8 w-8 disabled:pointer-events-none disabled:opacity-40" :disabled="page === 1" aria-label="Oldingi sahifa" @click="go(page - 1)">
        <ChevronLeft class="h-4 w-4" />
      </button>
      <template v-for="(p, i) in pages" :key="`${p}-${i}`">
        <span v-if="p === '…'" class="hidden w-6 text-center text-muted sm:inline">…</span>
        <button
          v-else
          :class="[
            'hidden h-8 min-w-8 rounded-lg px-2 text-[13px] font-medium tabular-nums transition-colors sm:inline-block',
            p === page ? 'bg-primary-50 text-primary-600' : 'text-slate-600 hover:bg-slate-100',
          ]"
          :aria-current="p === page ? 'page' : undefined"
          @click="go(p)"
        >
          {{ p }}
        </button>
      </template>
      <span class="px-2 text-[13px] tabular-nums text-muted sm:hidden">{{ page }} / {{ totalPages }}</span>
      <button class="icon-btn h-8 w-8 disabled:pointer-events-none disabled:opacity-40" :disabled="page === totalPages" aria-label="Keyingi sahifa" @click="go(page + 1)">
        <ChevronRight class="h-4 w-4" />
      </button>
    </nav>
  </div>
</template>
