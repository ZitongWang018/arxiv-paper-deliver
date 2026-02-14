<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from '@/components/AppNavbar.vue'

const auth = useAuthStore()
const darkMode = ref(localStorage.getItem('theme') === 'dark')

function toggleDark() {
  darkMode.value = !darkMode.value
  document.documentElement.classList.toggle('dark', darkMode.value)
  localStorage.setItem('theme', darkMode.value ? 'dark' : 'light')
}

onMounted(() => {
  document.documentElement.classList.toggle('dark', darkMode.value)
  if (auth.isLoggedIn) auth.fetchUser()
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppNavbar v-if="auth.isLoggedIn" :dark-mode="darkMode" @toggle-dark="toggleDark" />
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>
