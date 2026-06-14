import { Sparkles, FileText, LogIn, LogOut, User as UserIcon } from 'lucide-react'
import { useStore } from '../store'

const TITLES: Record<string, string> = {
  dashboard: 'Financial Dashboard',
  data: 'Your Data & Profile',
  transactions: 'Transactions & AI Categorization',
  analytics: 'Financial Analytics',
  debt: 'Debt Analyser',
  savings: 'Savings Strategist',
  budget: 'Budget Advisor',
  investment: 'Investment Advisor',
  portfolio: 'Portfolio Optimizer',
  india: 'India · Tax & Retirement',
  goals: 'Goal Tracking',
  coach: 'Ask the Coach',
}

export default function Header({ onSignIn }: { onSignIn: () => void }) {
  const { view, health, documents, user, logout } = useStore()
  return (
    <header className="flex items-center justify-between px-8 py-4 bg-white border-b border-slate-200">
      <h1 className="text-xl font-bold text-slate-800">{TITLES[view] ?? 'AI Financial Coach'}</h1>
      <div className="flex items-center gap-3 text-sm">
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 text-slate-600">
          <FileText size={14} /> {documents.length} doc{documents.length === 1 ? '' : 's'}
        </span>
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full ${
            health?.llm_enabled ? 'bg-brand-50 text-brand-700' : 'bg-amber-50 text-amber-700'
          }`}
        >
          <Sparkles size={14} />
          {health?.llm_enabled ? 'AI narration' : 'Rule-based narration'}
        </span>
        {user ? (
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-50 text-brand-700">
              <UserIcon size={14} /> {user.full_name || user.email}
            </span>
            <button
              onClick={logout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600"
            >
              <LogOut size={14} /> Sign out
            </button>
          </div>
        ) : (
          <button
            onClick={onSignIn}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-600 hover:bg-brand-700 text-white"
          >
            <LogIn size={14} /> Sign in
          </button>
        )}
      </div>
    </header>
  )
}
