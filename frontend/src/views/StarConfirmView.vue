<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { paperApi, starApi } from '@/api'
import { StarIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/solid'

const route = useRoute()
const router = useRouter()

const paper = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const status = ref<'form' | 'success' | 'error' | 'already'>('form')
const errorMsg = ref('')
const note = ref('')
const tags = ref('')

function closePage() {
  window.close()
}

onMounted(async () => {
  const paperId = Number(route.query.paper_id)
  const token = route.query.token as string

  if (!paperId || !token) {
    errorMsg.value = '链接参数无效'
    status.value = 'error'
    loading.value = false
    return
  }

  // Store token for API auth
  localStorage.setItem('token', token)

  try {
    const { data } = await paperApi.get(paperId)
    paper.value = data
  } catch {
    errorMsg.value = '论文不存在或链接已过期'
    status.value = 'error'
  } finally {
    loading.value = false
  }
})

async function handleStar() {
  if (!paper.value) return
  saving.value = true
  try {
    await starApi.create(paper.value.id, note.value, tags.value)
    status.value = 'success'
  } catch (e: any) {
    if (e.response?.status === 409) {
      status.value = 'already'
    } else {
      errorMsg.value = e.response?.data?.detail || '收藏失败'
      status.value = 'error'
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-primary-50 via-white to-amber-50 dark:from-gray-950 dark:via-gray-900 dark:to-primary-950">
    <div class="w-full max-w-lg">

      <!-- Loading -->
      <div v-if="loading" class="card p-8 text-center">
        <div class="animate-pulse space-y-4">
          <div class="h-6 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mx-auto"></div>
          <div class="h-4 bg-gray-100 dark:bg-gray-800 rounded w-1/2 mx-auto"></div>
        </div>
      </div>

      <!-- Success State -->
      <div v-else-if="status === 'success'" class="card p-8 text-center">
        <CheckCircleIcon class="w-16 h-16 text-emerald-500 mx-auto mb-4" />
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">收藏成功！</h2>
        <p class="text-sm text-gray-500 mb-6">论文已添加到您的研究库</p>
        <div class="flex gap-3 justify-center">
          <button @click="router.push('/library')" class="btn-primary">查看研究库</button>
          <button @click="closePage" class="btn-secondary">关闭页面</button>
        </div>
      </div>

      <!-- Already Starred -->
      <div v-else-if="status === 'already'" class="card p-8 text-center">
        <StarIcon class="w-16 h-16 text-amber-500 mx-auto mb-4" />
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">已经收藏过了</h2>
        <p class="text-sm text-gray-500 mb-6">这篇论文已在您的研究库中</p>
        <button @click="router.push('/library')" class="btn-primary">查看研究库</button>
      </div>

      <!-- Error State -->
      <div v-else-if="status === 'error'" class="card p-8 text-center">
        <ExclamationTriangleIcon class="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">出错了</h2>
        <p class="text-sm text-gray-500 mb-6">{{ errorMsg }}</p>
        <button @click="router.push('/login')" class="btn-primary">登录后重试</button>
      </div>

      <!-- Form State -->
      <div v-else class="space-y-5">
        <!-- Paper Preview Card -->
        <div class="card p-6">
          <div class="flex items-center gap-2 mb-4">
            <StarIcon class="w-5 h-5 text-amber-500" />
            <h2 class="text-lg font-bold text-gray-900 dark:text-white">收藏到研究库</h2>
          </div>

          <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 mb-4">
            <a :href="paper.url" target="_blank" class="text-base font-semibold text-primary-700 dark:text-primary-400 hover:underline leading-snug">
              {{ paper.title }}
            </a>
            <p class="text-xs text-gray-500 mt-1.5">{{ paper.authors }}</p>
            <p class="text-xs text-gray-400 mt-2 line-clamp-3 leading-relaxed">{{ paper.abstract }}</p>
          </div>

          <form @submit.prevent="handleStar" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">阅读笔记（可选）</label>
              <textarea
                v-model="note"
                rows="3"
                class="input-field text-sm resize-none"
                placeholder="为什么这篇论文对您的研究有价值？记录您的初步想法..."
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">标签（可选，逗号分隔）</label>
              <input v-model="tags" type="text" class="input-field text-sm" placeholder="例：LLM, RLHF, 多模态" />
            </div>
            <button type="submit" :disabled="saving" class="btn-primary w-full gap-2">
              <StarIcon class="w-4 h-4" />
              {{ saving ? '收藏中...' : '确认收藏' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
