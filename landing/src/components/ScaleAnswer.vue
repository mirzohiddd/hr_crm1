<script setup>
/** 1–5 ballik baho: katta plitkalar (mobil — ro‘yxat) */
const props = defineProps({
  modelValue: { type: Number, default: null },
  min: { type: Number, default: 1 },
  max: { type: Number, default: 5 },
  labels: { type: Array, default: () => [] },
  name: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])
const values = Array.from({ length: props.max - props.min + 1 }, (_, i) => props.min + i)
const label = (v) => props.labels[v - props.min] || String(v)
</script>

<template>
  <div>
    <div class="mb-3 hidden items-center gap-3 text-[11px] font-medium uppercase tracking-wider text-slate-400 sm:flex" aria-hidden="true">
      <span>{{ label(min) }}</span>
      <span class="h-px flex-1 bg-gradient-to-r from-slate-200 via-primary-200 to-primary-500" />
      <span class="text-primary-600">{{ label(max) }}</span>
    </div>
    <div role="radiogroup" :aria-label="name" class="grid gap-2.5 sm:grid-cols-5 sm:gap-3">
      <button
        v-for="(v, i) in values"
        :key="v"
        type="button"
        role="radio"
        :aria-checked="modelValue === v"
        :class="['scale-tile group', modelValue === v && 'is-active']"
        :style="{ '--i': i }"
        @click="emit('update:modelValue', v)"
      >
        <span class="scale-num">{{ v }}</span>
        <span class="scale-label">{{ label(v) }}</span>
        <span class="scale-bar" aria-hidden="true">
          <span v-for="n in values.length" :key="n" :class="['h-1 flex-1 rounded-full transition-colors duration-300', n <= i + 1 ? 'bg-current' : 'bg-current opacity-20']" />
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.scale-tile {
  @apply relative flex items-center gap-3 overflow-hidden rounded-2xl border border-line bg-white px-4 py-3 text-left text-primary-600;
  @apply transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-[0_12px_28px_-14px_rgba(37,99,235,0.45)];
  @apply focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/20;
  animation: tile-in 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  animation-delay: calc(var(--i) * 45ms);
}
@screen sm {
  .scale-tile {
    @apply flex-col items-center gap-2 px-2 pb-4 pt-5 text-center;
  }
}
.scale-num {
  @apply grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary-50 text-lg font-bold tabular-nums text-primary-700 transition-all duration-200;
}
@screen sm {
  .scale-num {
    @apply h-12 w-12 text-xl;
  }
}
.scale-label {
  @apply flex-1 text-sm font-medium leading-snug text-slate-600 transition-colors;
}
@screen sm {
  .scale-label {
    @apply min-h-[2.5rem] flex-none text-[12.5px];
  }
}
.scale-bar {
  @apply hidden w-14 gap-0.5;
}
@screen sm {
  .scale-bar {
    @apply flex;
  }
}
.scale-tile.is-active {
  @apply -translate-y-0.5 border-transparent bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-[0_16px_32px_-14px_rgba(37,99,235,0.7)];
}
.scale-tile.is-active .scale-num {
  @apply scale-110 bg-white/20 text-white;
}
.scale-tile.is-active .scale-label {
  @apply text-white;
}
@keyframes tile-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
