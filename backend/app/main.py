import sys, os
import datetime
from pathlib import Path
from contextlib import asynccontextmanager

# Add repo root and app directory to sys.path
_current_dir = Path(__file__).resolve().parent
_repo_root = _current_dir.parent.parent
for p in [str(_repo_root), str(_current_dir.parent)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from app.api.v1 import auth, detect
from app.core.config import settings
from app.core.security import get_current_user
from app.db.base import Base
from app.db.session import engine, get_db, init_db
from app.models.detection import Detection
import app.models.user
import app.models.detection

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as e:
        print(f"[Warning] Database initialization deferred: {e}")
    yield

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="DeepShield API",
    version="1.0.0",
    description="Enterprise Deepfake Detection Platform",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = getattr(settings, "CORS_ORIGINS", ["*"]) or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(detect.router, prefix="/api/v1/detect", tags=["detect"])

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "DeepShield API",
        "version": "1.0.0",
        "model": "DeepShield-B4 (EfficientNet + FFT + CBAM)",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/api/v1/stats")
def stats(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Detection).filter(Detection.user_id == user["sub"]).order_by(Detection.created_at.asc()).all()
    total = len(rows)
    fake  = sum(1 for r in rows if r.label == "FAKE")
    real  = sum(1 for r in rows if r.label == "REAL")
    unknown = sum(1 for r in rows if r.label == "UNKNOWN")

    images = sum(1 for r in rows if r.media_type == "image")
    videos = sum(1 for r in rows if r.media_type == "video")
    audio = sum(1 for r in rows if r.media_type == "audio")

    avg_confidence = round(sum(r.confidence for r in rows) / total, 4) if total > 0 else 0.0
    avg_proc_time = round(sum(r.processing_time_ms for r in rows) / total, 1) if total > 0 else 0.0

    # Build real daily telemetry for last 7 calendar days
    now = datetime.datetime.utcnow().date()
    days_map = {}
    for i in range(6, -1, -1):
        d = now - datetime.timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        day_name = d.strftime("%a")
        days_map[d_str] = {"date": d_str, "name": day_name, "total": 0, "fake": 0, "real": 0}

    for r in rows:
        if r.created_at:
            r_date = r.created_at.date().strftime("%Y-%m-%d")
            if r_date in days_map:
                days_map[r_date]["total"] += 1
                if r.label == "FAKE":
                    days_map[r_date]["fake"] += 1
                elif r.label == "REAL":
                    days_map[r_date]["real"] += 1

    return {
        "total": total,
        "fake": fake,
        "real": real,
        "unknown": unknown,
        "avg_confidence": avg_confidence,
        "avg_processing_time_ms": avg_proc_time,
        "media_distribution": {
            "image": images,
            "video": videos,
            "audio": audio,
        },
        "daily_trends": list(days_map.values()),
    }
