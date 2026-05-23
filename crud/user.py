from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import User


def get_users(session: Session) -> Sequence[User]:
    statement = select(User)
    results = session.exec(statement).all()
    return results


def get_user(session: Session, id: int) -> Optional[User]:
    user = session.get(User, id)
    return user


def add_user(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, id: int, data: User) -> Optional[User]:
    db_user: Optional[User] = session.get(User, id)

    if db_user is None:
        return None

    user = data.model_dump(exclude_unset=True)
    for key, value in user.items():
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


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
