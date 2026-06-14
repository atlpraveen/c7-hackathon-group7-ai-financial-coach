import { useEffect } from 'react'
import { useStore } from '../store'
import { Card, Stat, Narrative, Empty, money } from '../components/ui'
import { DebtPayoffChart } from '../components/charts'

export default function DebtAnalysis() {
  const { debt, runAgent, loading, profile, setView } = useStore()
  useEffect(() => { if (!debt && profile) runAgent('debt') }, [profile]) // eslint-disable-line

  if (!profile || profile.monthly_income === 0)
    return <Empty><button className="btn-primary mx-auto" onClick={() => setView('data')}>Add your data first →</button></Empty>

  const d = debt?.data
  if (!d) return <Card><button className="btn-primary" onClick={() => runAgent('debt')}>Analyse debt</button></Card>

  if (!d.has_debt)
    return (
      <div className="space-y-6">
        <Card>🎉 {d.message}</Card>
        {debt && <Narrative text={debt.narrative} by={debt.generated_by} />}
      </div>
    )

  const rec = d.recommended
  const chosen = d[rec]
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="btn-ghost" onClick={() => runAgent('debt')} disabled={!!loading.debt}>
          {loading.debt ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Total debt" value={money(d.total_debt)} tone="warn" />
        <Stat label="Blended APR" value={`${d.weighted_apr}%`} />
        <Stat label="Recommended" value={rec.charAt(0).toUpperCase() + rec.slice(1)} tone="good"
          sub={`debt-free in ${chosen.months} mo`} />
        <Stat label="Interest saved (avalanche)" value={money(d.interest_saved_with_avalanche)} tone="good" />
      </div>

      {debt && <Narrative text={debt.narrative} by={debt.generated_by} />}

      <Card title="Payoff trajectory — Avalanche vs Snowball"
        right={<span className="text-xs text-slate-500">{money(d.monthly_budget)}/mo budget</span>}>
        <DebtPayoffChart avalanche={d.avalanche} snowball={d.snowball} />
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {(['avalanche', 'snowball'] as const).map((s) => (
          <Card key={s} title={`${s[0].toUpperCase() + s.slice(1)} method`}
            right={s === rec ? <span className="text-xs font-semibold text-brand-600">★ recommended</span> : null}>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <KV k="Months to debt-free" v={`${d[s].months} (${d[s].years} yrs)`} />
              <KV k="Total interest" v={money(d[s].total_interest)} />
              <KV k="Payoff order" v={d[s].payoff_order.join(' → ') || '—'} />
              <KV k="Monthly budget" v={money(d[s].monthly_budget_used)} />
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

function KV({ k, v }: { k: string; v: any }) {
  return <div><div className="label">{k}</div><div className="font-semibold text-slate-800">{v}</div></div>
}
