<script>
// Ochiq modallar steki: Esc faqat eng yuqoridagisini yopadi, scroll-lock to'g'ri qaytadi.
const stack = []
let uid = 0
</script>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm | md | lg | xl
  persistent: { type: Boolean, default: false }, // fonni bosganda yopilmaydi
})
const emit = defineEmits(['close'])

const id = ++uid
const titleId = `modal-title-${id}`
const panel = ref(null)
let lastFocused = null

const sizes = { sm: 'sm:max-w-md', md: 'sm:max-w-lg', lg: 'sm:max-w-2xl', xl: 'sm:max-w-4xl' }

function onKeydown(event) {
  if (event.key === 'Escape' && stack[stack.length - 1] === id) {
    event.stopPropagation()
    emit('close')
  }
}

function activate() {
  lastFocused = document.activeElement
  stack.push(id)
  document.body.style.overflow = 'hidden'
  document.addEventListener('keydown', onKeydown)
  nextTick(() => panel.value?.focus({ preventScroll: true }))
}

function deactivate() {
  const index = stack.indexOf(id)
  if (index === -1) return
  stack.splice(index, 1)
  if (!stack.length) document.body.style.overflow = ''
  document.removeEventListener('keydown', onKeydown)
  if (lastFocused instanceof HTMLElement && document.contains(lastFocused)) lastFocused.focus({ preventScroll: true })
}

watch(
  () => props.open,
  (value) => (value ? activate() : deactivate()),
  { immediate: true },
)
onBeforeUnmount(deactivate)

function onBackdrop() {
  if (!props.persistent) emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-6">
        <div class="absolute inset-0 bg-slate-900/40" aria-hidden="true" @click="onBackdrop" />
        <div
          ref="panel"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : undefined"
          tabindex="-1"
          :class="[
            'modal-panel relative flex max-h-[92vh] w-full flex-col rounded-t-2xl border border-line bg-white shadow-pop outline-none sm:rounded-2xl',
            sizes[size],
          ]"
        >
          <header v-if="title || $slots.header" class="flex items-start justify-between gap-4 border-b border-line px-5 py-4 sm:px-6">
            <slot name="header">
              <div class="min-w-0">
                <h2 :id="titleId" class="text-base font-semibold text-ink sm:text-lg">{{ title }}</h2>
                <p v-if="subtitle" class="mt-0.5 text-sm text-muted">{{ subtitle }}</p>
              </div>
            </slot>
            <button class="icon-btn -mr-2 -mt-1" aria-label="Yopish" @click="emit('close')">
              <X class="h-5 w-5" />
            </button>
          </header>

          <div class="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
            <slot />
          </div>

          <footer
            v-if="$slots.footer"
            class="flex flex-col-reverse gap-2 rounded-b-2xl border-t border-line bg-slate-50/70 px-5 py-4 sm:flex-row sm:items-center sm:justify-end sm:px-6"
          >
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
