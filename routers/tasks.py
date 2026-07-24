from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.tasks as tasks
from auth.dependencies import get_current_user
from schema.database import get_session
from schema.models import Task, User, UserRole

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def _can_see_all(user: User) -> bool:
    return user.role in (UserRole.admin, UserRole.moderator)


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Task])
async def get_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if _can_see_all(current_user):
        return tasks.get_tasks(session)
    return tasks.get_tasks_for_user(session, current_user.id)


@router.get("/{task_id}", status_code=status.HTTP_200_OK, response_model=Task)
async def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    task = tasks.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not _can_see_all(current_user) and current_user.id not in (task.user_id, task.assigned_to):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this task")
    return task


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Task)
async def add_task(
    task: Task,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if (
        current_user.role == UserRole.user
        and task.assigned_to is not None
        and task.assigned_to != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign tasks to other users",
        )

    task.user_id = current_user.id
    if task.assigned_to is None:
        task.assigned_to = current_user.id

    return tasks.add_task(session, task)


@router.put("/{task_id}", status_code=status.HTTP_200_OK, response_model=Task)
async def update_task(
    task_id: int,
    data: Task,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = tasks.get_task(session, task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not _can_see_all(current_user) and current_user.id not in (existing.user_id, existing.assigned_to):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")

    if (
        current_user.role == UserRole.user
        and data.assigned_to is not None
        and data.assigned_to != existing.assigned_to
        and data.assigned_to != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign tasks to other users",
        )

    task = tasks.update_task(session, task_id, data)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = tasks.get_task(session, task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role != UserRole.admin and existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner or an admin can delete this task")

    tasks.delete_task(session, task_id)
