import React, { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  UploadCloud,
  FileCheck,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Clock,
  Cpu,
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Image as ImageIcon,
  Video as VideoIcon,
  Music as AudioIcon,
} from 'lucide-react'
import api from '../api/client'

type MediaType = 'image' | 'video' | 'audio'

interface Result {
  id?: string
  label: 'REAL' | 'FAKE' | 'UNKNOWN'
  confidence?: number
  video_confidence?: number
  frames_analyzed?: number
  face_detection?: boolean
  heatmap_b64?: string
  model?: string
  processing_time_ms?: number
  note?: string
}

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [mediaType, setMediaType] = useState<MediaType>('image')
  const [result, setResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f: File) => {
    setFile(f)
    setResult(null)
    setError('')

    let detected: MediaType = 'image'
    if (f.type.startsWith('video/') || /\.(mp4|mov|avi|mkv|webm)$/i.test(f.name)) {
      detected = 'video'
    } else if (f.type.startsWith('audio/') || /\.(wav|mp3|ogg|flac|m4a)$/i.test(f.name)) {
      detected = 'audio'
    }
    setMediaType(detected)

    if (detected === 'image') {
      setPreview(URL.createObjectURL(f))
    } else {
      setPreview(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleAnalyze = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const form = new FormData()
      form.append('file', file)
      const res = await api.post(`/api/v1/detect/${mediaType}`, form)
      setResult(res.data)
    } catch (err: any) {
      if (err?.response?.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user_email')
        setError('Your session has expired. Please sign in again.')
        return
      }
      setError(err?.response?.data?.detail ?? 'Detection pipeline failed. Check server status.')
    } finally {
      setLoading(false)
    }
  }

  const rawConfidence = result?.confidence ?? result?.video_confidence ?? 0
  const confidencePct = (rawConfidence * 100).toFixed(1)

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Multi-Modal Detection Studio</h2>
          <p className="text-sm text-slate-400 mt-0.5">Dual-domain neural architecture for images, videos, and synthetic voice</p>
        </div>
        <Link
          to="/history"
          className="text-xs text-slate-400 hover:text-white flex items-center gap-1 self-start sm:self-auto px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 transition-colors"
        >
          View Past Analyses <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Modality Selector Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => { setMediaType('image'); setResult(null) }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            mediaType === 'image'
              ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ImageIcon className="w-4 h-4" /> Image Detection
        </button>
        <button
          onClick={() => { setMediaType('video'); setResult(null) }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            mediaType === 'video'
              ? 'bg-purple-600/20 text-purple-400 border border-purple-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <VideoIcon className="w-4 h-4" /> Video Deepfake
        </button>
        <button
          onClick={() => { setMediaType('audio'); setResult(null) }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            mediaType === 'audio'
              ? 'bg-amber-600/20 text-amber-400 border border-amber-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <AudioIcon className="w-4 h-4" /> Voice & Audio
        </button>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed border-slate-800 hover:border-cyan-600/80 bg-slate-900/40 hover:bg-slate-900/70 rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all group shadow-inner"
      >
        <input
          ref={inputRef}
          type="file"
          accept={
            mediaType === 'image'
              ? 'image/jpeg,image/png,image/webp,image/bmp'
              : mediaType === 'video'
              ? 'video/mp4,video/quicktime,video/x-msvideo,video/webm'
              : 'audio/wav,audio/mpeg,audio/flac,audio/ogg'
          }
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handleFile(f)
          }}
        />

        <div className="flex flex-col items-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-cyan-400 group-hover:scale-105 group-hover:border-cyan-500 transition-all mb-4 shadow-lg shadow-black/40">
            <UploadCloud className="w-7 h-7" />
          </div>

          {file ? (
            <div className="space-y-1">
              <p className="font-semibold text-white text-base">{file.name}</p>
              <p className="text-slate-400 text-xs">
                {(file.size / 1024 / 1024).toFixed(2)} MB · {mediaType.toUpperCase()} file selected
              </p>
              <p className="text-cyan-400 text-xs pt-1 font-medium">Click or drop another file to change</p>
            </div>
          ) : (
            <div className="space-y-1.5">
              <p className="text-slate-200 font-medium text-sm">
                Drop your {mediaType} file here, or <span className="text-cyan-400 underline underline-offset-2">browse files</span>
              </p>
              <p className="text-slate-500 text-xs">
                {mediaType === 'image' && 'Supports JPG, PNG, WEBP, BMP (max 25MB)'}
                {mediaType === 'video' && 'Supports MP4, MOV, AVI, WEBM (sampled at 5fps, max 75MB)'}
                {mediaType === 'audio' && 'Supports WAV, MP3, FLAC, OGG (16kHz Mel FFT, max 25MB)'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Preview Section */}
      {preview && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
          <img src={preview} alt="Upload preview" className="w-20 h-20 rounded-lg object-cover border border-slate-800" />
          <div>
            <p className="text-sm font-semibold text-white">Source Image Loaded</p>
            <p className="text-xs text-slate-400">Ready for spatial feature extraction and 2D frequency spectrum analysis</p>
          </div>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={handleAnalyze}
        disabled={!file || loading}
        className="w-full bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:opacity-40 text-white font-semibold py-3 rounded-xl text-sm transition-all shadow-lg shadow-cyan-950/40 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin" />
            Analyzing {mediaType.toUpperCase()} through DeepShield Neural Engine…
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" /> Run Deepfake Analysis
          </>
        )}
      </button>

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-red-950/80 border border-red-800/80 rounded-xl text-red-300 text-sm flex items-center justify-between shadow-sm">
          <span>{error}</span>
          {error.includes('sign in') && (
            <Link
              to="/login"
              className="ml-3 bg-red-800 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors"
            >
              Sign In
            </Link>
          )}
        </div>
      )}

      {/* Results Card */}
      {result && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Analysis Result</span>
              <div className="flex items-center gap-3 mt-1">
                {result.label === 'FAKE' ? (
                  <div className="flex items-center gap-2 text-2xl font-black text-red-400">
                    <ShieldAlert className="w-7 h-7 text-red-500" /> DEEPFAKE DETECTED
                  </div>
                ) : result.label === 'REAL' ? (
                  <div className="flex items-center gap-2 text-2xl font-black text-emerald-400">
                    <ShieldCheck className="w-7 h-7 text-emerald-500" /> AUTHENTIC MEDIA
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-2xl font-black text-slate-300">
                    <HelpCircle className="w-7 h-7 text-slate-400" /> INCONCLUSIVE / UNKNOWN
                  </div>
                )}
              </div>
            </div>

            <div className="text-left sm:text-right">
              <span className="text-xs text-slate-400">Confidence Score</span>
              <p className="text-3xl font-extrabold text-cyan-400">{confidencePct}%</p>
            </div>
          </div>

          {/* Telemetry Pills */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold flex items-center gap-1">
                <Clock className="w-3 h-3" /> Latency
              </span>
              <p className="text-sm font-bold text-slate-200 mt-1">{result.processing_time_ms ?? '—'} ms</p>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold flex items-center gap-1">
                <Cpu className="w-3 h-3" /> Model
              </span>
              <p className="text-xs font-bold text-slate-200 mt-1 truncate">{result.model || 'EfficientNet-B4'}</p>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold flex items-center gap-1">
                <Layers className="w-3 h-3" /> Modality
              </span>
              <p className="text-sm font-bold text-slate-200 mt-1 uppercase">{mediaType}</p>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold flex items-center gap-1">
                <FileCheck className="w-3 h-3" /> Status
              </span>
              <p className="text-sm font-bold text-emerald-400 mt-1">Archived in DB</p>
            </div>
          </div>

          {result.note && (
            <div className="p-3.5 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-200">
              {result.note}
            </div>
          )}

          {/* Visual Grad-CAM Heatmap Comparison */}
          {result.heatmap_b64 && (
            <div className="pt-2 border-t border-slate-800/80">
              <h4 className="text-sm font-semibold text-white mb-1">Grad-CAM Attention Heatmap</h4>
              <p className="text-xs text-slate-400 mb-4">
                Red highlighted zones indicate features where the CNN backbone detected neural blending or frequency artifacts.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {preview && (
                  <div>
                    <span className="text-xs text-slate-500 mb-1 block font-medium">Original Input</span>
                    <img src={preview} alt="Original" className="w-full h-56 object-cover rounded-xl border border-slate-800 bg-black" />
                  </div>
                )}
                <div>
                  <span className="text-xs text-slate-500 mb-1 block font-medium">Neural Activation Overlay</span>
                  <img
                    src={`data:image/jpeg;base64,${result.heatmap_b64}`}
                    alt="Grad-CAM Heatmap"
                    className="w-full h-56 object-cover rounded-xl border border-slate-800 bg-black"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
            <button
              onClick={() => { setFile(null); setResult(null); setPreview(null) }}
              className="text-xs text-slate-400 hover:text-white transition-colors"
            >
              ← Analyze another file
            </button>
            <Link
              to="/history"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
            >
              View in Audit History <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
