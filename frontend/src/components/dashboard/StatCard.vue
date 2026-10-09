<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  icon: { type: [Object, Function], required: true },
  tone: { type: String, default: 'blue' }, // blue | green | amber | red | slate
  hint: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

const TONES = {
  blue: 'bg-primary-50 text-primary-600',
  green: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  red: 'bg-red-50 text-red-600',
  slate: 'bg-slate-100 text-slate-600',
}
</script>

<template>
  <div class="card card-hover group p-5">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-sm leading-snug text-muted">{{ label }}</p>
        <div v-if="loading" class="mt-2.5 h-7 w-20 animate-pulse rounded bg-slate-100" />
        <p v-else class="mt-2 text-[28px] font-semibold leading-none tracking-tight text-ink tabular-nums">{{ value }}</p>
      </div>
      <span :class="['grid h-10 w-10 shrink-0 place-items-center rounded-xl transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110', TONES[tone]]">
        <component :is="icon" class="h-5 w-5" />
      </span>
    </div>
    <p v-if="$slots.hint || hint" class="mt-3 text-xs text-muted">
      <span v-if="loading" class="block h-3 w-28 animate-pulse rounded bg-slate-100" />
      <slot v-else name="hint">{{ hint }}</slot>
    </p>
  </div>
</template>
