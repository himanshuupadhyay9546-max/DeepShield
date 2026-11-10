import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { ShieldCheck, ShieldAlert, Clock, Activity, FileText, Image, Video, Music, ArrowRight } from 'lucide-react'
import api from '../api/client'

interface DailyTrend {
  date: string
  name: string
  total: number
  fake: number
  real: number
}

interface StatsData {
  total: number
  fake: number
  real: number
  unknown: number
  avg_confidence: number
  avg_processing_time_ms: number
  media_distribution: {
    image: number
    video: number
    audio: number
  }
  daily_trends: DailyTrend[]
}

interface RecentItem {
  id: string
  filename: string
  media_type: string
  label: 'REAL' | 'FAKE' | 'UNKNOWN'
  confidence: number
  processing_time_ms: number
  created_at: string | null
}

export default function Dashboard() {
  const [stats, setStats] = useState<StatsData>({
    total: 0,
    fake: 0,
    real: 0,
    unknown: 0,
    avg_confidence: 0,
    avg_processing_time_ms: 0,
    media_distribution: { image: 0, video: 0, audio: 0 },
    daily_trends: [],
  })
  const [recent, setRecent] = useState<RecentItem[]>([])
  const [loading, setLoading] = useState(true)

  const fetchDashboardData = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        api.get('/api/v1/stats'),
        api.get('/api/v1/detect/history', { params: { page: 1, page_size: 5 } }),
      ])
      setStats(statsRes.data)
      setRecent(historyRes.data?.items || [])
    } catch {
      // Keep defaults on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fakePct = stats.total > 0 ? Math.round((stats.fake / stats.total) * 100) : 0
  const realPct = stats.total > 0 ? Math.round((stats.real / stats.total) * 100) : 0

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Security Analytics & Overview</h2>
          <p className="text-sm text-slate-400 mt-0.5">Real-time deepfake telemetry and media authentication metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/history"
            className="px-4 py-2 bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-lg text-sm font-medium text-slate-200 transition-colors"
          >
            Audit Log
          </Link>
          <Link
            to="/upload"
            className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors shadow-lg shadow-cyan-950/50"
          >
            + Analyze Media
          </Link>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Analyzed"
          value={loading ? '…' : stats.total.toString()}
          sub="Verified media files"
          icon={<FileText className="w-5 h-5 text-cyan-400" />}
        />
        <StatCard
          label="Deepfake Detected"
          value={loading ? '…' : stats.fake.toString()}
          sub={`${fakePct}% of total volume`}
          color="text-red-400"
          icon={<ShieldAlert className="w-5 h-5 text-red-400" />}
        />
        <StatCard
          label="Real Verified"
          value={loading ? '…' : stats.real.toString()}
          sub={`${realPct}% authentic content`}
          color="text-emerald-400"
          icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
        />
        <StatCard
          label="Avg Inference Latency"
          value={loading ? '…' : `${stats.avg_processing_time_ms} ms`}
          sub="Dual-branch throughput"
          icon={<Clock className="w-5 h-5 text-purple-400" />}
        />
      </div>

      {/* Analytics Grid: Chart + Media Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Real Trends Chart */}
        <div className="lg:col-span-2 bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Daily Telemetry (Last 7 Days)</h3>
                <p className="text-xs text-slate-500">Live counts verified directly from database records</p>
              </div>
              <span className="text-xs px-2.5 py-1 bg-cyan-950/80 border border-cyan-800 text-cyan-300 rounded-full font-medium">
                Live Data
              </span>
            </div>
            <div className="h-60 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.daily_trends}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 12 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <Bar dataKey="total" fill="#06b6d4" name="Total Analyzed" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="fake" fill="#ef4444" name="Fake Detected" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-4 border-t border-slate-800/80 mt-4">
            <span>Average Model Confidence: <strong className="text-white">{(stats.avg_confidence * 100).toFixed(1)}%</strong></span>
            <span>Historical Verification Archive</span>
          </div>
        </div>

        {/* Media Distribution Breakdown */}
        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Media Distribution</h3>
            <p className="text-xs text-slate-500 mb-6">Analyzed files segmented by modality</p>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-300 mb-1.5">
                  <span className="flex items-center gap-1.5"><Image className="w-4 h-4 text-cyan-400" /> Images</span>
                  <span>{stats.media_distribution.image} files</span>
                </div>
                <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full"
                    style={{ width: `${stats.total > 0 ? (stats.media_distribution.image / stats.total) * 100 : 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium text-slate-300 mb-1.5">
                  <span className="flex items-center gap-1.5"><Video className="w-4 h-4 text-purple-400" /> Videos</span>
                  <span>{stats.media_distribution.video} files</span>
                </div>
                <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full"
                    style={{ width: `${stats.total > 0 ? (stats.media_distribution.video / stats.total) * 100 : 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium text-slate-300 mb-1.5">
                  <span className="flex items-center gap-1.5"><Music className="w-4 h-4 text-amber-400" /> Audio</span>
                  <span>{stats.media_distribution.audio} files</span>
                </div>
                <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full"
                    style={{ width: `${stats.total > 0 ? (stats.media_distribution.audio / stats.total) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800/80 mt-6">
            <Link
              to="/upload"
              className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 font-medium py-2 rounded-lg text-xs transition-colors"
            >
              Analyze New Modality <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Detections Preview */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Recent Analyses</h3>
            <p className="text-xs text-slate-500">Latest files inspected by the DeepShield engine</p>
          </div>
          <Link to="/history" className="text-xs font-medium text-cyan-400 hover:underline flex items-center gap-1">
            View All History <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {recent.length === 0 && !loading ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            <p>No detection history recorded yet.</p>
            <Link to="/upload" className="text-cyan-500 hover:underline text-xs mt-1 inline-block">
              Analyze your first file →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {recent.map((item) => (
              <div key={item.id} className="px-6 py-3.5 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 text-xs font-bold uppercase">
                    {item.media_type[0]}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{item.filename || 'Uploaded File'}</p>
                    <p className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleString() : '—'}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-xs text-slate-400 font-medium">{(item.confidence * 100).toFixed(1)}%</p>
                    <p className="text-[11px] text-slate-600">{item.processing_time_ms} ms</p>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      item.label === 'FAKE'
                        ? 'bg-red-950/80 border border-red-700/60 text-red-300'
                        : 'bg-emerald-950/80 border border-emerald-700/60 text-emerald-300'
                    }`}
                  >
                    {item.label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  sub,
  color = 'text-white',
  icon,
}: {
  label: string
  value: string
  sub: string
  color?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-sm flex items-start justify-between">
      <div>
        <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">{label}</p>
        <p className={`text-2xl font-bold mt-1.5 ${color}`}>{value}</p>
        <p className="text-slate-500 text-xs mt-1">{sub}</p>
      </div>
      {icon && <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">{icon}</div>}
    </div>
  )
}
