from typing import Optional, Sequence

from sqlmodel import Session, or_, select

from schema.models import Task, TaskStatus
from utils.utils import clean_update_payload, now_local


def get_tasks(session: Session) -> Sequence[Task]:
    return session.exec(
        select(Task).order_by(Task.due_date.asc().nulls_last(), Task.id)
    ).all()


def get_tasks_for_user(session: Session, user_id: int) -> Sequence[Task]:
    return session.exec(
        select(Task)
        .where(or_(Task.user_id == user_id, Task.assigned_to == user_id))
        .order_by(Task.due_date.asc().nulls_last(), Task.id)
    ).all()


def get_task(session: Session, task_id: int) -> Optional[Task]:
    return session.get(Task, task_id)


def add_task(session: Session, task: Task) -> Task:
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def update_task(session: Session, task_id: int, data: Task) -> Optional[Task]:
    db_task = session.get(Task, task_id)
    if db_task is None:
        return None

    payload = clean_update_payload(data.model_dump(exclude_unset=True))
    payload.pop("user_id", None)  # owner is immutable once a task is created
    payload.pop("completed_at", None)  # derived from status transitions below, not client-settable

    new_status = payload.get("status", db_task.status)
    if new_status == TaskStatus.completed and db_task.status != TaskStatus.completed:
        payload["completed_at"] = now_local()
    elif new_status != TaskStatus.completed and db_task.status == TaskStatus.completed:
        payload["completed_at"] = None

    for key, value in payload.items():
        setattr(db_task, key, value)
    db_task.updated_at = now_local()

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


def delete_task(session: Session, task_id: int) -> bool:
    task = session.get(Task, task_id)
    if task is None:
        return False
    session.delete(task)
    session.commit()
    return True
