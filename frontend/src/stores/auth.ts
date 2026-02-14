import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<{ id: number; email: string; created_at: string } | null>(null)
  const isLoggedIn = computed(() => !!token.value)

  async function fetchUser() {
    if (!token.value) return
    try {
      const { data } = await authApi.me()
      user.value = data
    } catch {
      logout()
    }
  }

  async function login(email: string, password: string) {
    const { data } = await authApi.login(email, password)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
    router.push('/')
  }

  async function register(email: string, password: string) {
    const { data } = await authApi.register(email, password)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
    router.push('/')
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  return { token, user, isLoggedIn, fetchUser, login, register, logout }
})
