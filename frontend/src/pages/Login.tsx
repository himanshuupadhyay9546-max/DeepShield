import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import api from '../api/client'

type Tab = 'login' | 'register'

export default function Login() {
  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    if (params.get('expired')) {
      setError('Your session expired. Please sign in again.')
    }
  }, [location.search])

  const reset = () => { setError(''); setEmail(''); setPassword(''); setConfirmPw('') }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (tab === 'register') {
      if (password.length < 6) { setError('Password must be at least 6 characters'); return }
      if (password !== confirmPw) { setError('Passwords do not match'); return }
    }

    setLoading(true)
    try {
      const res = await api.post(`/api/v1/auth/${tab}`, { email, password })
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user_email', res.data.email)
      navigate('/')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg ?? JSON.stringify(d)).join(', '))
      } else {
        setError(typeof detail === 'string' ? detail : 'Something went wrong')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 w-full max-w-sm">
        <h2 className="text-xl font-bold mb-6">DeepShield</h2>

        {/* Tabs */}
        <div className="flex rounded-lg bg-slate-800 p-1 mb-6">
          {(['login', 'register'] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => { setTab(t); reset() }}
              className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors capitalize
                ${tab === t ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              {t === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              placeholder="••••••••"
            />
          </div>

          {tab === 'register' && (
            <div>
              <label className="block text-sm text-slate-400 mb-1">Confirm Password</label>
              <input
                type="password"
                value={confirmPw}
                onChange={e => setConfirmPw(e.target.value)}
                required
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
                placeholder="••••••••"
              />
            </div>
          )}

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 py-2 rounded font-medium text-sm transition-colors"
          >
            {loading ? (tab === 'login' ? 'Signing in…' : 'Creating account…') : (tab === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>
      </div>
    </div>
  )
}
