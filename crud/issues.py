from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Issue, IssueStatus
from utils.utils import clean_update_payload


def get_issues(session: Session) -> Sequence[Issue]:
    return session.exec(select(Issue).order_by(Issue.reported_at.desc())).all()


def get_issues_by_asset(session: Session, asset_id: str) -> Sequence[Issue]:
    return session.exec(select(Issue).where(Issue.asset_id == asset_id).order_by(Issue.reported_at.desc())).all()


def get_issue(session: Session, issue_id: int) -> Optional[Issue]:
    return session.get(Issue, issue_id)


def add_issue(session: Session, issue: Issue) -> Issue:
    session.add(issue)
    session.commit()
    session.refresh(issue)
    return issue


def update_issue(session: Session, issue_id: int, data: Issue) -> Optional[Issue]:
    db_issue = session.get(Issue, issue_id)
    if db_issue is None:
        return None
    for key, value in clean_update_payload(data.model_dump(exclude_unset=True)).items():
        setattr(db_issue, key, value)
    session.add(db_issue)
    session.commit()
    session.refresh(db_issue)
    return db_issue


def delete_issue(session: Session, issue_id: int) -> bool:
    issue = session.get(Issue, issue_id)
    if issue is None:
        return False
    session.delete(issue)
    session.commit()
    return True
