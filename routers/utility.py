from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.utility as utility
from schema.database import get_session
from schema.models import Holidays

router = APIRouter(prefix="/api/holidays", tags=["Holidays"])


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Holidays])
async def get_holidays(session: Session = Depends(get_session)):
    return utility.get_holidays(session)


@router.get("/{holiday_id}", status_code=status.HTTP_200_OK, response_model=Holidays)
async def get_holiday(holiday_id: int, session: Session = Depends(get_session)):
    holiday = utility.get_holiday(session, holiday_id)
    if not holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return holiday


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Holidays)
async def add_holiday(holiday: Holidays, session: Session = Depends(get_session)):
    return utility.add_holiday(session, holiday)


@router.put("/{holiday_id}", status_code=status.HTTP_200_OK, response_model=Holidays)
async def update_holiday(holiday_id: int, data: Holidays, session: Session = Depends(get_session)):
    holiday = utility.update_holiday(session, holiday_id, data)
    if holiday is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(holiday_id: int, session: Session = Depends(get_session)):
    deleted = utility.delete_holiday(session, holiday_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
