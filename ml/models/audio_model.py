import torch
import torch.nn as nn
from efficientnet_pytorch import EfficientNet


class AudioDeepShieldModel(nn.Module):
    """
    Mel spectrogram → EfficientNet-B0 backbone
    Raw waveform   → FFT branch
    Fuse → classifier
    """
    def __init__(self):
        super().__init__()
        # B0 outputs 1280-dim; swap fc for identity
        self.backbone = EfficientNet.from_pretrained('efficientnet-b0')
        self.backbone._fc = nn.Identity()
        # 1-channel mel → repeat to 3 channels in forward

        # FFT branch on raw waveform (1D)
        self.fft_branch = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=64, stride=16),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=32, stride=8),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.fft_fc = nn.Linear(64, 128)

        self.classifier = nn.Sequential(
            nn.Linear(1280 + 128, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
        )

    def forward(self, mel, wave):
        # mel:  [B, 1, 128, 128] → repeat to [B, 3, 128, 128]
        x = mel.repeat(1, 3, 1, 1)
        spec_feat = self.backbone.extract_features(x)
        spec_feat = nn.functional.adaptive_avg_pool2d(spec_feat, 1).flatten(1)

        # FFT on raw waveform
        fft = torch.fft.rfft(wave, dim=-1)
        mag = torch.log1p(fft.abs()).unsqueeze(1)   # [B, 1, T]
        freq_feat = self.fft_fc(self.fft_branch(mag).squeeze(-1))

        return self.classifier(torch.cat([spec_feat, freq_feat], dim=1)).squeeze(1)
