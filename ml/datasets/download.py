"""
Downloads the 140k-Real-and-Fake-Faces dataset from Kaggle.

Dataset: xhlulu/140k-real-and-fake-faces
  - 70k real faces (FFHQ thumbnails, 256x256)
  - 70k fake faces (StyleGAN2-generated, 256x256)
  - Pre-split: train / valid / test

Setup (2 min):
  1. Go to https://kaggle.com → Account → Create API Token → download kaggle.json
  2. mkdir -p ~/.kaggle && cp ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
  3. python ml/datasets/download.py
"""

import os
import sys
import subprocess
import zipfile

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
DATASET_SLUG = "xhlulu/140k-real-and-fake-faces"
EXPECTED_DIR = os.path.join(DATA_DIR, "real-vs-fake", "train")


def check_credentials():
    return os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json"))


def already_downloaded():
    return os.path.isdir(EXPECTED_DIR)


def download():
    if already_downloaded():
        n_real = len(os.listdir(os.path.join(EXPECTED_DIR, "real")))
        n_fake = len(os.listdir(os.path.join(EXPECTED_DIR, "fake")))
        print(f"Dataset already present — train/real: {n_real}, train/fake: {n_fake}")
        return

    if not check_credentials():
        print("""
ERROR: Kaggle credentials not found at ~/.kaggle/kaggle.json

Setup (2 minutes):
  1. Sign in at https://www.kaggle.com
  2. Go to Account → Settings → API → Create New Token
  3. This downloads kaggle.json — then run:

     mkdir -p ~/.kaggle
     cp ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
     chmod 600 ~/.kaggle/kaggle.json

  4. Run:  python ml/datasets/download.py
""")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)

    print("Downloading 140k-real-and-fake-faces (~2.5 GB) …")
    try:
        import kaggle
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(DATASET_SLUG, path=DATA_DIR, unzip=True, quiet=False)
    except Exception as e:
        print(f"Kaggle API error: {e}")
        sys.exit(1)

    # Verify
    if already_downloaded():
        n_real = len(os.listdir(os.path.join(EXPECTED_DIR, "real")))
        n_fake = len(os.listdir(os.path.join(EXPECTED_DIR, "fake")))
        print(f"\nDownload complete — train/real: {n_real}, train/fake: {n_fake}")
    else:
        print(f"ERROR: Expected folder not found after download: {EXPECTED_DIR}")
        sys.exit(1)


if __name__ == "__main__":
    download()
