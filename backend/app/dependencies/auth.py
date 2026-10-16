import uuid
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

# HTTPBearer security scheme for OpenAPI / Swagger authorization
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and validates RS256 JWT access token from Authorization: Bearer header.
    Validates token signature, expiration, type claim ('access'), and active non-deleted user status.
    Returns the authenticated User model or raises HTTP 401 Unauthorized.
    """
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise unauthorized_exc

    if payload.get("type") != "access":
        raise unauthorized_exc

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise unauthorized_exc

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise unauthorized_exc

    user = UserRepository.get_by_id(db, user_uuid)
    if not user or user.is_deleted or not user.is_active:
        raise unauthorized_exc

    return user
