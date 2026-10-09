<script setup>
import { Download, Eye, FileImage, FileSpreadsheet, FileText, Trash2 } from 'lucide-vue-next'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useEmployeesStore } from '@/stores/employees'
import { useCatalogStore } from '@/stores/catalog'
import { formatDate } from '@/utils/date'
import { formatBytes } from '@/utils/format'

defineProps({
  rows: { type: Array, required: true },
  hideEmployee: { type: Boolean, default: false }, // xodim profilida
})
const emit = defineEmits(['view', 'download', 'delete'])
const employees = useEmployeesStore()
const catalog = useCatalogStore()

const employeeOf = (d) => employees.findById(d.employeeId)
const nameOf = (d) => employeeOf(d)?.fullName || d.employeeName || 'O‘chirilgan xodim'
const iconOf = (d) => {
  const ext = d.fileName.split('.').pop().toLowerCase()
  if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) return FileImage
  if (['xls', 'xlsx', 'csv'].includes(ext)) return FileSpreadsheet
  return FileText
}
</script>

<template>
  <div>
    <div class="hidden overflow-x-auto md:block">
      <table class="min-w-full">
        <thead class="border-b border-line bg-slate-50/60">
          <tr>
            <th v-if="!hideEmployee" class="table-th">Xodim</th>
            <th class="table-th">Hujjat</th>
            <th class="table-th">Yuklangan sana</th>
            <th class="table-th">Holat</th>
            <th class="table-th text-right">Amallar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr v-for="d in rows" :key="d.id" class="cursor-pointer transition-colors hover:bg-slate-50/80" @click="emit('view', d)">
            <td v-if="!hideEmployee" class="table-td">
              <div class="flex items-center gap-3">
                <Avatar :name="nameOf(d)" :src="employeeOf(d)?.photo" size="sm" />
                <div>
                  <p class="font-medium text-ink">{{ nameOf(d) }}</p>
                  <p class="text-xs text-muted">{{ employeeOf(d) ? catalog.positionName(employeeOf(d).positionId) : '—' }}</p>
                </div>
              </div>
            </td>
            <td class="table-td">
              <div class="flex items-center gap-2.5">
                <component :is="iconOf(d)" class="h-4 w-4 shrink-0 text-slate-400" />
                <div class="min-w-0">
                  <p>{{ d.type }}</p>
                  <p class="max-w-[260px] truncate text-xs text-muted">{{ d.fileName }} · {{ formatBytes(d.fileSize) }}</p>
                </div>
              </div>
            </td>
            <td class="table-td tabular-nums text-slate-600">{{ formatDate(d.uploadedAt) }}</td>
            <td class="table-td"><StatusBadge :status="d.status" /></td>
            <td class="table-td text-right" @click.stop>
              <div class="inline-flex items-center gap-0.5">
                <button class="icon-btn h-8 w-8" :aria-label="`${d.fileName}: ko‘rish`" title="Ko‘rish" @click="emit('view', d)"><Eye class="h-4 w-4" /></button>
                <button class="icon-btn h-8 w-8" :aria-label="`${d.fileName}: yuklab olish`" title="Yuklab olish" @click="emit('download', d)"><Download class="h-4 w-4" /></button>
                <button class="icon-btn h-8 w-8 hover:bg-red-50 hover:text-red-600" :aria-label="`${d.fileName}: o‘chirish`" title="O‘chirish" @click="emit('delete', d)">
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ul class="divide-y divide-line md:hidden">
      <li v-for="d in rows" :key="d.id" class="flex items-start gap-3 px-4 py-3.5">
        <button class="flex min-w-0 flex-1 items-start gap-3 text-left" @click="emit('view', d)">
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600">
            <component :is="iconOf(d)" class="h-5 w-5" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="flex items-start justify-between gap-2">
              <span class="truncate font-medium text-ink">{{ d.type }}</span>
              <StatusBadge :status="d.status" size="sm" />
            </span>
            <span v-if="!hideEmployee" class="mt-0.5 block truncate text-[13px] text-slate-600">{{ nameOf(d) }}</span>
            <span class="mt-0.5 block truncate text-xs tabular-nums text-muted">{{ formatDate(d.uploadedAt) }} · {{ formatBytes(d.fileSize) }}</span>
          </span>
        </button>
        <button class="icon-btn h-9 w-9 hover:bg-red-50 hover:text-red-600" :aria-label="`${d.fileName}: o‘chirish`" @click="emit('delete', d)">
          <Trash2 class="h-4 w-4" />
        </button>
      </li>
    </ul>
  </div>
</template>
