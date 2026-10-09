<script setup>
import { computed } from 'vue'
import { FileSpreadsheet, Instagram, Share2, UserRoundPlus } from 'lucide-vue-next'

const props = defineProps({ source: { type: String, default: '' }, size: { type: String, default: 'h-3.5 w-3.5' } })
const MAP = {
  Instagram: { icon: Instagram, cls: 'text-pink-600' },
  'Google Sheets': { icon: FileSpreadsheet, cls: 'text-emerald-600' },
  Tavsiya: { icon: UserRoundPlus, cls: 'text-primary-600' },
}
const item = computed(() => MAP[props.source] || { icon: Share2, cls: 'text-slate-500' })
</script>

<template>
  <component :is="item.icon" :class="['shrink-0', size, item.cls]" aria-hidden="true" />
</template>
