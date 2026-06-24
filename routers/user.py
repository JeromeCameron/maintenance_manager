from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.user as users
from auth.dependencies import require_admin, get_current_user
from schema.database import get_session
from schema.models import User, UserRead, ChangePasswordRequest

router = APIRouter(prefix="/api/users", tags=["User"])

# Separate router for self-service endpoints that must bypass the admin_on_write gate
self_router = APIRouter(prefix="/api/users", tags=["User"])


@router.get("", response_model=list[UserRead])
async def get_users(session: Session = Depends(get_session)):
    return users.get_users(session)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    user = users.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@self_router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    ok = users.change_own_password(session, current_user, body.current_password, body.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(require_admin)])
async def add_user(user: User, session: Session = Depends(get_session)):
    return users.add_user(session, user)


@router.put("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
async def update_user(user_id: int, data: User, session: Session = Depends(get_session)):
    user = users.update_user(session, user_id, data)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
async def delete_user(user_id: int, session: Session = Depends(get_session)):
    deleted = users.delete_user(session, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
