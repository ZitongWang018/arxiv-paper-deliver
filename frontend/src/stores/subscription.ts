import { defineStore } from 'pinia'
import { ref } from 'vue'
import { subscriptionApi, type SubscriptionPayload } from '@/api'

export interface Subscription {
  id: number
  user_id: number
  name: string
  research_interest: string
  llm_provider: string
  llm_model: string | null
  arxiv_categories: string[]
  max_papers: number
  start_date: string | null
  end_date: string | null
  auto_daily: boolean
  cron_time: string | null
  is_active: boolean
  created_at: string
}

export const useSubscriptionStore = defineStore('subscription', () => {
  const subscriptions = ref<Subscription[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const { data } = await subscriptionApi.list()
      subscriptions.value = data
    } finally {
      loading.value = false
    }
  }

  async function create(payload: SubscriptionPayload) {
    const { data } = await subscriptionApi.create(payload)
    subscriptions.value.unshift(data)
    return data
  }

  async function update(id: number, payload: Partial<SubscriptionPayload & { is_active: boolean }>) {
    const { data } = await subscriptionApi.update(id, payload)
    const idx = subscriptions.value.findIndex((s) => s.id === id)
    if (idx !== -1) subscriptions.value[idx] = data
    return data
  }

  async function remove(id: number) {
    await subscriptionApi.delete(id)
    subscriptions.value = subscriptions.value.filter((s) => s.id !== id)
  }

  async function trigger(id: number) {
    await subscriptionApi.trigger(id)
  }

  return { subscriptions, loading, fetchAll, create, update, remove, trigger }
})
