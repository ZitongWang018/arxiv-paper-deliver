import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ──────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
}

// ── Subscriptions ────────────────────────────────────
export interface SubscriptionPayload {
  name: string
  research_interest: string
  llm_provider: 'qwen' | 'deepseek'
  llm_api_key: string
  llm_model?: string
  arxiv_categories: string[]
  max_papers: number
  start_date?: string | null
  end_date?: string | null
  auto_daily: boolean
  cron_time?: string
}

export interface TriggerPayload {
  start_date?: string | null
  end_date?: string | null
}

export interface PushStatus {
  task_id: string
  subscription_id: number
  step: string
  message: string
  progress: number
  papers_found: number
  papers_relevant: number
  papers_sent: number
  error: string | null
  is_done: boolean
}

export const subscriptionApi = {
  list: () => api.get('/subscriptions'),
  create: (data: SubscriptionPayload) => api.post('/subscriptions', data),
  get: (id: number) => api.get(`/subscriptions/${id}`),
  update: (id: number, data: Partial<SubscriptionPayload & { is_active: boolean }>) =>
    api.put(`/subscriptions/${id}`, data),
  delete: (id: number) => api.delete(`/subscriptions/${id}`),
  trigger: (id: number, dates?: TriggerPayload) =>
    api.post<{ message: string; task_id: string }>(`/subscriptions/${id}/trigger`, dates || {}),
  pushStatus: (id: number, taskId: string) =>
    api.get<PushStatus>(`/subscriptions/${id}/push-status/${taskId}`),
  history: (id: number) => api.get(`/subscriptions/${id}/history`),
}

// ── Papers ───────────────────────────────────────────
export const paperApi = {
  get: (id: number) => api.get(`/papers/${id}`),
  search: (q: string, limit = 20) => api.get('/papers', { params: { q, limit } }),
}

// ── Stars ────────────────────────────────────────────
export const starApi = {
  list: (tag = '', search = '') => api.get('/stars', { params: { tag, search } }),
  create: (paper_id: number, user_note = '', tags = '') =>
    api.post('/stars', { paper_id, user_note, tags }),
  update: (id: number, data: { user_note?: string; tags?: string }) =>
    api.put(`/stars/${id}`, data),
  delete: (id: number) => api.delete(`/stars/${id}`),
  tags: () => api.get('/stars/tags'),
}

export default api
