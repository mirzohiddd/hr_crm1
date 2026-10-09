<script setup>
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-vue-next'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const ICONS = {
  success: { icon: CheckCircle2, cls: 'text-emerald-600' },
  error: { icon: AlertCircle, cls: 'text-red-600' },
  info: { icon: Info, cls: 'text-primary-600' },
}
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed inset-x-4 top-4 z-[80] flex flex-col items-end gap-2 sm:inset-x-auto sm:right-6 sm:top-20" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="t in toast.items"
          :key="t.id"
          class="pointer-events-auto flex w-full items-start gap-3 rounded-xl border border-line bg-white p-3.5 pr-2.5 shadow-pop sm:w-[360px]"
          :role="t.type === 'error' ? 'alert' : 'status'"
        >
          <component :is="ICONS[t.type].icon" :class="['mt-0.5 h-5 w-5 shrink-0', ICONS[t.type].cls]" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-ink">{{ t.title }}</p>
            <p v-if="t.message" class="mt-0.5 text-[13px] leading-snug text-muted">{{ t.message }}</p>
          </div>
          <button class="grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted hover:bg-slate-100 hover:text-ink" aria-label="Yopish" @click="toast.dismiss(t.id)">
            <X class="h-4 w-4" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
