<script setup>
import { computed, ref } from 'vue'
import { Copy, Download, ExternalLink, Eye, KeyRound, Link2, SearchX, Trash2, UserRoundSearch } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import Select from '@/components/ui/Select.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import LandingResultDetails from './LandingResultDetails.vue'
import LandingKeyModal from './LandingKeyModal.vue'
import { useLandingStore } from '@/stores/landing'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { LANDING_RESULT_LABELS, LANDING_TEST_SLUG, isLandingPositive } from '@/constants'
const REL_TONE = { yuqori: 'text-emerald-600', 'o‘rtacha': 'text-amber-600', past: 'text-red-600' }
import { formatDateTime } from '@/utils/date'
import { downloadCsv, normalizeText, onlyDigits } from '@/utils/format'

/**
 * Landing (/test/sotuv) orqali test topshirgan yangi xodimlar / nomzodlar — har biri alohida qator.
 * 40 savolli test (format=profile): ko‘rsatkichlar, ishonchlilik, eng mos lavozim va HR tavsiyasi;
 * eski test natijalari — ball va foiz (o‘zgarmagan holda).
 */
const store = useLandingStore()
const toast = useToast()

const publicUrl = computed(() => `${window.location.origin}/test/${LANDING_TEST_SLUG}`)
async function copyLink() {
  try {
    await navigator.clipboard.writeText(publicUrl.value)
    toast.success('Havola nusxalandi', publicUrl.value)
  } catch {
    toast.info('Havolani qo‘lda nusxalang', publicUrl.value)
  }
}

const search = ref('')
const status = ref('')
const position = ref('')
const statusTabs = computed(() => [
  { value: '', label: 'Barchasi', count: store.stats.total },
  { value: 'good', label: 'Tavsiya etiladi / o‘tdi', count: store.stats.passed },
  { value: 'attention', label: 'E’tibor talab qiladi', count: store.stats.failed },
])
const isProfile = (r) => r?.format === 'profile'
const isPersona = (r) => r?.format === 'persona'
const SCALE_SHORT = { masuliyat: 'Mas’ul.', stress: 'Stress', muloqot: 'Muloq.', hamdardlik: 'Hamd.' }
const SCALE_TITLE = { masuliyat: 'Mas’uliyat', stress: 'Stressga chidamlilik', muloqot: 'Muloqot', hamdardlik: 'Hamdardlik' }
const scaleLabel = (id, r) => SCALE_SHORT[id] || r?.sections?.find((s) => s.id === id)?.title || id
const scaleTitle = (id, r) => r?.sections?.find((s) => s.id === id)?.title || SCALE_TITLE[id] || id
const levelBar = (p) => (p >= 75 ? 'bg-emerald-500' : p >= 50 ? 'bg-amber-500' : 'bg-red-500')
const relTone = (p) => (p >= 75 ? 'text-emerald-600' : p >= 50 ? 'text-amber-600' : 'text-red-600')
const positions = computed(() => [...new Set(store.items.map((r) => r.position).filter(Boolean))].sort())
const filtered = computed(() => {
  const q = normalizeText(search.value)
  const digits = onlyDigits(search.value)
  return store.items.filter(
    (r) =>
      (!status.value || (status.value === 'good') === isLandingPositive(r)) &&
      (!position.value || r.position === position.value) &&
      (!q || normalizeText(r.fullName).includes(q) || (digits.length >= 3 && onlyDigits(r.phone).includes(digits))),
  )
})
const { page, paged, total, pageSize } = usePagination(filtered, 10, () => [search.value, status.value, position.value])
function clearFilters() {
  search.value = ''
  status.value = ''
  position.value = ''
}

function exportCsv() {
  downloadCsv(
    `nomzodlar-testi-${new Date().toISOString().slice(0, 10)}.csv`,
    ['F.I.Sh.', 'Lavozim', 'Yosh', 'Telefon', 'Sana', 'Topshirilgan vaqt', 'Holati / HR xulosasi', 'Profil', 'Ishonchlilik',
      'Yuqori samaradorlik', 'To‘sqinlik qiluvchi', 'Xususiyatlar', 'Rasmli savollar', 'Eng mos lavozim', 'Ball', 'Foiz'],
    filtered.value.map((r) => {
      // «Ishdagi shaxsiyat 360»: foiz o‘rniga daraja (backend → positiveWord, traitLevels, bestPosition.fit)
      if (isPersona(r)) {
        return [
          r.fullName, r.position, r.age, r.phone, r.date, formatDateTime(r.submittedAt), LANDING_RESULT_LABELS[r.status] || r.status,
          r.profileTitle || '', r.reliabilityLevel || '', r.positiveWord || '', r.negativeWord || '',
          (r.traitLevels || []).map((t) => `${t.title} — ${t.levelLabel.toLowerCase()}`).join('; '),
          (r.pictures || []).map((p) => `${p.title}: ${p.answerText}`).join('; '),
          r.bestPosition ? `${r.bestPosition.name}${r.bestPosition.fit ? ` (${r.bestPosition.fit.toLowerCase()})` : ''}` : '',
          '', '',
        ]
      }
      const traits = (r.sections || []).map((s) => `${s.title} ${s.percent ?? Math.round((s.points / s.maxPoints) * 100)}%`).join('; ')
      return [
        r.fullName, r.position, r.age, r.phone, r.date, formatDateTime(r.submittedAt), LANDING_RESULT_LABELS[r.status] || r.status,
        r.profileTitle || '', r.reliabilityLevel || (typeof r.reliability === 'number' ? `${r.reliability}%` : ''),
        r.positive ?? '', r.negative ?? '', traits, '', r.bestPosition ? `${r.bestPosition.name} (${r.bestPosition.percent}%)` : '',
        `${r.points}/${r.maxPoints}`, `${r.percent}%`,
      ]
    }),
  )
}

const openId = ref(null)
const keyOpen = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)
function askDelete(r) {
  deleteTarget.value = r
}
async function confirmDelete() {
  deleting.value = true
  try {
    await store.remove(deleteTarget.value.id)
    toast.success('Natija o‘chirildi', deleteTarget.value.fullName)
    if (openId.value === deleteTarget.value.id) openId.value = null
    deleteTarget.value = null
  } catch (e) {
    toast.error('O‘chirib bo‘lmadi', e.message)
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="mt-4 space-y-4">
    <!-- Havola -->
    <div class="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
      <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/25"><Link2 class="h-5 w-5" /></span>
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-ink">«Ishdagi shaxsiyat 360» — yangi xodimlar testi havolasi (40 ta savol + 3 ta rasm, 5 bosqich)</p>
        <p class="text-[13px] text-muted">Yangi kelgan xodim yoki nomzodga yuboring — login talab qilinmaydi: <span class="break-all font-medium text-primary-700">{{ publicUrl }}</span></p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="secondary" size="sm" :icon="Copy" @click="copyLink">Nusxalash</Button>
        <a :href="publicUrl" target="_blank" rel="noopener" class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-line bg-white px-3 text-[13px] font-medium text-ink transition-colors hover:border-slate-300 hover:bg-slate-50"><ExternalLink class="h-4 w-4" /> Ochish</a>
        <Button variant="secondary" size="sm" :icon="KeyRound" @click="keyOpen = true">Baholash kaliti</Button>
      </div>
    </div>

    <ErrorState v-if="store.error" class="card" :message="store.error" @retry="store.fetchAll({ force: true })" />

    <section v-else class="card overflow-hidden">
      <div class="flex flex-col gap-3 border-b border-line p-4 xl:flex-row xl:items-center">
        <SegmentedControl v-model="status" :options="statusTabs" aria-label="Natija holati" />
        <div class="grid flex-1 gap-3 sm:grid-cols-[minmax(0,1fr)_200px_auto] xl:ml-auto xl:max-w-2xl">
          <SearchInput v-model="search" placeholder="F.I.Sh. yoki telefon..." label="Nomzodlardan qidirish" />
          <Select v-model="position" :options="positions" placeholder="Barcha lavozimlar" aria-label="Lavozim bo‘yicha filtr" />
          <Button variant="secondary" :icon="Download" :disabled="!filtered.length" @click="exportCsv">Excel</Button>
        </div>
      </div>

      <LoadingState v-if="!store.loaded && store.loading" :rows="6" />
      <EmptyState v-else-if="!store.items.length" :icon="UserRoundSearch" title="Hali nomzodlar test topshirmagan" description="Test havolasini nomzodlarga yuboring — topshirilgan har bir test shu yerda alohida ko‘rinadi.">
        <Button variant="secondary" :icon="Copy" @click="copyLink">Havolani nusxalash</Button>
      </EmptyState>
      <EmptyState v-else-if="!filtered.length" :icon="SearchX" title="Natija topilmadi" description="Filtrlarni o‘zgartirib ko‘ring.">
        <Button variant="secondary" @click="clearFilters">Filtrlarni tozalash</Button>
      </EmptyState>
      <template v-else>
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-full">
            <thead class="border-b border-line bg-slate-50/60">
              <tr>
                <th class="table-th">F.I.Sh.</th>
                <th class="table-th">Lavozim</th>
                <th class="table-th">Topshirgan sana</th>
                <th class="table-th">Profil / ko‘rsatkichlar</th>
                <th class="table-th">Natija / lavozim</th>
                <th class="table-th">Holati</th>
                <th class="table-th text-right" />
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr
                v-for="r in paged"
                :key="r.id"
                class="group cursor-pointer transition-colors duration-150 hover:bg-primary-50/40"
                tabindex="0"
                @click="openId = r.id"
                @keydown.enter="openId = r.id"
              >
                <td class="table-td">
                  <div class="flex items-center gap-3">
                    <span class="relative">
                      <Avatar :name="r.fullName" size="sm" />
                      <span v-if="!r.viewed" class="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-primary-600 ring-2 ring-white" title="Yangi — hali ko‘rilmagan" />
                    </span>
                    <span :class="['text-ink group-hover:text-primary-700', r.viewed ? 'font-medium' : 'font-semibold']">{{ r.fullName }}</span>
                  </div>
                </td>
                <td class="table-td text-slate-600">
                  <p>{{ r.position }}</p>
                  <p class="text-[11px] text-muted">{{ r.age }} yosh</p>
                </td>
                <td class="table-td whitespace-nowrap tabular-nums text-slate-600">{{ formatDateTime(r.submittedAt) }}</td>
                <td class="table-td">
                  <div v-if="isPersona(r)" class="min-w-0">
                    <p class="text-[13px] font-medium text-ink">{{ r.profileTitle }}</p>
                    <p class="text-[11px] text-muted">Ishonchlilik: <b :class="REL_TONE[r.reliabilityLevel]">{{ r.reliabilityLevel }}</b></p>
                  </div>
                  <div v-else-if="isProfile(r) && r.scores" class="grid w-40 grid-cols-2 gap-x-3 gap-y-1">
                    <div v-for="(v, id) in r.scores" :key="id" class="flex items-center gap-1" :title="`${scaleTitle(id, r)}: ${v}%`">
                      <span class="w-11 truncate text-[11px] text-muted">{{ scaleLabel(id, r) }}</span>
                      <span class="h-1 flex-1 overflow-hidden rounded-full bg-slate-100"><span :class="['block h-full rounded-full', levelBar(v)]" :style="{ width: `${v}%` }" /></span>
                      <span class="w-6 text-right text-[11px] font-semibold tabular-nums">{{ v }}</span>
                    </div>
                  </div>
                  <span v-else class="tabular-nums text-slate-600"><b class="text-ink">{{ r.points }}</b>/{{ r.maxPoints }} ball</span>
                </td>
                <td v-if="isPersona(r)" class="table-td">
                  <p class="text-[11px] text-muted">Eng mos lavozim</p>
                  <p class="max-w-[11rem] truncate text-[13px] font-medium text-ink">{{ r.bestPosition?.name || '—' }}</p>
                  <p v-if="r.bestPosition?.fit" class="text-[11px] text-muted">{{ r.bestPosition.fit }}</p>
                </td>
                <td v-else class="table-td">
                  <div class="flex items-center gap-2">
                    <div class="h-1.5 w-14 overflow-hidden rounded-full bg-slate-100">
                      <div :class="['h-full rounded-full transition-[width] duration-500', isProfile(r) ? levelBar(r.percent) : r.status === 'O‘tdi' ? 'bg-emerald-500' : 'bg-red-500']" :style="{ width: `${r.percent}%` }" />
                    </div>
                    <span class="font-semibold tabular-nums">{{ r.percent }}%</span>
                  </div>
                  <p v-if="typeof r.reliability === 'number'" class="mt-1 text-[11px] text-muted">Ishonchlilik: <b :class="['tabular-nums', relTone(r.reliability)]">{{ r.reliability }}%</b></p>
                  <p v-if="r.bestPosition" class="max-w-[10rem] truncate text-[11px] text-muted" :title="`Eng mos lavozim: ${r.bestPosition.name} (${r.bestPosition.percent}%)`">{{ r.bestPosition.name }} · {{ r.bestPosition.percent }}%</p>
                </td>
                <td class="table-td"><StatusBadge :status="r.status" :label="LANDING_RESULT_LABELS[r.status] || r.status" /></td>
                <td class="table-td text-right" @click.stop @keydown.enter.stop>
                  <div class="flex justify-end gap-1.5">
                    <button class="icon-btn h-8 w-8 border border-line bg-white hover:border-primary-200 hover:text-primary-600" :title="isProfile(r) || isPersona(r) ? 'HR hisobotini ko‘rish' : 'Javoblarni ko‘rish'" :aria-label="isProfile(r) || isPersona(r) ? 'HR hisobotini ko‘rish' : 'Javoblarni ko‘rish'" @click="openId = r.id">
                      <Eye class="h-4 w-4" />
                    </button>
                    <button class="icon-btn h-8 w-8 border border-line bg-white hover:border-red-200 hover:bg-red-50 hover:text-red-600" title="O‘chirish" :aria-label="`${r.fullName}: o‘chirish`" @click="askDelete(r)">
                      <Trash2 class="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ul class="divide-y divide-line md:hidden">
          <li v-for="r in paged" :key="r.id">
            <button class="flex w-full items-start gap-3 px-4 py-3.5 text-left transition-colors active:bg-slate-50" @click="openId = r.id">
              <span class="relative">
                <Avatar :name="r.fullName" size="md" />
                <span v-if="!r.viewed" class="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-primary-600 ring-2 ring-white" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="flex items-start justify-between gap-2">
                  <span class="truncate font-medium text-ink">{{ r.fullName }}</span>
                  <StatusBadge :status="r.status" :label="LANDING_RESULT_LABELS[r.status] || r.status" size="sm" />
                </span>
                <span class="mt-0.5 block truncate text-[13px] text-slate-600">{{ r.position }} · {{ r.age }} yosh</span>
                <span class="mt-1 flex flex-wrap gap-x-4 text-xs tabular-nums text-muted">
                  <span v-if="isPersona(r)"><b class="text-ink">{{ r.profileTitle }}</b> · ishonchlilik {{ r.reliabilityLevel }}<template v-if="r.bestPosition"> · {{ r.bestPosition.name }}</template></span>
                  <span v-else-if="isProfile(r)"><b class="text-ink">{{ r.percent }}%</b> indeks · ishonchlilik {{ r.reliability }}%<template v-if="r.bestPosition"> · {{ r.bestPosition.name }}</template></span>
                  <span v-else><b class="text-ink">{{ r.percent }}%</b> · {{ r.points }}/{{ r.maxPoints }} ball</span>
                  <span>{{ formatDateTime(r.submittedAt) }}</span>
                </span>
              </span>
            </button>
          </li>
        </ul>
        <Pagination v-model:page="page" :total="total" :page-size="pageSize" />
      </template>
    </section>

    <LandingResultDetails :open="!!openId" :result-id="openId" @close="openId = null" @delete="askDelete" />
    <LandingKeyModal :open="keyOpen" :slug="LANDING_TEST_SLUG" @close="keyOpen = false" />
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Natijani o‘chirasizmi?"
      :message="deleteTarget ? `${deleteTarget.fullName} ning test natijasi va barcha javoblari o‘chiriladi.` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </div>
</template>