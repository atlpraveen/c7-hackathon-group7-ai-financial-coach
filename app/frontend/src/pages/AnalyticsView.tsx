import { useEffect } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, ComposedChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { useStore } from '../store'
import { Card, Empty, Pill, Stat, money, pct } from '../components/ui'
import { CategoryPie } from '../components/charts'

const COLORS = ['#1f9d5b', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']

export default function AnalyticsView() {
  const { analytics, loadAnalytics, loading } = useStore()

  useEffect(() => { loadAnalytics() }, []) // eslint-disable-line

  if (loading.analytics) {
    return <div className="card text-center text-slate-500 text-sm py-10">Loading analytics…</div>
  }

  if (!analytics?.has_data) {
    return (
      <Empty>
        Load transactions first (Data &amp; Profile → Load sample data).
      </Empty>
    )
  }

  const mom = analytics.month_over_month
  const series = analytics.monthly_series ?? []
  const byCategory = analytics.by_category ?? []
  const pieData = byCategory.map((c) => ({ category: c.category, amount: c.total }))

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat
          label="Avg monthly income"
          value={money(analytics.avg_monthly_income)}
          tone="good"
        />
        <Stat
          label="Avg monthly expense"
          value={money(analytics.avg_monthly_expense)}
          tone="default"
        />
        <Stat
          label="Avg monthly savings"
          value={money(analytics.avg_monthly_savings)}
          tone={(analytics.avg_monthly_savings ?? 0) >= 0 ? 'good' : 'bad'}
        />
        <Stat
          label="Transactions"
          value={String(analytics.transaction_count ?? 0)}
          sub={`${analytics.months ?? 0} months of data`}
        />
      </div>

      {/* Month-over-month delta */}
      {mom && (
        <Card title="Month-over-month change">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-slate-600">
              {mom.prev_month} → {mom.last_month}
            </span>
            <span className={`text-lg font-bold ${mom.delta <= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
              {mom.delta <= 0 ? '▼' : '▲'} {money(Math.abs(mom.delta))}
            </span>
            <Pill tone={mom.delta <= 0 ? 'green' : 'rose'}>
              {pct(Math.abs(mom.pct), 1)} {mom.delta <= 0 ? 'decrease in spend' : 'increase in spend'}
            </Pill>
          </div>
        </Card>
      )}

      {/* Monthly series chart */}
      {series.length > 0 && (
        <Card title="Monthly income vs expense vs net">
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={series} margin={{ left: 10, right: 10, top: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(v: number) => money(v)} />
              <Legend />
              <Bar dataKey="income" name="Income" fill="#1f9d5b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="expense" name="Expense" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Line type="monotone" dataKey="net" name="Net" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Category breakdown */}
      {byCategory.length > 0 && (
        <div className="grid lg:grid-cols-2 gap-6">
          <Card title="Spending by category">
            <CategoryPie data={pieData} />
          </Card>

          <Card title="Category breakdown">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 font-medium text-slate-600">Category</th>
                    <th className="text-right py-2 font-medium text-slate-600">Total</th>
                    <th className="text-right py-2 font-medium text-slate-600">Txns</th>
                  </tr>
                </thead>
                <tbody>
                  {[...byCategory]
                    .sort((a, b) => b.total - a.total)
                    .map((row, i) => (
                      <tr key={row.category} className="border-b border-slate-50 hover:bg-slate-50">
                        <td className="py-2 flex items-center gap-2">
                          <span
                            className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                            style={{ backgroundColor: COLORS[i % COLORS.length] }}
                          />
                          {row.category}
                        </td>
                        <td className="py-2 text-right font-medium text-slate-800">{money(row.total)}</td>
                        <td className="py-2 text-right text-slate-500">{row.count}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
