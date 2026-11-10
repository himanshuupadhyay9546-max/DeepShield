# DeepShield API

## Auth
POST /api/v1/auth/register
POST /api/v1/auth/login → {access_token}

## Detection
POST /api/v1/detect/image (multipart)
POST /api/v1/detect/video
POST /api/v1/detect/audio
GET /api/v1/detect/history

Response:
{
  "label": "FAKE",
  "confidence": 0.973,
  "heatmap": "/results/abc_heatmap.jpg",
  "model": "EfficientNet-B4+FFT+CBAM",
  "processing_time_ms": 142
}
