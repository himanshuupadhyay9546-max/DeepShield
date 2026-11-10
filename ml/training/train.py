"""
DeepShield training — optimised for Apple Silicon MPS (1-2 hours).

Usage:
  cd /path/to/deepshield/backend
  venv/bin/python ../ml/training/train.py

Two-phase strategy:
  Phase 1 (5 epochs): backbone frozen  → trains CBAM + FFT + head fast
  Phase 2 (5 epochs): last 3 EfficientNet blocks unfrozen → fine-tune

On M2 Pro with 40k training images: ~50-70 min total.
"""

import os
import sys
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from tqdm import tqdm

# Resolve project root regardless of where the script is invoked from
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ml.models.deepshield import DeepShieldModel
from ml.datasets.deepfake_dataset import DeepfakeDataset

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR  = os.path.join(_ROOT, "data", "real-vs-fake")
CKPT_DIR  = os.path.join(_ROOT, "backend", "models")
CKPT_PATH = os.path.join(CKPT_DIR, "deepshield_b4.pth")

# ── Config ────────────────────────────────────────────────────────────────────
CFG = dict(
    batch_size      = 64,
    lr_head         = 3e-4,
    lr_backbone     = 3e-5,
    phase1_epochs   = 5,
    phase2_epochs   = 5,
    # cap per class — 20k real + 20k fake = 40k train images ≈ 60 min on M2
    max_train       = 20_000,
    max_val         = 5_000,
    weight_decay    = 1e-4,
    # MPS requires num_workers=0 (multiprocessing fork issue)
    num_workers     = 0,
)

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]


# ── Device ───────────────────────────────────────────────────────────────────
def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ── Transforms ───────────────────────────────────────────────────────────────
def train_tf():
    return transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05),
        transforms.RandomGrayscale(p=0.02),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def val_tf():
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


# ── Freeze / unfreeze ─────────────────────────────────────────────────────────
def freeze_backbone(model):
    for p in model.backbone.parameters():
        p.requires_grad = False


def unfreeze_last_blocks(model, n=3):
    blocks = list(model.backbone._blocks)
    for block in blocks[-n:]:
        for p in block.parameters():
            p.requires_grad = True
    for layer in (model.backbone._conv_head, model.backbone._bn1):
        for p in layer.parameters():
            p.requires_grad = True


# ── One epoch ────────────────────────────────────────────────────────────────
def run_epoch(model, loader, criterion, optimizer, device, train=True):
    model.train(train)
    total_loss = correct = total = 0

    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for x, y in tqdm(loader, desc="train" if train else " val ", leave=False):
            x, y = x.to(device), y.to(device)
            if train:
                optimizer.zero_grad()
            out  = model(x)
            loss = criterion(out, y)
            if train:
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * len(y)
            correct    += ((torch.sigmoid(out) > 0.5) == y.bool()).sum().item()
            total      += len(y)

    return total_loss / total, correct / total


# ── Main ─────────────────────────────────────────────────────────────────────
def train():
    device = get_device()
    print(f"\nDevice : {device}")
    print(f"Data   : {DATA_DIR}")
    print(f"Ckpt   : {CKPT_PATH}\n")

    os.makedirs(CKPT_DIR, exist_ok=True)

    print("Loading datasets …")
    train_ds = DeepfakeDataset(DATA_DIR, "train", max_per_class=CFG["max_train"], transform=train_tf())
    val_ds   = DeepfakeDataset(DATA_DIR, "valid", max_per_class=CFG["max_val"],   transform=val_tf())

    train_loader = DataLoader(train_ds, batch_size=CFG["batch_size"], shuffle=True,
                              num_workers=CFG["num_workers"], pin_memory=False)
    val_loader   = DataLoader(val_ds,   batch_size=CFG["batch_size"], shuffle=False,
                              num_workers=CFG["num_workers"], pin_memory=False)

    model     = DeepShieldModel().to(device)
    criterion = nn.BCEWithLogitsLoss()
    best_acc  = 0.0

    # ── Phase 1 ──────────────────────────────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"Phase 1 — head only  ({CFG['phase1_epochs']} epochs, backbone frozen)")
    print(f"{'─'*55}")
    freeze_backbone(model)
    opt1 = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=CFG["lr_head"], weight_decay=CFG["weight_decay"]
    )
    sched1 = torch.optim.lr_scheduler.CosineAnnealingLR(opt1, T_max=CFG["phase1_epochs"])

    for epoch in range(1, CFG["phase1_epochs"] + 1):
        t0 = time.time()
        tl, ta = run_epoch(model, train_loader, criterion, opt1, device, train=True)
        vl, va = run_epoch(model, val_loader,   criterion, opt1, device, train=False)
        sched1.step()
        flag = ""
        if va > best_acc:
            best_acc = va
            torch.save(model.state_dict(), CKPT_PATH)
            flag = "  ← saved"
        print(f"P1 [{epoch:02d}/{CFG['phase1_epochs']}]  "
              f"loss {tl:.4f}/{vl:.4f}  acc {ta:.4f}/{va:.4f}  "
              f"{time.time()-t0:.0f}s{flag}")

    # ── Phase 2 ──────────────────────────────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"Phase 2 — fine-tune  ({CFG['phase2_epochs']} epochs, last 3 blocks unfrozen)")
    print(f"{'─'*55}")
    unfreeze_last_blocks(model, n=3)

    backbone_params = [p for p in model.backbone.parameters() if p.requires_grad]
    head_params     = (list(model.cbam.parameters()) +
                       list(model.fft_branch.parameters()) +
                       list(model.fusion.parameters()) +
                       list(model.classifier.parameters()))

    opt2 = torch.optim.AdamW([
        {"params": backbone_params, "lr": CFG["lr_backbone"]},
        {"params": head_params,     "lr": CFG["lr_head"]},
    ], weight_decay=CFG["weight_decay"])
    sched2 = torch.optim.lr_scheduler.CosineAnnealingLR(opt2, T_max=CFG["phase2_epochs"])

    for epoch in range(1, CFG["phase2_epochs"] + 1):
        t0 = time.time()
        tl, ta = run_epoch(model, train_loader, criterion, opt2, device, train=True)
        vl, va = run_epoch(model, val_loader,   criterion, opt2, device, train=False)
        sched2.step()
        flag = ""
        if va > best_acc:
            best_acc = va
            torch.save(model.state_dict(), CKPT_PATH)
            flag = "  ← saved"
        print(f"P2 [{epoch:02d}/{CFG['phase2_epochs']}]  "
              f"loss {tl:.4f}/{vl:.4f}  acc {ta:.4f}/{va:.4f}  "
              f"{time.time()-t0:.0f}s{flag}")

    print(f"\n{'='*55}")
    print(f"Training complete.  Best val acc: {best_acc:.4f}")
    print(f"Weights saved to:   {CKPT_PATH}")
    print(f"{'='*55}\n")
    return CKPT_PATH


if __name__ == "__main__":
    train()
