import os
import json
import time
import tempfile
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, WebSocket, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.services.inference_service import DeepShieldService
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.detection import Detection

router = APIRouter()
service = DeepShieldService()

MAX_IMAGE_SIZE = 25 * 1024 * 1024   # 25 MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024   # 25 MB
MAX_VIDEO_SIZE = 75 * 1024 * 1024   # 75 MB

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _record(
    user: dict,
    label: str,
    media_type: str,
    filename: str,
    confidence: float,
    processing_time_ms: int,
    model_version: str,
    metadata: dict,
    db: Session,
) -> Detection:
    user_id = user["sub"]
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            pass
    record = Detection(
        user_id=user_id,
        filename=filename,
        media_type=media_type,
        label=label,
        confidence=round(float(confidence), 4),
        processing_time_ms=processing_time_ms,
        model_version=model_version,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    safe_name = os.path.basename(file.filename or "image.jpg")
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}",
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image file exceeds 25 MB size limit")

    path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{safe_name}")
    start_time = time.perf_counter()
    try:
        with open(path, "wb") as f:
            f.write(content)
        result = service.predict_image(path)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        record = _record(
            user=user,
            label=result["label"],
            media_type="image",
            filename=safe_name,
            confidence=result.get("confidence", 0.0),
            processing_time_ms=elapsed_ms,
            model_version=result.get("model", "EfficientNet-B4 + FFT + CBAM"),
            metadata={"size_bytes": len(content)},
            db=db,
        )

        result["id"] = str(record.id)
        result["filename"] = safe_name
        result["processing_time_ms"] = elapsed_ms
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.post("/video")
async def detect_video(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    safe_name = os.path.basename(file.filename or "video.mp4")
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_VIDEO_EXTS))}",
        )

    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=413, detail="Video file exceeds 75 MB size limit")

    path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{safe_name}")
    start_time = time.perf_counter()
    try:
        with open(path, "wb") as f:
            f.write(content)
        result = service.predict_video(path)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        conf = result.get("video_confidence", result.get("confidence", 0.5))
        record = _record(
            user=user,
            label=result["label"],
            media_type="video",
            filename=safe_name,
            confidence=conf,
            processing_time_ms=elapsed_ms,
            model_version="EfficientNet-B4 + MTCNN Face Tracking",
            metadata={
                "frames_analyzed": result.get("frames_analyzed", 0),
                "face_detection": result.get("face_detection", False),
                "size_bytes": len(content),
            },
            db=db,
        )

        result["id"] = str(record.id)
        result["filename"] = safe_name
        result["processing_time_ms"] = elapsed_ms
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process video: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.post("/audio")
async def detect_audio(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    safe_name = os.path.basename(file.filename or "audio.wav")
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_AUDIO_EXTS))}",
        )

    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file exceeds 25 MB size limit")

    path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{safe_name}")
    start_time = time.perf_counter()
    try:
        with open(path, "wb") as f:
            f.write(content)
        result = service.predict_audio(path)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        record = _record(
            user=user,
            label=result["label"],
            media_type="audio",
            filename=safe_name,
            confidence=result.get("confidence", 0.5),
            processing_time_ms=elapsed_ms,
            model_version="EfficientNet-B0 + Mel FFT Frequency",
            metadata={"note": result.get("note", ""), "size_bytes": len(content)},
            db=db,
        )

        result["id"] = str(record.id)
        result["filename"] = safe_name
        result["processing_time_ms"] = elapsed_ms
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process audio: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    media_type: Optional[str] = Query(None),
    label: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Detection).filter(Detection.user_id == user["sub"])
    if media_type and media_type.lower() != "all":
        query = query.filter(Detection.media_type == media_type.lower())
    if label and label.upper() != "ALL":
        query = query.filter(Detection.label == label.upper())
    if search and search.strip():
        query = query.filter(Detection.filename.ilike(f"%{search.strip()}%"))

    total = query.count()
    items = query.order_by(Detection.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": str(item.id),
                "filename": item.filename,
                "media_type": item.media_type,
                "label": item.label,
                "confidence": item.confidence,
                "processing_time_ms": item.processing_time_ms,
                "model_version": item.model_version,
                "metadata": json.loads(item.metadata_json or "{}"),
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
    }


@router.get("/{detection_id}")
def get_detection(
    detection_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        did = uuid.UUID(detection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid detection ID format")

    item = db.query(Detection).filter(Detection.id == did, Detection.user_id == user["sub"]).first()
    if not item:
        raise HTTPException(status_code=404, detail="Detection record not found")

    return {
        "id": str(item.id),
        "filename": item.filename,
        "media_type": item.media_type,
        "label": item.label,
        "confidence": item.confidence,
        "processing_time_ms": item.processing_time_ms,
        "model_version": item.model_version,
        "metadata": json.loads(item.metadata_json or "{}"),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.websocket("/ws")
async def ws_detect(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # Echo processing acknowledgment for real-time video streaming frame ingest
            await websocket.send_json({
                "status": "processing",
                "bytes_received": len(data),
                "timestamp": time.time(),
            })
    except Exception:
        pass
