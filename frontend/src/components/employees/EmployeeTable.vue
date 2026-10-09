<script setup>
import { computed } from 'vue'
import { Eye, Pencil, Trash2 } from 'lucide-vue-next'
import Avatar from '@/components/ui/Avatar.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useCatalogStore } from '@/stores/catalog'
import { formatDate } from '@/utils/date'

const props = defineProps({
  rows: { type: Array, required: true },
  compact: { type: Boolean, default: false }, // dashboard uchun: telefon va amallarsiz
  selectable: { type: Boolean, default: false }, // ommaviy amallar uchun belgilash
})
const emit = defineEmits(['view', 'edit', 'delete'])
const selected = defineModel('selected', { type: Array, default: () => [] })
const catalog = useCatalogStore()

const allOnPage = computed(() => props.rows.length > 0 && props.rows.every((e) => selected.value.includes(e.id)))
function toggleAll() {
  const ids = props.rows.map((e) => e.id)
  selected.value = allOnPage.value ? selected.value.filter((id) => !ids.includes(id)) : [...new Set([...selected.value, ...ids])]
}
function toggle(id) {
  selected.value = selected.value.includes(id) ? selected.value.filter((x) => x !== id) : [...selected.value, id]
}
</script>

<template>
  <div>
    <!-- Desktop / tablet -->
    <div class="hidden overflow-x-auto md:block">
      <table class="min-w-full">
        <thead class="border-b border-line bg-slate-50/60">
          <tr>
            <th v-if="selectable" class="table-th w-10 pr-0">
              <input type="checkbox" class="h-4 w-4 cursor-pointer rounded border-slate-300 text-primary-600 focus:ring-primary-500" :checked="allOnPage" aria-label="Sahifadagi barcha xodimlarni belgilash" @change="toggleAll" />
            </th>
            <th class="table-th">F.I.Sh</th>
            <th class="table-th">Lavozim</th>
            <th class="table-th">Bo‘lim</th>
            <th v-if="!compact" class="table-th">Telefon</th>
            <th class="table-th">Ishga kirgan sana</th>
            <th class="table-th">Holat</th>
            <th v-if="!compact" class="table-th text-right">Amallar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr
            v-for="e in rows"
            :key="e.id"
            :class="['cursor-pointer transition-colors duration-150', selected.includes(e.id) ? 'bg-primary-50/60' : 'hover:bg-slate-50/80']"
            tabindex="0"
            @click="emit('view', e)"
            @keydown.enter="emit('view', e)"
          >
            <td v-if="selectable" class="table-td w-10 pr-0" @click.stop>
              <input type="checkbox" class="h-4 w-4 cursor-pointer rounded border-slate-300 text-primary-600 focus:ring-primary-500" :checked="selected.includes(e.id)" :aria-label="`${e.fullName}: belgilash`" @change="toggle(e.id)" />
            </td>
            <td class="table-td">
              <div class="flex items-center gap-3">
                <Avatar :name="e.fullName" :src="e.photo" size="sm" />
                <div class="min-w-0">
                  <p class="font-medium text-ink">{{ e.fullName }}</p>
                  <p v-if="!compact && e.email" class="text-xs text-muted">{{ e.email }}</p>
                </div>
              </div>
            </td>
            <td class="table-td">{{ catalog.positionName(e.positionId) }}</td>
            <td class="table-td">
              <span class="inline-flex rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-medium text-primary-700">{{ catalog.departmentName(e.departmentId) }}</span>
            </td>
            <td v-if="!compact" class="table-td tabular-nums text-slate-600">{{ e.phone }}</td>
            <td class="table-td tabular-nums text-slate-600">{{ formatDate(e.hireDate) }}</td>
            <td class="table-td"><StatusBadge :status="e.status" /></td>
            <td v-if="!compact" class="table-td text-right" @click.stop @keydown.enter.stop>
              <div class="inline-flex items-center gap-0.5">
                <button class="icon-btn h-8 w-8" :aria-label="`${e.fullName}: profil`" title="Profil" @click="emit('view', e)">
                  <Eye class="h-4 w-4" />
                </button>
                <button class="icon-btn h-8 w-8" :aria-label="`${e.fullName}: tahrirlash`" title="Tahrirlash" @click="emit('edit', e)">
                  <Pencil class="h-4 w-4" />
                </button>
                <button class="icon-btn h-8 w-8 hover:bg-red-50 hover:text-red-600" :aria-label="`${e.fullName}: o‘chirish`" title="O‘chirish" @click="emit('delete', e)">
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile: kartochkalar -->
    <ul class="divide-y divide-line md:hidden">
      <li v-for="e in rows" :key="e.id">
        <button class="flex w-full items-start gap-3 px-4 py-3.5 text-left active:bg-slate-50" @click="emit('view', e)">
          <Avatar :name="e.fullName" :src="e.photo" size="md" />
          <span class="min-w-0 flex-1">
            <span class="flex items-start justify-between gap-2">
              <span class="truncate font-medium text-ink">{{ e.fullName }}</span>
              <StatusBadge :status="e.status" size="sm" />
            </span>
            <span class="mt-0.5 block truncate text-[13px] text-slate-600">{{ catalog.positionName(e.positionId) }} · {{ catalog.departmentName(e.departmentId) }}</span>
            <span class="mt-1 flex flex-wrap gap-x-4 text-xs tabular-nums text-muted">
              <span v-if="!compact">{{ e.phone }}</span>
              <span>{{ formatDate(e.hireDate) }} dan</span>
            </span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>
