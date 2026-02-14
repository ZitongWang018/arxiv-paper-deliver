<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSubscriptionStore } from '@/stores/subscription'
import { CheckIcon } from '@heroicons/vue/24/solid'
import { ArrowLeftIcon, ArrowRightIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const subStore = useSubscriptionStore()

const step = ref(1)
const totalSteps = 4
const loading = ref(false)
const error = ref('')

// Form data
const form = ref({
  name: '',
  research_interest: '',
  llm_provider: 'deepseek' as 'qwen' | 'deepseek',
  llm_api_key: '',
  llm_model: '',
  arxiv_categories: [] as string[],
  max_papers: 5,
  auto_daily: false,
  cron_time: '08:00',
  start_date: null as string | null,
  end_date: null as string | null,
})

// Step validation
const stepValid = computed(() => {
  switch (step.value) {
    case 1: return form.value.name.trim() !== '' && form.value.research_interest.trim() !== ''
    case 2: return form.value.llm_api_key.trim() !== ''
    case 3: return form.value.arxiv_categories.length > 0
    case 4: return true
    default: return false
  }
})

const steps = [
  { num: 1, title: '基本设置' },
  { num: 2, title: 'LLM 配置' },
  { num: 3, title: 'arXiv 类别' },
  { num: 4, title: '确认' },
]

// arXiv categories for selection
const categoryGroups: Record<string, string[]> = {
  'Computer Science': [
    'cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.IR', 'cs.NE',
    'cs.RO', 'cs.SE', 'cs.CR', 'cs.DC', 'cs.HC', 'cs.MA',
    'cs.DS', 'cs.DB', 'cs.GT', 'cs.CE', 'cs.CG', 'cs.CY',
    'cs.DL', 'cs.DM', 'cs.ET', 'cs.FL', 'cs.GR', 'cs.AR',
    'cs.IT', 'cs.LO', 'cs.MM', 'cs.NI', 'cs.NA', 'cs.OS',
    'cs.PF', 'cs.PL', 'cs.SI', 'cs.SD', 'cs.SC', 'cs.SY',
  ],
  'Mathematics': [
    'math.AG', 'math.NT', 'math.PR', 'math.ST', 'math.OC',
    'math.CO', 'math.CA', 'math.FA', 'math.NA', 'math.AP',
  ],
  'Statistics': ['stat.ML', 'stat.AP', 'stat.CO', 'stat.ME'],
  'Physics': ['quant-ph', 'hep-th', 'hep-ph', 'cond-mat', 'astro-ph', 'gr-qc'],
  'Other': ['q-bio', 'q-fin', 'eess', 'econ'],
}

function toggleCategory(cat: string) {
  const idx = form.value.arxiv_categories.indexOf(cat)
  if (idx >= 0) {
    form.value.arxiv_categories.splice(idx, 1)
  } else {
    form.value.arxiv_categories.push(cat)
  }
}

function isCatSelected(cat: string) {
  return form.value.arxiv_categories.includes(cat)
}

const llmModelOptions: Record<string, string[]> = {
  qwen: ['qwen-plus', 'qwen-turbo', 'qwen-max'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    await subStore.create({
      ...form.value,
      llm_model: form.value.llm_model || undefined,
    })
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '创建失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
    <!-- Header -->
    <div class="mb-8">
      <button @click="router.push('/')" class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-3 inline-flex items-center gap-1 transition-colors">
        <ArrowLeftIcon class="w-4 h-4" /> 返回仪表盘
      </button>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">新建订阅</h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">设置 AI 驱动的 arXiv 论文推送</p>
    </div>

    <!-- Stepper -->
    <div class="flex items-center gap-0 mb-10">
      <template v-for="(s, i) in steps" :key="s.num">
        <div class="flex items-center gap-2">
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300"
            :class="step > s.num
              ? 'bg-primary-600 text-white'
              : step === s.num
                ? 'bg-primary-600 text-white ring-4 ring-primary-100 dark:ring-primary-900'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'"
          >
            <CheckIcon v-if="step > s.num" class="w-4 h-4" />
            <span v-else>{{ s.num }}</span>
          </div>
          <span class="text-sm font-medium hidden sm:block" :class="step >= s.num ? 'text-gray-900 dark:text-white' : 'text-gray-400'">{{ s.title }}</span>
        </div>
        <div v-if="i < steps.length - 1" class="flex-1 h-px mx-3" :class="step > s.num ? 'bg-primary-500' : 'bg-gray-200 dark:bg-gray-700'"></div>
      </template>
    </div>

    <!-- Step Content -->
    <div class="card p-8">
      <!-- Step 1: Basic -->
      <div v-show="step === 1" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">订阅名称</label>
          <input v-model="form.name" type="text" class="input-field" placeholder="例：LLM 前沿进展" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">研究兴趣 / 想了解的问题</label>
          <textarea
            v-model="form.research_interest"
            rows="5"
            class="input-field resize-none"
            placeholder="详细描述您的研究问题或想要关注的领域。越详细，推荐越精准。&#10;&#10;例：&#10;1. 大语言模型的预训练和微调方法&#10;2. 多模态机器学习，特别是视觉-语言模型&#10;3. 对强化学习与人类反馈(RLHF)感兴趣"
          ></textarea>
          <p class="mt-1.5 text-xs text-gray-400">AI 将基于此描述分析每篇论文的相关性，而非简单的关键词匹配</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">最多推送篇数</label>
          <div class="flex items-center gap-4">
            <input v-model.number="form.max_papers" type="range" min="1" max="30" class="flex-1 accent-primary-600" />
            <span class="text-sm font-bold text-primary-600 w-8 text-center">{{ form.max_papers }}</span>
          </div>
        </div>
      </div>

      <!-- Step 2: LLM -->
      <div v-show="step === 2" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">选择大模型</label>
          <div class="grid grid-cols-2 gap-4">
            <button
              v-for="provider in ['deepseek', 'qwen'] as const"
              :key="provider"
              @click="form.llm_provider = provider; form.llm_model = ''"
              class="p-4 rounded-xl border-2 text-left transition-all duration-200"
              :class="form.llm_provider === provider
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-950'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
            >
              <span class="text-lg font-bold" :class="form.llm_provider === provider ? 'text-primary-700 dark:text-primary-300' : 'text-gray-700 dark:text-gray-300'">
                {{ provider === 'deepseek' ? 'DeepSeek' : 'Qwen (通义千问)' }}
              </span>
              <p class="text-xs text-gray-500 mt-1">
                {{ provider === 'deepseek' ? 'api.deepseek.com' : 'dashscope.aliyuncs.com' }}
              </p>
            </button>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">API Key</label>
          <input v-model="form.llm_api_key" type="password" class="input-field" placeholder="输入 API Key" />
          <p class="mt-1.5 text-xs text-gray-400">API Key 将加密存储，仅用于论文分析</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">模型（可选）</label>
          <select v-model="form.llm_model" class="input-field">
            <option value="">默认</option>
            <option v-for="m in llmModelOptions[form.llm_provider]" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
      </div>

      <!-- Step 3: Categories -->
      <div v-show="step === 3" class="space-y-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">选择您感兴趣的 arXiv 分类（可多选）</p>
        <div v-for="(cats, group) in categoryGroups" :key="group" class="space-y-2">
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ group }}</h4>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="cat in cats"
              :key="cat"
              @click="toggleCategory(cat)"
              class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
              :class="isCatSelected(cat)
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
            >
              {{ cat }}
            </button>
          </div>
        </div>
        <p class="text-xs text-gray-400">已选: {{ form.arxiv_categories.length }} 个分类</p>
      </div>

      <!-- Step 4: Confirm -->
      <div v-show="step === 4" class="space-y-6">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">确认订阅设置</h3>
        <div class="space-y-4">
          <div class="flex justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-500">订阅名称</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ form.name }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-500">大模型</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ form.llm_provider === 'deepseek' ? 'DeepSeek' : 'Qwen' }} {{ form.llm_model || '(默认)' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-500">最大推送数</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ form.max_papers }}</span>
          </div>
          <div class="py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-500 block mb-2">研究兴趣</span>
            <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">{{ form.research_interest }}</p>
          </div>
          <div class="py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-500 block mb-2">arXiv 分类</span>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="cat in form.arxiv_categories" :key="cat" class="px-2 py-0.5 rounded-md text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
                {{ cat }}
              </span>
            </div>
          </div>
        </div>

        <!-- Schedule options -->
        <div class="card bg-gray-50 dark:bg-gray-800/50 p-5 space-y-4 border-0">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">每日自动推送</p>
              <p class="text-xs text-gray-400">开启后每天定时自动抓取论文并推送到邮箱</p>
            </div>
            <button
              @click="form.auto_daily = !form.auto_daily"
              class="relative inline-flex h-6 w-11 rounded-full transition-colors duration-200"
              :class="form.auto_daily ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-5 w-5 rounded-full bg-white shadow-sm transform transition-transform duration-200 mt-0.5"
                :class="form.auto_daily ? 'translate-x-[22px]' : 'translate-x-0.5'"
              ></span>
            </button>
          </div>
          <div v-if="form.auto_daily" class="flex items-center gap-3">
            <label class="text-sm text-gray-500">推送时间</label>
            <input v-model="form.cron_time" type="time" class="input-field w-32" />
          </div>
        </div>

        <div v-if="error" class="p-3 rounded-xl bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400 text-sm">
          {{ error }}
        </div>
      </div>

      <!-- Navigation -->
      <div class="flex items-center justify-between mt-8 pt-6 border-t border-gray-100 dark:border-gray-800">
        <button v-if="step > 1" @click="step--" class="btn-secondary gap-2">
          <ArrowLeftIcon class="w-4 h-4" /> 上一步
        </button>
        <div v-else></div>

        <button v-if="step < totalSteps" @click="step++" :disabled="!stepValid" class="btn-primary gap-2">
          下一步 <ArrowRightIcon class="w-4 h-4" />
        </button>
        <button v-else @click="handleSubmit" :disabled="loading" class="btn-primary gap-2">
          <svg v-if="loading" class="animate-spin -ml-1 mr-1 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          {{ loading ? '创建中...' : '创建订阅' }}
        </button>
      </div>
    </div>
  </div>
</template>
