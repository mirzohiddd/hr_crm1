<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'

const props = defineProps({
  data: { type: Array, default: () => [] }, // [{ label, fullLabel, total, hired, left }]
})

const mode = ref('total')
const modes = [
  { value: 'total', label: 'Jami xodimlar' },
  { value: 'flow', label: 'Qabul va ketish' },
]

// O'lcham konteyner kengligiga moslashadi (matn cho'zilmasligi uchun viewBox emas, haqiqiy piksel)
const wrap = ref(null)
const width = ref(640)
const HEIGHT = 260
const PAD = { top: 16, right: 8, bottom: 30, left: 36 }
let observer

onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    width.value = Math.max(280, Math.floor(entry.contentRect.width))
  })
  observer.observe(wrap.value)
})
onBeforeUnmount(() => observer?.disconnect())

const innerW = computed(() => width.value - PAD.left - PAD.right)
const innerH = HEIGHT - PAD.top - PAD.bottom
const n = computed(() => Math.max(1, props.data.length))
const band = computed(() => innerW.value / n.value)
const xAt = (i) => PAD.left + band.value * (i + 0.5)

const scale = computed(() => {
  if (!props.data.length) return { lo: 0, hi: 4 }
  if (mode.value === 'total') {
    const values = props.data.map((d) => d.total)
    const lo = Math.max(0, Math.floor((Math.min(...values) - 5) / 10) * 10)
    const hi = lo + Math.ceil((Math.max(...values) - lo + 5) / 40) * 40
    return { lo, hi }
  }
  const max = Math.max(...props.data.flatMap((d) => [d.hired, d.left]))
  return { lo: 0, hi: Math.max(4, Math.ceil((max + 1) / 4) * 4) }
})
const yAt = (v) => PAD.top + innerH * (1 - (v - scale.value.lo) / (scale.value.hi - scale.value.lo))
const ticks = computed(() => Array.from({ length: 5 }, (_, i) => scale.value.lo + ((scale.value.hi - scale.value.lo) * i) / 4))

const linePath = computed(() => props.data.map((d, i) => `${i ? 'L' : 'M'}${xAt(i)},${yAt(d.total)}`).join(' '))
const areaPath = computed(() => {
  if (!props.data.length) return ''
  const base = PAD.top + innerH
  return `${linePath.value} L${xAt(props.data.length - 1)},${base} L${xAt(0)},${base} Z`
})
const barW = computed(() => Math.max(4, Math.min(14, band.value * 0.26)))
const showLabel = (i) => band.value >= 36 || i % 2 === (props.data.length - 1) % 2

const active = ref(null)
const activeItem = computed(() => (active.value === null ? null : props.data[active.value]))
const tooltipLeft = computed(() => {
  if (active.value === null) return 0
  return Math.min(Math.max(xAt(active.value), 80), width.value - 80)
})

const totals = computed(() => ({
  current: props.data.at(-1)?.total ?? 0,
  hired: props.data.reduce((s, d) => s + d.hired, 0),
  left: props.data.reduce((s, d) => s + d.left, 0),
}))
</script>

<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 class="text-base font-semibold text-ink">Xodimlar statistikasi</h2>
        <p class="mt-0.5 text-sm text-muted">So‘nggi 12 oy</p>
      </div>
      <SegmentedControl v-model="mode" :options="modes" aria-label="Grafik turi" />
    </div>

    <dl class="mt-5 flex flex-wrap gap-x-8 gap-y-3">
      <div>
        <dt class="flex items-center gap-2 text-xs text-muted"><span class="h-2 w-2 rounded-full bg-primary-600" />Jami xodimlar</dt>
        <dd class="mt-1 text-lg font-semibold tabular-nums text-ink">{{ totals.current }}</dd>
      </div>
      <div>
        <dt class="flex items-center gap-2 text-xs text-muted"><span class="h-2 w-2 rounded-sm bg-primary-600" />Yangi xodimlar</dt>
        <dd class="mt-1 text-lg font-semibold tabular-nums text-ink">+{{ totals.hired }}</dd>
      </div>
      <div>
        <dt class="flex items-center gap-2 text-xs text-muted"><span class="h-2 w-2 rounded-sm bg-primary-300" />Ishdan ketganlar</dt>
        <dd class="mt-1 text-lg font-semibold tabular-nums text-ink">−{{ totals.left }}</dd>
      </div>
    </dl>

    <div ref="wrap" class="relative mt-4 w-full min-w-0 overflow-hidden" @mouseleave="active = null">
      <svg :width="width" :height="HEIGHT" class="block" role="img" :aria-label="mode === 'total' ? 'Jami xodimlar soni dinamikasi' : 'Oylik qabul qilingan va ishdan ketgan xodimlar'">
        <!-- grid -->
        <g>
          <template v-for="t in ticks" :key="t">
            <line :x1="PAD.left" :x2="width - PAD.right" :y1="yAt(t)" :y2="yAt(t)" stroke="#E2E8F0" :stroke-dasharray="t === scale.lo ? '' : '3 4'" />
            <text :x="PAD.left - 10" :y="yAt(t) + 4" text-anchor="end" class="fill-slate-400 text-[11px] tabular-nums">{{ Math.round(t) }}</text>
          </template>
        </g>

        <!-- active column highlight -->
        <rect v-if="active !== null" :x="xAt(active) - band / 2" :y="PAD.top" :width="band" :height="innerH" fill="#F1F5F9" rx="6" />

        <g v-if="mode === 'total'">
          <path :d="areaPath" fill="#EFF6FF" />
          <path :d="linePath" fill="none" stroke="#2563EB" stroke-width="2.25" stroke-linejoin="round" stroke-linecap="round" />
          <circle
            v-for="(d, i) in data"
            :key="d.key"
            :cx="xAt(i)"
            :cy="yAt(d.total)"
            :r="active === i ? 5 : 3"
            fill="#fff"
            stroke="#2563EB"
            stroke-width="2"
          />
        </g>
        <g v-else>
          <template v-for="(d, i) in data" :key="d.key">
            <rect :x="xAt(i) - barW - 1.5" :y="yAt(d.hired)" :width="barW" :height="Math.max(0, PAD.top + innerH - yAt(d.hired))" rx="3" fill="#2563EB" />
            <rect :x="xAt(i) + 1.5" :y="yAt(d.left)" :width="barW" :height="Math.max(0, PAD.top + innerH - yAt(d.left))" rx="3" fill="#93C5FD" />
          </template>
        </g>

        <!-- x labels -->
        <template v-for="(d, i) in data" :key="`l-${d.key}`">
          <text
            v-if="showLabel(i)"
            :x="xAt(i)"
            :y="HEIGHT - 8"
            text-anchor="middle"
            :class="['text-[11px]', active === i ? 'fill-ink font-medium' : 'fill-slate-400']"
          >{{ d.label }}</text>
        </template>

        <!-- hover zones -->
        <rect
          v-for="(d, i) in data"
          :key="`h-${d.key}`"
          :x="xAt(i) - band / 2"
          :y="PAD.top"
          :width="band"
          :height="innerH + PAD.bottom"
          fill="transparent"
          @mouseenter="active = i"
          @click="active = i"
        />
      </svg>

      <div
        v-if="activeItem"
        class="pointer-events-none absolute top-0 z-10 w-40 -translate-x-1/2 rounded-lg border border-line bg-white px-3 py-2.5 shadow-pop"
        :style="{ left: `${tooltipLeft}px` }"
      >
        <p class="text-xs font-medium text-ink">{{ activeItem.fullLabel }}</p>
        <div class="mt-1.5 space-y-1 text-xs">
          <p class="flex justify-between gap-3"><span class="text-muted">Jami</span><span class="font-medium tabular-nums text-ink">{{ activeItem.total }}</span></p>
          <p class="flex justify-between gap-3"><span class="text-muted">Yangi</span><span class="font-medium tabular-nums text-primary-600">+{{ activeItem.hired }}</span></p>
          <p class="flex justify-between gap-3"><span class="text-muted">Ketgan</span><span class="font-medium tabular-nums text-slate-600">−{{ activeItem.left }}</span></p>
        </div>
      </div>
    </div>
  </div>
</template>
