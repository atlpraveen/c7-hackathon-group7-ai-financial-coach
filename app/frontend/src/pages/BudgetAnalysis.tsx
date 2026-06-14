import { useEffect } from 'react'
import { useStore } from '../store'
import { Card, Stat, Narrative, Empty, money } from '../components/ui'
import { BucketBars, CategoryPie } from '../components/charts'

export default function BudgetAnalysis() {
  const { budget, runAgent, loading, profile, setView } = useStore()
  useEffect(() => { if (!budget && profile) runAgent('budget') }, [profile]) // eslint-disable-line

  if (!profile || profile.monthly_income === 0)
    return <Empty><button className="btn-primary mx-auto" onClick={() => setView('data')}>Add your data first →</button></Empty>

  const d = budget?.data
  if (!d) return <Card><button className="btn-primary" onClick={() => runAgent('budget')}>Analyse budget</button></Card>

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="btn-ghost" onClick={() => runAgent('budget')} disabled={!!loading.budget}>
          {loading.budget ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Income" value={money(d.monthly_income)} />
        <Stat label="Expenses" value={money(d.total_expenses)} />
        <Stat label="Surplus" value={money(d.surplus)} tone={d.surplus >= 0 ? 'good' : 'bad'} />
        <Stat label="Savings rate" value={`${d.savings_rate}%`} tone={d.savings_rate >= 20 ? 'good' : 'warn'} />
      </div>

      {budget && <Narrative text={budget.narrative} by={budget.generated_by} />}

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="50 / 30 / 20 — actual vs target"><BucketBars buckets={d.buckets} /></Card>
        <Card title="Top spending categories">
          <CategoryPie data={d.top_expenses.map((t: any) => ({ category: t.category, amount: t.amount }))} />
        </Card>
      </div>

      <Card title="Actionable advice">
        <ul className="space-y-2 text-sm">
          {d.advice.map((a: string, i: number) => (
            <li key={i} className="flex gap-2"><span className="text-brand-600">▸</span><span>{a}</span></li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
