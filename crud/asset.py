from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Asset, AssetModel, AssetScores


def get_assets(session: Session) -> Sequence[Asset]:
    statement = select(Asset)
    results = session.exec(statement).all()
    return results


def get_assets_by_location(session: Session, location_id: int) -> Sequence[Asset]:
    return session.exec(select(Asset).where(Asset.location_id == location_id)).all()


def get_asset(session: Session, asset_id: str) -> Optional[Asset]:
    asset = session.get(Asset, asset_id)
    return asset


def add_asset(session: Session, asset: Asset) -> Asset:
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def update_asset(session: Session, asset_id: str, data: Asset) -> Optional[Asset]:
    db_asset: Optional[Asset] = session.get(Asset, asset_id)

    if db_asset is None:
        return None

    asset = data.model_dump(exclude_unset=True)
    for key, value in asset.items():
        setattr(db_asset, key, value)

    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


def delete_asset(session: Session, asset_id: str) -> bool:
    asset = session.get(Asset, asset_id)
    if asset is None:
        return False
    session.delete(asset)
    session.commit()
    return True


# ------------------------------------------------------------------
# Asset Model


def get_asset_models(session: Session) -> Sequence[AssetModel]:
    return session.exec(select(AssetModel)).all()


def get_asset_model(session: Session, model_no: str) -> Optional[AssetModel]:
    return session.get(AssetModel, model_no)


def add_asset_model(session: Session, asset_model: AssetModel) -> AssetModel:
    session.add(asset_model)
    session.commit()
    session.refresh(asset_model)
    return asset_model


def update_asset_model(
    session: Session, model_no: str, data: AssetModel
) -> Optional[AssetModel]:
    db_model: Optional[AssetModel] = session.get(AssetModel, model_no)
    if db_model is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_model, key, value)
    session.add(db_model)
    session.commit()
    session.refresh(db_model)
    return db_model


def delete_asset_model(session: Session, model_no: str) -> bool:
    asset_model = session.get(AssetModel, model_no)
    if asset_model is None:
        return False
    session.delete(asset_model)
    session.commit()
    return True


# ------------------------------------------------------------------
# Asset Scores


def get_asset_scores(session: Session) -> Sequence[AssetScores]:
    return session.exec(select(AssetScores)).all()


def get_asset_score(session: Session, score_id: int) -> Optional[AssetScores]:
    return session.get(AssetScores, score_id)


def get_asset_score_by_asset(session: Session, asset_id: str) -> Optional[AssetScores]:
    return session.exec(select(AssetScores).where(AssetScores.asset_id == asset_id)).first()


def add_asset_score(session: Session, asset_score: AssetScores) -> AssetScores:
    session.add(asset_score)
    session.commit()
    session.refresh(asset_score)
    return asset_score


def update_asset_score(
    session: Session, score_id: int, data: AssetScores
) -> Optional[AssetScores]:
    db_score: Optional[AssetScores] = session.get(AssetScores, score_id)
    if db_score is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_score, key, value)
    session.add(db_score)
    session.commit()
    session.refresh(db_score)
    return db_score


def delete_asset_score(session: Session, score_id: int) -> bool:
    score = session.get(AssetScores, score_id)
    if score is None:
        return False
    session.delete(score)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
