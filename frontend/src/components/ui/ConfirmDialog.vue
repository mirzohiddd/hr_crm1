<script setup>
import { AlertTriangle } from 'lucide-vue-next'
import Modal from './Modal.vue'
import Button from './Button.vue'

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  message: { type: String, default: '' },
  confirmText: { type: String, default: 'Tasdiqlash' },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'close'])
</script>

<template>
  <Modal :open="open" size="sm" :persistent="loading" @close="!loading && emit('close')">
    <div class="flex gap-4">
      <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-red-50 text-red-600">
        <AlertTriangle class="h-5 w-5" />
      </span>
      <div>
        <h2 class="text-base font-semibold text-ink">{{ title }}</h2>
        <p v-if="message" class="mt-1 text-sm text-muted">{{ message }}</p>
      </div>
    </div>
    <template #footer>
      <Button variant="secondary" :disabled="loading" @click="emit('close')">Bekor qilish</Button>
      <Button variant="danger" :loading="loading" @click="emit('confirm')">{{ confirmText }}</Button>
    </template>
  </Modal>
</template>
