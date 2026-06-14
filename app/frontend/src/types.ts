// Shared types mirroring the backend API responses.

export interface Debt {
  name: string
  balance: number
  interest_rate: number
  min_payment: number
  inferred?: boolean
}

export interface Goal {
  name: string
  target_amount: number
  months: number
  current?: number
  annual_return?: number
}

export interface Profile {
  monthly_income: number
  monthly_expenses: number
  expenses_by_category: Record<string, number>
  debts: Debt[]
  savings_balance: number
  investment_balance: number
  age: number | null
  risk_tolerance: string
  goals: Goal[]
  currency?: string
}

export interface AgentResult<T = any> {
  agent: string
  title: string
  data: T
  narrative: string
  generated_by: 'llm' | 'deterministic'
}

export interface CoachResult {
  query: string | null
  engine?: string
  routed_by?: string
  agents_run: string[]
  results: Record<string, AgentResult>
  synthesis: string
  synthesis_generated_by: 'llm' | 'deterministic'
  conversation_id?: number
}

export interface AskResult {
  answer: string
  sources: { text: string; score: number; meta: any }[]
  generated_by: 'llm' | 'deterministic'
  retriever?: string
  conversation_id?: number
}

export interface Health {
  status: string
  app: string
  currency?: string
  llm_enabled: boolean
  narration: string
  capabilities?: Record<string, any>
  agents?: string[]
}

export interface DocRecord {
  filename: string
  kind: string
  chunks: number
  transactions: number
}

// ---- Auth ----------------------------------------------------------------
export interface User {
  id: number
  email: string
  full_name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

// ---- Analytics -----------------------------------------------------------
export interface MonthPoint {
  month: string
  income: number
  expense: number
  net: number
}

export interface AnalyticsSummary {
  has_data: boolean
  transaction_count?: number
  months?: number
  monthly_series?: MonthPoint[]
  by_category?: { category: string; total: number; count: number }[]
  avg_monthly_income?: number
  avg_monthly_expense?: number
  avg_monthly_savings?: number
  month_over_month?: { prev_month: string; last_month: string; delta: number; pct: number } | null
  top_category?: string | null
}

// ---- Goals ---------------------------------------------------------------
export interface TrackedGoal {
  id: number
  name: string
  category: string
  target_amount: number
  current_amount: number
  monthly_contribution: number
  target_months: number
  annual_return: number
  progress_pct: number
  remaining: number
  projected_months: number | null
  monthly_required_for_deadline: number
  monthly_shortfall: number
  on_track: boolean
  status: 'complete' | 'on_track' | 'behind'
}

export interface GoalsSummary {
  goals: TrackedGoal[]
  count: number
  total_target: number
  total_current: number
  total_monthly_commitment: number
  overall_progress_pct: number
  on_track_count: number
}

export interface GoalInput {
  name: string
  category?: string
  target_amount: number
  current_amount?: number
  monthly_contribution?: number
  target_months?: number
  annual_return?: number
}

// ---- Transactions --------------------------------------------------------
export interface Txn {
  id: number
  date: string
  month: string
  description: string
  amount: number
  category: string
  kind: string
}

export interface CategorizeResult {
  results: { description: string; category: string; method: 'keyword' | 'llm' }[]
  categories: string[]
  ai_used: boolean
  counts: Record<string, number>
}
