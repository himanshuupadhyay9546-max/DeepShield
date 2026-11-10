from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text
import uuid, datetime
from app.db.base import Base, GUID


class Detection(Base):
    __tablename__ = "detections"
    id                 = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id            = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    filename           = Column(String(255), default="", nullable=False)
    media_type         = Column(String(50), nullable=False)   # "image" | "video" | "audio"
    label              = Column(String(20), nullable=False)   # "FAKE" | "REAL" | "UNKNOWN"
    confidence         = Column(Float, default=0.0, nullable=False)
    processing_time_ms = Column(Integer, default=0, nullable=False)
    model_version      = Column(String(100), default="", nullable=False)
    metadata_json      = Column(Text, default="{}", nullable=False)
    created_at         = Column(DateTime, default=datetime.datetime.utcnow, index=True)
