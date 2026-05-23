from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.maintenance as maintenance
from schema.database import get_session
from schema.models import AssetPM, PmPlans

pm_plan_router = APIRouter(prefix="/api/maintenance/pm-plans", tags=["PmPlans"])
asset_pm_router = APIRouter(prefix="/api/maintenance/asset-pms", tags=["AssetPM"])


# ------------------------------------------------------------------
# PM Plan endpoints


@pm_plan_router.get("", status_code=status.HTTP_200_OK, response_model=list[PmPlans])
async def get_pm_plans(session: Session = Depends(get_session)):
    return maintenance.get_pm_plans(session)


@pm_plan_router.get("/{pm_id}", status_code=status.HTTP_200_OK, response_model=PmPlans)
async def get_pm_plan(pm_id: str, session: Session = Depends(get_session)):
    pm = maintenance.get_pm_plan(session, pm_id)
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PM plan not found")
    return pm


@pm_plan_router.post("", status_code=status.HTTP_201_CREATED, response_model=PmPlans)
async def add_pm_plan(pm_plan: PmPlans, session: Session = Depends(get_session)):
    return maintenance.add_pm_plan(session, pm_plan)


@pm_plan_router.put("/{pm_id}", status_code=status.HTTP_200_OK, response_model=PmPlans)
async def update_pm_plan(pm_id: str, data: PmPlans, session: Session = Depends(get_session)):
    pm = maintenance.update_pm_plan(session, pm_id, data)
    if pm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PM plan not found")
    return pm


@pm_plan_router.delete("/{pm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pm_plan(pm_id: str, session: Session = Depends(get_session)):
    deleted = maintenance.delete_pm_plan(session, pm_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PM plan not found")


# ------------------------------------------------------------------
# Asset PM endpoints


@asset_pm_router.get("", status_code=status.HTTP_200_OK, response_model=list[AssetPM])
async def get_asset_pms(session: Session = Depends(get_session)):
    return maintenance.get_asset_pms(session)


@asset_pm_router.get("/asset/{asset_id}", status_code=status.HTTP_200_OK, response_model=list[AssetPM])
async def get_asset_pms_by_asset(asset_id: str, session: Session = Depends(get_session)):
    return maintenance.get_asset_pms_by_asset(session, asset_id)


@asset_pm_router.get("/{asset_pm_id}", status_code=status.HTTP_200_OK, response_model=AssetPM)
async def get_asset_pm(asset_pm_id: int, session: Session = Depends(get_session)):
    apm = maintenance.get_asset_pm(session, asset_pm_id)
    if not apm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset PM not found")
    return apm


@asset_pm_router.post("", status_code=status.HTTP_201_CREATED, response_model=AssetPM)
async def add_asset_pm(asset_pm: AssetPM, session: Session = Depends(get_session)):
    return maintenance.add_asset_pm(session, asset_pm)


@asset_pm_router.put("/{asset_pm_id}", status_code=status.HTTP_200_OK, response_model=AssetPM)
async def update_asset_pm(
    asset_pm_id: int, data: AssetPM, session: Session = Depends(get_session)
):
    apm = maintenance.update_asset_pm(session, asset_pm_id, data)
    if apm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset PM not found")
    return apm


@asset_pm_router.delete("/{asset_pm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_pm(asset_pm_id: int, session: Session = Depends(get_session)):
    deleted = maintenance.delete_asset_pm(session, asset_pm_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset PM not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
