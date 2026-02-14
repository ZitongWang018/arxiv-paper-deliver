import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { auth: true },
    },
    {
      path: '/subscriptions/new',
      name: 'NewSubscription',
      component: () => import('@/views/NewSubscriptionView.vue'),
      meta: { auth: true },
    },
    {
      path: '/library',
      name: 'Library',
      component: () => import('@/views/LibraryView.vue'),
      meta: { auth: true },
    },
    {
      path: '/star',
      name: 'StarConfirm',
      component: () => import('@/views/StarConfirmView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.auth && !token) return { name: 'Login' }
  if (to.meta.guest && token) return { name: 'Dashboard' }
})

export default router
