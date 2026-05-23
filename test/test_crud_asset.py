from sqlmodel import Session

import crud.asset as asset_crud
from schema.models import Asset, AssetCategory, AssetModel, AssetOwnership, AssetScores, AssetStatus, Baler, BalerSize, BalerType


# ------------------------------------------------------------------ #
# Helpers


def make_asset(asset_id: str = "ASSET-001") -> Asset:
    return Asset(
        asset_id=asset_id,
        manufacturer="Caterpillar",
        category=AssetCategory.baler,
        owned=AssetOwnership.owned,
        status=AssetStatus.operational,
    )


def make_asset_model(model_no: str = "CAT-100") -> AssetModel:
    return AssetModel(
        model_no=model_no,
        manufacturer="Caterpillar",
        category=AssetCategory.baler,
    )


def make_baler(asset_id: str | None = None) -> Baler:
    return Baler(
        asset_id=asset_id,
        bale_weight=500,
        baler_type=BalerType.vertical,
        baler_size=BalerSize.medium,
    )


def make_asset_score(asset_id: str | None = None) -> AssetScores:
    return AssetScores(
        asset_id=asset_id,
        operational_score=3,
        safety_score=4,
        backup_score=2,
        repair_score=1,
        usage_score=2,
    )


# ------------------------------------------------------------------ #
# Asset


class TestAsset:
    def test_add_asset(self, session: Session):
        asset = asset_crud.add_asset(session, make_asset())
        assert asset.asset_id == "ASSET-001"
        assert asset.manufacturer == "Caterpillar"

    def test_get_assets_empty(self, session: Session):
        results = asset_crud.get_assets(session)
        assert results == []

    def test_get_assets(self, session: Session):
        asset_crud.add_asset(session, make_asset("ASSET-001"))
        asset_crud.add_asset(session, make_asset("ASSET-002"))
        results = asset_crud.get_assets(session)
        assert len(results) == 2

    def test_get_asset(self, session: Session):
        asset_crud.add_asset(session, make_asset())
        result = asset_crud.get_asset(session, "ASSET-001")
        assert result is not None
        assert result.asset_id == "ASSET-001"

    def test_get_asset_not_found(self, session: Session):
        result = asset_crud.get_asset(session, "MISSING")
        assert result is None

    def test_update_asset(self, session: Session):
        asset_crud.add_asset(session, make_asset())
        updated = make_asset()
        updated.manufacturer = "Volvo"
        result = asset_crud.update_asset(session, "ASSET-001", updated)
        assert result is not None
        assert result.manufacturer == "Volvo"

    def test_update_asset_not_found(self, session: Session):
        result = asset_crud.update_asset(session, "MISSING", make_asset())
        assert result is None

    def test_delete_asset(self, session: Session):
        asset_crud.add_asset(session, make_asset())
        deleted = asset_crud.delete_asset(session, "ASSET-001")
        assert deleted is True
        assert asset_crud.get_asset(session, "ASSET-001") is None

    def test_delete_asset_not_found(self, session: Session):
        deleted = asset_crud.delete_asset(session, "MISSING")
        assert deleted is False


# ------------------------------------------------------------------ #
# Asset Model


class TestAssetModel:
    def test_add_asset_model(self, session: Session):
        model = asset_crud.add_asset_model(session, make_asset_model())
        assert model.model_no == "CAT-100"
        assert model.manufacturer == "Caterpillar"

    def test_get_asset_models_empty(self, session: Session):
        assert asset_crud.get_asset_models(session) == []

    def test_get_asset_models(self, session: Session):
        asset_crud.add_asset_model(session, make_asset_model("CAT-100"))
        asset_crud.add_asset_model(session, make_asset_model("CAT-200"))
        assert len(asset_crud.get_asset_models(session)) == 2

    def test_get_asset_model(self, session: Session):
        asset_crud.add_asset_model(session, make_asset_model())
        result = asset_crud.get_asset_model(session, "CAT-100")
        assert result is not None
        assert result.model_no == "CAT-100"

    def test_get_asset_model_not_found(self, session: Session):
        assert asset_crud.get_asset_model(session, "MISSING") is None

    def test_update_asset_model(self, session: Session):
        asset_crud.add_asset_model(session, make_asset_model())
        updated = make_asset_model()
        updated.manufacturer = "Volvo"
        result = asset_crud.update_asset_model(session, "CAT-100", updated)
        assert result is not None
        assert result.manufacturer == "Volvo"

    def test_update_asset_model_not_found(self, session: Session):
        assert asset_crud.update_asset_model(session, "MISSING", make_asset_model()) is None

    def test_delete_asset_model(self, session: Session):
        asset_crud.add_asset_model(session, make_asset_model())
        assert asset_crud.delete_asset_model(session, "CAT-100") is True
        assert asset_crud.get_asset_model(session, "CAT-100") is None

    def test_delete_asset_model_not_found(self, session: Session):
        assert asset_crud.delete_asset_model(session, "MISSING") is False


# ------------------------------------------------------------------ #
# Baler


class TestBaler:
    def test_add_baler(self, session: Session):
        baler = asset_crud.add_baler(session, make_baler())
        assert baler.baler_id is not None
        assert baler.bale_weight == 500

    def test_get_balers_empty(self, session: Session):
        assert asset_crud.get_balers(session) == []

    def test_get_balers(self, session: Session):
        asset_crud.add_baler(session, make_baler())
        asset_crud.add_baler(session, make_baler())
        assert len(asset_crud.get_balers(session)) == 2

    def test_get_baler(self, session: Session):
        added = asset_crud.add_baler(session, make_baler())
        result = asset_crud.get_baler(session, added.baler_id)
        assert result is not None
        assert result.baler_id == added.baler_id

    def test_get_baler_not_found(self, session: Session):
        assert asset_crud.get_baler(session, 999) is None

    def test_update_baler(self, session: Session):
        added = asset_crud.add_baler(session, make_baler())
        updated = make_baler()
        updated.bale_weight = 750
        result = asset_crud.update_baler(session, added.baler_id, updated)
        assert result is not None
        assert result.bale_weight == 750

    def test_update_baler_not_found(self, session: Session):
        assert asset_crud.update_baler(session, 999, make_baler()) is None

    def test_delete_baler(self, session: Session):
        added = asset_crud.add_baler(session, make_baler())
        assert asset_crud.delete_baler(session, added.baler_id) is True
        assert asset_crud.get_baler(session, added.baler_id) is None

    def test_delete_baler_not_found(self, session: Session):
        assert asset_crud.delete_baler(session, 999) is False


# ------------------------------------------------------------------ #
# Asset Scores


class TestAssetScores:
    def test_add_asset_score(self, session: Session):
        score = asset_crud.add_asset_score(session, make_asset_score())
        assert score.score_id is not None
        assert score.operational_score == 3

    def test_get_asset_scores_empty(self, session: Session):
        assert asset_crud.get_asset_scores(session) == []

    def test_get_asset_scores(self, session: Session):
        asset_crud.add_asset_score(session, make_asset_score())
        asset_crud.add_asset_score(session, make_asset_score())
        assert len(asset_crud.get_asset_scores(session)) == 2

    def test_get_asset_score(self, session: Session):
        added = asset_crud.add_asset_score(session, make_asset_score())
        result = asset_crud.get_asset_score(session, added.score_id)
        assert result is not None
        assert result.score_id == added.score_id

    def test_get_asset_score_not_found(self, session: Session):
        assert asset_crud.get_asset_score(session, 999) is None

    def test_update_asset_score(self, session: Session):
        added = asset_crud.add_asset_score(session, make_asset_score())
        updated = make_asset_score()
        updated.operational_score = 1
        result = asset_crud.update_asset_score(session, added.score_id, updated)
        assert result is not None
        assert result.operational_score == 1

    def test_update_asset_score_not_found(self, session: Session):
        assert asset_crud.update_asset_score(session, 999, make_asset_score()) is None

    def test_delete_asset_score(self, session: Session):
        added = asset_crud.add_asset_score(session, make_asset_score())
        assert asset_crud.delete_asset_score(session, added.score_id) is True
        assert asset_crud.get_asset_score(session, added.score_id) is None

    def test_delete_asset_score_not_found(self, session: Session):
        assert asset_crud.delete_asset_score(session, 999) is False
