<script setup>
import { Inbox } from 'lucide-vue-next'

defineProps({
  icon: { type: [Object, Function], default: () => Inbox },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <div :class="['flex flex-col items-center px-6 text-center', compact ? 'py-10' : 'py-16']">
    <span class="grid h-12 w-12 place-items-center rounded-xl bg-primary-50 text-primary-600">
      <component :is="icon" class="h-6 w-6" />
    </span>
    <h3 class="mt-4 text-[15px] font-semibold text-ink">{{ title }}</h3>
    <p v-if="description" class="mt-1 max-w-sm text-sm text-muted">{{ description }}</p>
    <div v-if="$slots.default" class="mt-5 flex flex-wrap justify-center gap-2">
      <slot />
    </div>
  </div>
</template>
