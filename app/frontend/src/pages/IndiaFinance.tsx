import { useEffect } from 'react'
import { useStore } from '../store'
import { Card, Empty, Narrative, Pill, Stat, money, pct } from '../components/ui'
import { GrowthChart } from '../components/charts'

export default function IndiaFinance() {
  const { india, runAgent, loading, profile } = useStore()

  useEffect(() => {
    if (!india && profile) runAgent('india')
  }, [profile]) // eslint-disable-line

  if (!profile || profile.monthly_income === 0) {
    return (
      <Empty>
        Add your data first — visit Data &amp; Profile to set up your profile.
      </Empty>
    )
  }

  if (loading.india) {
    return <div className="card text-center text-slate-500 text-sm py-10">Computing India finance plan…</div>
  }

  if (!india) {
    return (
      <Card>
        <button className="btn-primary" onClick={() => runAgent('india')}>
          Build India finance plan
        </button>
      </Card>
    )
  }

  const d = india.data

  // Safe accessors
  const tax = d?.tax_comparison ?? {}
  const oldTax = tax?.old ?? {}
  const newTax = tax?.new ?? {}
  const recommended: 'old' | 'new' = tax?.recommended ?? 'new'
  const sip = d?.sip ?? {}
  const epf = d?.epf ?? {}
  const nps = d?.nps ?? {}
  const elss = d?.elss ?? {}
  const recommendations: string[] = d?.recommendations ?? []

  return (
    <div className="space-y-6">
      {/* Recompute */}
      <div className="flex justify-end">
        <button
          className="btn-ghost"
          onClick={() => runAgent('india')}
          disabled={!!loading.india}
        >
          {loading.india ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>

      {/* Top summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <Stat label="Annual gross income" value={money(d?.annual_gross)} />
        <Stat label="Investable monthly" value={money(d?.investable_monthly)} tone="good" />
        <Stat
          label="Recommended tax regime"
          value={recommended.toUpperCase()}
          tone="good"
          sub={`saves ${money(tax?.savings)} vs other`}
        />
      </div>

      {/* Narrative */}
      <Narrative text={india.narrative} by={india.generated_by} />

      {/* Tax regime comparison */}
      <Card title="Tax regime comparison">
        <div className="grid sm:grid-cols-2 gap-6">
          {/* Old regime */}
          <div className={`rounded-xl p-4 border ${recommended === 'old' ? 'border-emerald-300 bg-emerald-50' : 'border-slate-100 bg-slate-50'}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="font-semibold text-slate-700">Old Regime</span>
              {recommended === 'old' && <Pill tone="green">Recommended</Pill>}
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Taxable income</span>
                <span className="font-medium">{money(oldTax?.taxable_income)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Total deductions</span>
                <span className="font-medium">{money(oldTax?.total_deductions)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-2 mt-2">
                <span className="text-slate-500">Total tax</span>
                <span className="font-bold text-slate-800">{money(oldTax?.total_tax)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Effective rate</span>
                <span className="font-medium">{pct(oldTax?.effective_rate_pct, 2)}</span>
              </div>
            </div>
          </div>

          {/* New regime */}
          <div className={`rounded-xl p-4 border ${recommended === 'new' ? 'border-emerald-300 bg-emerald-50' : 'border-slate-100 bg-slate-50'}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="font-semibold text-slate-700">New Regime</span>
              {recommended === 'new' && <Pill tone="green">Recommended</Pill>}
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Taxable income</span>
                <span className="font-medium">{money(newTax?.taxable_income)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Standard deduction</span>
                <span className="font-medium">{money(newTax?.total_deductions)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-2 mt-2">
                <span className="text-slate-500">Total tax</span>
                <span className="font-bold text-slate-800">{money(newTax?.total_tax)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Effective rate</span>
                <span className="font-medium">{pct(newTax?.effective_rate_pct, 2)}</span>
              </div>
            </div>
          </div>
        </div>
        {tax?.savings != null && (
          <div className="mt-4 text-sm text-emerald-700 bg-emerald-50 rounded-lg px-4 py-2">
            Switching to the <strong>{recommended}</strong> regime saves{' '}
            <strong>{money(tax.savings)}</strong> per year in taxes.
          </div>
        )}
      </Card>

      {/* SIP */}
      <Card title="SIP — Systematic Investment Plan">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <Stat label="Monthly SIP" value={money(sip?.monthly_investment ?? sip?.monthly)} />
          <Stat label="Maturity value" value={money(sip?.maturity)} tone="good" />
          <Stat label="Total invested" value={money(sip?.invested)} />
          <Stat label="Gains" value={money(sip?.gains)} tone="good" />
        </div>
        {Array.isArray(sip?.projection) && sip.projection.length > 0 && (
          <GrowthChart
            data={sip.projection}
            xKey="year"
            balanceKey="value"
            contributedKey="invested"
          />
        )}
      </Card>

      {/* EPF */}
      <Card title="EPF — Employee Provident Fund">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Stat label="Maturity corpus" value={money(epf?.maturity)} tone="good" />
          <Stat label="Total contributed" value={money(epf?.total_contributed)} />
          <Stat label="Interest earned" value={money(epf?.interest_earned)} tone="good" />
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Annual rate: {epf?.annual_rate ?? 8.25}% | Horizon: {epf?.years ?? '—'} years
        </p>
      </Card>

      {/* NPS */}
      <Card title="NPS — National Pension System">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Stat label="Maturity corpus" value={money(nps?.maturity_corpus)} tone="good" />
          <Stat label="Est. monthly pension" value={money(nps?.est_monthly_pension)} tone="good" sub="/month" />
          <Stat label="Lump sum (60%)" value={money(nps?.lump_sum)} />
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Annuity corpus: {money(nps?.annuity_corpus)} | Horizon: {nps?.years ?? '—'} years
        </p>
      </Card>

      {/* ELSS */}
      <Card title="ELSS — Equity Linked Savings Scheme">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Stat label="80C eligible" value={money(elss?.eligible_80c)} />
          <Stat label="Tax saved / yr" value={money(elss?.tax_saved_per_year)} tone="good" />
          <Stat label="Maturity value" value={money(elss?.maturity)} tone="good" />
          <Stat label="Gains" value={money(elss?.gains)} tone="good" />
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Lock-in: {elss?.lock_in_years ?? 3} years | Return: {elss?.annual_return_pct ?? 12}% p.a.
        </p>
      </Card>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card title="Recommendations">
          <ul className="space-y-2">
            {recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-0.5 text-emerald-500 flex-shrink-0">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Disclaimer */}
      {d?.disclaimer && (
        <p className="text-xs text-slate-400">{d.disclaimer}</p>
      )}
    </div>
  )
}
