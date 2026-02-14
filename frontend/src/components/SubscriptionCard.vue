<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Subscription } from '@/stores/subscription'
import { useSubscriptionStore } from '@/stores/subscription'
import type { PushStatus } from '@/api'
import {
  PlayIcon, PauseIcon, TrashIcon, BoltIcon, CalendarDaysIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps<{ sub: Subscription }>()
const store = useSubscriptionStore()

// ── Push state ──
const triggerLoading = ref(false)
const pushStatus = ref<PushStatus | null>(null)
const showDatePicker = ref(false)
const startDate = ref('')
const endDate = ref('')

const statusColor = computed(() => {
  if (!pushStatus.value) return ''
  if (pushStatus.value.step === 'failed') return 'text-red-600 dark:text-red-400'
  if (pushStatus.value.step === 'completed') return 'text-emerald-600 dark:text-emerald-400'
  return 'text-primary-600 dark:text-primary-400'
})

const progressBarColor = computed(() => {
  if (!pushStatus.value) return 'bg-primary-500'
  if (pushStatus.value.step === 'failed') return 'bg-red-500'
  if (pushStatus.value.step === 'completed') return 'bg-emerald-500'
  return 'bg-primary-500'
})

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function handleTrigger() {
  triggerLoading.value = true
  pushStatus.value = null

  try {
    const dates = (startDate.value && endDate.value)
      ? { start_date: startDate.value, end_date: endDate.value }
      : undefined

    const taskId = await store.trigger(props.sub.id, dates)

    // Poll for status updates
    let done = false
    while (!done) {
      await sleep(2000)
      try {
        const status = await store.pollPushStatus(props.sub.id, taskId)
        pushStatus.value = status
        done = status.is_done
      } catch {
        // If polling fails, show generic error and stop
        pushStatus.value = {
          task_id: taskId,
          subscription_id: props.sub.id,
          step: 'failed',
          message: '无法获取推送状态，请检查后端日志',
          progress: 100,
          papers_found: 0,
          papers_relevant: 0,
          papers_sent: 0,
          error: '状态查询失败',
          is_done: true,
        }
        done = true
      }
    }
  } catch (e: any) {
    pushStatus.value = {
      task_id: '',
      subscription_id: props.sub.id,
      step: 'failed',
      message: e.response?.data?.detail || '推送请求失败，请重试',
      progress: 100,
      papers_found: 0,
      papers_relevant: 0,
      papers_sent: 0,
      error: e.response?.data?.detail || '请求失败',
      is_done: true,
    }
  } finally {
    triggerLoading.value = false
    showDatePicker.value = false
  }
}

function dismissStatus() {
  pushStatus.value = null
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

    <!-- Date Picker (toggle) -->
    <transition name="fade">
      <div v-if="showDatePicker && !triggerLoading" class="mb-4 p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 space-y-2">
        <p class="text-xs font-medium text-gray-500 dark:text-gray-400">选择论文日期范围（可选，留空则抓取今日）</p>
        <div class="flex gap-2">
          <input v-model="startDate" type="date" class="input-field text-xs flex-1" placeholder="开始日期" />
          <input v-model="endDate" type="date" class="input-field text-xs flex-1" placeholder="结束日期" />
        </div>
      </div>
    </transition>

    <!-- Push Progress -->
    <transition name="fade">
      <div v-if="pushStatus" class="mb-4 p-3 rounded-xl" :class="pushStatus.step === 'failed' ? 'bg-red-50 dark:bg-red-950/50' : pushStatus.step === 'completed' ? 'bg-emerald-50 dark:bg-emerald-950/50' : 'bg-primary-50 dark:bg-primary-950/50'">
        <!-- Progress bar -->
        <div class="w-full h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 mb-2 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500 ease-out"
            :class="progressBarColor"
            :style="{ width: pushStatus.progress + '%' }"
          ></div>
        </div>

        <!-- Status message -->
        <p class="text-xs font-medium" :class="statusColor">
          {{ pushStatus.message }}
        </p>

        <!-- Stats (when available) -->
        <div v-if="pushStatus.papers_found > 0 || pushStatus.papers_sent > 0" class="flex gap-3 mt-1.5 text-[10px] text-gray-500 dark:text-gray-400">
          <span v-if="pushStatus.papers_found">抓取: {{ pushStatus.papers_found }} 篇</span>
          <span v-if="pushStatus.papers_relevant">相关: {{ pushStatus.papers_relevant }} 篇</span>
          <span v-if="pushStatus.papers_sent">发送: {{ pushStatus.papers_sent }} 篇</span>
        </div>

        <!-- Dismiss button (when done) -->
        <button v-if="pushStatus.is_done" @click="dismissStatus" class="mt-2 text-[10px] underline text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          关闭
        </button>
      </div>
    </transition>

    <!-- Actions -->
    <div class="flex items-center gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
      <!-- Date toggle button -->
      <button
        v-if="!triggerLoading"
        @click="showDatePicker = !showDatePicker"
        class="p-1.5 rounded-lg transition-colors"
        :class="showDatePicker ? 'text-primary-500 bg-primary-50 dark:bg-primary-950' : 'text-gray-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950'"
        title="选择日期范围"
      >
        <CalendarDaysIcon class="w-4 h-4" />
      </button>

      <!-- Trigger button -->
      <button
        @click="handleTrigger"
        :disabled="triggerLoading || !sub.is_active"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 transition-colors"
      >
        <svg v-if="triggerLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <BoltIcon v-else class="w-3.5 h-3.5" />
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
