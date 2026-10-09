<script setup>
import { ref } from 'vue'
import { Search, X } from 'lucide-vue-next'

const model = defineModel({ type: String, default: '' })
defineProps({
  placeholder: { type: String, default: 'Qidirish...' },
  label: { type: String, default: 'Qidirish' },
})
const input = ref(null)

function clear() {
  model.value = ''
  input.value?.focus()
}
defineExpose({ focus: () => input.value?.focus() })
</script>

<template>
  <label class="relative block">
    <span class="sr-only">{{ label }}</span>
    <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
    <input ref="input" v-model="model" type="search" :placeholder="placeholder" class="form-input pl-9 pr-9" autocomplete="off" />
    <button
      v-if="model"
      type="button"
      class="absolute right-1.5 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-md text-muted hover:bg-slate-100 hover:text-ink"
      aria-label="Qidiruvni tozalash"
      @click="clear"
    >
      <X class="h-4 w-4" />
    </button>
  </label>
</template>
