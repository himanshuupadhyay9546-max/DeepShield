import torch, torch.nn as nn
import librosa
import numpy as np

class AudioDeepfakeModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1,32,3), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32,64,3), nn.ReLU(), nn.AdaptiveAvgPool2d(1)
        )
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=64, nhead=4, batch_first=True),
            num_layers=2
        )
        self.fc = nn.Linear(64,1)
    
    def forward(self, x):
        x = self.cnn(x).flatten(1).unsqueeze(1)
        x = self.transformer(x)
        return self.fc(x[:,0])

def predict_audio(path):
    y, sr = librosa.load(path, sr=16000, duration=5)
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mel_db = librosa.power_to_db(mel)
    x = torch.tensor(mel_db).unsqueeze(0).unsqueeze(0).float()
    model = AudioDeepfakeModel().eval()
    with torch.no_grad():
        score = torch.sigmoid(model(x)).item()
    return {"label": "FAKE" if score>0.5 else "REAL", "confidence": score}
