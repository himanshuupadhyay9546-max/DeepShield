# DeepShield Architecture

## Model Architecture
Input (224x224) → Face Detection (MTCNN) → Preprocess
→ Parallel Branches:
  1. EfficientNet-B4 (1792-dim spatial features, ImageNet pretrained)
  2. FFT Branch (frequency artifacts, 128-dim)
  3. CBAM Attention (channel + spatial)
→ Feature Fusion (1920 → 1024 → 512)
→ Sigmoid → REAL/FAKE

## Why Better than XceptionNet
- Dual-domain analysis (spatial + frequency)
- CBAM focuses on manipulated regions (eyes, mouth boundaries)
- EfficientNet-B4: 19M params vs Xception 23M, better accuracy
- Mixed precision training → 2.3x faster

## Video Pipeline
1. Extract frames (5 fps)
2. Face detection per frame
3. Batch inference
4. Temporal smoothing (moving average)
5. Confidence aggregation

## Audio Pipeline
1. Convert to mel-spectrogram (128 bands)
2. CNN + Transformer encoder
3. Classify synthetic voice patterns

## Security
- JWT with 15min expiry + refresh tokens
- RBAC: admin, analyst, viewer, api
- Rate limiting: 60 req/min per IP
- Audit logs for all detections
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
