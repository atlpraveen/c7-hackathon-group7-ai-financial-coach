import { useRef, useState } from 'react'
import { useStore } from '../store'
import { Card, money } from '../components/ui'
import { UploadCloud, FlaskConical, Save } from 'lucide-react'

export default function DataAndProfile() {
  const { profile, documents, derivedFromDocs, loadSample, uploadFile, saveProfile, resetProfile, loading } =
    useStore()
  const fileRef = useRef<HTMLInputElement>(null)

  // Local form state seeded from the current profile.
  const [form, setForm] = useState<any>({})
  const f = (k: string) => (form[k] ?? (profile as any)?.[k] ?? '')

  const submit = async () => {
    const payload: any = {}
    for (const k of ['monthly_income', 'savings_balance', 'investment_balance', 'age']) {
      if (form[k] !== undefined && form[k] !== '') payload[k] = Number(form[k])
    }
    if (form.risk_tolerance) payload.risk_tolerance = form.risk_tolerance
    await saveProfile(payload)
    setForm({})
  }

  return (
    <div className="space-y-6">
      <Card title="1 · Bring your financial data">
        <p className="text-sm text-slate-600 mb-4">
          Upload a transactions CSV or a statement (PDF/TXT). The coach parses it into a
          financial profile and indexes it for question-answering. No data leaves your machine.
        </p>
        <div className="flex flex-wrap gap-3">
          <input
            ref={fileRef} type="file" accept=".csv,.pdf,.txt,.md" className="hidden"
            onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
          />
          <button className="btn-primary" disabled={!!loading.upload} onClick={() => fileRef.current?.click()}>
            <UploadCloud size={16} /> {loading.upload ? 'Ingesting…' : 'Upload document'}
          </button>
          <button className="btn-ghost" disabled={!!loading.upload} onClick={() => loadSample()}>
            <FlaskConical size={16} /> Load sample data
          </button>
        </div>
        {documents.length > 0 && (
          <table className="w-full text-sm mt-5">
            <thead className="text-left text-slate-500">
              <tr><th className="py-1">File</th><th>Type</th><th>Chunks</th><th>Transactions</th></tr>
            </thead>
            <tbody>
              {documents.map((d, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-1.5 font-medium">{d.filename}</td>
                  <td>{d.kind}</td><td>{d.chunks}</td><td>{d.transactions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="2 · Fine-tune your profile">
        <p className="text-sm text-slate-600 mb-4">
          {derivedFromDocs
            ? 'Values below are derived from your documents — override anything that needs adjusting.'
            : 'Enter your numbers directly, or upload data above to auto-fill them.'}
        </p>
        <div className="grid sm:grid-cols-3 gap-4">
          <Field label="Monthly income (₹)" k="monthly_income" f={f} setForm={setForm} />
          <Field label="Savings balance (₹)" k="savings_balance" f={f} setForm={setForm} />
          <Field label="Investment balance (₹)" k="investment_balance" f={f} setForm={setForm} />
          <Field label="Age" k="age" f={f} setForm={setForm} />
          <div>
            <label className="label">Risk tolerance</label>
            <select className="input" value={f('risk_tolerance')}
              onChange={(e) => setForm((s: any) => ({ ...s, risk_tolerance: e.target.value }))}>
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>
        </div>
        <div className="flex gap-3 mt-5">
          <button className="btn-primary" onClick={submit}><Save size={16} /> Save profile</button>
          <button className="btn-ghost" onClick={() => resetProfile()}>Reset overrides</button>
        </div>
      </Card>

      {profile && (
        <Card title="Current effective profile">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <KV k="Income" v={money(profile.monthly_income)} />
            <KV k="Expenses" v={money(profile.monthly_expenses)} />
            <KV k="Savings" v={money(profile.savings_balance)} />
            <KV k="Investments" v={money(profile.investment_balance)} />
            <KV k="Age" v={profile.age ?? '—'} />
            <KV k="Risk" v={profile.risk_tolerance} />
            <KV k="Debts" v={`${profile.debts.length}`} />
            <KV k="Categories" v={`${Object.keys(profile.expenses_by_category).length}`} />
          </div>
        </Card>
      )}
    </div>
  )
}

function Field({ label, k, f, setForm }: any) {
  return (
    <div>
      <label className="label">{label}</label>
      <input className="input" type="number" value={f(k)}
        onChange={(e) => setForm((s: any) => ({ ...s, [k]: e.target.value }))} />
    </div>
  )
}

function KV({ k, v }: { k: string; v: any }) {
  return (
    <div>
      <div className="label">{k}</div>
      <div className="font-semibold text-slate-800 capitalize">{v}</div>
    </div>
  )
}
