// Thin typed fetch wrapper. In dev, Vite proxies /api → http://localhost:8000.
import type {
  AgentResult,
  AnalyticsSummary,
  AskResult,
  CategorizeResult,
  CoachResult,
  DocRecord,
  GoalInput,
  GoalsSummary,
  Health,
  Profile,
  TokenResponse,
  Txn,
} from '../types'

const BASE = import.meta.env.VITE_API_URL || '/api'
const TOKEN_KEY = 'afc_token'

export const auth = {
  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },
  set(token: string | null) {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  },
}

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const t = auth.token
  return t ? { ...extra, Authorization: `Bearer ${t}` } : extra
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: authHeaders({ 'Content-Type': 'application/json', ...(init?.headers as any) }),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} — ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => req<Health>('/health'),

  // ---- Auth --------------------------------------------------------------
  register: (email: string, password: string, full_name: string) =>
    req<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    }),
  login: (email: string, password: string) =>
    req<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => req<{ id: number; email: string; full_name: string }>('/auth/me'),
  googleLoginUrl: () => req<{ authorize_url: string }>('/auth/google/login'),

  // ---- Profile -----------------------------------------------------------
  getProfile: () => req<{ profile: Profile; derived_from_documents: boolean }>('/profile'),
  saveProfile: (p: Partial<Profile>) =>
    req<{ profile: Profile }>('/profile', { method: 'PUT', body: JSON.stringify(p) }),
  resetProfile: () => req<{ profile: Profile }>('/profile/reset', { method: 'POST' }),

  // ---- Documents ---------------------------------------------------------
  listDocuments: () =>
    req<{ documents: DocRecord[]; index_size: number; retriever?: string; derived_profile: any }>('/documents'),
  loadSample: () => req<{ ingested: DocRecord; derived_profile: any }>('/documents/sample', { method: 'POST' }),
  uploadDocument: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/documents/upload`, {
      method: 'POST',
      body: form,
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
    return res.json()
  },

  // ---- Transactions ------------------------------------------------------
  listTransactions: () => req<{ transactions: Txn[] }>('/transactions'),
  categorize: (descriptions?: string[]) =>
    req<CategorizeResult>('/transactions/categorize', {
      method: 'POST',
      body: JSON.stringify({ descriptions: descriptions || null }),
    }),
  setCategory: (transaction_id: number, category: string) =>
    req<{ ok: boolean }>('/transactions/category', {
      method: 'PUT',
      body: JSON.stringify({ transaction_id, category }),
    }),

  // ---- Analytics + Goals -------------------------------------------------
  analytics: () => req<AnalyticsSummary>('/analytics/summary'),
  goals: () => req<GoalsSummary>('/goals'),
  createGoal: (g: GoalInput) => req<GoalsSummary>('/goals', { method: 'POST', body: JSON.stringify(g) }),
  updateGoal: (id: number, patch: Partial<GoalInput>) =>
    req<GoalsSummary>(`/goals/${id}`, { method: 'PUT', body: JSON.stringify(patch) }),
  deleteGoal: (id: number) => req<GoalsSummary>(`/goals/${id}`, { method: 'DELETE' }),

  // ---- Agents ------------------------------------------------------------
  debt: () => req<AgentResult>('/debt/analyze', { method: 'POST', body: '{}' }),
  savings: () => req<AgentResult>('/savings/plan', { method: 'POST', body: '{}' }),
  budget: () => req<AgentResult>('/budget/analyze', { method: 'POST', body: '{}' }),
  investment: () => req<AgentResult>('/investment/recommend', { method: 'POST', body: '{}' }),
  portfolio: () => req<AgentResult>('/portfolio/optimize', { method: 'POST', body: '{}' }),
  india: () => req<AgentResult>('/india/plan', { method: 'POST', body: '{}' }),

  // ---- Coach -------------------------------------------------------------
  coachReview: (query?: string) =>
    req<CoachResult>('/coach/review', { method: 'POST', body: JSON.stringify({ query: query || null }) }),
  ask: (question: string, conversation_id?: number) =>
    req<AskResult>('/coach/ask', {
      method: 'POST',
      body: JSON.stringify({ question, conversation_id: conversation_id ?? null }),
    }),

  /**
   * Stream a grounded answer over Server-Sent Events. `onDelta` fires per token;
   * resolves with the full text. Falls back transparently if streaming fails.
   */
  askStream: async (
    question: string,
    onDelta: (text: string) => void,
    conversation_id?: number,
  ): Promise<{ text: string; conversation_id?: number }> => {
    const res = await fetch(`${BASE}/coach/ask/stream`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ question, conversation_id: conversation_id ?? null }),
    })
    if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`)
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let full = ''
    let convId: number | undefined = conversation_id
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue
        try {
          const evt = JSON.parse(line.slice(5).trim())
          if (evt.type === 'delta') {
            full += evt.text
            onDelta(evt.text)
          } else if (evt.type === 'meta' && evt.conversation_id) {
            convId = evt.conversation_id
          }
        } catch {
          /* ignore malformed keep-alive lines */
        }
      }
    }
    return { text: full, conversation_id: convId }
  },
}
