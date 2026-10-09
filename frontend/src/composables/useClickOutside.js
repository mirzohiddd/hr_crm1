import { onBeforeUnmount, onMounted } from 'vue'

export function useClickOutside(targetRef, handler) {
  const listener = (event) => {
    const el = targetRef.value
    if (el && !el.contains(event.target)) handler(event)
  }
  onMounted(() => document.addEventListener('pointerdown', listener))
  onBeforeUnmount(() => document.removeEventListener('pointerdown', listener))
}
