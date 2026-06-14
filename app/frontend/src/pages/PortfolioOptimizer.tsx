import { useEffect } from 'react'
import {
  CartesianGrid, ResponsiveContainer, Scatter, ScatterChart,
  Tooltip, XAxis, YAxis, ZAxis,
} from 'recharts'
import { useStore } from '../store'
import { Card, Empty, Narrative, Stat, money, pct } from '../components/ui'
import { AllocationDonut, GrowthChart } from '../components/charts'

export default function PortfolioOptimizer() {
  const { portfolio, runAgent, loading, profile } = useStore()

  useEffect(() => {
    if (!portfolio && profile) runAgent('portfolio')
  }, [profile]) // eslint-disable-line

  if (!profile || profile.monthly_income === 0) {
    return (
      <Empty>
        Add your data first — visit Data &amp; Profile to set up your profile.
      </Empty>
    )
  }

  if (loading.portfolio) {
    return <div className="card text-center text-slate-500 text-sm py-10">Running portfolio optimisation…</div>
  }

  if (!portfolio) {
    return (
      <Card>
        <button className="btn-primary" onClick={() => runAgent('portfolio')}>
          Run portfolio optimisation
        </button>
      </Card>
    )
  }

  const d = portfolio.data

  // Safe accessors
  const opt = d?.optimization ?? {}
  const recommended = opt?.recommended ?? {}
  const weights: Record<string, number> = recommended?.weights ?? {}
  const frontier: { volatility: number; return: number }[] = opt?.frontier ?? []
  const rupeeAlloc: Record<string, number> = d?.rupee_allocation ?? {}
  const projection: any[] = d?.projection ?? []

  // Recommended point for scatter highlight (already in % from python)
  const recPoint = recommended?.volatility != null && recommended?.return != null
    ? [{ x: recommended.volatility, y: recommended.return }]
    : []

  return (
    <div className="space-y-6">
      {/* Recompute button */}
      <div className="flex justify-end">
        <button
          className="btn-ghost"
          onClick={() => runAgent('portfolio')}
          disabled={!!loading.portfolio}
        >
          {loading.portfolio ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat
          label="Expected annual return"
          value={pct(d?.expected_annual_return, 1)}
          tone="good"
        />
        <Stat
          label="Expected volatility"
          value={pct(d?.expected_volatility, 1)}
          tone="warn"
        />
        <Stat
          label="Sharpe ratio"
          value={d?.sharpe != null ? Number(d.sharpe).toFixed(2) : '—'}
          tone="default"
        />
        <Stat
          label={`Projected (${d?.horizon_years ?? '?'}y)`}
          value={money(d?.projected_balance)}
          sub={`contributed ${money(d?.total_contributed)}`}
          tone="good"
        />
      </div>

      {/* Narrative */}
      <Narrative text={portfolio.narrative} by={portfolio.generated_by} />

      {/* Allocation donut + frontier scatter */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card title={`Recommended allocation — ${recommended?.label ?? ''}`}>
          {Object.keys(weights).length > 0
            ? <AllocationDonut allocation={weights} />
            : <p className="text-sm text-slate-500">No allocation data available.</p>
          }
        </Card>

        <Card title="Efficient frontier">
          {frontier.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <ScatterChart margin={{ left: 10, right: 20, top: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
                <XAxis
                  dataKey="x"
                  name="Volatility"
                  type="number"
                  domain={['auto', 'auto']}
                  label={{ value: 'Volatility %', position: 'insideBottom', offset: -10, fontSize: 11 }}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v.toFixed(0)}%`}
                />
                <YAxis
                  dataKey="y"
                  name="Return"
                  type="number"
                  domain={['auto', 'auto']}
                  label={{ value: 'Return %', angle: -90, position: 'insideLeft', offset: 10, fontSize: 11 }}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v.toFixed(0)}%`}
                />
                <ZAxis range={[30, 30]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  formatter={(v: number, name: string) => [`${v.toFixed(1)}%`, name]}
                />
                {/* Frontier cloud */}
                <Scatter
                  name="Frontier"
                  data={frontier.map((p) => ({ x: p.volatility, y: p.return }))}
                  fill="#94a3b8"
                  opacity={0.5}
                />
                {/* Recommended point */}
                {recPoint.length > 0 && (
                  <Scatter
                    name="Recommended"
                    data={recPoint}
                    fill="#1f9d5b"
                    shape="star"
                  />
                )}
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500">No frontier data.</p>
          )}
        </Card>
      </div>

      {/* Monthly rupee allocation table */}
      {Object.keys(rupeeAlloc).length > 0 && (
        <Card title="Monthly ₹ allocation by asset">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 font-medium text-slate-600">Asset</th>
                  <th className="text-right py-2 font-medium text-slate-600">Amount / month</th>
                  <th className="text-right py-2 font-medium text-slate-600">Weight</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(rupeeAlloc).map(([asset, amt]) => (
                  <tr key={asset} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2 text-slate-700">
                      {asset.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </td>
                    <td className="py-2 text-right font-medium text-slate-800">{money(amt)}</td>
                    <td className="py-2 text-right text-slate-500">
                      {weights[asset] != null ? `${weights[asset]}%` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Growth projection chart */}
      {projection.length > 0 && (
        <Card title={`Growth projection (${d?.horizon_years ?? ''} years)`}>
          <GrowthChart data={projection} xKey="year" balanceKey="balance" contributedKey="contributed" />
        </Card>
      )}

      {/* Disclaimer */}
      {d?.disclaimer && (
        <p className="text-xs text-slate-400">{d.disclaimer}</p>
      )}
    </div>
  )
}
