<script setup lang="ts">
import { ref } from 'vue'
import { starApi } from '@/api'
import {
  ChevronDownIcon, ChevronUpIcon, PencilIcon,
  TrashIcon, ArrowTopRightOnSquareIcon, TagIcon,
} from '@heroicons/vue/24/outline'

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

const props = defineProps<{ star: StarredPaper }>()
const emit = defineEmits<{ updated: []; deleted: [] }>()

const expanded = ref(false)
const editing = ref(false)
const editNote = ref(props.star.user_note || '')
const editTags = ref(props.star.tags || '')
const saving = ref(false)

async function saveEdit() {
  saving.value = true
  try {
    await starApi.update(props.star.id, {
      user_note: editNote.value,
      tags: editTags.value,
    })
    editing.value = false
    emit('updated')
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (confirm('确认取消收藏？')) {
    await starApi.delete(props.star.id)
    emit('deleted')
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}
</script>

<template>
  <div class="card overflow-hidden transition-all duration-200" :class="expanded ? 'ring-1 ring-primary-200 dark:ring-primary-800' : ''">
    <div class="p-5">
      <!-- Header -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1 min-w-0">
          <a :href="star.paper.url" target="_blank" class="text-base font-semibold text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 transition-colors leading-snug line-clamp-2">
            {{ star.paper.title }}
            <ArrowTopRightOnSquareIcon class="inline w-3.5 h-3.5 ml-1 opacity-40" />
          </a>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">{{ star.paper.authors }}</p>
        </div>
        <button @click="expanded = !expanded" class="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0 transition-colors">
          <ChevronUpIcon v-if="expanded" class="w-4 h-4" />
          <ChevronDownIcon v-else class="w-4 h-4" />
        </button>
      </div>

      <!-- Tags -->
      <div class="flex items-center gap-2 mt-3">
        <TagIcon class="w-3.5 h-3.5 text-gray-400" />
        <div v-if="star.tags" class="flex flex-wrap gap-1.5">
          <span v-for="tag in star.tags.split(',').filter(Boolean)" :key="tag"
            class="px-2 py-0.5 rounded-md text-[10px] font-medium bg-primary-50 dark:bg-primary-950 text-primary-600 dark:text-primary-400">
            {{ tag.trim() }}
          </span>
        </div>
        <span v-else class="text-xs text-gray-400">无标签</span>
        <span class="ml-auto text-[10px] text-gray-400">{{ formatDate(star.starred_at) }}</span>
      </div>

      <!-- Note preview -->
      <p v-if="star.user_note && !expanded" class="text-xs text-gray-500 dark:text-gray-400 mt-2 line-clamp-1 italic">
        📝 {{ star.user_note }}
      </p>
    </div>

    <!-- Expanded content -->
    <transition name="slide">
      <div v-if="expanded" class="px-5 pb-5 space-y-4">
        <!-- Abstract -->
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50">
          <p class="text-xs font-medium text-gray-500 mb-1">Abstract</p>
          <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{{ star.paper.abstract }}</p>
        </div>

        <!-- Note edit section -->
        <div v-if="editing" class="space-y-3">
          <div>
            <label class="text-xs font-medium text-gray-500 block mb-1">笔记</label>
            <textarea v-model="editNote" rows="3" class="input-field text-sm resize-none" placeholder="记录您的阅读想法..."></textarea>
          </div>
          <div>
            <label class="text-xs font-medium text-gray-500 block mb-1">标签（逗号分隔）</label>
            <input v-model="editTags" type="text" class="input-field text-sm" placeholder="例：LLM, RLHF, 多模态" />
          </div>
          <div class="flex gap-2">
            <button @click="saveEdit" :disabled="saving" class="btn-primary text-xs px-4 py-1.5">
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button @click="editing = false" class="btn-secondary text-xs px-4 py-1.5">取消</button>
          </div>
        </div>
        <div v-else-if="star.user_note" class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
          <p class="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">📝 我的笔记</p>
          <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{{ star.user_note }}</p>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2 pt-2 border-t border-gray-100 dark:border-gray-800">
          <a :href="star.paper.pdf_url" target="_blank" class="btn-secondary text-xs px-3 py-1.5">📥 PDF</a>
          <button @click="editing = true" class="btn-secondary text-xs px-3 py-1.5 gap-1">
            <PencilIcon class="w-3 h-3" /> 编辑
          </button>
          <button @click="handleDelete" class="ml-auto p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors">
            <TrashIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
