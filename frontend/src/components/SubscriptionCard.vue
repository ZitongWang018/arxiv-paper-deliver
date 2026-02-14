<script setup lang="ts">
import { ref } from 'vue'
import type { Subscription } from '@/stores/subscription'
import { useSubscriptionStore } from '@/stores/subscription'
import {
  PlayIcon, PauseIcon, TrashIcon, BoltIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps<{ sub: Subscription }>()
const store = useSubscriptionStore()
const triggerLoading = ref(false)
const toastMsg = ref('')

async function handleTrigger() {
  triggerLoading.value = true
  try {
    await store.trigger(props.sub.id)
    toastMsg.value = '推送任务已提交！请查收邮件'
    setTimeout(() => (toastMsg.value = ''), 3000)
  } catch {
    toastMsg.value = '推送失败，请重试'
    setTimeout(() => (toastMsg.value = ''), 3000)
  } finally {
    triggerLoading.value = false
  }
}

async function toggleActive() {
  await store.update(props.sub.id, { is_active: !props.sub.is_active })
}

async function handleDelete() {
  if (confirm(`确认删除订阅「${props.sub.name}」？此操作不可撤销。`)) {
    await store.remove(props.sub.id)
  }
}

const providerLabel: Record<string, string> = {
  qwen: 'Qwen',
  deepseek: 'DeepSeek',
}
</script>

<template>
  <div class="card p-6 relative overflow-hidden group">
    <!-- Status indicator -->
    <div class="absolute top-0 right-0 w-20 h-20">
      <div
        class="absolute top-3 right-[-28px] w-[100px] text-center text-[10px] font-bold uppercase tracking-wider py-1 rotate-45"
        :class="sub.is_active ? 'bg-emerald-500 text-white' : 'bg-gray-300 dark:bg-gray-700 text-gray-600 dark:text-gray-400'"
      >
        {{ sub.is_active ? '运行中' : '已暂停' }}
      </div>
    </div>

    <!-- Header -->
    <div class="mb-4">
      <h3 class="text-lg font-bold text-gray-900 dark:text-white pr-16 truncate">{{ sub.name }}</h3>
      <div class="flex items-center gap-2 mt-1.5">
        <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
          {{ providerLabel[sub.llm_provider] || sub.llm_provider }}
        </span>
        <span v-if="sub.auto_daily" class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
          每日 {{ sub.cron_time || '08:00' }}
        </span>
        <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
          Top {{ sub.max_papers }}
        </span>
      </div>
    </div>

    <!-- Research Interest Preview -->
    <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3 leading-relaxed">
      {{ sub.research_interest }}
    </p>

    <!-- Categories -->
    <div class="flex flex-wrap gap-1.5 mb-4">
      <span
        v-for="cat in sub.arxiv_categories.slice(0, 4)"
        :key="cat"
        class="px-2 py-0.5 text-xs rounded-md bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400"
      >
        {{ cat }}
      </span>
      <span v-if="sub.arxiv_categories.length > 4" class="text-xs text-gray-400">
        +{{ sub.arxiv_categories.length - 4 }}
      </span>
    </div>

    <!-- Toast -->
    <transition name="fade">
      <div v-if="toastMsg" class="mb-3 p-2.5 rounded-lg text-xs font-medium bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300">
        {{ toastMsg }}
      </div>
    </transition>

    <!-- Actions -->
    <div class="flex items-center gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
      <button
        @click="handleTrigger"
        :disabled="triggerLoading || !sub.is_active"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 transition-colors"
      >
        <BoltIcon class="w-3.5 h-3.5" />
        {{ triggerLoading ? '推送中...' : '立即推送' }}
      </button>
      <button @click="toggleActive" class="p-1.5 rounded-lg text-gray-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950 transition-colors" :title="sub.is_active ? '暂停' : '启用'">
        <PauseIcon v-if="sub.is_active" class="w-4 h-4" />
        <PlayIcon v-else class="w-4 h-4" />
      </button>
      <button @click="handleDelete" class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors ml-auto" title="删除">
        <TrashIcon class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>
