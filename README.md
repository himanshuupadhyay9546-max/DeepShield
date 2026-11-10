# DeepShield — AI Deepfake Detection Platform

Detects deepfakes in images, videos, and audio using EfficientNet + FFT + CBAM attention.

---

## What you need before starting

- **Python 3.11** — [python.org/downloads](https://python.org/downloads)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **PostgreSQL** — database to store users and detections
- **Redis** — used for rate limiting

---

## Setup on Mac

### 1. Install PostgreSQL and Redis

```bash
brew install postgresql redis
brew services start postgresql
brew services start redis
```

### 2. Create the database

```bash
psql postgres -c "CREATE USER deepshield WITH PASSWORD 'changeme';"
psql postgres -c "CREATE DATABASE deepshield OWNER deepshield;"
```

### 3. Set up the backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Set up the frontend

```bash
cd frontend
npm install
```

### 5. Add environment file

Create a file called `.env` in the root `deepshield/` folder:

```
DATABASE_URL=postgresql://deepshield:changeme@localhost:5432/deepshield
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-this-to-something-random
JWT_ALGORITHM=HS256
MODEL_PATH=./backend/models/deepshield_b4.pth
MODEL_BACKEND=efficientnet
```

---

## Setup on Windows

### 1. Install PostgreSQL and Redis

- PostgreSQL: [postgresql.org/download/windows](https://www.postgresql.org/download/windows)
  - During install, set password to `changeme` for the `postgres` user
- Redis: [github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases) — download the `.msi` installer

### 2. Create the database

Open **pgAdmin** (installed with PostgreSQL) or run in Command Prompt:

  ```cmd
  psql -U postgres -c "CREATE USER deepshield WITH PASSWORD 'changeme';"
  psql -U postgres -c "CREATE DATABASE deepshield OWNER deepshield;"
```

### 3. Set up the backend

Open Command Prompt in the `deepshield/backend` folder:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Set up the frontend

```cmd
cd frontend
npm install
```

### 5. Add environment file

Same as Mac — create `.env` in the root `deepshield/` folder with the same content shown above.

---

## Running the app

You need **two terminal windows** open at the same time.

**Terminal 1 — Backend:**

```bash
# Mac
cd deepshield/backend
source venv/bin/activate
uvicorn app.main:app --reload --reload-dir . --reload-dir ../ml --port 8000

# Windows
cd deepshield\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd deepshield/frontend
npm run dev
```

Then open your browser at: **http://localhost:5173**

---

## Using the app

1. Go to `http://localhost:5173`
2. Click **Register** and create an account
3. You'll be logged in automatically
4. Click **Analyze** in the top nav
5. Drop an image, video, or audio file
6. Click **Analyze with DeepShield**
7. See the verdict, confidence score, and heatmap showing which areas the model focused on
8. **Dashboard** shows your personal detection history

---

## Switching AI models

Edit the `.env` file and change `MODEL_BACKEND`:

```
# Use custom EfficientNet model (default, needs deepshield_b4.pth)
MODEL_BACKEND=efficientnet

# Use ViT model from HuggingFace (downloads ~340MB automatically)
MODEL_BACKEND=vit
```

Then restart the backend.

---

## Training your own model

### Image model

Download the dataset first:

```bash
cd deepshield
source backend/venv/bin/activate   # Mac
# or: backend\venv\Scripts\activate  (Windows)

python ml/datasets/download.py
python ml/training/train.py
```

This saves weights to `backend/models/deepshield_b4.pth`.

### Audio model

Download **ASVspoof 2019 LA** dataset from:
`https://datashare.ed.ac.uk/handle/10283/3336`

Put it at `deepshield/data/asvspoof2019/LA/`, then:

```bash
python ml/training/train_audio.py
```

This saves weights to `backend/models/deepshield_audio.pth`.

---

## Project structure

```
deepshield/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # auth + detect endpoints
│   │   ├── core/          # config, JWT security
│   │   ├── db/            # SQLAlchemy session
│   │   ├── models/        # User, Detection DB models
│   │   └── services/      # inference_service.py (main AI logic)
│   └── models/            # trained .pth weight files go here
├── frontend/
│   └── src/pages/         # Login, Dashboard, Upload
├── ml/
│   ├── models/            # DeepShieldModel, FFTBranch, CBAM, AudioModel
│   ├── inference/         # Grad-CAM heatmap
│   └── training/          # train.py, train_audio.py
└── .env                   # your config (never commit this)
```

---

## Common errors

**`psql: command not found` on Mac**
```bash
export PATH="/usr/local/opt/postgresql/bin:$PATH"
# or for Apple Silicon:
export PATH="/opt/homebrew/opt/postgresql/bin:$PATH"
```

**`No module named 'app'` when starting backend**
Make sure you are inside the `backend/` folder before running uvicorn.

**Port 8000 already in use**
```bash
lsof -i :8000       # find the process
kill -9 <PID>       # kill it
```

**Model not found warning at startup**
The app runs without weights (random predictions). Drop your `.pth` file into `backend/models/` and restart.

**`venv\Scripts\activate` not recognized on Windows**
Run this first in PowerShell: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
