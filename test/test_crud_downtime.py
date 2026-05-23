from datetime import date

from sqlmodel import Session

import crud.downtime as downtime_crud
from schema.models import Downtime, DowntimeCause


def make_downtime_cause(name: str = "Mechanical Failure") -> DowntimeCause:
    return DowntimeCause(name=name, description="General mechanical failure")


def make_downtime(asset_id: str | None = None, work_order: str = "WO-001") -> Downtime:
    return Downtime(
        asset_id=asset_id,
        start_date=date(2025, 1, 10),
        end_date=date(2025, 1, 11),
        work_order=work_order,
        downtime_hours=8.0,
    )


class TestDowntimeCause:
    def test_add_downtime_cause(self, session: Session):
        cause = downtime_crud.add_downtime_cause(session, make_downtime_cause())
        assert cause.cause_id is not None
        assert cause.name == "Mechanical Failure"

    def test_get_downtime_causes_empty(self, session: Session):
        assert downtime_crud.get_downtime_causes(session) == []

    def test_get_downtime_causes(self, session: Session):
        downtime_crud.add_downtime_cause(session, make_downtime_cause("Cause A"))
        downtime_crud.add_downtime_cause(session, make_downtime_cause("Cause B"))
        assert len(downtime_crud.get_downtime_causes(session)) == 2

    def test_get_downtime_cause(self, session: Session):
        added = downtime_crud.add_downtime_cause(session, make_downtime_cause())
        result = downtime_crud.get_downtime_cause(session, added.cause_id)
        assert result is not None
        assert result.cause_id == added.cause_id

    def test_get_downtime_cause_not_found(self, session: Session):
        assert downtime_crud.get_downtime_cause(session, 999) is None

    def test_update_downtime_cause(self, session: Session):
        added = downtime_crud.add_downtime_cause(session, make_downtime_cause())
        updated = make_downtime_cause()
        updated.description = "Updated description"
        result = downtime_crud.update_downtime_cause(session, added.cause_id, updated)
        assert result is not None
        assert result.description == "Updated description"

    def test_update_downtime_cause_not_found(self, session: Session):
        assert downtime_crud.update_downtime_cause(session, 999, make_downtime_cause()) is None

    def test_delete_downtime_cause(self, session: Session):
        added = downtime_crud.add_downtime_cause(session, make_downtime_cause())
        assert downtime_crud.delete_downtime_cause(session, added.cause_id) is True
        assert downtime_crud.get_downtime_cause(session, added.cause_id) is None

    def test_delete_downtime_cause_not_found(self, session: Session):
        assert downtime_crud.delete_downtime_cause(session, 999) is False


class TestDowntime:
    def test_add_downtime(self, session: Session):
        downtime = downtime_crud.add_downtime(session, make_downtime())
        assert downtime.downtime_id is not None
        assert downtime.work_order == "WO-001"

    def test_get_downtimes_empty(self, session: Session):
        assert downtime_crud.get_downtimes(session) == []

    def test_get_downtimes(self, session: Session):
        downtime_crud.add_downtime(session, make_downtime(work_order="WO-001"))
        downtime_crud.add_downtime(session, make_downtime(work_order="WO-002"))
        assert len(downtime_crud.get_downtimes(session)) == 2

    def test_get_downtime(self, session: Session):
        added = downtime_crud.add_downtime(session, make_downtime())
        result = downtime_crud.get_downtime(session, added.downtime_id)
        assert result is not None
        assert result.downtime_id == added.downtime_id

    def test_get_downtime_not_found(self, session: Session):
        assert downtime_crud.get_downtime(session, 999) is None

    def test_update_downtime(self, session: Session):
        added = downtime_crud.add_downtime(session, make_downtime())
        updated = make_downtime()
        updated.downtime_hours = 16.0
        result = downtime_crud.update_downtime(session, added.downtime_id, updated)
        assert result is not None
        assert result.downtime_hours == 16.0

    def test_update_downtime_not_found(self, session: Session):
        assert downtime_crud.update_downtime(session, 999, make_downtime()) is None

    def test_delete_downtime(self, session: Session):
        added = downtime_crud.add_downtime(session, make_downtime())
        assert downtime_crud.delete_downtime(session, added.downtime_id) is True
        assert downtime_crud.get_downtime(session, added.downtime_id) is None

    def test_delete_downtime_not_found(self, session: Session):
        assert downtime_crud.delete_downtime(session, 999) is False

    def test_get_downtimes_by_asset(self, session: Session):
        downtime_crud.add_downtime(session, make_downtime(asset_id="ASSET-001"))
        downtime_crud.add_downtime(session, make_downtime(asset_id="ASSET-001", work_order="WO-002"))
        downtime_crud.add_downtime(session, make_downtime(asset_id="ASSET-002", work_order="WO-003"))
        results = downtime_crud.get_downtimes_by_asset(session, "ASSET-001")
        assert len(results) == 2
        assert all(d.asset_id == "ASSET-001" for d in results)

    def test_get_downtimes_by_asset_empty(self, session: Session):
        downtime_crud.add_downtime(session, make_downtime(asset_id="ASSET-002"))
        results = downtime_crud.get_downtimes_by_asset(session, "ASSET-001")
        assert results == []
