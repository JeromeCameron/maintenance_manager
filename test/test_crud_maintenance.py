from datetime import date

from sqlmodel import Session

import crud.maintenance as maintenance_crud
from schema.models import AssetCategory, AssetPM, PmFrequency, PmOwner, PmPlans, PmTriggers


def make_pm_plan(pm_id: str = "PM-001") -> PmPlans:
    return PmPlans(
        pm_id=pm_id,
        asset_type=AssetCategory.baler,
        trigger=PmTriggers.calendar_based,
        frequency=PmFrequency.monthly,
        owner=PmOwner.maintenance_team,
        description="Monthly baler inspection",
    )


def make_asset_pm(asset_id: str | None = None) -> AssetPM:
    return AssetPM(
        asset_id=asset_id,
        last_service=date(2025, 1, 1),
        next_service=date(2025, 4, 1),
        active=True,
    )


class TestPmPlans:
    def test_add_pm_plan(self, session: Session):
        pm = maintenance_crud.add_pm_plan(session, make_pm_plan())
        assert pm.pm_id == "PM-001"
        assert pm.frequency == PmFrequency.monthly

    def test_get_pm_plans_empty(self, session: Session):
        assert maintenance_crud.get_pm_plans(session) == []

    def test_get_pm_plans(self, session: Session):
        maintenance_crud.add_pm_plan(session, make_pm_plan("PM-001"))
        maintenance_crud.add_pm_plan(session, make_pm_plan("PM-002"))
        assert len(maintenance_crud.get_pm_plans(session)) == 2

    def test_get_pm_plan(self, session: Session):
        maintenance_crud.add_pm_plan(session, make_pm_plan())
        result = maintenance_crud.get_pm_plan(session, "PM-001")
        assert result is not None
        assert result.pm_id == "PM-001"

    def test_get_pm_plan_not_found(self, session: Session):
        assert maintenance_crud.get_pm_plan(session, "MISSING") is None

    def test_update_pm_plan(self, session: Session):
        maintenance_crud.add_pm_plan(session, make_pm_plan())
        updated = make_pm_plan()
        updated.frequency = PmFrequency.quarterly
        result = maintenance_crud.update_pm_plan(session, "PM-001", updated)
        assert result is not None
        assert result.frequency == PmFrequency.quarterly

    def test_update_pm_plan_not_found(self, session: Session):
        assert maintenance_crud.update_pm_plan(session, "MISSING", make_pm_plan()) is None

    def test_delete_pm_plan(self, session: Session):
        maintenance_crud.add_pm_plan(session, make_pm_plan())
        assert maintenance_crud.delete_pm_plan(session, "PM-001") is True
        assert maintenance_crud.get_pm_plan(session, "PM-001") is None

    def test_delete_pm_plan_not_found(self, session: Session):
        assert maintenance_crud.delete_pm_plan(session, "MISSING") is False


class TestAssetPM:
    def test_add_asset_pm(self, session: Session):
        apm = maintenance_crud.add_asset_pm(session, make_asset_pm())
        assert apm.id is not None
        assert apm.active is True

    def test_get_asset_pms_empty(self, session: Session):
        assert maintenance_crud.get_asset_pms(session) == []

    def test_get_asset_pms(self, session: Session):
        maintenance_crud.add_asset_pm(session, make_asset_pm())
        maintenance_crud.add_asset_pm(session, make_asset_pm())
        assert len(maintenance_crud.get_asset_pms(session)) == 2

    def test_get_asset_pm(self, session: Session):
        added = maintenance_crud.add_asset_pm(session, make_asset_pm())
        result = maintenance_crud.get_asset_pm(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_asset_pm_not_found(self, session: Session):
        assert maintenance_crud.get_asset_pm(session, 999) is None

    def test_update_asset_pm(self, session: Session):
        added = maintenance_crud.add_asset_pm(session, make_asset_pm())
        updated = make_asset_pm()
        updated.active = False
        result = maintenance_crud.update_asset_pm(session, added.id, updated)
        assert result is not None
        assert result.active is False

    def test_update_asset_pm_not_found(self, session: Session):
        assert maintenance_crud.update_asset_pm(session, 999, make_asset_pm()) is None

    def test_delete_asset_pm(self, session: Session):
        added = maintenance_crud.add_asset_pm(session, make_asset_pm())
        assert maintenance_crud.delete_asset_pm(session, added.id) is True
        assert maintenance_crud.get_asset_pm(session, added.id) is None

    def test_delete_asset_pm_not_found(self, session: Session):
        assert maintenance_crud.delete_asset_pm(session, 999) is False

    def test_get_asset_pms_by_asset(self, session: Session):
        maintenance_crud.add_asset_pm(session, make_asset_pm(asset_id="ASSET-001"))
        maintenance_crud.add_asset_pm(session, make_asset_pm(asset_id="ASSET-001"))
        maintenance_crud.add_asset_pm(session, make_asset_pm(asset_id="ASSET-002"))
        results = maintenance_crud.get_asset_pms_by_asset(session, "ASSET-001")
        assert len(results) == 2
        assert all(a.asset_id == "ASSET-001" for a in results)

    def test_get_asset_pms_by_asset_empty(self, session: Session):
        maintenance_crud.add_asset_pm(session, make_asset_pm(asset_id="ASSET-002"))
        results = maintenance_crud.get_asset_pms_by_asset(session, "ASSET-001")
        assert results == []
