from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Asset


def get_assets(session: Session) -> Sequence[Asset]:
    statement = select(Asset)
    results = session.exec(statement).all()
    return results


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


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
