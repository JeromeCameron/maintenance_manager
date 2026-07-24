from sqlmodel import Session

import crud.tasks as task_crud
import crud.user as user_crud
from schema.models import Task, TaskPriority, TaskStatus, User, UserRole


def make_user(username: str = "jsmith", email: str = "jsmith@example.com") -> User:
    return User(
        username=username,
        firstname="John",
        lastname="Smith",
        role=UserRole.user,
        email=email,
        password="hashed_password",
    )


def make_task(**kwargs) -> Task:
    defaults = dict(title="Replace forklift battery", description="Battery is due for replacement")
    defaults.update(kwargs)
    return Task(**defaults)


class TestTask:
    def test_add_task_defaults(self, session: Session):
        task = task_crud.add_task(session, make_task())
        assert task.id is not None
        assert task.status == TaskStatus.not_started
        assert task.priority == TaskPriority.medium
        assert task.completed_at is None

    def test_get_tasks_empty(self, session: Session):
        assert task_crud.get_tasks(session) == []

    def test_get_task(self, session: Session):
        added = task_crud.add_task(session, make_task())
        result = task_crud.get_task(session, added.id)
        assert result is not None
        assert result.title == "Replace forklift battery"

    def test_get_task_not_found(self, session: Session):
        assert task_crud.get_task(session, 999) is None

    def test_get_tasks_sorted_by_due_date_oldest_first(self, session: Session):
        from datetime import date

        task_crud.add_task(session, make_task(title="Later", due_date=date(2026, 6, 1)))
        task_crud.add_task(session, make_task(title="Sooner", due_date=date(2026, 1, 1)))
        task_crud.add_task(session, make_task(title="No date"))

        results = task_crud.get_tasks(session)
        assert [t.title for t in results] == ["Sooner", "Later", "No date"]

    def test_get_tasks_for_user_owner_or_assignee(self, session: Session):
        owner = user_crud.add_user(session, make_user("owner", "owner@example.com"))
        assignee = user_crud.add_user(session, make_user("assignee", "assignee@example.com"))
        other = user_crud.add_user(session, make_user("other", "other@example.com"))

        task_crud.add_task(session, make_task(title="Owned by owner", user_id=owner.id, assigned_to=owner.id))
        task_crud.add_task(session, make_task(title="Assigned to assignee", user_id=owner.id, assigned_to=assignee.id))
        task_crud.add_task(session, make_task(title="Unrelated", user_id=other.id, assigned_to=other.id))

        owner_tasks = task_crud.get_tasks_for_user(session, owner.id)
        assert {t.title for t in owner_tasks} == {"Owned by owner", "Assigned to assignee"}

        assignee_tasks = task_crud.get_tasks_for_user(session, assignee.id)
        assert {t.title for t in assignee_tasks} == {"Assigned to assignee"}

    def test_update_task_sets_completed_at_when_marked_completed(self, session: Session):
        added = task_crud.add_task(session, make_task())
        assert added.completed_at is None

        updated = task_crud.update_task(session, added.id, Task(title="x", status=TaskStatus.completed))
        assert updated.completed_at is not None

    def test_update_task_clears_completed_at_when_reopened(self, session: Session):
        added = task_crud.add_task(session, make_task())
        task_crud.update_task(session, added.id, Task(title="x", status=TaskStatus.completed))

        reopened = task_crud.update_task(session, added.id, Task(title="x", status=TaskStatus.in_progress))
        assert reopened.completed_at is None

    def test_update_task_ignores_user_id_change(self, session: Session):
        owner = user_crud.add_user(session, make_user("owner2", "owner2@example.com"))
        other = user_crud.add_user(session, make_user("other2", "other2@example.com"))
        added = task_crud.add_task(session, make_task(user_id=owner.id))

        updated = task_crud.update_task(session, added.id, Task(title="x", user_id=other.id))
        assert updated.user_id == owner.id

    def test_update_task_not_found(self, session: Session):
        assert task_crud.update_task(session, 999, Task(title="x")) is None

    def test_delete_task(self, session: Session):
        added = task_crud.add_task(session, make_task())
        assert task_crud.delete_task(session, added.id) is True
        assert task_crud.get_task(session, added.id) is None

    def test_delete_task_not_found(self, session: Session):
        assert task_crud.delete_task(session, 999) is False
