from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.issues as issues
from schema.database import get_session
from schema.models import Issue

router = APIRouter(prefix="/api/issues", tags=["Issues"])


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Issue])
async def get_issues(session: Session = Depends(get_session)):
    return issues.get_issues(session)


@router.get("/asset/{asset_id}", status_code=status.HTTP_200_OK, response_model=list[Issue])
async def get_issues_by_asset(asset_id: str, session: Session = Depends(get_session)):
    return issues.get_issues_by_asset(session, asset_id)


@router.get("/{issue_id}", status_code=status.HTTP_200_OK, response_model=Issue)
async def get_issue(issue_id: int, session: Session = Depends(get_session)):
    issue = issues.get_issue(session, issue_id)
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Issue)
async def add_issue(issue: Issue, session: Session = Depends(get_session)):
    return issues.add_issue(session, issue)


@router.put("/{issue_id}", status_code=status.HTTP_200_OK, response_model=Issue)
async def update_issue(issue_id: int, data: Issue, session: Session = Depends(get_session)):
    issue = issues.update_issue(session, issue_id, data)
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(issue_id: int, session: Session = Depends(get_session)):
    deleted = issues.delete_issue(session, issue_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
