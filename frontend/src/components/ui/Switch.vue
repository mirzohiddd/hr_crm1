<script setup>
const model = defineModel({ type: Boolean, default: false })
defineProps({ label: { type: String, default: '' }, disabled: { type: Boolean, default: false } })
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="model"
    :aria-label="label || undefined"
    :disabled="disabled"
    :class="[
      'relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-150 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-50',
      model ? 'bg-primary-600' : 'bg-slate-200',
    ]"
    @click="model = !model"
  >
    <span :class="['inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-150', model ? 'translate-x-[22px]' : 'translate-x-0.5']" />
  </button>
</template>
