from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from auth.dependencies import require_admin, require_write
from sqlmodel import Session

import crud.asset as assets
from schema.database import get_session
from schema.models import Asset, AssetModel, AssetScores, Baler

router = APIRouter(prefix="/api/assets", tags=["Asset"])
asset_model_router = APIRouter(prefix="/api/asset-models", tags=["AssetModel"])
baler_router = APIRouter(prefix="/api/balers", tags=["Baler"])
asset_scores_router = APIRouter(prefix="/api/asset-scores", tags=["AssetScores"])


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
    deleted = assets.delete_asset(session, asset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )


# ------------------------------------------------------------------
# Asset Model endpoints


@asset_model_router.get("", status_code=status.HTTP_200_OK, response_model=list[AssetModel])
async def get_asset_models(session: Session = Depends(get_session)):
    return assets.get_asset_models(session)


@asset_model_router.get("/{model_no}", status_code=status.HTTP_200_OK, response_model=AssetModel)
async def get_asset_model(model_no: str, session: Session = Depends(get_session)):
    model = assets.get_asset_model(session, model_no)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset model not found")
    return model


@asset_model_router.post("", status_code=status.HTTP_201_CREATED, response_model=AssetModel)
async def add_asset_model(asset_model: AssetModel, session: Session = Depends(get_session)):
    return assets.add_asset_model(session, asset_model)


@asset_model_router.put("/{model_no}", status_code=status.HTTP_200_OK, response_model=AssetModel)
async def update_asset_model(
    model_no: str, data: AssetModel, session: Session = Depends(get_session)
):
    model = assets.update_asset_model(session, model_no, data)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset model not found")
    return model


@asset_model_router.delete("/{model_no}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_model(model_no: str, session: Session = Depends(get_session)):
    deleted = assets.delete_asset_model(session, model_no)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset model not found")


# ------------------------------------------------------------------
# Baler endpoints


@baler_router.get("", status_code=status.HTTP_200_OK, response_model=list[Baler])
async def get_balers(session: Session = Depends(get_session)):
    return assets.get_balers(session)


@baler_router.get("/asset/{asset_id}", status_code=status.HTTP_200_OK, response_model=Optional[Baler])
async def get_baler_by_asset(asset_id: str, session: Session = Depends(get_session)):
    return assets.get_baler_by_asset(session, asset_id)


@baler_router.get("/{baler_id}", status_code=status.HTTP_200_OK, response_model=Baler)
async def get_baler(baler_id: int, session: Session = Depends(get_session)):
    baler = assets.get_baler(session, baler_id)
    if not baler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baler not found")
    return baler


@baler_router.post("", status_code=status.HTTP_201_CREATED, response_model=Baler)
async def add_baler(baler: Baler, session: Session = Depends(get_session)):
    return assets.add_baler(session, baler)


@baler_router.put("/{baler_id}", status_code=status.HTTP_200_OK, response_model=Baler)
async def update_baler(baler_id: int, data: Baler, session: Session = Depends(get_session)):
    baler = assets.update_baler(session, baler_id, data)
    if baler is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baler not found")
    return baler


@baler_router.delete("/{baler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_baler(baler_id: int, session: Session = Depends(get_session)):
    deleted = assets.delete_baler(session, baler_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baler not found")


# ------------------------------------------------------------------
# Asset Scores endpoints


@asset_scores_router.get("", status_code=status.HTTP_200_OK, response_model=list[AssetScores])
async def get_asset_scores(session: Session = Depends(get_session)):
    return assets.get_asset_scores(session)


@asset_scores_router.get("/asset/{asset_id}", status_code=status.HTTP_200_OK, response_model=Optional[AssetScores])
async def get_asset_score_by_asset(asset_id: str, session: Session = Depends(get_session)):
    return assets.get_asset_score_by_asset(session, asset_id)


@asset_scores_router.get("/{score_id}", status_code=status.HTTP_200_OK, response_model=AssetScores)
async def get_asset_score(score_id: int, session: Session = Depends(get_session)):
    score = assets.get_asset_score(session, score_id)
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset score not found")
    return score


@asset_scores_router.post("", status_code=status.HTTP_201_CREATED, response_model=AssetScores)
async def add_asset_score(asset_score: AssetScores, session: Session = Depends(get_session)):
    return assets.add_asset_score(session, asset_score)


@asset_scores_router.put("/{score_id}", status_code=status.HTTP_200_OK, response_model=AssetScores)
async def update_asset_score(
    score_id: int, data: AssetScores, session: Session = Depends(get_session)
):
    score = assets.update_asset_score(session, score_id, data)
    if score is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset score not found")
    return score


@asset_scores_router.delete("/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_score(score_id: int, session: Session = Depends(get_session)):
    deleted = assets.delete_asset_score(session, score_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset score not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
