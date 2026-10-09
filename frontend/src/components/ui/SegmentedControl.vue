<script setup>
const model = defineModel({ type: [String, Number], default: '' })
defineProps({
  options: { type: Array, required: true }, // [{ value, label, count? }]
  ariaLabel: { type: String, default: '' },
})
</script>

<template>
  <div class="inline-flex max-w-full overflow-x-auto rounded-lg bg-slate-100 p-1" role="tablist" :aria-label="ariaLabel">
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      role="tab"
      :aria-selected="model === o.value"
      :class="[
        'inline-flex h-8 items-center gap-1.5 whitespace-nowrap rounded-md px-3 text-[13px] font-medium transition-colors',
        model === o.value ? 'bg-white text-ink shadow-sm ring-1 ring-line' : 'text-muted hover:text-ink',
      ]"
      @click="model = o.value"
    >
      {{ o.label }}
      <span
        v-if="o.count !== undefined"
        :class="['rounded px-1.5 text-[11px] tabular-nums', model === o.value ? 'bg-primary-50 text-primary-700' : 'bg-slate-200/70 text-slate-500']"
      >{{ o.count }}</span>
    </button>
  </div>
</template>
