import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Filter, RefreshCw, Eye, ArrowLeft, ArrowRight, ShieldCheck, ShieldAlert, HelpCircle } from 'lucide-react'
import api from '../api/client'

interface DetectionItem {
  id: string
  filename: string
  media_type: string
  label: 'REAL' | 'FAKE' | 'UNKNOWN'
  confidence: number
  processing_time_ms: number
  model_version: string
  metadata: Record<string, any>
  created_at: string | null
}

export default function History() {
  const [items, setItems] = useState<DetectionItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [mediaType, setMediaType] = useState('all')
  const [label, setLabel] = useState('ALL')
  const [search, setSearch] = useState('')
  const [selectedItem, setSelectedItem] = useState<DetectionItem | null>(null)

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/v1/detect/history', {
        params: {
          page,
          page_size: 10,
          media_type: mediaType !== 'all' ? mediaType : undefined,
          label: label !== 'ALL' ? label : undefined,
          search: search.trim() || undefined,
        },
      })
      setItems(res.data.items || [])
      setTotal(res.data.total || 0)
      setTotalPages(res.data.total_pages || 1)
    } catch {
      // Keep empty list on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [page, mediaType, label])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchHistory()
  }

  const getVerdictBadge = (verdict: string) => {
    if (verdict === 'FAKE') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-950/80 border border-red-700/60 text-red-300">
          <ShieldAlert className="w-3.5 h-3.5 text-red-400" /> FAKE
        </span>
      )
    }
    if (verdict === 'REAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 border border-emerald-700/60 text-emerald-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> REAL
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 border border-slate-700 text-slate-300">
        <HelpCircle className="w-3.5 h-3.5 text-slate-400" /> UNKNOWN
      </span>
    )
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Detection History & Telemetry</h2>
          <p className="text-sm text-slate-400 mt-0.5">Comprehensive audit trail of analyzed images, videos, and audio</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setPage(1); fetchHistory() }}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-lg text-sm text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <Link
            to="/upload"
            className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors shadow-lg shadow-cyan-950/50"
          >
            + New Analysis
          </Link>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 mb-6 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-1 min-w-[240px]">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by filename..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-sm font-medium rounded-lg text-white transition-colors"
            >
              Search
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Type:</span>
              <select
                value={mediaType}
                onChange={(e) => { setMediaType(e.target.value); setPage(1) }}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="all">All Media</option>
                <option value="image">Image</option>
                <option value="video">Video</option>
                <option value="audio">Audio</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Verdict:</span>
              <select
                value={label}
                onChange={(e) => { setLabel(e.target.value); setPage(1) }}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">All Verdicts</option>
                <option value="FAKE">Fake Only</option>
                <option value="REAL">Real Only</option>
                <option value="UNKNOWN">Unknown</option>
              </select>
            </div>
          </div>
        </form>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5 font-semibold">File & Media</th>
                <th className="px-5 py-3.5 font-semibold">Verdict</th>
                <th className="px-5 py-3.5 font-semibold">Confidence</th>
                <th className="px-5 py-3.5 font-semibold">Model</th>
                <th className="px-5 py-3.5 font-semibold">Processing Time</th>
                <th className="px-5 py-3.5 font-semibold">Timestamp</th>
                <th className="px-5 py-3.5 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-500">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                      Loading records...
                    </div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-14 text-center text-slate-500">
                    <p className="font-medium text-slate-400">No detection records found.</p>
                    <p className="text-xs text-slate-600 mt-1">Try adjusting your search criteria or analyze a new file.</p>
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-slate-200">{item.filename || 'Unnamed file'}</div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider mt-0.5">{item.media_type}</div>
                    </td>
                    <td className="px-5 py-3.5">{getVerdictBadge(item.label)}</td>
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-200">{(item.confidence * 100).toFixed(1)}%</div>
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
                        <div
                          className={`h-full ${item.label === 'FAKE' ? 'bg-red-500' : 'bg-emerald-500'}`}
                          style={{ width: `${Math.min(100, item.confidence * 100)}%` }}
                        />
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-400 max-w-[180px] truncate">
                      {item.model_version || 'DeepShield-B4'}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-400">
                      {item.processing_time_ms ? `${item.processing_time_ms} ms` : '—'}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-400">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-cyan-400 rounded-lg transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" /> Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {total > 0 && (
          <div className="px-5 py-3.5 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing <span className="text-white font-medium">{(page - 1) * 10 + 1}</span> to{' '}
              <span className="text-white font-medium">{Math.min(page * 10, total)}</span> of{' '}
              <span className="text-white font-medium">{total}</span> records
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-white transition-colors flex items-center gap-1 font-medium"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Prev
              </button>
              <span>Page {page} of {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded-lg text-white transition-colors flex items-center gap-1 font-medium"
              >
                Next <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <h3 className="text-base font-bold text-white">Detection Audit Record</h3>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-slate-400 hover:text-white text-lg font-semibold px-2 py-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3.5 text-sm">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Record ID:</span>
                <span className="font-mono text-xs text-slate-300">{selectedItem.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">File Name:</span>
                <span className="font-semibold text-white truncate max-w-[260px]">{selectedItem.filename}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Media Type:</span>
                <span className="uppercase text-xs font-semibold text-slate-300">{selectedItem.media_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">AI Verdict:</span>
                {getVerdictBadge(selectedItem.label)}
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Confidence Score:</span>
                <span className="font-bold text-cyan-400">{(selectedItem.confidence * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Inference Architecture:</span>
                <span className="text-xs text-slate-300">{selectedItem.model_version}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Inference Latency:</span>
                <span className="text-xs text-slate-300">{selectedItem.processing_time_ms} ms</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Analysis Timestamp:</span>
                <span className="text-xs text-slate-300">
                  {selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleString() : '—'}
                </span>
              </div>

              {selectedItem.metadata && Object.keys(selectedItem.metadata).length > 0 && (
                <div className="pt-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Execution Metadata:</span>
                  <pre className="mt-1.5 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300 overflow-x-auto">
                    {JSON.stringify(selectedItem.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

