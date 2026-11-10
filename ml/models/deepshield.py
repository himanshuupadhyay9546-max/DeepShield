import torch
import torch.nn as nn
from efficientnet_pytorch import EfficientNet
from .cbam import CBAM
from .fft_branch import FFTBranch

class DeepShieldModel(nn.Module):
    def __init__(self, num_classes=1):
        super().__init__()
        # Spatial Branch - EfficientNet-B4 Backbone
        self.backbone = EfficientNet.from_pretrained('efficientnet-b4')
        self.backbone._fc = nn.Identity()  # 1792-dim features
        
        # Frequency Branch
        self.fft_branch = FFTBranch()
        
        # CBAM Attention
        self.cbam = CBAM(1792)
        
        # Feature Fusion
        self.fusion = nn.Sequential(
            nn.Linear(1792 + 128, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        self.classifier = nn.Linear(512, num_classes)
    
    def forward(self, x):
        # Spatial features
        features = self.backbone.extract_features(x)  # [B,1792,7,7]
        features = self.cbam(features)
        spatial = torch.nn.functional.adaptive_avg_pool2d(features, 1).flatten(1)  # [B,1792]
        
        # Frequency features
        freq = self.fft_branch(x)  # [B,128]
        
        # Fuse
        fused = torch.cat([spatial, freq], dim=1)
        fused = self.fusion(fused)
        out = self.classifier(fused)
        return out.squeeze(1)
