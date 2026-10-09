import { defineStore } from 'pinia'
import { ref } from 'vue'

let seq = 0

export const useToastStore = defineStore('toast', () => {
  const items = ref([])

  function dismiss(id) {
    items.value = items.value.filter((t) => t.id !== id)
  }

  function push({ type = 'success', title, message = '', duration = 3800 }) {
    const id = ++seq
    items.value.push({ id, type, title, message })
    if (items.value.length > 4) items.value.shift()
    if (duration) setTimeout(() => dismiss(id), duration)
    return id
  }

  return {
    items,
    push,
    dismiss,
    success: (title, message) => push({ type: 'success', title, message }),
    error: (title, message) => push({ type: 'error', title, message, duration: 6000 }),
    info: (title, message) => push({ type: 'info', title, message }),
  }
})
