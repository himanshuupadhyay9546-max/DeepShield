# How DeepShield Works

A plain-English explanation of everything under the hood — the models, how they detect deepfakes, the datasets they were trained on, and how the pieces connect.

---

## What the app does

DeepShield takes an image, video, or audio file and tells you whether it is **REAL**, **FAKE**, or **INCONCLUSIVE**. It runs two AI models simultaneously, combines their scores, and refuses to give a verdict when it isn't confident enough.

---

## The three detection modes

### Image detection

The most capable mode. Two models analyze the same image independently, then their scores are merged.

### Video detection

The video is read frame by frame. Every 5th frame is extracted (so for a 25fps video that's one frame per 5 frames ≈ up to 20 frames analyzed). Each frame is cropped to just the face using **MTCNN** (a face-detector), then the image model runs on that crop. The final verdict is the average fake-probability across all analyzed frames.

### Audio detection

Takes the first 4 seconds of audio. Converts it to a **mel spectrogram** (a picture of sound) and runs an EfficientNet model on that picture, combined with a raw waveform analysis. The audio model requires separate training (see below) — without trained weights the app returns `UNKNOWN`.

---

## The two image models

### Model 1 — Custom EfficientNet-B4

This is the model trained specifically for DeepShield. It has three parts that work in parallel:

```
Input image (224×224 pixels)
        │
        ├──► EfficientNet-B4 backbone
        │         CNN pretrained on ImageNet (1.2M images)
        │         Extracts 1792 visual features (textures, edges, blending artifacts)
        │         + CBAM attention on top (focuses on face regions)
        │
        └──► FFT Branch
                  Converts image to frequency domain
                  Extracts 128 frequency features
                  (GAN artifacts show up here as repeating patterns)

1792 spatial features + 128 frequency features
        │
        └──► Fusion MLP → single number 0–1 (0=real, 1=fake)
```

**Why EfficientNet?**
EfficientNet-B4 was chosen because it's accurate but not huge — it runs on a laptop GPU (or Apple Silicon) in under a second. It was originally trained on ImageNet for general image classification, then fine-tuned to detect deepfakes.

**Why the FFT branch?**
GAN-generated images (StyleGAN, Midjourney, DALL-E etc) leave repeating artifacts in the frequency domain that are completely invisible to the human eye. A standard CNN only looks at pixels — FFT makes these artifacts visible. Running both together makes the model much harder to fool.

**What is CBAM?**
CBAM (Convolutional Block Attention Module) is added on top of EfficientNet. It learns two things:
- *Channel attention* — which feature maps matter most (e.g. face texture vs background)
- *Spatial attention* — which spatial regions of the image to focus on (usually the face itself)

This helps the model ignore irrelevant parts of the image like backgrounds or clothing.

**What is Grad-CAM?**
After the model makes a prediction, Grad-CAM (Gradient-weighted Class Activation Mapping) generates the heatmap overlay you see in the result. It works by looking at which pixels most strongly activated the "fake" signal and draws them in red/yellow. It does not affect the verdict — it's purely visual explanation.

---

### Model 2 — ViT (Vision Transformer)

This is a pre-trained model from HuggingFace, not trained by DeepShield:

- **Model ID:** `dima806/deepfake_vs_real_image_detection`
- **Architecture:** ViT-base-patch16 (Vision Transformer)
- **Size:** ~340 MB, downloaded automatically on first run
- **What it was trained on:** a curated deepfake detection dataset from HuggingFace Hub

**How ViT works differently from CNN:**
A CNN looks at small patches of pixels locally. A Vision Transformer divides the image into 16×16 patches and uses self-attention to look at relationships between ALL patches at once. This makes it better at catching subtle global inconsistencies (like lighting mismatches across the face) that a CNN might miss.

**Attention heatmap for ViT:**
Instead of Grad-CAM, ViT generates an attention heatmap from the last transformer layer's attention weights. It shows which patches the model paid attention to when making its decision.

---

## How the two models are combined (Ensemble)

The default mode (`MODEL_BACKEND=ensemble`) runs both models and combines them:

```
EfficientNet fake-probability × 0.55
+
ViT fake-probability × 0.45
= combined fake-probability
```

EfficientNet gets slightly more weight (0.55) because it was trained specifically on the GAN-artifact detection task that this app focuses on. ViT gets 0.45 because it's better on face-swaps and acts as a second opinion.

**Why not just use one model?**

The two models fail in different ways:
- EfficientNet is very good at StyleGAN faces but sometimes aggressive on real photos with unusual lighting
- ViT is more conservative and rarely calls a real photo fake, but may miss some GAN artifacts

When they agree, the combined score is very high confidence. When they disagree, the score stays near 50% and triggers the INCONCLUSIVE verdict. This is intentional — the system admits it doesn't know rather than guessing wrong.

**The INCONCLUSIVE threshold:**
If the final confidence is below **65%**, the verdict is changed to `INCONCLUSIVE` with an explanation. From testing on 10 sample images:
- 8/10 gave confident REAL or FAKE verdicts (all correct)
- 2/10 returned INCONCLUSIVE (both were cases where the two models sharply disagreed — better to admit uncertainty than commit to a wrong answer)

---

## Dataset used for training EfficientNet

**140k Real and Fake Faces**
- Source: Kaggle — `xhlulu/140k-real-and-fake-faces`
- Real images: ~70,000 photos of real people sourced from Flickr
- Fake images: ~70,000 faces generated by **StyleGAN2** (NVIDIA's GAN)
- Image resolution: 256×256, resized to 224×224 during training
- Split: 80% train / 20% validation

**Training strategy (two phases):**

*Phase 1 — 5 epochs, backbone frozen:*
Only the FFT branch, CBAM, and the classifier head are trained. The EfficientNet backbone weights stay frozen. This is fast and teaches the new layers what to do before the backbone is touched.

*Phase 2 — 5 epochs, partial unfreeze:*
The last 3 blocks of EfficientNet are unfrozen with a very low learning rate (0.00003) so they adapt slightly without forgetting ImageNet knowledge. The rest of the network trains at 0.0003.

**Data augmentation used during training:**
- Random crop (80–100% of image)
- Random horizontal flip
- Color jitter (brightness ±20%, contrast ±20%, saturation ±20%, hue ±5%)
- 2% chance of random grayscale
- ImageNet normalization

**Important limitation:**
The EfficientNet model was trained on StyleGAN2-generated faces only. It is very good at detecting AI-generated faces (Midjourney, StyleGAN, DALL-E) but may not reliably catch face-swap deepfakes (like the Tom Cruise TikTok ones created with FaceSwap or DeepFaceLab). For face-swap detection, the ViT model or retraining on **FaceForensics++** is recommended.

---

## Dataset used for audio model

**ASVspoof 2019 — Logical Access (LA) subset**
- Source: University of Edinburgh — `datashare.ed.ac.uk/handle/10283/3336`
- Real audio: recordings of real human speakers
- Fake audio: generated by 17 different text-to-speech and voice conversion systems
- Format: FLAC, 16kHz mono

The audio model architecture is the same idea as the image model:
- Mel spectrogram → EfficientNet-B0 → 1280 features (treats sound as an image)
- Raw waveform → 1D FFT → Conv1D layers → 128 features
- Combined → binary classifier (real/fake)

The audio model requires separate training. Without `backend/models/deepshield_audio.pth`, the audio endpoint returns `UNKNOWN`.

---

## ViT model dataset

The HuggingFace model `dima806/deepfake_vs_real_image_detection` was trained on a mixed dataset of real and AI-generated/deepfake images from HuggingFace Hub, including face-swap deepfakes. This is why it catches some cases that the EfficientNet model misses — it has seen a broader variety of manipulation techniques.

---

## What happens step by step when you upload an image

1. Frontend sends the image as `multipart/form-data` to `POST /api/v1/detect/image`
2. Backend saves it to a temp file (`/tmp/...`)
3. `DeepShieldService.predict_image()` is called
4. **EfficientNet path:**
   - Image is resized to 224×224 and normalized with ImageNet stats
   - Run through EfficientNet-B4 backbone → 1792 spatial features
   - Same image run through FFT branch → 128 frequency features
   - Features fused → single sigmoid output (0 = real, 1 = fake)
   - Grad-CAM hook generates heatmap
5. **ViT path:**
   - Image loaded as PIL, processed through ViT processor (patch tokenization)
   - Run through ViT transformer → softmax over [Real, Fake] → probability
   - Attention weights from last layer generate attention heatmap
6. **Ensemble combination:**
   - Both fake-probabilities combined: `0.55 × eff_fp + 0.45 × vit_fp`
   - If combined confidence < 65% → label changed to INCONCLUSIVE
7. Response JSON sent back with: `label`, `confidence`, `eff_score`, `vit_score`, `model`, `heatmap_b64`, (optionally `note` for INCONCLUSIVE)
8. Frontend `ResultCard` component renders the verdict card, scores breakdown, and Grad-CAM heatmap

---

## Switching models

The active backend is controlled by the `.env` file in the project root:

```
MODEL_BACKEND=ensemble     # recommended — best accuracy
MODEL_BACKEND=efficientnet # only the custom EfficientNet model
MODEL_BACKEND=vit          # only the ViT model (no .pth file needed)
```

After changing `.env`, restart the backend:
```bash
# Mac
pkill -f "uvicorn app.main:app"
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Windows
taskkill /F /IM python.exe
cd backend && venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

---

## Model accuracy summary (tested on 10 sample images)

| Image type | EfficientNet | ViT | Ensemble |
|---|---|---|---|
| Real celebrity photos | REAL ✅ | REAL ✅ | REAL ✅ |
| StyleGAN faces (obvious) | FAKE ✅ | FAKE ✅ | FAKE ✅ |
| StyleGAN faces (borderline) | FAKE (overconfident) | REAL (unsure) | INCONCLUSIVE ✅ |
| AI-generated (ThisPersonDoesNotExist) | FAKE ✅ | FAKE ✅ | FAKE ✅ |

The `INCONCLUSIVE` outcome on borderline cases is the correct behavior — it is better to say "I'm not sure" than to randomly pick the wrong answer.

---

## Windows-specific fixes applied

These issues were found and fixed during development on Windows. They are already in the code — this section explains what was fixed and why, so you know what to do if you hit them again.

### `ModuleNotFoundError: No module named 'ml'`

**What happened:** When running the backend on Windows, Python couldn't find the `ml/` package even though it exists in the repo.

**Why:** The `ml/` folder sits at the repo root, one level above `backend/`. On Mac/Linux, running uvicorn from `backend/` with `--reload-dir ../ml` keeps the parent on the path. Windows Python does not automatically add the repo root, so `import ml.models.deepshield` fails.

**Fix applied:** Both `backend/app/main.py` and `backend/app/services/inference_service.py` now do this at the top:
```python
import os, sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
```
This finds the repo root at runtime and adds it to `sys.path` before any `ml` imports happen.

---

### `RuntimeError: Unsupported type byte size: ComplexFloat` (Apple Silicon MPS)

**What happened:** When running on a Mac with Apple Silicon (M1/M2/M3), the FFT branch crashed because MPS (Metal Performance Shaders) does not support complex float tensors.

**Why:** `torch.fft.fft2()` returns complex numbers. MPS can't handle complex dtype, so any operation on the result on the MPS device throws this error.

**Fix applied:** `ml/models/fft_branch.py` now runs FFT on CPU explicitly and moves the result back to the original device:
```python
def forward(self, x):
    dev = x.device
    fft = torch.fft.fft2(x.cpu(), dim=(-2, -1))   # force CPU
    mag = torch.log1p(torch.abs(fft)).to(dev)       # back to MPS/CUDA
    ...
```

---

### `module 'bcrypt' has no attribute '__about__'` (passlib incompatibility)

**What happened:** The auth system used `passlib` to hash passwords, but bcrypt 4.x removed the `__about__` attribute that passlib relies on. This caused a crash on any login or register attempt.

**Fix applied:** Replaced passlib entirely with direct `bcrypt` calls in `backend/app/core/security.py`:
```python
import bcrypt

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())
```

---

### Grad-CAM crash: `ComplexFloat` in numpy (Apple Silicon)

**What happened:** Grad-CAM tried to pass the gradient tensor directly to OpenCV/numpy. On MPS, gradient tensors can be complex-typed, and OpenCV does not accept complex arrays.

**Fix applied:** `ml/inference/gradcam.py` now strips the imaginary part before converting:
```python
def _to_real_numpy(t: torch.Tensor) -> np.ndarray:
    if t.is_complex():
        t = t.real
    return t.float().cpu().numpy()
```

---

## Key files

| File | What it does |
|---|---|
| `backend/app/services/inference_service.py` | Main detection service — all three backends, ensemble logic, confidence threshold |
| `ml/models/deepshield.py` | EfficientNet-B4 + FFT + CBAM model definition |
| `ml/models/fft_branch.py` | FFT frequency analysis branch |
| `ml/models/cbam.py` | Channel + Spatial attention module |
| `ml/models/audio_model.py` | Audio detection model (mel + waveform FFT) |
| `ml/inference/gradcam.py` | Grad-CAM heatmap generation |
| `ml/training/train.py` | Image model training script |
| `ml/training/train_audio.py` | Audio model training script |
| `ml/datasets/deepfake_dataset.py` | Dataset loader for training |
| `ml/datasets/download.py` | Downloads the Kaggle dataset |
| `backend/models/deepshield_b4.pth` | Trained EfficientNet weights (not in git) |
| `backend/models/deepshield_audio.pth` | Trained audio weights (requires training) |
| `.env` | `MODEL_BACKEND` setting |
