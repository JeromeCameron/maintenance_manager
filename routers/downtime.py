from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.downtime as downtimes
from schema.database import get_session
from schema.models import Downtime, DowntimeCause

downtime_cause_router = APIRouter(prefix="/api/downtime-causes", tags=["DowntimeCause"])
router = APIRouter(prefix="/api/downtimes", tags=["Downtime"])


# ------------------------------------------------------------------
# Downtime Cause endpoints


@downtime_cause_router.get("", status_code=status.HTTP_200_OK, response_model=list[DowntimeCause])
async def get_downtime_causes(session: Session = Depends(get_session)):
    return downtimes.get_downtime_causes(session)


@downtime_cause_router.get("/{cause_id}", status_code=status.HTTP_200_OK, response_model=DowntimeCause)
async def get_downtime_cause(cause_id: int, session: Session = Depends(get_session)):
    cause = downtimes.get_downtime_cause(session, cause_id)
    if not cause:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime cause not found")
    return cause


@downtime_cause_router.post("", status_code=status.HTTP_201_CREATED, response_model=DowntimeCause)
async def add_downtime_cause(cause: DowntimeCause, session: Session = Depends(get_session)):
    return downtimes.add_downtime_cause(session, cause)


@downtime_cause_router.put("/{cause_id}", status_code=status.HTTP_200_OK, response_model=DowntimeCause)
async def update_downtime_cause(
    cause_id: int, data: DowntimeCause, session: Session = Depends(get_session)
):
    cause = downtimes.update_downtime_cause(session, cause_id, data)
    if cause is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime cause not found")
    return cause


@downtime_cause_router.delete("/{cause_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_downtime_cause(cause_id: int, session: Session = Depends(get_session)):
    deleted = downtimes.delete_downtime_cause(session, cause_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime cause not found")


# ------------------------------------------------------------------
# Downtime endpoints


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Downtime])
async def get_downtimes(session: Session = Depends(get_session)):
    return downtimes.get_downtimes(session)


@router.get("/{downtime_id}", status_code=status.HTTP_200_OK, response_model=Downtime)
async def get_downtime(downtime_id: int, session: Session = Depends(get_session)):
    downtime = downtimes.get_downtime(session, downtime_id)
    if not downtime:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime not found")
    return downtime


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Downtime)
async def add_downtime(downtime: Downtime, session: Session = Depends(get_session)):
    return downtimes.add_downtime(session, downtime)


@router.put("/{downtime_id}", status_code=status.HTTP_200_OK, response_model=Downtime)
async def update_downtime(
    downtime_id: int, data: Downtime, session: Session = Depends(get_session)
):
    downtime = downtimes.update_downtime(session, downtime_id, data)
    if downtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime not found")
    return downtime


@router.delete("/{downtime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_downtime(downtime_id: int, session: Session = Depends(get_session)):
    deleted = downtimes.delete_downtime(session, downtime_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
