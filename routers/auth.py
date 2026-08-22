from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session

import crud.user as user_crud
from auth.dependencies import get_current_user
from auth.rate_limit import limiter
from auth.security import create_access_token, verify_password
from schema.database import get_session
from schema.models import User
from utils.activity_log import record_login, record_logout

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    firstname: str
    lastname: str


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    ip = request.client.host if request.client else None
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = user_crud.get_user_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        record_login(session, None, success=False, ip=ip, username_attempted=form_data.username)
        raise _invalid
    if not user.active:
        record_login(session, None, success=False, ip=ip, username_attempted=form_data.username)
        raise _invalid  # same 401 — avoids leaking whether the account exists

    record_login(session, user, success=True, ip=ip)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
        firstname=user.firstname,
        lastname=user.lastname,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ip = request.client.host if request.client else None
    record_logout(session, current_user, ip=ip)
