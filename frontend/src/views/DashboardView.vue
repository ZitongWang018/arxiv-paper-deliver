<script setup lang="ts">
import { onMounted } from 'vue'
import { useSubscriptionStore } from '@/stores/subscription'
import SubscriptionCard from '@/components/SubscriptionCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { PlusIcon } from '@heroicons/vue/24/outline'

const store = useSubscriptionStore()

onMounted(() => {
  store.fetchAll()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">我的订阅</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">管理您的 arXiv 论文推送订阅</p>
      </div>
      <router-link to="/subscriptions/new" class="btn-primary gap-2">
        <PlusIcon class="w-4 h-4" />
        新建订阅
      </router-link>
    </div>

    <!-- Loading state -->
    <div v-if="store.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="i in 3" :key="i" class="card p-6 animate-pulse">
        <div class="h-5 bg-gray-200 dark:bg-gray-800 rounded w-2/3 mb-3"></div>
        <div class="h-3 bg-gray-100 dark:bg-gray-800 rounded w-1/3 mb-4"></div>
        <div class="h-3 bg-gray-100 dark:bg-gray-800 rounded w-full mb-2"></div>
        <div class="h-3 bg-gray-100 dark:bg-gray-800 rounded w-4/5 mb-4"></div>
        <div class="flex gap-2">
          <div class="h-6 bg-gray-100 dark:bg-gray-800 rounded w-16"></div>
          <div class="h-6 bg-gray-100 dark:bg-gray-800 rounded w-16"></div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="store.subscriptions.length === 0"
      title="暂无订阅"
      description="创建您的第一个论文推送订阅，让 AI 为您精选每日最相关的 arXiv 论文"
      icon="🔬"
    >
      <router-link to="/subscriptions/new" class="btn-primary gap-2">
        <PlusIcon class="w-4 h-4" />
        创建第一个订阅
      </router-link>
    </EmptyState>

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <SubscriptionCard v-for="sub in store.subscriptions" :key="sub.id" :sub="sub" />
    </div>
  </div>
</template>
