<script setup>
import { computed } from 'vue'
import { initials } from '@/utils/format'
import { hashString } from '@/utils/random'

const props = defineProps({
  name: { type: String, default: '' },
  src: { type: String, default: null },
  size: { type: String, default: 'md' }, // xs | sm | md | lg | xl
})

const SIZES = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-14 w-14 text-base',
  xl: 'h-20 w-20 text-xl',
}
const PALETTE = [
  'bg-primary-50 text-primary-700',
  'bg-sky-50 text-sky-700',
  'bg-cyan-50 text-cyan-700',
  'bg-slate-100 text-slate-700',
  'bg-primary-100 text-primary-700',
]
const tone = computed(() => PALETTE[hashString(props.name) % PALETTE.length])
</script>

<template>
  <span :class="['relative inline-grid shrink-0 place-items-center overflow-hidden rounded-full font-semibold', SIZES[size], !src && tone]">
    <img v-if="src" :src="src" :alt="name" class="h-full w-full object-cover" />
    <span v-else aria-hidden="true">{{ initials(name) }}</span>
  </span>
</template>
