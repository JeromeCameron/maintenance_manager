from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.asset as assets
from schema.database import get_session
from schema.models import Asset

router = APIRouter(prefix="/api/assets", tags=["Asset"])


@router.get(
    "", status_code=status.HTTP_200_OK, response_model=list[Asset], tags=["Asset"]
)
async def get_assets(session: Session = Depends(get_session)):
    results = assets.get_assets(session)
    return results


@router.get(
    "/{asset_id}",
    status_code=status.HTTP_200_OK,
    response_model=Asset,
    tags=["Asset"],
)
async def get_asset(asset_id: str, session: Session = Depends(get_session)) -> Asset:
    asset = assets.get_asset(session, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return asset


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=Asset, tags=["Asset"]
)
async def add_asset(asset: Asset, session: Session = Depends(get_session)):
    result = assets.add_asset(session, asset)
    return result


@router.put(
    "/{asset_id}",
    status_code=status.HTTP_200_OK,
    response_model=Asset,
    tags=["Asset"],
)
async def update_asset(
    asset_id: str, data: Asset, session: Session = Depends(get_session)
):
    asset = assets.update_asset(session, asset_id, data)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Asset"])
async def delete_asset(asset_id: str, session: Session = Depends(get_session)):
    delelted = assets.delete_asset(session, asset_id)
    if delelted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
