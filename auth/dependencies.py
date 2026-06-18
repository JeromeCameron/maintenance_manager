from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError as JWTError
from sqlmodel import Session

import crud.user as user_crud
from auth.security import decode_token
from schema.database import get_session
from schema.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc

    user = user_crud.get_user(session, int(user_id))
    if not user or not user.active:
        raise exc
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_write(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role == UserRole.moderator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access not permitted for moderators")
    return current_user


def admin_on_write(request: Request, current_user: User = Depends(get_current_user)) -> User:
    """GET = any authenticated user. POST/PUT/DELETE = admin only."""
    if request.method in _MUTATING and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def write_on_write(request: Request, current_user: User = Depends(get_current_user)) -> User:
    """GET = any authenticated user. POST/PUT/DELETE = admin or user (not moderator)."""
    if request.method in _MUTATING and current_user.role == UserRole.moderator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access not permitted for moderators")
    return current_user
