"""
Audio deepfake training — ASVspoof 2019 LA subset.

Dataset layout expected:
  data/asvspoof2019/
    LA/
      ASVspoof2019_LA_train/
        flac/  *.flac
      ASVspoof2019_LA_cm_protocols/
        ASVspoof2019.LA.cm.train.trn.txt

Run:
  python ml/training/train_audio.py
"""

import os, sys
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import librosa
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from ml.models.audio_model import AudioDeepShieldModel


SR = 16000
DURATION = 4.0
N_MELS = 128
TARGET_LEN = int(SR * DURATION)
DATA_ROOT = "data/asvspoof2019/LA"
OUT_PATH = "backend/models/deepshield_audio.pth"


class ASVspoofDataset(Dataset):
    def __init__(self, protocol_file, audio_dir):
        self.samples = []
        with open(protocol_file) as f:
            for line in f:
                parts = line.strip().split()
                # format: speaker_id file_id - system_id label
                file_id, label = parts[1], parts[-1]
                self.samples.append((os.path.join(audio_dir, file_id + ".flac"), int(label == "spoof")))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        wave, _ = librosa.load(path, sr=SR, mono=True, duration=DURATION)
        if len(wave) < TARGET_LEN:
            wave = np.pad(wave, (0, TARGET_LEN - len(wave)))
        else:
            wave = wave[:TARGET_LEN]

        mel = librosa.feature.melspectrogram(y=wave, sr=SR, n_mels=N_MELS, fmax=8000)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        mel_img = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
        mel_img = torch.tensor(mel_img, dtype=torch.float32).unsqueeze(0)
        # resize to 128×128
        mel_img = torch.nn.functional.interpolate(mel_img.unsqueeze(0), size=(128, 128)).squeeze(0)

        wave_t = torch.tensor(wave, dtype=torch.float32)
        return mel_img, wave_t, torch.tensor(label, dtype=torch.float32)


def get_device():
    if torch.cuda.is_available(): return torch.device("cuda")
    if torch.backends.mps.is_available(): return torch.device("mps")
    return torch.device("cpu")


def train():
    device = get_device()
    print(f"Device: {device}")

    train_proto = os.path.join(DATA_ROOT, "ASVspoof2019_LA_cm_protocols/ASVspoof2019.LA.cm.train.trn.txt")
    train_audio = os.path.join(DATA_ROOT, "ASVspoof2019_LA_train/flac")

    if not os.path.exists(train_proto):
        print(f"Dataset not found at {DATA_ROOT}")
        print("Download ASVspoof2019 from: https://datashare.ed.ac.uk/handle/10283/3336")
        return

    ds = ASVspoofDataset(train_proto, train_audio)
    loader = DataLoader(ds, batch_size=32, shuffle=True, num_workers=0)

    model = AudioDeepShieldModel().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()

    best_loss = float("inf")
    for epoch in range(10):
        model.train()
        total_loss, correct, n = 0, 0, 0
        for mel, wave, labels in tqdm(loader, desc=f"Epoch {epoch+1}/10"):
            mel, wave, labels = mel.to(device), wave.to(device), labels.to(device)
            opt.zero_grad()
            logits = model(mel, wave)
            loss = criterion(logits, labels)
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(labels)
            correct += ((logits.sigmoid() > 0.5) == labels.bool()).sum().item()
            n += len(labels)

        avg_loss = total_loss / n
        acc = correct / n * 100
        print(f"Epoch {epoch+1}: loss={avg_loss:.4f}  acc={acc:.1f}%")

        if avg_loss < best_loss:
            best_loss = avg_loss
            os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
            torch.save(model.state_dict(), OUT_PATH)
            print(f"  -> saved to {OUT_PATH}")

    print("Done.")


if __name__ == "__main__":
    train()
