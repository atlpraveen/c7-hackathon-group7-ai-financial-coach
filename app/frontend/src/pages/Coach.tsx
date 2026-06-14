import { useState } from 'react'
import { useStore } from '../store'
import { Card, Narrative, Empty } from '../components/ui'
import { Send, Wand2 } from 'lucide-react'

const SUGGESTIONS = [
  'How should I prioritise paying off my debt?',
  'Am I saving enough for emergencies?',
  'Where can I cut spending?',
  'How much do I spend on dining and subscriptions?',
]

export default function Coach() {
  const { chat, ask, loading, coach, runCoach, profile, setView } = useStore()
  const [q, setQ] = useState('')

  if (!profile || profile.monthly_income === 0)
    return <Empty><button className="btn-primary mx-auto" onClick={() => setView('data')}>Add your data first →</button></Empty>

  const send = (text: string) => {
    if (!text.trim() || loading.ask) return
    ask(text)
    setQ('')
  }

  return (
    <div className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <Card title="Chat — grounded in your documents">
          <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
            {chat.length === 0 && (
              <p className="text-sm text-slate-500">
                Ask anything about your finances. Answers are grounded in the documents you uploaded.
              </p>
            )}
            {chat.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                  m.role === 'user' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-800'
                }`}>
                  {m.text}
                  {m.streaming && <span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-slate-400 animate-pulse" />}
                  {m.sources && m.sources.length > 0 && (
                    <details className="mt-2 text-xs opacity-80">
                      <summary className="cursor-pointer">sources ({m.sources.length})</summary>
                      <ul className="mt-1 space-y-1">
                        {m.sources.slice(0, 3).map((s, j) => (
                          <li key={j} className="opacity-90">• {s.text.slice(0, 120)}…</li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>
              </div>
            ))}
            {loading.ask && <div className="text-sm text-slate-400">Coach is thinking…</div>}
          </div>
          <div className="flex gap-2 mt-4">
            <input
              className="input" placeholder="Ask the coach…" value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send(q)}
            />
            <button className="btn-primary" onClick={() => send(q)} disabled={!!loading.ask}>
              <Send size={16} />
            </button>
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="text-xs px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600"
                onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        </Card>
      </div>

      <div className="space-y-4">
        <Card title="Full orchestrated review">
          <p className="text-sm text-slate-600 mb-3">
            Routes your request to the right specialist agents and synthesises one
            prioritised action plan.
          </p>
          <button className="btn-primary w-full justify-center" onClick={() => runCoach()} disabled={!!loading.coach}>
            <Wand2 size={16} /> {loading.coach ? 'Coaching…' : 'Run full review'}
          </button>
          {coach && (
            <div className="text-xs text-slate-400 mt-2 space-y-0.5">
              <div>Agents run: {coach.agents_run.join(', ')}</div>
              <div>Routing: {coach.routed_by} · Engine: {coach.engine}</div>
            </div>
          )}
        </Card>
        {coach && <Narrative text={coach.synthesis} by={coach.synthesis_generated_by} />}
      </div>
    </div>
  )
}
