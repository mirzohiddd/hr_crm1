<script setup>
defineProps({
  icon: { type: [Object, Function], required: true },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <section class="card overflow-hidden">
    <div class="flex flex-col gap-3 border-b border-line px-5 py-4 sm:flex-row sm:items-center">
      <div class="flex min-w-0 flex-1 items-center gap-3">
        <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600"><component :is="icon" class="h-[18px] w-[18px]" /></span>
        <div class="min-w-0">
          <h2 class="text-base font-semibold text-ink">{{ title }}</h2>
          <p v-if="subtitle" class="text-sm text-muted">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.actions" class="flex shrink-0 gap-2"><slot name="actions" /></div>
    </div>
    <slot />
    <div v-if="$slots.footer" class="flex justify-end gap-2 border-t border-line bg-slate-50/60 px-5 py-3">
      <slot name="footer" />
    </div>
  </section>
</template>
