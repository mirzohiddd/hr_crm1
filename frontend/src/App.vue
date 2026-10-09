<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import Topbar from '@/components/layout/Topbar.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const ui = useUiStore()

watch(() => route.fullPath, () => ui.closeOverlays())
</script>

<template>
  <div class="min-h-screen">
    <!-- Login sahifasi: menyusiz -->
    <RouterView v-if="route.meta.layout === 'blank'" />

    <template v-else-if="route.matched.length">
      <Sidebar />

      <div
        :class="[
          'flex min-h-screen flex-col transition-[padding] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] md:pl-[76px]',
          ui.collapsedPref ? 'lg:pl-[76px]' : 'lg:pl-64',
        ]"
      >
        <Topbar @toggle-sidebar="ui.toggleSidebar()" />
        <main class="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div class="mx-auto w-full max-w-[1480px]">
            <RouterView v-slot="{ Component }">
              <Transition name="page" mode="out-in">
                <component :is="Component" :key="route.path" />
              </Transition>
            </RouterView>
          </div>
        </main>
      </div>
    </template>

    <ToastContainer />
  </div>
</template>
