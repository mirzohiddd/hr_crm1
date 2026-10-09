<script setup>
import { computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const model = defineModel({ type: [String, Number], default: '' })
const props = defineProps({
  options: { type: Array, default: () => [] }, // ['A', 'B'] yoki [{ value, label, disabled }]
  placeholder: { type: String, default: '' },
  id: { type: String, default: undefined },
  name: { type: String, default: undefined },
  error: { type: [String, Boolean], default: '' },
  disabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: undefined },
})

const normalized = computed(() =>
  props.options.map((o) => (typeof o === 'object' ? o : { value: o, label: o })),
)
</script>

<template>
  <div class="relative">
    <select
      :id="id"
      v-model="model"
      :name="name"
      :disabled="disabled"
      :aria-label="ariaLabel"
      :aria-invalid="!!error || undefined"
      :class="['form-input cursor-pointer appearance-none pr-9', error && 'has-error', model === '' && placeholder && 'text-slate-400']"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option v-for="o in normalized" :key="o.value" :value="o.value" :disabled="o.disabled" class="text-ink">{{ o.label }}</option>
    </select>
    <ChevronDown class="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
  </div>
</template>
