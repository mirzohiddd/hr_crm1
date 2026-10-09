<script setup>
defineProps({
  label: { type: String, default: '' },
  for: { type: String, default: undefined },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  required: { type: Boolean, default: false },
})
</script>

<template>
  <div>
    <label v-if="label" :for="$props.for" class="form-label">
      {{ label }}<span v-if="required" class="ml-0.5 text-red-500" aria-hidden="true">*</span>
    </label>
    <slot />
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-else-if="hint" class="form-hint">{{ hint }}</p>
  </div>
</template>
