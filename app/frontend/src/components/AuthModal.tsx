import { useState } from 'react'
import { useStore } from '../store'

type Tab = 'login' | 'signup'

interface Props {
  onClose: () => void
}

export default function AuthModal({ onClose }: Props) {
  const { login, register, loginWithGoogle } = useStore()

  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      if (tab === 'login') {
        await login(email, password)
      } else {
        await register(email, password, fullName)
      }
      onClose()
    } catch (err: any) {
      setError(err?.message ?? 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGoogle() {
    setError('')
    try {
      await loginWithGoogle()
      // loginWithGoogle redirects; onClose not needed
    } catch {
      setError("Google sign-in isn't configured")
    }
  }

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Panel */}
      <div className="card w-full max-w-md p-6 space-y-5">
        {/* Tabs */}
        <div className="flex rounded-lg bg-slate-100 p-1 gap-1">
          {(['login', 'signup'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError('') }}
              className={`flex-1 text-sm font-medium py-1.5 rounded-md transition-colors ${
                tab === t
                  ? 'bg-white text-slate-800 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {t === 'login' ? 'Log in' : 'Sign up'}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === 'signup' && (
            <div>
              <label className="label">Full name</label>
              <input
                className="input w-full"
                type="text"
                autoComplete="name"
                placeholder="Ravi Kumar"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
          )}
          <div>
            <label className="label">Email</label>
            <input
              className="input w-full"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input w-full"
              type="password"
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
              placeholder="••••••••"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-rose-600 bg-rose-50 rounded-lg px-3 py-2">{error}</p>
          )}

          <button className="btn-primary w-full" type="submit" disabled={submitting}>
            {submitting
              ? (tab === 'login' ? 'Logging in…' : 'Creating account…')
              : (tab === 'login' ? 'Log in' : 'Create account')}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-slate-200" />
          <span className="text-xs text-slate-400">or</span>
          <div className="flex-1 h-px bg-slate-200" />
        </div>

        {/* Google */}
        <button
          onClick={handleGoogle}
          className="w-full flex items-center justify-center gap-2 border border-slate-200 rounded-lg py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          {/* Simple Google "G" logo */}
          <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
            <path fill="#4285F4" d="M44.5 20H24v8.5h11.7C34.7 33.9 30 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 5.1 29.6 3 24 3 12.9 3 4 11.9 4 23s8.9 20 20 20c11 0 19.7-8 19.7-20 0-1.3-.1-2.7-.2-3z" />
            <path fill="#34A853" d="M6.3 14.7l7 5.1C15 16.1 19.1 13 24 13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 5.1 29.6 3 24 3c-7.6 0-14.2 4.3-17.7 10.7z" />
            <path fill="#FBBC05" d="M24 43c5.8 0 10.8-1.9 14.5-5.2l-6.7-5.5C29.8 33.9 27 35 24 35c-5.9 0-10.8-3.9-12.5-9.3l-7 5.4C8.1 38.6 15.4 43 24 43z" />
            <path fill="#EA4335" d="M43.6 20H24v8.5h11.7c-.9 2.8-2.8 5.1-5.3 6.7l6.7 5.5C40.9 37.3 44 31 44 24c0-1.4-.2-2.7-.4-4z" />
          </svg>
          Continue with Google
        </button>

        {/* Guest link */}
        <div className="text-center">
          <button
            onClick={onClose}
            className="text-sm text-slate-500 hover:text-brand-600 transition-colors underline underline-offset-2"
          >
            Continue as guest
          </button>
        </div>
      </div>
    </div>
  )
}
