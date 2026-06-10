from typing import Optional, Sequence

from sqlmodel import Session, select

from auth.security import hash_password
from schema.models import User


def get_users(session: Session) -> Sequence[User]:
    return session.exec(select(User)).all()


def get_user(session: Session, id: int) -> Optional[User]:
    return session.get(User, id)


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()


def add_user(session: Session, user: User) -> User:
    user.password = hash_password(user.password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, id: int, data: User) -> Optional[User]:
    db_user = session.get(User, id)
    if db_user is None:
        return None

    updates = data.model_dump(exclude_unset=True)
    # Re-hash if password is being changed
    if "password" in updates and updates["password"]:
        updates["password"] = hash_password(updates["password"])
    for key, value in updates.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def delete_user(session: Session, id: int) -> bool:
    user = session.get(User, id)
    if user is None:
        return False
    session.delete(user)
    session.commit()
    return True
