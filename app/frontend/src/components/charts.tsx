import {
  Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, LineChart, Pie,
  PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'

const COLORS = ['#1f9d5b', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']

/** Debt payoff: total balance over time for both strategies. */
export function DebtPayoffChart({ avalanche, snowball }: { avalanche: any; snowball: any }) {
  const len = Math.max(avalanche?.timeline?.length || 0, snowball?.timeline?.length || 0)
  const data = Array.from({ length: len }, (_, i) => ({
    month: i + 1,
    Avalanche: avalanche?.timeline?.[i]?.total_balance ?? 0,
    Snowball: snowball?.timeline?.[i]?.total_balance ?? 0,
  }))
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ left: 10, right: 10, top: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} label={{ value: 'Month', position: 'insideBottom', offset: -2, fontSize: 11 }} />
        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
        <Tooltip formatter={(v: number) => `₹${v.toLocaleString('en-IN')}`} />
        <Legend />
        <Line type="monotone" dataKey="Avalanche" stroke="#1f9d5b" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Snowball" stroke="#f59e0b" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

/** Budget: spending by category as a pie. */
export function CategoryPie({ data }: { data: { category: string; amount: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="amount" nameKey="category" cx="50%" cy="50%" outerRadius={100} label={(e: any) => e.category}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip formatter={(v: number) => `₹${v.toLocaleString('en-IN')}`} />
      </PieChart>
    </ResponsiveContainer>
  )
}

/** Budget buckets: actual vs target percentages. */
export function BucketBars({ buckets }: { buckets: Record<string, any> }) {
  const data = Object.entries(buckets).map(([name, b]: any) => ({
    name: name[0].toUpperCase() + name.slice(1),
    Actual: b.pct_of_income,
    Target: b.target_pct,
  }))
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
        <Tooltip formatter={(v: number) => `${v}%`} />
        <Legend />
        <Bar dataKey="Actual" fill="#1f9d5b" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Target" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Investment / savings growth projection. */
export function GrowthChart({ data, xKey, contributedKey = 'contributed', balanceKey = 'balance' }: {
  data: any[]; xKey: string; contributedKey?: string; balanceKey?: string
}) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ left: 10, right: 10, top: 10 }}>
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#1f9d5b" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#1f9d5b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
        <Tooltip formatter={(v: number) => `₹${v.toLocaleString('en-IN')}`} />
        <Legend />
        <Area type="monotone" dataKey={balanceKey} name="Projected balance" stroke="#1f9d5b" strokeWidth={2} fill="url(#g)" />
        <Line type="monotone" dataKey={contributedKey} name="Contributed" stroke="#94a3b8" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

/** Allocation donut. */
export function AllocationDonut({ allocation }: { allocation: Record<string, number> }) {
  const data = Object.entries(allocation).map(([k, v]) => ({ name: k, value: v }))
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={95}
          label={(e: any) => `${e.name} ${e.value}%`}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip formatter={(v: number) => `${v}%`} />
      </PieChart>
    </ResponsiveContainer>
  )
}
