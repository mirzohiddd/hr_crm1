<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  size: { type: String, default: 'md' },
  label: { type: String, default: '' }, // ko‘rinadigan matn (bo‘lmasa status)
})

const TONE_BY_STATUS = {
  Faol: 'green',
  Yangi: 'blue',
  'Faol emas': 'slate',
  Tasdiqlangan: 'green',
  Kutilmoqda: 'amber',
  'Rad etilgan': 'red',
  // Nomzodlar
  'Bog‘lanildi': 'sky',
  'Bog‘lanilmadi': 'orange',
  Suhbat: 'amber',
  'Ishga qabul qilindi': 'green',
  'Rad etildi': 'red',
  // Darslar va testlar
  Jarayonda: 'blue',
  Yakunlandi: 'green',
  'Testga yuborildi': 'amber',
  'O‘tdi': 'green',
  'O‘tmadi': 'red',
  Yiqildi: 'red',
  'Boshlanmagan': 'slate',
  // Yangi xodimlar testi (HR tavsiyasi)
  'Tavsiya etiladi': 'green',
  'Suhbatda aniqlashtirish': 'amber',
  'Qo‘shimcha baholash kerak': 'orange',
  'Ishonchsiz natija': 'red',
  // Foydalanuvchilar
  Bloklangan: 'red',
}
const TONES = {
  green: ['bg-emerald-50 text-emerald-700 ring-emerald-600/15', 'bg-emerald-500'],
  blue: ['bg-primary-50 text-primary-700 ring-primary-600/15', 'bg-primary-600'],
  sky: ['bg-sky-50 text-sky-700 ring-sky-600/15', 'bg-sky-500'],
  orange: ['bg-orange-50 text-orange-700 ring-orange-600/20', 'bg-orange-500'],
  amber: ['bg-amber-50 text-amber-700 ring-amber-600/20', 'bg-amber-500'],
  red: ['bg-red-50 text-red-700 ring-red-600/15', 'bg-red-500'],
  slate: ['bg-slate-100 text-slate-600 ring-slate-500/15', 'bg-slate-400'],
}
const tone = computed(() => TONES[TONE_BY_STATUS[props.status] || 'slate'])
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 whitespace-nowrap rounded-full font-medium ring-1 ring-inset',
      size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-0.5 text-xs',
      tone[0],
    ]"
  >
    <span :class="['h-1.5 w-1.5 rounded-full', tone[1]]" aria-hidden="true" />
    {{ label || status }}
  </span>
</template>