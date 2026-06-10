from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.user as users
from auth.dependencies import require_admin, get_current_user
from schema.database import get_session
from schema.models import User

router = APIRouter(prefix="/api/users", tags=["User"])


@router.get("", response_model=list[User])
async def get_users(session: Session = Depends(get_session)):
    return users.get_users(session)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    user = users.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", status_code=status.HTTP_201_CREATED, response_model=User,
             dependencies=[Depends(require_admin)])
async def add_user(user: User, session: Session = Depends(get_session)):
    return users.add_user(session, user)


@router.put("/{user_id}", response_model=User, dependencies=[Depends(require_admin)])
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
