from sqlmodel import Session

import crud.user as user_crud
from schema.models import User, UserRole


def make_user(username: str = "jsmith", email: str = "jsmith@example.com") -> User:
    return User(
        username=username,
        firstname="John",
        lastname="Smith",
        role=UserRole.user,
        email=email,
        password="hashed_password",
    )


class TestUser:
    def test_add_user(self, session: Session):
        user = user_crud.add_user(session, make_user())
        assert user.id is not None
        assert user.username == "jsmith"

    def test_get_users_empty(self, session: Session):
        assert user_crud.get_users(session) == []

    def test_get_users(self, session: Session):
        user_crud.add_user(session, make_user("user1", "user1@example.com"))
        user_crud.add_user(session, make_user("user2", "user2@example.com"))
        assert len(user_crud.get_users(session)) == 2

    def test_get_user(self, session: Session):
        added = user_crud.add_user(session, make_user())
        result = user_crud.get_user(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_user_not_found(self, session: Session):
        assert user_crud.get_user(session, 999) is None

    def test_update_user(self, session: Session):
        added = user_crud.add_user(session, make_user())
        updated = make_user()
        updated.firstname = "Jane"
        result = user_crud.update_user(session, added.id, updated)
        assert result is not None
        assert result.firstname == "Jane"

    def test_update_user_not_found(self, session: Session):
        assert user_crud.update_user(session, 999, make_user()) is None

    def test_delete_user(self, session: Session):
        added = user_crud.add_user(session, make_user())
        assert user_crud.delete_user(session, added.id) is True
        assert user_crud.get_user(session, added.id) is None

    def test_delete_user_not_found(self, session: Session):
        assert user_crud.delete_user(session, 999) is False
