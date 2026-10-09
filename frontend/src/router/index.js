import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { title: 'Kirish', public: true, layout: 'blank' } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: 'Bosh sahifa' } },
  { path: '/candidates', name: 'candidates', component: () => import('@/views/CandidatesView.vue'), meta: { title: 'Nomzodlar' } },
  { path: '/employees', name: 'employees', component: () => import('@/views/EmployeesView.vue'), meta: { title: 'Xodimlar' } },
  { path: '/employees/:id(\\d+)', name: 'employee', component: () => import('@/views/EmployeeProfileView.vue'), meta: { title: 'Xodim profili', menu: '/employees' } },
  { path: '/lessons', name: 'lessons', component: () => import('@/views/LessonsView.vue'), meta: { title: 'Darslar' } },
  { path: '/tests', name: 'tests', component: () => import('@/views/TestsView.vue'), meta: { title: 'Testlar' } },
  { path: '/documents', name: 'documents', component: () => import('@/views/DocumentsView.vue'), meta: { title: 'Hujjatlar' } },
  { path: '/settings', name: 'settings', component: () => import('@/views/SettingsView.vue'), meta: { title: 'Sozlamalar' } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue'), meta: { title: 'Sahifa topilmadi' } },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: (to, from) => (to.path === from.path ? false : { top: 0 }),
})

// Login qilmagan foydalanuvchi CRM sahifalariga kira olmaydi
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (to.name === 'login' && (await auth.verify())) return { path: String(to.query.redirect || '/dashboard') }
    return true
  }
  if (!(await auth.verify())) {
    return { name: 'login', query: to.fullPath !== '/dashboard' && to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }
  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} — HR CRM` : 'HR CRM'
})

export default router
