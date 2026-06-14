import { useEffect } from 'react'
import { useStore } from '../store'
import { Card, Stat, Narrative, Empty, money } from '../components/ui'
import { CategoryPie } from '../components/charts'
import { RefreshCw, Wand2 } from 'lucide-react'

export default function Dashboard() {
  const { profile, documents, runAll, runCoach, coach, debt, savings, budget, investment, loading, setView } =
    useStore()

  useEffect(() => {
    if (profile && profile.monthly_income > 0 && !coach) {
      runAll()
      runCoach()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile?.monthly_income])

  if (!profile || profile.monthly_income === 0) {
    return (
      <Empty>
        <p className="mb-4 text-base">No financial data yet.</p>
        <button className="btn-primary mx-auto" onClick={() => setView('data')}>
          Upload data or load the sample →
        </button>
      </Empty>
    )
  }

  const surplus = profile.monthly_income - profile.monthly_expenses
  const cats = Object.entries(profile.expenses_by_category).map(([category, amount]) => ({ category, amount }))
  const totalDebt = profile.debts.reduce((s, d) => s + d.balance, 0)

  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-2">
        <button className="btn-ghost" onClick={() => { runAll(); runCoach() }} disabled={!!loading.coach}>
          <RefreshCw size={16} className={loading.coach ? 'animate-spin' : ''} /> Refresh analysis
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Monthly Income" value={money(profile.monthly_income)} />
        <Stat label="Monthly Expenses" value={money(profile.monthly_expenses)} />
        <Stat label="Monthly Surplus" value={money(surplus)} tone={surplus >= 0 ? 'good' : 'bad'}
          sub={`${((surplus / profile.monthly_income) * 100).toFixed(0)}% savings rate`} />
        <Stat label="Total Debt" value={money(totalDebt)} tone={totalDebt > 0 ? 'warn' : 'good'}
          sub={`${profile.debts.length} account(s)`} />
      </div>

      {coach ? (
        <Narrative text={coach.synthesis} by={coach.synthesis_generated_by} />
      ) : (
        <Card>
          <button className="btn-primary" onClick={() => runCoach()} disabled={!!loading.coach}>
            <Wand2 size={16} /> {loading.coach ? 'Coaching…' : 'Generate my action plan'}
          </button>
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Where your money goes">
          {cats.length ? <CategoryPie data={cats} /> : <p className="text-sm text-slate-500">No expense data.</p>}
        </Card>
        <Card title="Agent summaries">
          <ul className="space-y-3 text-sm">
            <AgentRow label="Debt" go={() => setView('debt')} text={debt?.narrative} />
            <AgentRow label="Savings" go={() => setView('savings')} text={savings?.narrative} />
            <AgentRow label="Budget" go={() => setView('budget')} text={budget?.narrative} />
            <AgentRow label="Investment" go={() => setView('investment')} text={investment?.narrative} />
          </ul>
        </Card>
      </div>

      <p className="text-xs text-slate-400">
        {documents.length} document(s) ingested · analysis grounded in your uploaded data.
      </p>
    </div>
  )
}

function AgentRow({ label, text, go }: { label: string; text?: string; go: () => void }) {
  return (
    <li className="flex items-start gap-3">
      <button onClick={go} className="shrink-0 w-24 text-left font-semibold text-brand-700 hover:underline">
        {label}
      </button>
      <span className="text-slate-600 line-clamp-2">{text ? text.slice(0, 160) + '…' : 'Run analysis to see insights.'}</span>
    </li>
  )
}
