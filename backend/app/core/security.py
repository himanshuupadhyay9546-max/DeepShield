from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_access_token(data: dict, expires: int = 60 * 24 * 7):
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires)
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(allowed_roles: list[str]):
    def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "analyst")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden: requires one of [{', '.join(allowed_roles)}] role permissions",
            )
        return user
    return role_checker
