<script setup>
import { AlertTriangle, RotateCw } from 'lucide-vue-next'
import Button from './Button.vue'

defineProps({
  title: { type: String, default: 'Ma’lumotlarni yuklab bo‘lmadi' },
  message: { type: String, default: '' },
})
const emit = defineEmits(['retry'])
</script>

<template>
  <div class="flex flex-col items-center px-6 py-14 text-center" role="alert">
    <span class="grid h-12 w-12 place-items-center rounded-xl bg-red-50 text-red-600">
      <AlertTriangle class="h-6 w-6" />
    </span>
    <h3 class="mt-4 text-[15px] font-semibold text-ink">{{ title }}</h3>
    <p v-if="message" class="mt-1 max-w-sm text-sm text-muted">{{ message }}</p>
    <Button class="mt-5" variant="secondary" :icon="RotateCw" @click="emit('retry')">Qayta urinish</Button>
  </div>
</template>
