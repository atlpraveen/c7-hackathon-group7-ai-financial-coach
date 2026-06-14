import {
  LayoutDashboard, Upload, Receipt, BarChart3, CreditCard, PiggyBank, Wallet,
  TrendingUp, Scale, Landmark, Target, MessagesSquare,
} from 'lucide-react'
import { useStore, type View } from '../store'

const NAV: { id: View; label: string; icon: any }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'data', label: 'Data & Profile', icon: Upload },
  { id: 'transactions', label: 'Transactions', icon: Receipt },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'debt', label: 'Debt Analyser', icon: CreditCard },
  { id: 'savings', label: 'Savings', icon: PiggyBank },
  { id: 'budget', label: 'Budget', icon: Wallet },
  { id: 'investment', label: 'Investments', icon: TrendingUp },
  { id: 'portfolio', label: 'Portfolio Optimizer', icon: Scale },
  { id: 'india', label: 'India · Tax & Retirement', icon: Landmark },
  { id: 'goals', label: 'Goals', icon: Target },
  { id: 'coach', label: 'Ask the Coach', icon: MessagesSquare },
]

export default function Sidebar() {
  const { view, setView } = useStore()
  return (
    <aside className="w-60 shrink-0 bg-slate-900 text-slate-300 flex flex-col">
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="text-white font-bold text-lg leading-tight">AI Financial</div>
        <div className="text-brand-300 font-bold text-lg leading-tight">Coach</div>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setView(id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
              view === id ? 'bg-brand-600 text-white' : 'hover:bg-slate-800'
            }`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
      <div className="p-4 text-[11px] text-slate-500 border-t border-slate-800">
        LLM routing · LangGraph · Qdrant RAG · multi-user
      </div>
    </aside>
  )
}
