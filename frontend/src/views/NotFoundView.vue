<script setup>
import { Compass } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
</script>

<template>
  <div class="grid min-h-[60vh] place-items-center text-center">
    <div class="max-w-sm">
      <span class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-primary-50 text-primary-600">
        <Compass class="h-7 w-7" />
      </span>
      <p class="mt-5 text-sm font-medium text-primary-600">404</p>
      <h1 class="mt-1 text-2xl font-semibold tracking-tight text-ink">Sahifa topilmadi</h1>
      <p class="mt-2 text-sm text-muted">Siz qidirgan sahifa mavjud emas yoki boshqa manzilga ko‘chirilgan.</p>
      <Button class="mt-6" @click="$router.push('/dashboard')">Bosh sahifaga qaytish</Button>
    </div>
  </div>
</template>
