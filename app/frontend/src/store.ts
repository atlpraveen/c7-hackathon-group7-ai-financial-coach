import { create } from 'zustand'
import { api, auth } from './api/client'
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
  Txn,
  User,
} from './types'

export type View =
  | 'dashboard'
  | 'data'
  | 'transactions'
  | 'analytics'
  | 'debt'
  | 'savings'
  | 'budget'
  | 'investment'
  | 'portfolio'
  | 'goals'
  | 'india'
  | 'coach'

type AgentName = 'debt' | 'savings' | 'budget' | 'investment' | 'portfolio' | 'india'

interface ChatMsg {
  role: 'user' | 'coach'
  text: string
  sources?: AskResult['sources']
  streaming?: boolean
}

interface AppState {
  view: View
  setView: (v: View) => void

  health: Health | null
  user: User | null
  profile: Profile | null
  documents: DocRecord[]
  derivedFromDocs: boolean

  transactions: Txn[]
  categorization: CategorizeResult | null
  analytics: AnalyticsSummary | null
  goals: GoalsSummary | null

  debt: AgentResult | null
  savings: AgentResult | null
  budget: AgentResult | null
  investment: AgentResult | null
  portfolio: AgentResult | null
  india: AgentResult | null
  coach: CoachResult | null
  chat: ChatMsg[]
  conversationId?: number

  loading: Record<string, boolean>
  error: string | null

  init: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => void

  refreshProfile: () => Promise<void>
  loadSample: () => Promise<void>
  uploadFile: (f: File) => Promise<void>
  saveProfile: (p: Partial<Profile>) => Promise<void>
  resetProfile: () => Promise<void>

  loadTransactions: () => Promise<void>
  categorizeAll: () => Promise<void>
  loadAnalytics: () => Promise<void>
  loadGoals: () => Promise<void>
  createGoal: (g: GoalInput) => Promise<void>
  updateGoal: (id: number, patch: Partial<GoalInput>) => Promise<void>
  deleteGoal: (id: number) => Promise<void>

  runAll: () => Promise<void>
  runAgent: (name: AgentName) => Promise<void>
  runCoach: (query?: string) => Promise<void>
  ask: (question: string) => Promise<void>
}

const setLoading = (key: string, val: boolean) => (s: AppState) => ({
  loading: { ...s.loading, [key]: val },
})

export const useStore = create<AppState>((set, get) => ({
  view: 'dashboard',
  setView: (v) => set({ view: v }),

  health: null,
  user: null,
  profile: null,
  documents: [],
  derivedFromDocs: false,

  transactions: [],
  categorization: null,
  analytics: null,
  goals: null,

  debt: null,
  savings: null,
  budget: null,
  investment: null,
  portfolio: null,
  india: null,
  coach: null,
  chat: [],
  conversationId: undefined,

  loading: {},
  error: null,

  init: async () => {
    // Capture an OAuth token handed back via ?token=… then clean the URL.
    const url = new URL(window.location.href)
    const oauthToken = url.searchParams.get('token')
    if (oauthToken) {
      auth.set(oauthToken)
      url.searchParams.delete('token')
      window.history.replaceState({}, '', url.toString())
    }
    try {
      const health = await api.health()
      set({ health })
      if (auth.token) {
        try {
          const me = await api.me()
          set({ user: me })
        } catch {
          auth.set(null)
        }
      }
      const [prof, docs] = await Promise.all([api.getProfile(), api.listDocuments()])
      set({
        profile: prof.profile,
        derivedFromDocs: prof.derived_from_documents,
        documents: docs.documents,
      })
    } catch (e: any) {
      set({ error: e.message })
    }
  },

  login: async (email, password) => {
    const r = await api.login(email, password)
    auth.set(r.access_token)
    set({ user: r.user, chat: [], coach: null, conversationId: undefined })
    await get().init()
  },

  register: async (email, password, fullName) => {
    const r = await api.register(email, password, fullName)
    auth.set(r.access_token)
    set({ user: r.user, chat: [], coach: null, conversationId: undefined })
    await get().init()
  },

  loginWithGoogle: async () => {
    const { authorize_url } = await api.googleLoginUrl()
    window.location.href = authorize_url
  },

  logout: () => {
    auth.set(null)
    set({
      user: null, profile: null, documents: [], transactions: [], analytics: null,
      goals: null, debt: null, savings: null, budget: null, investment: null,
      portfolio: null, india: null, coach: null, chat: [], conversationId: undefined,
    })
    get().init()
  },

  refreshProfile: async () => {
    const prof = await api.getProfile()
    set({ profile: prof.profile, derivedFromDocs: prof.derived_from_documents })
  },

  loadSample: async () => {
    set(setLoading('upload', true))
    try {
      await api.loadSample()
      const docs = await api.listDocuments()
      set({ documents: docs.documents })
      await get().refreshProfile()
    } finally {
      set(setLoading('upload', false))
    }
  },

  uploadFile: async (f) => {
    set(setLoading('upload', true))
    try {
      await api.uploadDocument(f)
      const docs = await api.listDocuments()
      set({ documents: docs.documents })
      await get().refreshProfile()
    } finally {
      set(setLoading('upload', false))
    }
  },

  saveProfile: async (p) => {
    const r = await api.saveProfile(p)
    set({ profile: r.profile })
  },

  resetProfile: async () => {
    const r = await api.resetProfile()
    set({ profile: r.profile })
  },

  loadTransactions: async () => {
    set(setLoading('transactions', true))
    try {
      const r = await api.listTransactions()
      set({ transactions: r.transactions })
    } finally {
      set(setLoading('transactions', false))
    }
  },

  categorizeAll: async () => {
    set(setLoading('categorize', true))
    try {
      const r = await api.categorize()
      set({ categorization: r })
    } finally {
      set(setLoading('categorize', false))
    }
  },

  loadAnalytics: async () => {
    set(setLoading('analytics', true))
    try {
      const r = await api.analytics()
      set({ analytics: r })
    } finally {
      set(setLoading('analytics', false))
    }
  },

  loadGoals: async () => {
    set(setLoading('goals', true))
    try {
      const r = await api.goals()
      set({ goals: r })
    } finally {
      set(setLoading('goals', false))
    }
  },

  createGoal: async (g) => set({ goals: await api.createGoal(g) }),
  updateGoal: async (id, patch) => set({ goals: await api.updateGoal(id, patch) }),
  deleteGoal: async (id) => set({ goals: await api.deleteGoal(id) }),

  runAgent: async (name) => {
    set(setLoading(name, true))
    try {
      const fn = {
        debt: api.debt, savings: api.savings, budget: api.budget,
        investment: api.investment, portfolio: api.portfolio, india: api.india,
      }[name]
      const res = await fn()
      set({ [name]: res } as any)
    } catch (e: any) {
      set({ error: e.message })
    } finally {
      set(setLoading(name, false))
    }
  },

  runAll: async () => {
    await Promise.all([
      get().runAgent('debt'),
      get().runAgent('savings'),
      get().runAgent('budget'),
      get().runAgent('investment'),
    ])
  },

  runCoach: async (query) => {
    set(setLoading('coach', true))
    try {
      const res = await api.coachReview(query)
      set({ coach: res, conversationId: res.conversation_id })
    } catch (e: any) {
      set({ error: e.message })
    } finally {
      set(setLoading('coach', false))
    }
  },

  ask: async (question) => {
    set((s) => ({
      chat: [...s.chat, { role: 'user', text: question }, { role: 'coach', text: '', streaming: true }],
    }))
    set(setLoading('ask', true))
    const patchLast = (text: string, extra: Partial<ChatMsg> = {}) =>
      set((s) => {
        const chat = s.chat.slice()
        chat[chat.length - 1] = { ...chat[chat.length - 1], text, ...extra }
        return { chat }
      })
    try {
      let acc = ''
      const { conversation_id } = await api.askStream(
        question,
        (delta) => {
          acc += delta
          patchLast(acc)
        },
        get().conversationId,
      )
      patchLast(acc, { streaming: false })
      if (conversation_id) set({ conversationId: conversation_id })
    } catch {
      // Fallback to the non-streaming endpoint.
      try {
        const res = await api.ask(question, get().conversationId)
        patchLast(res.answer, { streaming: false, sources: res.sources })
        if (res.conversation_id) set({ conversationId: res.conversation_id })
      } catch (e: any) {
        patchLast(`Error: ${e.message}`, { streaming: false })
      }
    } finally {
      set(setLoading('ask', false))
    }
  },
}))
