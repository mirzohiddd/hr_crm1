<script setup>
defineProps({
  variant: { type: String, default: 'table' }, // table | cards | block
  rows: { type: Number, default: 6 },
  label: { type: String, default: 'Yuklanmoqda...' },
})
</script>

<template>
  <div role="status" aria-live="polite" :aria-label="label">
    <span class="sr-only">{{ label }}</span>

    <div v-if="variant === 'table'" class="divide-y divide-line">
      <div v-for="i in rows" :key="i" class="flex items-center gap-4 px-4 py-4">
        <div class="h-8 w-8 shrink-0 animate-pulse rounded-full bg-slate-100" />
        <div class="flex-1 space-y-2">
          <div class="h-3 w-1/3 animate-pulse rounded bg-slate-100" />
          <div class="h-2.5 w-1/5 animate-pulse rounded bg-slate-100" />
        </div>
        <div class="hidden h-3 w-24 animate-pulse rounded bg-slate-100 sm:block" />
        <div class="h-5 w-16 animate-pulse rounded-full bg-slate-100" />
      </div>
    </div>

    <div v-else-if="variant === 'cards'" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <div v-for="i in rows" :key="i" class="card space-y-4 p-5">
        <div class="h-4 w-1/2 animate-pulse rounded bg-slate-100" />
        <div class="space-y-2.5">
          <div class="h-3 w-2/3 animate-pulse rounded bg-slate-100" />
          <div class="h-3 w-3/4 animate-pulse rounded bg-slate-100" />
          <div class="h-3 w-1/2 animate-pulse rounded bg-slate-100" />
        </div>
        <div class="h-8 w-full animate-pulse rounded-lg bg-slate-100" />
      </div>
    </div>

    <div v-else class="h-full min-h-[200px] w-full animate-pulse rounded-lg bg-slate-100" />
  </div>
</template>
