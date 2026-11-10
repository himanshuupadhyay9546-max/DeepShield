import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from PIL import Image


class DeepfakeDataset(Dataset):
    """
    Expects folder layout:
      <root>/<split>/real/*.jpg
      <root>/<split>/fake/*.jpg
    Label: 0 = real, 1 = fake
    """

    def __init__(self, root, split="train", max_per_class=None, transform=None):
        self.transform = transform
        self.samples = []

        for label, folder in enumerate(["real", "fake"]):
            path = os.path.join(root, split, folder)
            if not os.path.isdir(path):
                raise FileNotFoundError(
                    f"Expected folder not found: {path}\n"
                    "Run:  python ml/datasets/download.py"
                )
            files = sorted(
                f for f in os.listdir(path)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            )
            if max_per_class:
                files = files[:max_per_class]
            for f in files:
                self.samples.append((os.path.join(path, f), float(label)))

        real_n = sum(1 for _, l in self.samples if l == 0)
        fake_n = sum(1 for _, l in self.samples if l == 1)
        print(f"  [{split}] {real_n} real + {fake_n} fake = {len(self.samples)} total")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]

        img = cv2.imread(path)
        if img is None:
            img = np.zeros((224, 224, 3), dtype=np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        pil = Image.fromarray(img)
        if self.transform:
            tensor = self.transform(pil)
        else:
            arr = np.array(pil.resize((224, 224))).astype(np.float32) / 255.0
            tensor = torch.from_numpy(arr).permute(2, 0, 1)

        return tensor, torch.tensor(label)
