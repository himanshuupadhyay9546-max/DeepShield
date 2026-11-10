import torch
import torch.nn as nn
import torch.nn.functional as F

class FFTBranch(nn.Module):
    """Extracts GAN-specific artifacts from frequency domain"""
    def __init__(self, in_channels=3):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.fc = nn.Linear(64, 128)
    
    def forward(self, x):
        # x: [B,3,224,224]
        # torch.fft.fft2 is not supported on MPS — run on CPU, return to original device
        dev = x.device
        fft = torch.fft.fft2(x.cpu(), dim=(-2, -1))
        mag = torch.log1p(torch.abs(fft)).to(dev)
        mag = (mag - mag.mean()) / (mag.std() + 1e-6)
        feat = self.conv(mag)
        feat = feat.view(feat.size(0), -1)
        return self.fc(feat)  # [B,128]
