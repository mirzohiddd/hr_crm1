<script setup>
import { computed } from 'vue'
import { ArrowLeft, Building2, CalendarCheck, CheckCircle2, Circle, ExternalLink, FolderOpen, Phone, Send, Upload, Wallet } from 'lucide-vue-next'
import Avatar from '@/components/ui/Avatar.vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import DocumentTable from './DocumentTable.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useDocumentsStore } from '@/stores/documents'
import { DOCUMENT_TYPES } from '@/constants'
import { formatDate, tenure } from '@/utils/date'
import { formatMoney, telegramHandle, telegramLink } from '@/utils/format'

/** Bitta xodimning ma'lumotlari va hujjatlari (Hujjatlar sahifasida) */
const props = defineProps({ employee: { type: Object, required: true } })
const emit = defineEmits(['back', 'upload', 'view', 'download', 'delete'])

const catalog = useCatalogStore()
const store = useDocumentsStore()

const docs = computed(() => store.ofEmployee(props.employee.id).sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt)))
const stats = computed(() => ({
  total: docs.value.length,
  approved: docs.value.filter((d) => d.status === 'Tasdiqlangan').length,
  pending: docs.value.filter((d) => d.status === 'Kutilmoqda').length,
}))
// Asosiy hujjatlar ro‘yxati: qaysilari yuklangan
const checklist = computed(() =>
  DOCUMENT_TYPES.filter((t) => t !== 'Boshqa').map((type) => ({ type, has: docs.value.some((d) => d.type === type && d.status !== 'Rad etilgan') })),
)
const completeness = computed(() => Math.round((checklist.value.filter((c) => c.has).length / checklist.value.length) * 100))
</script>

<template>
  <div class="space-y-5">
    <!-- Xodim ma'lumotlari -->
    <section class="card overflow-hidden">
      <div class="relative bg-gradient-to-r from-primary-600 to-primary-500 px-5 pb-12 pt-4 text-white">
        <button class="inline-flex items-center gap-1.5 rounded-md text-sm font-medium text-primary-50 hover:text-white lg:hidden" @click="emit('back')">
          <ArrowLeft class="h-4 w-4" /> Xodimlar ro‘yxati
        </button>
        <p class="hidden text-xs font-medium uppercase tracking-wider text-primary-100 lg:block">Xodim ma’lumotlari</p>
      </div>
      <div class="-mt-9 px-5 pb-5">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start">
          <Avatar :name="employee.fullName" :src="employee.photo" size="xl" class="ring-4 ring-white" />
          <!-- Matn banner ostida boshlanadi (avatar banner ustiga chiqadi) -->
          <div class="min-w-0 flex-1 sm:pt-11">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-xl font-semibold text-ink">{{ employee.fullName }}</h2>
              <StatusBadge :status="employee.status" />
            </div>
            <div class="mt-2 flex flex-wrap gap-2 text-sm">
              <span class="inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-2.5 py-1 font-medium text-primary-700 ring-1 ring-primary-100">
                <Building2 class="h-3.5 w-3.5" />{{ catalog.departmentName(employee.departmentId) }}
              </span>
              <span class="inline-flex rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700">{{ catalog.positionName(employee.positionId) }}</span>
            </div>
          </div>
          <RouterLink :to="`/employees/${employee.id}`" class="inline-flex shrink-0 items-center gap-1.5 self-start sm:mt-11 rounded-lg border border-line px-3 py-2 text-sm font-medium text-ink transition-colors hover:border-primary-200 hover:text-primary-700">
            Profil <ExternalLink class="h-3.5 w-3.5" />
          </RouterLink>
        </div>

        <dl class="mt-5 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
          <div class="flex items-center gap-2.5 rounded-xl bg-slate-50 px-3 py-2.5">
            <Phone class="h-4 w-4 shrink-0 text-muted" />
            <div class="min-w-0"><dt class="text-[11px] text-muted">Telefon</dt><dd class="truncate font-medium tabular-nums text-ink">{{ employee.phone || '—' }}</dd></div>
          </div>
          <div class="flex items-center gap-2.5 rounded-xl bg-slate-50 px-3 py-2.5">
            <Send class="h-4 w-4 shrink-0 text-muted" />
            <div class="min-w-0">
              <dt class="text-[11px] text-muted">Telegram</dt>
              <dd class="truncate font-medium">
                <a v-if="employee.telegram" :href="telegramLink(employee.telegram)" target="_blank" rel="noopener" class="text-primary-700 hover:underline">{{ telegramHandle(employee.telegram) }}</a>
                <span v-else class="text-ink">—</span>
              </dd>
            </div>
          </div>
          <div class="flex items-center gap-2.5 rounded-xl bg-slate-50 px-3 py-2.5">
            <CalendarCheck class="h-4 w-4 shrink-0 text-muted" />
            <div class="min-w-0"><dt class="text-[11px] text-muted">Ishga qabul qilingan</dt><dd class="truncate font-medium text-ink">{{ formatDate(employee.hireDate) }} · {{ tenure(employee.hireDate) }}</dd></div>
          </div>
          <div class="flex items-center gap-2.5 rounded-xl bg-slate-50 px-3 py-2.5">
            <Wallet class="h-4 w-4 shrink-0 text-muted" />
            <div class="min-w-0"><dt class="text-[11px] text-muted">Oylik kutuvi</dt><dd class="truncate font-medium tabular-nums text-ink">{{ formatMoney(employee.expectedSalary) }}</dd></div>
          </div>
        </dl>
      </div>
    </section>

    <!-- Hujjatlar to‘liqligi -->
    <section class="card p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="text-base font-semibold text-ink">Asosiy hujjatlar</h3>
          <p class="text-sm text-muted">{{ stats.total }} ta hujjat · {{ stats.approved }} tasdiqlangan<template v-if="stats.pending"> · {{ stats.pending }} kutilmoqda</template></p>
        </div>
        <div class="flex items-center gap-3">
          <div class="text-right">
            <p class="text-xs text-muted">To‘liqlik</p>
            <p class="font-semibold tabular-nums text-ink">{{ completeness }}%</p>
          </div>
          <div class="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full bg-primary-600 transition-[width] duration-500" :style="{ width: `${completeness}%` }" />
          </div>
        </div>
      </div>
      <ul class="mt-4 flex flex-wrap gap-2">
        <li
          v-for="c in checklist"
          :key="c.type"
          :class="['inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[13px] font-medium ring-1 transition-colors', c.has ? 'bg-emerald-50 text-emerald-700 ring-emerald-100' : 'bg-white text-slate-500 ring-line']"
        >
          <component :is="c.has ? CheckCircle2 : Circle" class="h-3.5 w-3.5" />{{ c.type }}
        </li>
      </ul>
    </section>

    <!-- Hujjatlar ro‘yxati -->
    <section class="card overflow-hidden">
      <div class="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
        <h3 class="text-base font-semibold text-ink">Hujjatlar</h3>
        <Button size="sm" :icon="Upload" @click="emit('upload')">Hujjat yuklash</Button>
      </div>
      <EmptyState v-if="!docs.length" compact :icon="FolderOpen" title="Hujjatlar hali yuklanmagan" description="Pasport, mehnat shartnomasi va boshqa hujjatlarni yuklang.">
        <Button :icon="Upload" @click="emit('upload')">Hujjat yuklash</Button>
      </EmptyState>
      <DocumentTable v-else :rows="docs" hide-employee @view="(d) => emit('view', d)" @download="(d) => emit('download', d)" @delete="(d) => emit('delete', d)" />
    </section>
  </div>
</template>
