import { useEffect } from 'react'
import { useStore } from '../store'
import { Card, Stat, Narrative, Empty, money } from '../components/ui'
import { AllocationDonut, GrowthChart } from '../components/charts'

export default function InvestmentAdvisor() {
  const { investment, runAgent, loading, profile, setView } = useStore()
  useEffect(() => { if (!investment && profile) runAgent('investment') }, [profile]) // eslint-disable-line

  if (!profile || profile.monthly_income === 0)
    return <Empty><button className="btn-primary mx-auto" onClick={() => setView('data')}>Add your data first →</button></Empty>

  const d = investment?.data
  if (!d) return <Card><button className="btn-primary" onClick={() => runAgent('investment')}>Get recommendation</button></Card>

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="btn-ghost" onClick={() => runAgent('investment')} disabled={!!loading.investment}>
          {loading.investment ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Risk profile" value={d.risk_tolerance} />
        <Stat label="Investing / mo" value={money(d.investable_monthly)} />
        <Stat label="Exp. annual return" value={`${d.expected_annual_return}%`} tone="good" />
        <Stat label={`Projected (${d.horizon_years}y)`} value={money(d.projected_balance)} tone="good"
          sub={`${money(d.projected_growth)} growth`} />
      </div>

      {investment && <Narrative text={investment.narrative} by={investment.generated_by} />}

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Recommended allocation"><AllocationDonut allocation={d.allocation} /></Card>
        <Card title={`Growth projection (${d.horizon_years} years)`}>
          <GrowthChart data={d.projection} xKey="year" />
        </Card>
      </div>
      <p className="text-xs text-slate-400">{d.disclaimer}</p>
    </div>
  )
}
