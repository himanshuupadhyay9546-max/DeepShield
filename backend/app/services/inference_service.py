"""
Deepfake inference service — two swappable backends.

Switch in .env:
    MODEL_BACKEND=efficientnet   # custom EfficientNet-B4 + FFT + CBAM
    MODEL_BACKEND=vit            # ViT-base fine-tuned on real deepfakes (HuggingFace)
"""

import base64
import os
import sys
import tempfile
import uuid
import cv2
import numpy as np
import torch
from PIL import Image

from app.core.config import settings

_current_dir = os.path.dirname(__file__)
_repo_root = os.path.abspath(os.path.join(_current_dir, "../../../"))
_backend_root = os.path.abspath(os.path.join(_current_dir, "../../"))
for p in [_repo_root, _backend_root, os.path.abspath(os.path.join(_current_dir, "../.."))]:
    if p not in sys.path:
        sys.path.insert(0, p)

def _find_model_path(filename: str) -> str:
    candidates = [
        os.path.join(_backend_root, "models", filename),
        os.path.join(_repo_root, "backend", "models", filename),
        os.path.join(_repo_root, "models", filename),
        os.path.join("/app/backend/models", filename),
        os.path.join("/app/models", filename),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def _get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ── EfficientNet backend ──────────────────────────────────────────────────────

class _EfficientNetBackend:
    """
    Custom EfficientNet-B4 + FFT branch + CBAM attention.
    Loads weights from backend/models/deepshield_b4.pth.
    NOTE: currently trained on StyleGAN2 faces (not real face-swap deepfakes).
    """

    _MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    _STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __init__(self):
        from ml.models.deepshield import DeepShieldModel
        from ml.inference.gradcam import generate_gradcam
        self._gradcam = generate_gradcam

        self.device = _get_device()
        self.model  = DeepShieldModel().to(self.device).eval()

        model_path = _find_model_path("deepshield_b4.pth")
        if os.path.exists(model_path):
            state = torch.load(model_path, map_location=self.device)
            state = {k.replace("module.", ""): v for k, v in state.items()}
            self.model.load_state_dict(state)
            print(f"[EfficientNet] Loaded weights from {model_path}")
        else:
            print("[EfficientNet] No checkpoint — using random weights")

    def _preprocess(self, bgr: np.ndarray) -> torch.Tensor:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (224, 224)).astype(np.float32) / 255.0
        rgb = (rgb - self._MEAN) / self._STD
        return torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)

    def predict_image(self, path: str) -> dict:
        bgr = cv2.imread(path)
        if bgr is None:
            raise ValueError(f"Cannot read image: {path}")
        tensor = self._preprocess(bgr).to(self.device)

        with torch.no_grad():
            pred = torch.sigmoid(self.model(tensor)).item()

        label = "FAKE" if pred > 0.5 else "REAL"
        # confidence = how sure the model is about the verdict (always 0–1)
        confidence = pred if label == "FAKE" else 1.0 - pred
        heatmap_path = self._gradcam(self.model, tensor, path)
        heatmap_b64  = _read_and_delete_b64(heatmap_path)

        return {
            "label":       label,
            "confidence":  round(confidence, 4),
            "heatmap_b64": heatmap_b64,
            "model":       "EfficientNet-B4 + FFT + CBAM",
        }

    def predict_video(self, path: str) -> dict:
        return _generic_video(self, path)

    def predict_audio(self, path: str) -> dict:
        return _predict_audio(path)


# ── ViT backend ───────────────────────────────────────────────────────────────

class _ViTBackend:
    """
    ViT-base-patch16 fine-tuned on real deepfake data.
    HuggingFace: dima806/deepfake_vs_real_image_detection
    Downloads ~340 MB on first use, cached at ~/.cache/huggingface.
    """

    _HF_MODEL = "dima806/deepfake_vs_real_image_detection"

    def __init__(self):
        from transformers import ViTForImageClassification, ViTImageProcessor

        self.device    = _get_device()
        self.processor = ViTImageProcessor.from_pretrained(self._HF_MODEL)
        self.model     = ViTForImageClassification.from_pretrained(
            self._HF_MODEL, attn_implementation="eager"
        ).to(self.device).eval()
        self.id2label  = self.model.config.id2label
        print(f"[ViT] Ready on {self.device}. Labels: {self.id2label}")

    def predict_image(self, path: str) -> dict:
        bgr = cv2.imread(path)
        if bgr is None:
            raise ValueError(f"Cannot read image: {path}")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)

        inputs = self.processor(images=pil, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)

        probs     = torch.softmax(outputs.logits[0], dim=-1)
        pred_idx  = probs.argmax().item()
        raw_label = self.id2label[pred_idx]
        label     = "FAKE" if "fake" in raw_label.lower() else "REAL"
        confidence = probs[pred_idx].item()

        heatmap_b64 = self._attention_heatmap(outputs.attentions, rgb)

        return {
            "label":       label,
            "confidence":  round(float(confidence), 4),
            "heatmap_b64": heatmap_b64,
            "model":       "ViT-base-patch16 (deepfake-tuned)",
        }

    def predict_video(self, path: str) -> dict:
        return _generic_video(self, path)

    def predict_audio(self, path: str) -> dict:
        return _predict_audio(path)

    def _attention_heatmap(self, attentions, orig_rgb: np.ndarray) -> str:
        last     = attentions[-1][0].mean(dim=0)
        cls_attn = last[0, 1:].detach().cpu().float().numpy()
        size     = int(cls_attn.shape[0] ** 0.5)
        attn_map = cv2.resize(cls_attn.reshape(size, size), (224, 224))
        attn_map = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-8)
        heatmap  = cv2.applyColorMap(np.uint8(255 * attn_map), cv2.COLORMAP_JET)
        base     = cv2.resize(cv2.cvtColor(orig_rgb, cv2.COLOR_RGB2BGR), (224, 224))
        overlay  = cv2.addWeighted(base, 0.6, heatmap, 0.4, 0)
        _, buf   = cv2.imencode(".jpg", overlay)
        return base64.b64encode(buf).decode()


# ── shared helpers ────────────────────────────────────────────────────────────

def _read_and_delete_b64(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    os.remove(path)
    return data


def _generic_video(backend, path: str) -> dict:
    """Sample every 5th frame, optionally crop face with MTCNN, run image model."""
    try:
        from facenet_pytorch import MTCNN
        mtcnn = MTCNN(image_size=224, margin=20, keep_all=False, post_process=False)
        use_mtcnn = True
    except ImportError:
        mtcnn = None
        use_mtcnn = False

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {path}")

    scores, count = [], 0
    while len(scores) < 20:  # max 20 sampled frames
        ret, frame = cap.read()
        if not ret:
            break
        if count % 5 != 0:
            count += 1
            continue

        tmp = os.path.join(tempfile.gettempdir(), f"frame_{uuid.uuid4()}_{count}.jpg")
        try:
            if use_mtcnn:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb)
                face = mtcnn(pil)  # returns tensor or None
                if face is not None:
                    face_np = face.permute(1, 2, 0).numpy().astype(np.uint8)
                    cv2.imwrite(tmp, cv2.cvtColor(face_np, cv2.COLOR_RGB2BGR))
                else:
                    cv2.imwrite(tmp, frame)
            else:
                cv2.imwrite(tmp, frame)

            res = backend.predict_image(tmp)
            conf = res["confidence"] if res["label"] == "FAKE" else 1 - res["confidence"]
            scores.append(conf)
        except Exception:
            pass
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        count += 1

    cap.release()
    avg = float(np.mean(scores)) if scores else 0.5
    return {
        "label": "FAKE" if avg > 0.5 else "REAL",
        "video_confidence": avg,
        "frames_analyzed": len(scores),
        "face_detection": use_mtcnn,
    }


def _predict_audio(path: str) -> dict:
    """EfficientNet-B0 + FFT on mel spectrogram. Falls back to stub if model not found."""
    import librosa
    import uuid

    model_path = _find_model_path("deepshield_audio.pth")

    # Load audio
    wave, sr = librosa.load(path, sr=16000, mono=True, duration=4.0)
    # Pad/trim to 4s
    target = 16000 * 4
    if len(wave) < target:
        wave = np.pad(wave, (0, target - len(wave)))
    else:
        wave = wave[:target]

    # Mel spectrogram 128×128
    mel = librosa.feature.melspectrogram(y=wave, sr=sr, n_mels=128, fmax=8000)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    mel_img = cv2.resize(mel_db, (128, 128))
    mel_img = (mel_img - mel_img.min()) / (mel_img.max() - mel_img.min() + 1e-8)

    if not os.path.exists(model_path):
        # Stub: no trained weights yet
        return {"label": "UNKNOWN", "confidence": 0.5, "note": "Audio model not trained yet — run ml/training/train_audio.py"}

    from ml.models.audio_model import AudioDeepShieldModel
    device = _get_device()
    model = AudioDeepShieldModel().to(device).eval()
    state = torch.load(model_path, map_location=device)
    model.load_state_dict({k.replace("module.", ""): v for k, v in state.items()})

    mel_t  = torch.tensor(mel_img, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
    wave_t = torch.tensor(wave, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        logit = model(mel_t, wave_t).item()
    prob = float(torch.sigmoid(torch.tensor(logit)))
    return {"label": "FAKE" if prob > 0.5 else "REAL", "confidence": prob, "type": "audio"}


# ── public facade ─────────────────────────────────────────────────────────────

class DeepShieldService:
    def __init__(self):
        backend = settings.MODEL_BACKEND.lower()
        print(f"[DeepShield] Backend: {backend}")
        if backend == "vit":
            self._backend = _ViTBackend()
        else:
            self._backend = _EfficientNetBackend()

    def predict_image(self, path: str) -> dict:
        return self._backend.predict_image(path)

    def predict_video(self, path: str) -> dict:
        return self._backend.predict_video(path)

    def predict_audio(self, path: str) -> dict:
        return self._backend.predict_audio(path)
