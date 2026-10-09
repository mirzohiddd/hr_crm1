<script setup>
import { computed, ref } from 'vue'
import { Copy, Download, ExternalLink, Eye, GraduationCap, SearchX, Trash2, UserRoundCheck } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SearchInput from '@/components/ui/SearchInput.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import Pagination from '@/components/ui/Pagination.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import FinalResultDetails from './FinalResultDetails.vue'
import { FINAL_RESULT_LABELS, isPassed, participantName, useFinalTestStore } from '@/stores/finalTest'
import { useToast } from '@/composables/useToast'
import { usePagination } from '@/composables/usePagination'
import { formatDateTime } from '@/utils/date'
import { downloadCsv, normalizeText } from '@/utils/format'

/** Yakuniy bilim testi (/test/yakuniy): har bir topshirish — alohida qator */
const store = useFinalTestStore()
const toast = useToast()

const publicUrl = computed(() => `${window.location.origin}${store.info?.path || '/test/yakuniy'}`)
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
const statusTabs = computed(() => [
  { value: '', label: 'Barchasi', count: store.stats.total },
  { value: 'passed', label: 'Testdan o‘tdi', count: store.stats.passed },
  { value: 'failed', label: 'Testdan o‘tmadi', count: store.stats.failed },
])
const filtered = computed(() => {
  const q = normalizeText(search.value)
  return store.rows.filter(
    (r) =>
      (!status.value || (status.value === 'passed') === isPassed(r)) &&
      (!q || normalizeText(`${r.name} ${r.position || ''} ${r.participantNo || r.id}`).includes(q)),
  )
})
const { page, paged, total, pageSize } = usePagination(filtered, 10, () => [search.value, status.value])

const detailId = ref(null)
const deleteTarget = ref(null)
const deleting = ref(false)
async function confirmDelete() {
  deleting.value = true
  try {
    await store.remove(deleteTarget.value.id)
    toast.success('Natija o‘chirildi', deleteTarget.value.name)
    if (detailId.value === deleteTarget.value.id) detailId.value = null
    deleteTarget.value = null
  } catch (e) {
    toast.error('O‘chirib bo‘lmadi', e.message)
  } finally {
    deleting.value = false
  }
}

function exportCsv() {
  const rows = [...store.results].sort((a, b) => (a.submittedAt || '').localeCompare(b.submittedAt || ''))
  downloadCsv(
    `yakuniy-test-${new Date().toISOString().slice(0, 10)}.csv`,
    ['Ishtirokchi', 'Lavozim', 'Topshirgan sana', 'To‘g‘ri', 'Xato', 'Ball', 'Foiz', 'Holati', 'Sarflangan vaqt (son)'],
    rows.map((r) => [participantName(r), r.position, formatDateTime(r.submittedAt), r.correct, r.wrong, `${r.correct}/${r.total}`, `${r.percent}%`, FINAL_RESULT_LABELS[r.status], r.durationSec ?? '']),
  )
}
</script>

<template>
  <div class="mt-4 space-y-4">
    <!-- Test havolasi -->
    <div class="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
      <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 text-white shadow-md shadow-primary-600/25"><GraduationCap class="h-5 w-5" /></span>
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-ink">Yakuniy bilim testi — {{ store.info?.questions ?? 20 }} ta savol, o‘tish: 16–20 ball</p>
        <p class="text-[13px] text-muted">Ochiq test — havola yoki ism talab qilinmaydi: <span class="break-all font-medium text-primary-700">{{ publicUrl }}</span></p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="secondary" size="sm" :icon="Copy" @click="copyLink">Nusxalash</Button>
        <a :href="publicUrl" target="_blank" rel="noopener" class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-line bg-white px-3 text-[13px] font-medium text-ink transition-colors hover:border-slate-300 hover:bg-slate-50"><ExternalLink class="h-4 w-4" /> Ochish</a>
      </div>
    </div>

    <ErrorState v-if="store.error" class="card" :message="store.error" @retry="store.fetchAll()" />

    <section v-else class="card overflow-hidden">
      <div class="flex flex-col gap-3 border-b border-line p-4 xl:flex-row xl:items-center">
        <SegmentedControl v-model="status" :options="statusTabs" aria-label="Natija holati" />
        <div class="grid flex-1 gap-3 sm:grid-cols-[minmax(0,1fr)_auto] xl:ml-auto xl:max-w-xl">
          <SearchInput v-model="search" placeholder="Ishtirokchi raqami yoki ism..." label="Natijalardan qidirish" />
          <Button variant="secondary" :icon="Download" :disabled="!store.results.length" @click="exportCsv">Excel</Button>
        </div>
      </div>

      <LoadingState v-if="!store.loaded && store.loading" :rows="6" />
      <EmptyState v-else-if="!store.rows.length" :icon="UserRoundCheck" title="Hali hech kim yakuniy testni topshirmagan" description="Test havolasini yuboring — har bir topshirilgan test shu yerda alohida qator bo‘lib ko‘rinadi.">
        <Button variant="secondary" :icon="Copy" @click="copyLink">Havolani nusxalash</Button>
      </EmptyState>
      <EmptyState v-else-if="!filtered.length" :icon="SearchX" title="Natija topilmadi" description="Filtrlarni o‘zgartirib ko‘ring.">
        <Button variant="secondary" @click="search = ''; status = ''">Filtrlarni tozalash</Button>
      </EmptyState>
      <template v-else>
        <div class="hidden overflow-x-auto md:block">
          <table class="min-w-full">
            <thead class="border-b border-line bg-slate-50/60">
              <tr>
                <th class="table-th">Ishtirokchi</th>
                <th class="table-th">Topshirgan sana</th>
                <th class="table-th text-center">To‘g‘ri</th>
                <th class="table-th text-center">Xato</th>
                <th class="table-th text-center">Ball</th>
                <th class="table-th">Foiz</th>
                <th class="table-th">Holati</th>
                <th class="table-th text-right" />
              </tr>
            </thead>
            <tbody class="divide-y divide-line">
              <tr v-for="r in paged" :key="r.id" class="group cursor-pointer transition-colors duration-150 hover:bg-primary-50/40" tabindex="0" @click="detailId = r.id" @keydown.enter="detailId = r.id">
                <td class="table-td">
                  <div class="flex items-center gap-3">
                    <Avatar :name="r.fullName || `# ${r.participantNo ?? r.id}`" size="sm" />
                    <div class="min-w-0">
                      <p class="font-medium text-ink group-hover:text-primary-700">{{ r.name }}</p>
                      <p v-if="r.position || r.attempts > 1" class="text-xs text-muted">{{ [r.position, r.attempts > 1 ? `${r.attempts} ta urinish` : ''].filter(Boolean).join(' · ') }}</p>
                    </div>
                  </div>
                </td>
                <td class="table-td tabular-nums text-slate-600">{{ formatDateTime(r.submittedAt) }}</td>
                <td class="table-td text-center font-semibold tabular-nums text-emerald-600">{{ r.correct }}</td>
                <td class="table-td text-center font-semibold tabular-nums text-red-600">{{ r.wrong }}</td>
                <td class="table-td text-center tabular-nums text-slate-600"><b class="text-ink">{{ r.correct }}</b>/{{ r.total }}</td>
                <td class="table-td">
                  <div class="flex items-center gap-2">
                    <div class="h-1.5 w-14 overflow-hidden rounded-full bg-slate-100">
                      <div :class="['h-full rounded-full', isPassed(r) ? 'bg-emerald-500' : 'bg-red-500']" :style="{ width: `${r.percent}%` }" />
                    </div>
                    <span class="font-semibold tabular-nums">{{ r.percent }}%</span>
                  </div>
                </td>
                <td class="table-td"><StatusBadge :status="isPassed(r) ? 'O‘tdi' : 'O‘tmadi'" :label="FINAL_RESULT_LABELS[r.status]" /></td>
                <td class="table-td text-right" @click.stop @keydown.enter.stop>
                  <div class="flex justify-end gap-1.5">
                    <button class="icon-btn h-8 w-8 border border-line bg-white hover:border-primary-200 hover:text-primary-600" title="Javoblarni ko‘rish" aria-label="Javoblarni ko‘rish" @click="detailId = r.id"><Eye class="h-4 w-4" /></button>
                    <button class="icon-btn h-8 w-8 border border-line bg-white hover:border-red-200 hover:bg-red-50 hover:text-red-600" title="O‘chirish" :aria-label="`${r.name}: o‘chirish`" @click="deleteTarget = r"><Trash2 class="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ul class="divide-y divide-line md:hidden">
          <li v-for="r in paged" :key="r.id">
            <button class="flex w-full items-start gap-3 px-4 py-3.5 text-left transition-colors active:bg-slate-50" @click="detailId = r.id">
              <Avatar :name="r.fullName || `# ${r.participantNo ?? r.id}`" size="md" />
              <span class="min-w-0 flex-1">
                <span class="flex items-start justify-between gap-2">
                  <span class="truncate font-medium text-ink">{{ r.name }}</span>
                  <StatusBadge :status="isPassed(r) ? 'O‘tdi' : 'O‘tmadi'" :label="FINAL_RESULT_LABELS[r.status]" size="sm" />
                </span>
                <span class="mt-1 flex flex-wrap gap-x-4 text-xs tabular-nums text-muted">
                  <span><b class="text-ink">{{ r.correct }}/{{ r.total }}</b> ball · {{ r.percent }}%</span>
                  <span>{{ formatDateTime(r.submittedAt) }}</span>
                </span>
              </span>
            </button>
          </li>
        </ul>
        <Pagination v-model:page="page" :total="total" :page-size="pageSize" />
      </template>
    </section>

    <FinalResultDetails :open="!!detailId" :result-id="detailId" @close="detailId = null" @delete="deleteTarget = $event" />
    <ConfirmDialog
      :open="!!deleteTarget"
      title="Natijani o‘chirasizmi?"
      :message="deleteTarget ? `${deleteTarget.name || participantName(deleteTarget)} natijasi va barcha javoblari o‘chiriladi.` : ''"
      confirm-text="O‘chirish"
      :loading="deleting"
      @confirm="confirmDelete"
      @close="deleteTarget = null"
    />
  </div>
</template>
