import os, cv2
from torch.utils.data import Dataset
import torch

class FaceForensicsDataset(Dataset):
    def __init__(self, root="/data/FaceForensics++", split="train", transform=None):
        self.samples = []
        # Support real/fake folders
        for label, folder in enumerate(["real", "fake"]):
            path = os.path.join(root, split, folder)
            if os.path.exists(path):
                for f in os.listdir(path)[:5000]:
                    self.samples.append((os.path.join(path,f), label))
    
    def __len__(self): return len(self.samples)
    
    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(path)
        img = cv2.resize(img, (224,224))
        img = torch.from_numpy(img).permute(2,0,1).float()/255.0
        return img, torch.tensor(label, dtype=torch.float32)
