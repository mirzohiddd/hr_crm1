<script setup>
import logoUrl from '@/assets/logo.png'

/** HR+ logotipi. Logotip ko‘k rangda — doim oq fonda ko‘rsatiladi. */
defineProps({
  size: { type: String, default: 'md' }, // sm | md | lg | xl
  text: { type: Boolean, default: true },
  framed: { type: Boolean, default: false }, // oq kartochka ichida (rangli fon ustida)
})
const SIZES = { sm: 'h-8 w-8', md: 'h-10 w-10', lg: 'h-14 w-14', xl: 'h-20 w-20' }
const TEXT = { sm: 'text-[15px]', md: 'text-[17px]', lg: 'text-xl', xl: 'text-2xl' }
</script>

<template>
  <span class="inline-flex min-w-0 items-center gap-2.5">
    <span :class="['grid shrink-0 place-items-center', framed && 'rounded-2xl bg-white p-1.5 shadow-lg shadow-primary-900/20 ring-1 ring-white/60']">
      <img :src="logoUrl" alt="HR+" :class="[SIZES[size], 'select-none object-contain']" draggable="false" />
    </span>
    <span v-if="text" :class="['truncate font-semibold tracking-tight', TEXT[size]]"><slot>HR CRM</slot></span>
  </span>
</template>
