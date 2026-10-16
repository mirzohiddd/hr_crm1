<script setup>
import { Check, ThumbsDown, ThumbsUp } from 'lucide-vue-next'

/** «Qo‘shilmayman» (0) / «Qo‘shilaman» (1) — ikki variantli javob */
defineProps({
  modelValue: { type: Number, default: null },
  options: { type: Array, default: () => ['Qo‘shilmayman', 'Qo‘shilaman'] },
  name: { type: String, required: true },
  invalid: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const ICONS = [ThumbsDown, ThumbsUp]
</script>

<template>
  <div role="radiogroup" :aria-label="name" :aria-invalid="invalid || undefined" class="grid grid-cols-2 gap-2.5">
    <button
      v-for="(text, i) in options"
      :key="i"
      type="button"
      role="radio"
      :aria-checked="modelValue === i"
      :class="['agree', i === 1 ? 'is-yes' : 'is-no', modelValue === i && 'is-active', invalid && 'is-invalid']"
      @click="emit('update:modelValue', i)"
    >
      <component :is="ICONS[i] || Check" class="h-4 w-4 shrink-0" aria-hidden="true" />
      <span class="truncate">{{ text }}</span>
    </button>
  </div>
</template>

<style scoped>
.agree {
  @apply flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-line bg-white px-3 text-sm font-semibold text-slate-600 transition-all duration-150 sm:h-12;
  @apply hover:-translate-y-0.5 hover:border-primary-300 hover:text-ink focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/20 active:translate-y-0;
}
.agree.is-invalid {
  @apply border-red-200 bg-red-50/40;
}
.agree.is-no.is-active {
  @apply border-transparent bg-slate-700 text-white shadow-md shadow-slate-700/25;
}
.agree.is-yes.is-active {
  @apply border-transparent bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/30;
}
</style>
