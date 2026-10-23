<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  BadgeCheck, Briefcase, Building2, CalendarClock, CalendarPlus, Check, ChevronRight, ClipboardCheck, MapPin, MessageSquareText, Pencil, Phone,
  PhoneCall, PhoneMissed, RotateCcw, Trash2, User, UserRound, XCircle,
} from 'lucide-vue-next'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SourceIcon from './SourceIcon.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useEmployeesStore } from '@/stores/employees'
import { formatDateTime } from '@/utils/date'
import { candidatesApi } from '@/api/candidates'
import { LANDING_RESULT_LABELS } from '@/constants'
import { FINAL_RESULT_LABELS, isPassed } from '@/stores/finalTest'

const props = defineProps({
  open: { type: Boolean, default: false },
  candidate: { type: Object, default: null },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'edit', 'delete', 'contacted', 'not-reached', 'interview', 'hire', 'reject', 'reopen', 'open-employee'])
const catalog = useCatalogStore()
const employees = useEmployeesStore()

const STEPS = ['Yangi', 'Bog‘lanildi', 'Suhbat', 'Ishga qabul qilindi']
const stepIndex = computed(() => {
  const c = props.candidate
  if (!c) return 0
  if (c.status === 'Bog‘lanilmadi') return 0
  if (c.status === 'Rad etildi') {
    // Rad etilishdan oldingi oxirgi bosqich
    const prev = [...(c.history || [])].reverse().find((h) => STEPS.includes(h.status))
    return STEPS.indexOf(prev?.status || 'Yangi')
  }
  return STEPS.indexOf(c.status)
})
const rejected = computed(() => props.candidate?.status === 'Rad etildi')
const notReached = computed(() => props.candidate?.status === 'Bog‘lanilmadi')
const hired = computed(() => props.candidate?.status === 'Ishga qabul qilindi')
const employee = computed(() => (props.candidate?.employeeId ? employees.findById(props.candidate.employeeId) : null))

const info = computed(() => {
  const c = props.candidate
  if (!c) return []
  return [
    { icon: Phone, label: 'Telefon', value: c.phone, href: `tel:${c.phone.replace(/\s/g, '')}` },
    { icon: Briefcase, label: 'Lavozim', value: catalog.positionName(c.positionId) },
    { icon: Building2, label: 'Bo‘lim', value: c.departmentId ? catalog.departmentName(c.departmentId) : 'Tanlanmagan' },
    { icon: User, label: 'Yosh / jinsi', value: [c.age ? `${c.age} yosh` : '', c.gender].filter(Boolean).join(', ') || '—' },
    { icon: MapPin, label: 'Shahar', value: c.city || '—' },
    { icon: CalendarPlus, label: 'Ariza kelgan', value: formatDateTime(c.createdAt) },
    ...(c.interviewAt ? [{ icon: CalendarClock, label: 'Suhbat', value: formatDateTime(c.interviewAt) }] : []),
  ]
})
const history = computed(() => [...(props.candidate?.history || [])].reverse())

// ---------- Test natijalari (faqat HR panelida; backend HR/admin rolini tekshiradi) ----------
const router = useRouter()
const tests = ref({ landing: [], final: [] })
const testsLoading = ref(false)
const testsError = ref('')
let testsReq = 0
async function loadTests(id) {
  const req = ++testsReq
  tests.value = { landing: [], final: [] }
  testsError.value = ''
  if (!id) return
  testsLoading.value = true
  try {
    const data = await candidatesApi.testResults(id)
    if (req === testsReq) tests.value = { landing: data?.landing || [], final: data?.final || [] }
  } catch (e) {
    if (req === testsReq) testsError.value = e.message || 'Test natijalarini yuklab bo‘lmadi'
  } finally {
    if (req === testsReq) testsLoading.value = false
  }
}
watch(() => [props.open, props.candidate?.id], ([open, id]) => open && loadTests(id), { immediate: true })

const testRows = computed(() =>
  [
    ...tests.value.final.map((r) => ({
      key: `f${r.id}`, tab: 'final', id: r.id, title: r.testTitle || 'Yakuniy bilim testi', at: r.submittedAt,
      status: isPassed(r) ? 'O‘tdi' : 'O‘tmadi', label: FINAL_RESULT_LABELS[r.status] || r.status,
      summary: `${r.correct}/${r.total} to‘g‘ri · ${r.percent}%${r.attemptNo > 1 ? ` · ${r.attemptNo}-urinish` : ''}`,
    })),
    ...tests.value.landing.map((r) => ({
      key: `l${r.id}`, tab: 'landing', id: r.id, title: r.testTitle || 'Nomzodlar testi', at: r.submittedAt,
      status: r.status, label: LANDING_RESULT_LABELS[r.status] || r.status,
      summary: r.format === 'persona'
        ? [r.profileTitle, r.bestPosition?.name ? `Eng mos: ${r.bestPosition.name}` : ''].filter(Boolean).join(' · ')
        : [typeof r.percent === 'number' ? `${r.percent}%` : '', r.bestPosition?.name ? `Eng mos: ${r.bestPosition.name}` : ''].filter(Boolean).join(' · '),
    })),
  ].sort((a, b) => (b.at || '').localeCompare(a.at || '')),
)
function openTestResult(row) {
  emit('close')
  router.push({ path: '/tests', query: { tab: row.tab, result: row.id } })
}
</script>

<template>
  <Modal :open="open && !!candidate" size="lg" :persistent="busy" @close="!busy && emit('close')">
    <template #header>
      <div v-if="candidate" class="flex min-w-0 items-center gap-4">
        <Avatar :name="candidate.fullName" size="lg" />
        <div class="min-w-0">
          <h2 class="truncate text-lg font-semibold text-ink">{{ candidate.fullName }}</h2>
          <p class="mt-0.5 flex items-center gap-1.5 text-sm text-muted">
            <SourceIcon :source="candidate.source" /> {{ candidate.source }} · {{ catalog.positionName(candidate.positionId) }}
          </p>
          <div class="mt-2"><StatusBadge :status="candidate.status" /></div>
        </div>
      </div>
    </template>

    <template v-if="candidate">
      <!-- Bosqichlar -->
      <ol class="flex items-center gap-1.5" aria-label="Bosqichlar">
        <li v-for="(s, i) in STEPS" :key="s" class="flex min-w-0 flex-1 flex-col gap-1.5">
          <span
            :class="[
              'h-1.5 rounded-full',
              rejected && i === stepIndex ? 'bg-red-500' : i <= stepIndex ? (hired ? 'bg-emerald-500' : 'bg-primary-600') : 'bg-slate-100',
            ]"
          />
          <span :class="['truncate text-[11px] sm:text-xs', i <= stepIndex ? 'font-medium text-ink' : 'text-muted']">{{ s }}</span>
        </li>
      </ol>

      <div v-if="notReached" class="mt-4 flex gap-2.5 rounded-lg bg-orange-50 p-3 text-sm text-orange-800">
        <PhoneMissed class="mt-0.5 h-4 w-4 shrink-0" />
        <span><span class="font-medium">Bog‘lanib bo‘lmadi</span> — {{ candidate.contactAttempts || 1 }} marta qo‘ng‘iroq qilindi. Qayta urinib ko‘ring.</span>
      </div>
      <div v-if="rejected" class="mt-4 flex gap-2.5 rounded-lg bg-red-50 p-3 text-sm text-red-800">
        <XCircle class="mt-0.5 h-4 w-4 shrink-0" />
        <span><span class="font-medium">Rad etildi:</span> {{ candidate.rejectReason || 'sabab ko‘rsatilmagan' }}</span>
      </div>
      <div v-if="hired" class="mt-4 flex flex-col gap-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800 sm:flex-row sm:items-center">
        <BadgeCheck class="h-5 w-5 shrink-0" />
        <span class="flex-1">{{ employee ? 'Nomzod xodimlar ro‘yxatiga qo‘shilgan.' : 'Xodim yozuvi o‘chirilgan.' }}</span>
        <Button v-if="employee" size="sm" variant="secondary" :icon="UserRound" @click="emit('open-employee', employee)">Xodim profili</Button>
      </div>

      <dl class="mt-5 grid gap-x-6 gap-y-4 sm:grid-cols-2">
        <div v-for="r in info" :key="r.label" class="flex gap-3">
          <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-50 text-muted"><component :is="r.icon" class="h-4 w-4" /></span>
          <div class="min-w-0">
            <dt class="text-xs text-muted">{{ r.label }}</dt>
            <dd class="mt-0.5 text-sm font-medium text-ink">
              <a v-if="r.href" :href="r.href" class="tabular-nums hover:text-primary-600 hover:underline">{{ r.value }}</a>
              <span v-else>{{ r.value }}</span>
            </dd>
          </div>
        </div>
      </dl>

      <div v-if="candidate.note" class="mt-5 rounded-lg bg-slate-50 p-3.5 text-sm text-slate-700">
        <p class="mb-1 flex items-center gap-1.5 text-xs font-medium text-muted"><MessageSquareText class="h-3.5 w-3.5" /> Izoh</p>
        {{ candidate.note }}
      </div>

      <div class="mt-6">
        <h3 class="flex items-center gap-1.5 text-sm font-semibold text-ink"><ClipboardCheck class="h-4 w-4 text-muted" /> Test natijalari</h3>
        <p v-if="testsLoading" class="mt-3 text-sm text-muted">Yuklanmoqda...</p>
        <p v-else-if="testsError" class="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{{ testsError }}</p>
        <p v-else-if="!testRows.length" class="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-muted">Bu nomzod hali test topshirmagan (yoki natija telefon raqami / ism-familiya bo‘yicha profilga bog‘lanmagan).</p>
        <ul v-else class="mt-3 divide-y divide-line overflow-hidden rounded-lg border border-line">
          <li v-for="t in testRows" :key="t.key">
            <button type="button" class="flex w-full items-center gap-3 px-3.5 py-3 text-left transition-colors hover:bg-primary-50/40" @click="openTestResult(t)">
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium text-ink">{{ t.title }}</span>
                <span class="mt-0.5 block truncate text-xs text-muted">{{ formatDateTime(t.at) }}<template v-if="t.summary"> · {{ t.summary }}</template></span>
              </span>
              <StatusBadge v-if="t.status" :status="t.status" :label="t.label" size="sm" />
              <ChevronRight class="h-4 w-4 shrink-0 text-muted" />
            </button>
          </li>
        </ul>
      </div>

      <div v-if="history.length" class="mt-6">
        <h3 class="text-sm font-semibold text-ink">Tarix</h3>
        <ol class="mt-3 space-y-3 border-l border-line pl-4">
          <li v-for="(h, i) in history" :key="i" class="relative">
            <span class="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-white ring-2 ring-primary-400" />
            <p class="text-sm text-ink"><span class="font-medium">{{ h.status }}</span></p>
            <p class="text-xs text-muted">{{ formatDateTime(h.at) }}<template v-if="h.by"> · {{ h.by }}</template></p>
          </li>
        </ol>
      </div>
    </template>

    <template #footer>
      <template v-if="candidate">
        <div class="flex gap-2 sm:mr-auto">
          <Button class="flex-1 sm:flex-none" variant="secondary" :icon="Pencil" :disabled="busy" @click="emit('edit', candidate)">Tahrirlash</Button>
          <button class="icon-btn h-10 w-10 border border-line bg-white hover:border-red-200 hover:bg-red-50 hover:text-red-600" aria-label="Nomzodni o‘chirish" title="O‘chirish" :disabled="busy" @click="emit('delete', candidate)">
            <Trash2 class="h-4 w-4" />
          </button>
        </div>
        <template v-if="candidate.status === 'Yangi' || notReached">
          <Button variant="danger-outline" :icon="XCircle" :disabled="busy" @click="emit('reject', candidate)">Rad etish</Button>
          <Button variant="secondary" :icon="PhoneMissed" :disabled="busy" @click="emit('not-reached', candidate)">{{ notReached ? 'Yana bog‘lanilmadi' : 'Bog‘lanilmadi' }}</Button>
          <Button :icon="PhoneCall" :loading="busy" @click="emit('contacted', candidate)">Bog‘lanildi</Button>
        </template>
        <template v-else-if="candidate.status === 'Bog‘lanildi'">
          <Button variant="danger-outline" :icon="XCircle" :disabled="busy" @click="emit('reject', candidate)">Rad etish</Button>
          <Button variant="secondary" :icon="BadgeCheck" :disabled="busy" @click="emit('hire', candidate)">Ishga olish</Button>
          <Button :icon="CalendarClock" :disabled="busy" @click="emit('interview', candidate)">Suhbatga chaqirish</Button>
        </template>
        <template v-else-if="candidate.status === 'Suhbat'">
          <Button variant="danger-outline" :icon="XCircle" :disabled="busy" @click="emit('reject', candidate)">Rad etish</Button>
          <Button variant="secondary" :icon="CalendarClock" :disabled="busy" @click="emit('interview', candidate)">Vaqtni o‘zgartirish</Button>
          <Button :icon="Check" :disabled="busy" @click="emit('hire', candidate)">Ishga qabul qilish</Button>
        </template>
        <Button v-else-if="rejected" variant="secondary" :icon="RotateCcw" :loading="busy" @click="emit('reopen', candidate)">Qayta ko‘rib chiqish</Button>
        <Button v-else variant="secondary" @click="emit('close')">Yopish</Button>
      </template>
    </template>
  </Modal>
</template>