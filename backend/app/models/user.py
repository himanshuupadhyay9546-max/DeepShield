from sqlalchemy import Column, String, DateTime, Boolean
import uuid, datetime
from app.db.base import Base, GUID

class User(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst")
    organization = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
