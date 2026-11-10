import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Upload = lazy(() => import('./pages/Upload'))
const History = lazy(() => import('./pages/History'))
const Login = lazy(() => import('./pages/Login'))

export function isTokenValid(token: string | null): boolean {
  if (!token) return false
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return false
    const payload = JSON.parse(atob(parts[1]))
    if (payload.exp && Date.now() >= payload.exp * 1000) {
      return false
    }
    return true
  } catch {
    return false
  }
}

function Nav() {
  const { pathname } = useLocation()
  const rawToken = localStorage.getItem('token')
  const token = isTokenValid(rawToken) ? rawToken : null
  if (rawToken && !token) {
    localStorage.removeItem('token')
    localStorage.removeItem('user_email')
  }

  const link = (to: string, label: string) => (
    <Link
      to={to}
      className={`px-3 py-1 rounded text-sm transition-colors ${
        pathname === to
          ? 'bg-cyan-600 text-white'
          : 'text-slate-400 hover:text-white'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold text-cyan-400">DeepShield</h1>
        <p className="text-xs text-slate-500">AI-Powered Deepfake Detection</p>
      </div>
      <div className="flex items-center gap-2">
        {token ? (
          <>
            {link('/', 'Dashboard')}
            {link('/upload', 'Analyze')}
            {link('/history', 'History')}
            <span className="text-slate-600 text-xs hidden sm:inline">
              {localStorage.getItem('user_email')}
            </span>
            <button
              onClick={() => {
                localStorage.removeItem('token')
                localStorage.removeItem('user_email')
                window.location.href = '/login'
              }}
              className="px-3 py-1 rounded text-sm text-slate-400 hover:text-white transition-colors"
            >
              Sign out
            </button>
          </>
        ) : (
          link('/login', 'Sign in')
        )}
      </div>
    </nav>
  )
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!isTokenValid(token)) {
    localStorage.removeItem('token')
    localStorage.removeItem('user_email')
    return <Navigate to="/login?expired=1" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-white">
        <Nav />
        <Suspense
          fallback={
            <div className="flex items-center justify-center min-h-[60vh] text-slate-400 text-sm gap-2">
              <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              Loading view…
            </div>
          }
        >
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/upload" element={<RequireAuth><Upload /></RequireAuth>} />
            <Route path="/history" element={<RequireAuth><History /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </div>
    </BrowserRouter>
  )
}
