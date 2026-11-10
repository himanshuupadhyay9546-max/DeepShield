# DeepShield Test Samples

Use these files to manually test the model at http://localhost:5173

---

## Images (`images/`)

### `real/` — should return REAL
| File | Who | Expected |
|------|-----|----------|
| `obama_real.jpg` | Barack Obama | REAL ~99% |
| `musk_real.jpg` | Elon Musk | REAL ~95% |
| `einstein_real.jpg` | Albert Einstein (historical photo) | REAL |
| `lincoln_real.jpg` | Abraham Lincoln (historical photo) | REAL |
| `marie_curie_real.jpg` | Marie Curie (historical photo) | REAL |
| `darwin_real.jpg` | Charles Darwin (historical photo) | REAL |

### `fake/` — should return FAKE
| File | Source | Expected |
|------|--------|----------|
| `ai_generated_face_1.jpg` – `face_6.jpg` | ThisPersonDoesNotExist.com (StyleGAN3) | FAKE |
| `stylegan_0_fake.jpg` | StyleGAN dataset | FAKE ~99% |
| `stylegan_2_fake.jpg` | StyleGAN dataset | FAKE ~97% |
| `stylegan_4_fake.jpg` | StyleGAN dataset | FAKE ~71% |
| `stylegan_5_fake.jpg` | StyleGAN dataset | FAKE ~97% |

### `inconclusive/` — should return INCONCLUSIVE
These are StyleGAN images where EfficientNet and ViT disagree sharply.
The ensemble confidence falls below 65%, so the model refuses to commit.
| File | EfficientNet | ViT | Combined |
|------|-------------|-----|---------|
| `stylegan_1_inconclusive.jpg` | 92% fake | 31% fake | 64.5% → INCONCLUSIVE |
| `stylegan_3_inconclusive.jpg` | 100% fake | 1% fake | 55.4% → INCONCLUSIVE |

---

## Videos (`videos/`)

> Video pages at http://localhost:5173/video
> Videos are static face clips (5 seconds). The model analyzes every 5th frame.

### `real/`
- `obama_real.mp4` — Obama face loop → REAL
- `musk_real.mp4` — Musk face loop → REAL

### `fake/`
- `ai_face_1_fake.mp4` — ThisPersonDoesNotExist AI face → FAKE
- `ai_face_3_fake.mp4` — ThisPersonDoesNotExist AI face → FAKE
- `stylegan_0_fake.mp4` — StyleGAN face → FAKE

---

## Audio (`audio/`)

> Audio page at http://localhost:5173/audio
> **Note: Audio model not trained yet** — all audio results will show UNKNOWN until
> you train `ml/training/train_audio.py` on the ASVspoof 2019 dataset.
> Files are included so you can test the upload UI and error handling.

### `real/` — human speech (macOS `say` TTS, natural voice synthesis)
- `natural_voice_1.wav` — "Hello, my name is John..."
- `natural_voice_2.wav` — "The quick brown fox..."
- `natural_voice_3.wav` — News-style sentence

### `fake/` — synthetic / non-speech signals
- `sine_440hz.wav` — Pure 440 Hz sine tone
- `sine_220hz.wav` — Pure 220 Hz sine tone
- `white_noise.wav` — White noise burst
- `frequency_sweep.wav` — Chirp (200→500 Hz sweep)
- `robotic_tone.wav` — Multi-harmonic robotic tone

---

## Tips

- Drag & drop files directly into the upload box on each page
- Check the **Ensemble breakdown** section in the result — it shows EfficientNet and ViT scores separately
- The **Grad-CAM heatmap** highlights which face regions the model focused on
- Dashboard shows per-account detection history after you log in
