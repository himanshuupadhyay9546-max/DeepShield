import React from 'react'

export type DetectionResult = {
  label: string
  confidence?: number
  video_confidence?: number
  frames_analyzed?: number
  face_detection?: boolean
  heatmap_b64?: string
  model?: string
  note?: string
  eff_score?: number
  vit_score?: number
}

export default function ResultCard({ result }: { result: DetectionResult }) {
  const isInconclusive = result.label === 'INCONCLUSIVE'
  const isFake = result.label === 'FAKE'

  const rawConf = result.confidence ?? result.video_confidence ?? 0
  const confidence = (rawConf * 100).toFixed(2)

  const cardClass = isInconclusive
    ? 'bg-yellow-950 border-yellow-700'
    : isFake
    ? 'bg-red-950 border-red-800'
    : 'bg-green-950 border-green-800'

  const labelClass = isInconclusive
    ? 'text-yellow-400'
    : isFake
    ? 'text-red-400'
    : 'text-green-400'

  return (
    <div className="space-y-4">
      <div className={`p-5 rounded-xl border ${cardClass}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wide">Verdict</p>
            <p className={`text-3xl font-bold mt-1 ${labelClass}`}>{result.label}</p>
          </div>
          {!isInconclusive && (
            <div className="text-right">
              <p className="text-xs text-slate-400 uppercase tracking-wide">Confidence</p>
              <p className="text-2xl font-bold mt-1">{confidence}%</p>
            </div>
          )}
        </div>

        {/* Note (inconclusive explanation or audio not trained) */}
        {result.note && (
          <p className={`text-sm mt-3 ${isInconclusive ? 'text-yellow-400' : 'text-yellow-500'}`}>
            {result.note}
          </p>
        )}

        {/* Ensemble breakdown */}
        {result.eff_score != null && result.vit_score != null && (
          <div className="mt-3 flex gap-4 text-xs text-slate-400">
            <span>EfficientNet: <span className="text-white">{(result.eff_score * 100).toFixed(1)}% fake</span></span>
            <span>ViT: <span className="text-white">{(result.vit_score * 100).toFixed(1)}% fake</span></span>
          </div>
        )}

        {/* Video-specific info */}
        {result.frames_analyzed != null && (
          <div className="mt-2 flex gap-4 text-xs text-slate-400">
            <span>Frames: <span className="text-white">{result.frames_analyzed}</span></span>
            {result.face_detection != null && (
              <span>Face detection: <span className="text-white">{result.face_detection ? 'MTCNN ✓' : 'off'}</span></span>
            )}
          </div>
        )}

        {result.model && (
          <p className="text-slate-600 text-xs mt-2">Model: {result.model}</p>
        )}
      </div>

      {/* Grad-CAM heatmap */}
      {result.heatmap_b64 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-sm text-slate-400 mb-3">Grad-CAM Attention Heatmap</p>
          <img
            src={`data:image/jpeg;base64,${result.heatmap_b64}`}
            alt="heatmap"
            className="rounded-lg w-full max-h-64 object-contain"
          />
          <p className="text-slate-600 text-xs mt-2">
            Red/yellow = regions the model focused on most
          </p>
        </div>
      )}
    </div>
  )
}
