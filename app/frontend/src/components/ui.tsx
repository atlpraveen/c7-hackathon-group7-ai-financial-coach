import type { ReactNode } from 'react'

// All money is rendered in Indian Rupees with Indian digit grouping (lakh/crore).
export const money = (n: number | null | undefined) =>
  n == null
    ? '—'
    : n.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

export const pct = (n: number | null | undefined, digits = 0) =>
  n == null ? '—' : `${n.toFixed(digits)}%`

export function Card({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="card">
      {(title || right) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="font-semibold text-slate-800">{title}</h3>}
          {right}
        </div>
      )}
      {children}
    </div>
  )
}

export function Stat({ label, value, sub, tone = 'default' }: {
  label: string; value: string; sub?: string; tone?: 'default' | 'good' | 'warn' | 'bad'
}) {
  const tones: Record<string, string> = {
    default: 'text-slate-800', good: 'text-brand-600', warn: 'text-amber-600', bad: 'text-rose-600',
  }
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className={`text-2xl font-bold ${tones[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

export function Narrative({ text, by }: { text: string; by?: 'llm' | 'deterministic' }) {
  return (
    <div className="card bg-brand-50 border-brand-100">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm font-semibold text-brand-700">Coach's take</span>
        {by && (
          <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-white text-slate-500 border border-slate-200">
            {by === 'llm' ? 'AI' : 'rule-based'}
          </span>
        )}
      </div>
      <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{text}</p>
    </div>
  )
}

export function ProgressBar({ value, tone = 'brand' }: { value: number; tone?: 'brand' | 'amber' | 'rose' | 'emerald' }) {
  const colors: Record<string, string> = {
    brand: 'bg-brand-500', amber: 'bg-amber-500', rose: 'bg-rose-500', emerald: 'bg-emerald-500',
  }
  return (
    <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
      <div className={`h-full ${colors[tone]} rounded-full transition-all`} style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
    </div>
  )
}

export function Pill({ children, tone = 'slate' }: { children: ReactNode; tone?: 'slate' | 'green' | 'amber' | 'rose' | 'brand' }) {
  const tones: Record<string, string> = {
    slate: 'bg-slate-100 text-slate-600',
    green: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    rose: 'bg-rose-100 text-rose-700',
    brand: 'bg-brand-100 text-brand-700',
  }
  return <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${tones[tone]}`}>{children}</span>
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="card text-center text-slate-500 text-sm py-10">{children}</div>
}
