from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.commodity_rates as cr
from schema.database import get_session
from schema.models import CommodityRate

router = APIRouter(prefix="/api/commodity-rates", tags=["CommodityRate"])


@router.get("", response_model=list[CommodityRate])
async def list_rates(session: Session = Depends(get_session)):
    return cr.get_rates(session)


@router.get("/{rate_id}", response_model=CommodityRate)
async def get_rate(rate_id: int, session: Session = Depends(get_session)):
    rec = cr.get_rate(session, rate_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rate not found")
    return rec


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CommodityRate)
async def add_rate(rate: CommodityRate, session: Session = Depends(get_session)):
    return cr.add_rate(session, rate)


@router.put("/{rate_id}", response_model=CommodityRate)
async def update_rate(rate_id: int, data: CommodityRate, session: Session = Depends(get_session)):
    rec = cr.update_rate(session, rate_id, data)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rate not found")
    return rec


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(rate_id: int, session: Session = Depends(get_session)):
    if not cr.delete_rate(session, rate_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rate not found")
