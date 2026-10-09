<script setup>
import { Loader2 } from 'lucide-vue-next'

defineProps({
  variant: { type: String, default: 'primary' }, // primary | secondary | ghost | danger | danger-outline
  size: { type: String, default: 'md' }, // sm | md
  type: { type: String, default: 'button' },
  icon: { type: [Object, Function], default: null },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
})

const variants = {
  primary: 'bg-primary-600 text-white shadow-sm shadow-primary-600/20 hover:bg-primary-700 hover:shadow-md hover:shadow-primary-600/25',
  secondary: 'border border-line bg-white text-ink hover:border-slate-300 hover:bg-slate-50',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-ink',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  'danger-outline': 'border border-red-200 bg-white text-red-600 hover:border-red-300 hover:bg-red-50',
}
const sizes = {
  sm: 'h-8 gap-1.5 px-3 text-[13px]',
  md: 'h-10 gap-2 px-4 text-sm',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :class="[
      'inline-flex select-none items-center justify-center whitespace-nowrap rounded-lg font-medium transition-all duration-150 active:scale-[0.97]',
      'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-60',
      variants[variant],
      sizes[size],
      block && 'w-full',
    ]"
  >
    <Loader2 v-if="loading" class="h-4 w-4 shrink-0 animate-spin" />
    <component :is="icon" v-else-if="icon" class="h-4 w-4 shrink-0" />
    <slot />
  </button>
</template>
