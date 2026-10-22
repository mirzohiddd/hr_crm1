<script setup>
import { ref } from 'vue'
import { Expand, ImageOff, Lock, X } from 'lucide-vue-next'
import ChoiceAnswer from '@/components/ChoiceAnswer.vue'

/**
 * Rasmli savol (persona testi, oxirgi bosqich): rasm + 4 ta variant (A–D).
 * Nomzod rasmda birinchi bo‘lib ko‘rgan narsani tanlaydi. Tanlangan variant qulflanadi (o‘zgartirib bo‘lmaydi).
 * Variant tavsiflari faqat HR hisobotida.
 */
defineProps({
  picture: { type: Object, required: true }, // { id, title, question, image, options: [text] }
  src: { type: String, required: true },
  number: { type: Number, required: true },
  modelValue: { type: Number, default: null },
  invalid: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const zoom = ref(false)
const broken = ref(false)
</script>

<template>
  <div class="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:gap-7">
    <div>
      <button
        type="button"
        class="pic-frame group"
        :class="{ 'is-invalid': invalid }"
        :aria-label="`${picture.title}: kattalashtirish`"
        :disabled="broken"
        @click="zoom = true"
      >
        <img v-if="!broken" :src="src" :alt="picture.title" class="h-full w-full object-contain" loading="lazy" draggable="false" @error="broken = true" />
        <span v-else class="flex flex-col items-center gap-2 text-sm text-muted"><ImageOff class="h-6 w-6" /> Rasmni yuklab bo‘lmadi</span>
        <span v-if="!broken" class="pic-zoom"><Expand class="h-4 w-4" /></span>
        <span class="pic-badge">{{ number }}</span>
      </button>
    </div>
    <div class="min-w-0">
      <p class="text-xs font-semibold uppercase tracking-wider text-primary-600">{{ picture.title }}</p>
      <h3 class="mt-1 text-lg font-semibold leading-snug tracking-tight text-ink">{{ picture.question }}</h3>
      <div class="mt-4">
        <!-- Javob tanlangach qulflanadi: boshqa variantni tanlab bo‘lmaydi -->
        <ChoiceAnswer :model-value="modelValue" :options="picture.options" :name="`${picture.title}: ${picture.question}`" :locked="modelValue !== null" @update:model-value="emit('update:modelValue', $event)" />
      </div>
      <p v-if="modelValue !== null" class="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
        <Lock class="h-3.5 w-3.5" /> Javob qabul qilindi — o‘zgartirib bo‘lmaydi
      </p>
    </div>

    <Teleport to="body">
      <Transition name="zoom">
        <div v-if="zoom" class="fixed inset-0 z-50 grid place-items-center bg-slate-950/85 p-4 backdrop-blur-sm" role="dialog" :aria-label="picture.title" @click.self="zoom = false" @keydown.esc="zoom = false">
          <img :src="src" :alt="picture.title" class="max-h-[88vh] max-w-full rounded-2xl bg-white object-contain shadow-2xl" />
          <button type="button" class="absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-full bg-white/90 text-ink shadow-lg" aria-label="Yopish" @click="zoom = false"><X class="h-5 w-5" /></button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.pic-frame {
  @apply relative grid aspect-[4/3] w-full place-items-center overflow-hidden rounded-2xl border border-line bg-white p-2 transition-all duration-200;
  @apply hover:border-primary-300 hover:shadow-[0_16px_36px_-20px_rgba(37,99,235,0.5)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary-500/20;
}
.pic-frame.is-invalid {
  @apply border-red-300 ring-4 ring-red-100;
}
.pic-zoom {
  @apply absolute bottom-3 right-3 grid h-8 w-8 place-items-center rounded-lg bg-white/90 text-slate-600 opacity-0 shadow-md transition-opacity group-hover:opacity-100;
}
.pic-badge {
  @apply absolute left-3 top-3 grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary-600 to-primary-500 text-sm font-bold text-white shadow-md shadow-primary-600/30;
}
.zoom-enter-active,
.zoom-leave-active {
  transition: opacity 0.2s ease;
}
.zoom-enter-from,
.zoom-leave-to {
  opacity: 0;
}
</style>