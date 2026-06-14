import { useEffect } from 'react'
import { useStore } from '../store'
import { Card, Stat, Narrative, Empty, money } from '../components/ui'
import { GrowthChart } from '../components/charts'

export default function SavingsPlanner() {
  const { savings, runAgent, loading, profile, setView } = useStore()
  useEffect(() => { if (!savings && profile) runAgent('savings') }, [profile]) // eslint-disable-line

  if (!profile || profile.monthly_income === 0)
    return <Empty><button className="btn-primary mx-auto" onClick={() => setView('data')}>Add your data first →</button></Empty>

  const d = savings?.data
  if (!d) return <Card><button className="btn-primary" onClick={() => runAgent('savings')}>Build savings plan</button></Card>

  const ef = d.emergency_fund
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="btn-ghost" onClick={() => runAgent('savings')} disabled={!!loading.savings}>
          {loading.savings ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Monthly surplus" value={money(d.monthly_surplus)} tone={d.monthly_surplus >= 0 ? 'good' : 'bad'} />
        <Stat label="Savings rate" value={`${d.current_savings_rate}%`}
          tone={d.current_savings_rate >= d.target_savings_rate ? 'good' : 'warn'}
          sub={`target ${d.target_savings_rate}%`} />
        <Stat label="Emergency fund" value={`${ef.funded_pct}%`} tone={ef.gap > 0 ? 'warn' : 'good'}
          sub={`${money(ef.target)} target`} />
        <Stat label="Fund gap" value={money(ef.gap)} tone={ef.gap > 0 ? 'bad' : 'good'}
          sub={ef.months_to_fully_fund ? `~${ef.months_to_fully_fund} mo to fund` : 'fully funded'} />
      </div>

      {savings && <Narrative text={savings.narrative} by={savings.generated_by} />}

      {d.goals?.length > 0 && (
        <div className="space-y-6">
          {d.goals.map((g: any, i: number) => (
            <Card key={i} title={`Goal: ${g.name}`}
              right={<span className="text-sm text-slate-500">{money(g.monthly_required)}/mo for {g.months} mo</span>}>
              <GrowthChart data={g.projection} xKey="month" balanceKey="balance" contributedKey="balance" />
            </Card>
          ))}
        </div>
      )}
      {(!d.goals || d.goals.length === 0) && (
        <Card>Add savings goals on the Data &amp; Profile page (or via the API) to see funding projections.</Card>
      )}
    </div>
  )
}
