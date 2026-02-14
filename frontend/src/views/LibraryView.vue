<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { starApi } from '@/api'
import PaperCard from '@/components/PaperCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { MagnifyingGlassIcon, FunnelIcon } from '@heroicons/vue/24/outline'

interface StarredPaper {
  id: number
  user_id: number
  paper: {
    id: number
    arxiv_id: string
    title: string
    authors: string
    abstract: string
    url: string
    pdf_url: string
    categories: string | null
    published_date: string | null
  }
  user_note: string | null
  tags: string | null
  starred_at: string
}

const stars = ref<StarredPaper[]>([])
const allTags = ref<string[]>([])
const loading = ref(true)
const searchQuery = ref('')
const selectedTag = ref('')

const filteredStars = computed(() => {
  let result = stars.value
  if (selectedTag.value) {
    result = result.filter(s => (s.tags || '').toLowerCase().includes(selectedTag.value.toLowerCase()))
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.paper.title.toLowerCase().includes(q) ||
      s.paper.authors.toLowerCase().includes(q) ||
      (s.user_note || '').toLowerCase().includes(q)
    )
  }
  return result
})

// Stats
const statsCategories = computed(() => {
  const catMap: Record<string, number> = {}
  stars.value.forEach(s => {
    const cats = (s.paper.categories || '').split(/[\s;,]+/).filter(Boolean)
    cats.forEach(c => { catMap[c] = (catMap[c] || 0) + 1 })
  })
  return Object.entries(catMap).sort((a, b) => b[1] - a[1]).slice(0, 8)
})

async function fetchData() {
  loading.value = true
  try {
    const [starsRes, tagsRes] = await Promise.all([
      starApi.list(),
      starApi.tags(),
    ])
    stars.value = starsRes.data
    allTags.value = tagsRes.data
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">研究库</h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">您收藏的论文和研究笔记</p>
    </div>

    <!-- Stats Overview -->
    <div v-if="!loading && stars.length > 0" class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-primary-600">{{ stars.length }}</p>
        <p class="text-xs text-gray-500 mt-0.5">收藏论文</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-amber-600">{{ allTags.length }}</p>
        <p class="text-xs text-gray-500 mt-0.5">标签分类</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-emerald-600">{{ stars.filter(s => s.user_note).length }}</p>
        <p class="text-xs text-gray-500 mt-0.5">带笔记</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-violet-600">{{ statsCategories.length }}</p>
        <p class="text-xs text-gray-500 mt-0.5">涉及领域</p>
      </div>
    </div>

    <!-- Research field distribution -->
    <div v-if="!loading && statsCategories.length > 0" class="card p-5 mb-8">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">研究领域分布</h3>
      <div class="flex flex-wrap gap-2">
        <div v-for="[cat, count] in statsCategories" :key="cat" class="flex items-center gap-2">
          <span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-primary-50 dark:bg-primary-950 text-primary-600 dark:text-primary-400">
            {{ cat }}
          </span>
          <span class="text-xs text-gray-400">{{ count }}</span>
        </div>
      </div>
    </div>

    <!-- Search + Filter bar -->
    <div v-if="!loading && stars.length > 0" class="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-6">
      <div class="relative flex-1 w-full">
        <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索标题、作者或笔记..."
          class="input-field pl-10"
        />
      </div>
      <div class="flex items-center gap-2">
        <FunnelIcon class="w-4 h-4 text-gray-400" />
        <select v-model="selectedTag" class="input-field py-2 w-40">
          <option value="">全部标签</option>
          <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 4" :key="i" class="card p-5 animate-pulse">
        <div class="h-5 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2"></div>
        <div class="h-3 bg-gray-100 dark:bg-gray-800 rounded w-1/2 mb-3"></div>
        <div class="flex gap-2">
          <div class="h-5 bg-gray-100 dark:bg-gray-800 rounded w-12"></div>
          <div class="h-5 bg-gray-100 dark:bg-gray-800 rounded w-16"></div>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="stars.length === 0"
      title="研究库为空"
      description="通过邮件中的「收藏到研究库」按钮来收藏论文，或者在论文推送后手动收藏"
      icon="📚"
    />

    <!-- No results -->
    <EmptyState
      v-else-if="filteredStars.length === 0"
      title="没有找到匹配的论文"
      description="试试调整搜索条件或清除筛选"
      icon="🔍"
    >
      <button @click="searchQuery = ''; selectedTag = ''" class="btn-secondary text-sm">清除筛选</button>
    </EmptyState>

    <!-- Paper list -->
    <div v-else class="space-y-4">
      <PaperCard
        v-for="star in filteredStars"
        :key="star.id"
        :star="star"
        @updated="fetchData"
        @deleted="fetchData"
      />
    </div>
  </div>
</template>
