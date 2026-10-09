<script setup>
import { ref, watch } from 'vue'
import { AlertCircle, Star } from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import { landingResultsApi } from '@/api/landing'

/** HR bilan kelishilgan baholash kaliti (backend/app/landing_tests/<slug>.json) */
const props = defineProps({
  open: { type: Boolean, default: false },
  slug: { type: String, required: true },
})
const emit = defineEmits(['close'])

const key = ref(null)
const loading = ref(false)
const error = ref('')

watch(
  () => props.open,
  async (open) => {
    if (!open || key.value) return
    loading.value = true
    error.value = ''
    try {
      key.value = await landingResultsApi.key(props.slug)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)
const sectionItems = (id) => key.value.questions.filter((q) => q.section === id)
</script>

<template>
  <Modal :open="open" size="xl" title="Baholash kaliti" :subtitle="key?.title || 'Nomzodlar testi'" @close="emit('close')">
    <LoadingState v-if="loading" :rows="5" />
    <p v-else-if="error" class="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700"><AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> {{ error }}</p>
    <template v-else-if="key">
      <div class="rounded-2xl border border-primary-100 bg-primary-50/60 p-4 text-sm leading-relaxed text-slate-700">
        <p class="font-semibold text-ink">Natija qanday hisoblanadi</p>
        <ul class="mt-2 list-disc space-y-1 pl-5">
          <li><b>1–14-savollar</b> (shaxsiy sifatlar, obyektiv to‘g‘ri javob yo‘q) — 1–5 ballik shkala. <b>To‘g‘ri savol:</b> tanlangan raqam = ball. <b>Teskari savol</b> (salbiy xulq haqida): ball = 6 − tanlangan raqam. Har savol maksimal 5 ball.</li>
          <li><b>15–20-savollar</b> (savdo vaziyatlari) — har bir A/B/C/D variant uchun 0–5 ball; eng to‘g‘ri harakat 5 ball.</li>
          <li><b>Foiz</b> = to‘plangan ball / {{ key.maxPoints }} × 100. <b>{{ key.passPercent }}% va yuqori — “Testdan o‘tdi”</b>, past — “Testdan yiqildi”.</li>
        </ul>
        <p class="mt-2 text-xs text-muted">Kalitni o‘zgartirish: <code class="rounded bg-white px-1 py-0.5">backend/app/landing_tests/{{ key.slug }}.json</code>. Avval topshirilgan natijalar o‘zgarmaydi.</p>
      </div>

      <section v-for="s in key.sections" :key="s.id" class="mt-6">
        <h3 class="text-sm font-semibold text-ink">{{ s.title }}</h3>
        <div class="mt-2 overflow-x-auto rounded-xl border border-line">
          <table class="min-w-full text-sm">
            <thead class="bg-slate-50/70">
              <tr>
                <th class="table-th w-10">№</th>
                <th class="table-th">Savol</th>
                <th v-if="sectionItems(s.id)[0]?.type === 'scale'" class="table-th">Turi</th>
                <th class="table-th">Ball (javob → ball)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr v-for="q in sectionItems(s.id)" :key="q.id" class="align-top">
                <td class="table-td font-semibold tabular-nums text-primary-700">{{ q.id }}</td>
                <td class="table-td min-w-[240px] whitespace-normal">
                  <p class="text-ink">{{ q.text }}</p>
                  <p v-if="q.keyNote" class="mt-0.5 text-xs text-muted">{{ q.keyNote }}</p>
                </td>
                <td v-if="q.type === 'scale'" class="table-td">
                  <span :class="['rounded-full px-2 py-0.5 text-xs font-medium', q.key === 'reverse' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700']">
                    {{ q.key === 'reverse' ? 'Teskari' : 'To‘g‘ri' }}
                  </span>
                </td>
                <td class="table-td whitespace-normal">
                  <div v-if="q.type === 'scale'" class="flex flex-wrap gap-1">
                    <span v-for="c in q.choices" :key="c.label" :class="['rounded-md px-1.5 py-0.5 text-xs tabular-nums', c.best ? 'bg-emerald-50 font-semibold text-emerald-700' : 'bg-slate-100 text-slate-600']">{{ c.label }}→{{ c.points }}</span>
                  </div>
                  <ul v-else class="min-w-[260px] space-y-1">
                    <li v-for="c in q.choices" :key="c.label" class="flex items-start gap-2 text-xs">
                      <b class="w-4 shrink-0 text-slate-500">{{ c.label }}</b>
                      <span :class="['flex-1', c.best ? 'font-medium text-emerald-700' : 'text-slate-600']">{{ c.text }}</span>
                      <span :class="['inline-flex shrink-0 items-center gap-0.5 font-semibold tabular-nums', c.best ? 'text-emerald-700' : 'text-slate-500']"><Star v-if="c.best" class="h-3 w-3 fill-emerald-500 text-emerald-500" />{{ c.points }}</span>
                    </li>
                  </ul>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
    <template #footer>
      <Button variant="secondary" @click="emit('close')">Yopish</Button>
    </template>
  </Modal>
</template>
