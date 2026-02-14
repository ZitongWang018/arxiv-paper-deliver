<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { MoonIcon, SunIcon, Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'
import { ref } from 'vue'

defineProps<{ darkMode: boolean }>()
const emit = defineEmits<{ 'toggle-dark': [] }>()

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const mobileOpen = ref(false)

const navLinks = [
  { name: '仪表盘', path: '/' },
  { name: '新建订阅', path: '/subscriptions/new' },
  { name: '研究库', path: '/library' },
]

function isActive(path: string) {
  return route.path === path
}
</script>

<template>
  <nav class="sticky top-0 z-50 backdrop-blur-xl bg-white/80 dark:bg-gray-950/80 border-b border-gray-200 dark:border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2.5 shrink-0">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <span class="text-white text-sm font-bold">A</span>
          </div>
          <span class="text-lg font-bold tracking-tight text-gray-900 dark:text-white">ArxivDigest</span>
        </router-link>

        <!-- Desktop nav -->
        <div class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150"
            :class="isActive(link.path)
              ? 'bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800'"
          >
            {{ link.name }}
          </router-link>
        </div>

        <!-- Right actions -->
        <div class="flex items-center gap-3">
          <button @click="emit('toggle-dark')" class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <MoonIcon v-if="!darkMode" class="w-5 h-5" />
            <SunIcon v-else class="w-5 h-5" />
          </button>
          <div class="hidden md:flex items-center gap-3">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ auth.user?.email }}</span>
            <button @click="auth.logout()" class="text-sm text-red-500 hover:text-red-600 font-medium transition-colors">退出</button>
          </div>
          <!-- Mobile hamburger -->
          <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
            <Bars3Icon v-if="!mobileOpen" class="w-5 h-5" />
            <XMarkIcon v-else class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <transition name="slide">
      <div v-if="mobileOpen" class="md:hidden border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 px-4 py-3 space-y-1">
        <router-link
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          @click="mobileOpen = false"
          class="block px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="isActive(link.path) ? 'bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300' : 'text-gray-600 dark:text-gray-400'"
        >
          {{ link.name }}
        </router-link>
        <div class="pt-2 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <span class="text-sm text-gray-500">{{ auth.user?.email }}</span>
          <button @click="auth.logout()" class="text-sm text-red-500 font-medium">退出</button>
        </div>
      </div>
    </transition>
  </nav>
</template>
