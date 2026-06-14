import { useEffect, useState } from 'react'
import { useStore } from '../store'
import { Card, Empty, Pill, ProgressBar, Stat, money, pct } from '../components/ui'
import type { GoalInput, TrackedGoal } from '../types'

const BLANK: GoalInput = {
  name: '',
  category: '',
  target_amount: 0,
  current_amount: 0,
  monthly_contribution: 0,
  target_months: 60,
  annual_return: 8,
}

function statusTone(status: TrackedGoal['status']): 'green' | 'rose' | 'brand' {
  if (status === 'complete' || status === 'on_track') return 'green'
  if (status === 'behind') return 'rose'
  return 'brand'
}

export default function Goals() {
  const { goals, loadGoals, createGoal, updateGoal, deleteGoal, loading } = useStore()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<GoalInput>(BLANK)
  const [submitting, setSubmitting] = useState(false)
  // Per-goal editing state: id -> new current_amount string
  const [editAmount, setEditAmount] = useState<Record<number, string>>({})

  useEffect(() => { loadGoals() }, []) // eslint-disable-line

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await createGoal(form)
      setForm(BLANK)
      setShowForm(false)
    } finally {
      setSubmitting(false)
    }
  }

  function setField(key: keyof GoalInput, value: string | number) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSaveAmount(goal: TrackedGoal) {
    const raw = editAmount[goal.id]
    if (raw == null) return
    const val = parseFloat(raw)
    if (!isNaN(val)) await updateGoal(goal.id, { current_amount: val })
    setEditAmount((m) => { const next = { ...m }; delete next[goal.id]; return next })
  }

  const list = goals?.goals ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Goals</h2>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : 'New goal'}
        </button>
      </div>

      {/* Inline new-goal form */}
      {showForm && (
        <Card title="Add new goal">
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Name</label>
              <input
                className="input w-full"
                required
                value={form.name}
                onChange={(e) => setField('name', e.target.value)}
              />
            </div>
            <div>
              <label className="label">Category</label>
              <input
                className="input w-full"
                placeholder="e.g. Home, Education, Retirement"
                value={form.category ?? ''}
                onChange={(e) => setField('category', e.target.value)}
              />
            </div>
            <div>
              <label className="label">Target amount (₹)</label>
              <input
                className="input w-full"
                type="number"
                min={0}
                required
                value={form.target_amount || ''}
                onChange={(e) => setField('target_amount', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div>
              <label className="label">Current amount (₹)</label>
              <input
                className="input w-full"
                type="number"
                min={0}
                value={form.current_amount || ''}
                onChange={(e) => setField('current_amount', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div>
              <label className="label">Monthly contribution (₹)</label>
              <input
                className="input w-full"
                type="number"
                min={0}
                value={form.monthly_contribution || ''}
                onChange={(e) => setField('monthly_contribution', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div>
              <label className="label">Target months</label>
              <input
                className="input w-full"
                type="number"
                min={1}
                value={form.target_months || ''}
                onChange={(e) => setField('target_months', parseInt(e.target.value) || 60)}
              />
            </div>
            <div>
              <label className="label">Annual return (%)</label>
              <input
                className="input w-full"
                type="number"
                min={0}
                max={50}
                step={0.5}
                value={form.annual_return || ''}
                onChange={(e) => setField('annual_return', parseFloat(e.target.value) || 8)}
              />
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <button className="btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving…' : 'Create goal'}
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* Summary row */}
      {goals && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat label="Total goals" value={String(goals.count)} />
          <Stat
            label="Overall progress"
            value={pct(goals.overall_progress_pct, 1)}
            tone={goals.overall_progress_pct >= 50 ? 'good' : 'warn'}
          />
          <Stat
            label="Saved / target"
            value={money(goals.total_current)}
            sub={`of ${money(goals.total_target)}`}
          />
          <Stat
            label="On track"
            value={`${goals.on_track_count} / ${goals.count}`}
            tone={goals.on_track_count === goals.count ? 'good' : 'warn'}
          />
        </div>
      )}

      {/* Loading */}
      {loading.goals && (
        <div className="card text-center text-slate-500 text-sm py-6">Loading goals…</div>
      )}

      {/* Empty */}
      {!loading.goals && list.length === 0 && (
        <Empty>No goals yet — click "New goal" to add one.</Empty>
      )}

      {/* Goal cards */}
      <div className="space-y-4">
        {list.map((goal) => {
          const isEditing = goal.id in editAmount
          const tone = statusTone(goal.status)
          const progressTone =
            goal.status === 'complete' ? 'emerald'
            : goal.status === 'on_track' ? 'brand'
            : 'rose'

          return (
            <Card key={goal.id}
              title={goal.name}
              right={
                <div className="flex items-center gap-2">
                  <Pill tone={tone}>{goal.status.replace('_', ' ')}</Pill>
                  {goal.category && (
                    <Pill tone="slate">{goal.category}</Pill>
                  )}
                </div>
              }
            >
              <div className="space-y-3">
                {/* Progress bar */}
                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>{pct(goal.progress_pct, 1)} complete</span>
                    <span>{money(goal.current_amount)} of {money(goal.target_amount)}</span>
                  </div>
                  <ProgressBar value={goal.progress_pct} tone={progressTone} />
                </div>

                {/* Key metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                  <div>
                    <div className="label">Projected months</div>
                    <div className="font-medium text-slate-700">
                      {goal.projected_months != null ? `${goal.projected_months} mo` : '—'}
                    </div>
                  </div>
                  <div>
                    <div className="label">Monthly contribution</div>
                    <div className="font-medium text-slate-700">{money(goal.monthly_contribution)}</div>
                  </div>
                  <div>
                    <div className="label">Required / month</div>
                    <div className="font-medium text-slate-700">
                      {money(goal.monthly_required_for_deadline)}
                    </div>
                  </div>
                </div>

                {/* Shortfall warning */}
                {goal.monthly_shortfall > 0 && (
                  <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                    <span className="font-medium">Monthly shortfall:</span>
                    <span>{money(goal.monthly_shortfall)}</span>
                    <Pill tone="amber">increase contributions</Pill>
                  </div>
                )}

                {/* Inline current-amount edit */}
                <div className="flex items-center gap-3 pt-1 border-t border-slate-100">
                  {!isEditing ? (
                    <button
                      className="btn-ghost text-xs"
                      onClick={() => setEditAmount((m) => ({ ...m, [goal.id]: String(goal.current_amount) }))}
                    >
                      Edit current amount
                    </button>
                  ) : (
                    <div className="flex items-center gap-2">
                      <input
                        className="input w-40 text-sm"
                        type="number"
                        min={0}
                        value={editAmount[goal.id]}
                        onChange={(e) => setEditAmount((m) => ({ ...m, [goal.id]: e.target.value }))}
                      />
                      <button className="btn-primary text-xs" onClick={() => handleSaveAmount(goal)}>
                        Save
                      </button>
                      <button
                        className="btn-ghost text-xs"
                        onClick={() => setEditAmount((m) => { const next = { ...m }; delete next[goal.id]; return next })}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                  <div className="flex-1" />
                  <button
                    className="text-xs text-rose-500 hover:text-rose-700 transition-colors"
                    onClick={() => deleteGoal(goal.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
