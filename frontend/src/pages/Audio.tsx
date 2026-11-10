import React, { useState, useRef } from 'react'
import axios from 'axios'
import ResultCard, { DetectionResult } from '../components/ResultCard'

export default function Audio() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f: File) => {
    if (!f.type.startsWith('audio/')) { setError('Please upload an audio file (mp3, wav, flac, etc.)'); return }
    setFile(f); setResult(null); setError('')
    setPreview(URL.createObjectURL(f))
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleAnalyze = async () => {
    if (!file) return
    setLoading(true); setError(''); setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const token = localStorage.getItem('token')
      const res = await axios.post('http://localhost:8000/api/v1/detect/audio', form, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      setResult(res.data)
    } catch (err: any) {
      if (err?.response?.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user_email')
        setError('Your session has expired. Please sign in again.')
        return
      }
      const detail = err?.response?.data?.detail
      setError(Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : detail ?? 'Detection failed.')
    } finally {
      setLoading(false)
    }
  }

  const isUnknown = result?.label === 'UNKNOWN'

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-lg font-semibold mb-1">Audio Detection</h2>
      <p className="text-slate-500 text-sm mb-6">Mel spectrogram + FFT · EfficientNet-B0 · detects AI-generated / cloned voices</p>

      <div
        onDrop={handleDrop}
        onDragOver={e => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed border-slate-700 hover:border-cyan-600 rounded-xl p-10 text-center cursor-pointer transition-colors mb-4"
      >
        <input ref={inputRef} type="file" accept="audio/*" className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
        {file ? (
          <div>
            <p className="font-medium">{file.name}</p>
            <p className="text-slate-500 text-sm mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB · audio</p>
          </div>
        ) : (
          <div>
            <p className="text-4xl mb-3">🎙️</p>
            <p className="text-slate-400">Drop an audio file here or click to browse</p>
            <p className="text-slate-600 text-sm mt-1">MP3, WAV, FLAC, M4A · first 4 seconds analyzed</p>
          </div>
        )}
      </div>

      {preview && <audio src={preview} controls className="w-full mb-4" />}

      <button onClick={handleAnalyze} disabled={!file || loading}
        className="w-full bg-cyan-600 hover:bg-cyan-700 disabled:opacity-40 py-2.5 rounded font-medium text-sm transition-colors">
        {loading ? <span className="flex items-center justify-center gap-2"><Spinner /> Analyzing audio…</span> : 'Analyze Audio'}
      </button>

      {error && <div className="mt-4 p-4 bg-red-950 border border-red-800 rounded-lg text-red-300 text-sm">{error}</div>}

      {result && (
        <div className="mt-6">
          {isUnknown ? (
            <div className="p-5 rounded-xl border bg-slate-900 border-slate-700">
              <p className="text-slate-300 font-semibold mb-2">Audio model not trained yet</p>
              <p className="text-slate-500 text-sm">{result.note}</p>
              <p className="text-slate-600 text-xs mt-3">
                Download ASVspoof 2019 and run{' '}
                <code className="bg-slate-800 px-1 rounded">python ml/training/train_audio.py</code>
              </p>
            </div>
          ) : (
            <ResultCard result={result} />
          )}
        </div>
      )}
    </div>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  )
}
