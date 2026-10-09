<script setup>
import { Check } from 'lucide-vue-next'

/** A/B/C/D variantli savol */
defineProps({
  modelValue: { type: Number, default: null },
  options: { type: Array, required: true },
  name: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])
const LETTERS = 'ABCDEFGH'
</script>

<template>
  <div role="radiogroup" :aria-label="name" class="grid gap-3">
    <button
      v-for="(text, i) in options"
      :key="i"
      type="button"
      role="radio"
      :aria-checked="modelValue === i"
      :class="['choice group', modelValue === i && 'is-active']"
      :style="{ '--i': i }"
      @click="emit('update:modelValue', i)"
    >
      <span class="choice-letter">{{ LETTERS[i] }}</span>
      <span class="flex-1 text-[15px] font-medium leading-snug">{{ text }}</span>
      <span class="choice-check" aria-hidden="true"><Check class="h-3.5 w-3.5" stroke-width="3" /></span>
    </button>
  </div>
</template>

<style scoped>
.choice {
  @apply relative flex w-full items-center gap-4 overflow-hidden rounded-2xl border border-line bg-white px-4 py-3.5 text-left text-ink sm:px-5 sm:py-4;
  @apply transition-all duration-200 ease-out hover:translate-x-1 hover:border-primary-300 hover:shadow-[0_12px_28px_-16px_rgba(37,99,235,0.45)];
  @apply focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/20;
  animation: choice-in 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  animation-delay: calc(var(--i) * 60ms);
}
.choice::before {
  content: '';
  @apply absolute inset-y-0 left-0 w-1 origin-top scale-y-0 bg-gradient-to-b from-primary-500 to-primary-700 transition-transform duration-300;
}
.choice-letter {
  @apply grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-primary-100 bg-primary-50 text-sm font-bold text-primary-700 transition-all duration-200;
}
.choice-check {
  @apply grid h-6 w-6 shrink-0 scale-50 place-items-center rounded-full bg-primary-600 text-white opacity-0 transition-all duration-200;
}
.choice.is-active {
  @apply border-primary-500 bg-primary-50/70 shadow-[0_14px_30px_-18px_rgba(37,99,235,0.6)];
}
.choice.is-active::before {
  @apply scale-y-100;
}
.choice.is-active .choice-letter {
  @apply border-transparent bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/30;
}
.choice.is-active .choice-check {
  @apply scale-100 opacity-100;
}
@keyframes choice-in {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
