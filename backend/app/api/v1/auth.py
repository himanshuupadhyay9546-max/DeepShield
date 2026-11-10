import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    organization: str = ""


class LoginBody(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    clean_email = body.email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=clean_email,
        password_hash=hash_password(body.password),
        role="analyst",
        organization=body.organization.strip(),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email,
        "role": user.role,
        "user_id": str(user.id),
    }


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    clean_email = body.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email,
        "role": user.role,
        "user_id": str(user.id),
    }


@router.get("/me")
def get_current_profile(user_payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(user_payload["sub"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format in token")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "organization": user.organization or "",
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
