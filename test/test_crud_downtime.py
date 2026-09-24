from datetime import date, time

from sqlmodel import Session

import crud.downtime as downtime_crud
from schema.models import Downtime, DowntimeCause, DowntimeFactor, DowntimeFactorType


def make_downtime_cause(name: str = "Mechanical Failure") -> DowntimeCause:
    return DowntimeCause(name=name, description="General mechanical failure")


def make_downtime(asset_id: str | None = None, work_order: str = "WO-001") -> Downtime:
    return Downtime(
        asset_id=asset_id,
        shift_asset=False,
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


def make_factor_type(name: str = "Parts unavailable") -> DowntimeFactorType:
    return DowntimeFactorType(name=name, description="Awaiting part delivery")


class TestDowntimeFactorType:
    def test_add_factor_type(self, session: Session):
        ftype = downtime_crud.add_downtime_factor_type(session, make_factor_type())
        assert ftype.factor_type_id is not None
        assert ftype.active is True

    def test_get_factor_types(self, session: Session):
        downtime_crud.add_downtime_factor_type(session, make_factor_type("A"))
        downtime_crud.add_downtime_factor_type(session, make_factor_type("B"))
        assert len(downtime_crud.get_downtime_factor_types(session)) == 2

    def test_get_factor_type_not_found(self, session: Session):
        assert downtime_crud.get_downtime_factor_type(session, 999) is None

    def test_update_factor_type(self, session: Session):
        added = downtime_crud.add_downtime_factor_type(session, make_factor_type())
        patch = DowntimeFactorType(name="Parts unavailable", active=False)
        result = downtime_crud.update_downtime_factor_type(
            session, added.factor_type_id, patch
        )
        assert result is not None
        assert result.active is False

    def test_update_factor_type_not_found(self, session: Session):
        assert (
            downtime_crud.update_downtime_factor_type(session, 999, make_factor_type())
            is None
        )

    def test_delete_factor_type(self, session: Session):
        added = downtime_crud.add_downtime_factor_type(session, make_factor_type())
        assert downtime_crud.delete_downtime_factor_type(session, added.factor_type_id)
        assert downtime_crud.get_downtime_factor_type(session, added.factor_type_id) is None

    def test_delete_factor_type_not_found(self, session: Session):
        assert downtime_crud.delete_downtime_factor_type(session, 999) is False


class TestDowntimeFactor:
    def _downtime_and_type(self, session: Session):
        downtime = downtime_crud.add_downtime(session, make_downtime())
        ftype = downtime_crud.add_downtime_factor_type(session, make_factor_type())
        return downtime, ftype

    def test_add_factor(self, session: Session):
        downtime, ftype = self._downtime_and_type(session)
        factor = downtime_crud.add_downtime_factor(
            session,
            DowntimeFactor(
                downtime_id=downtime.downtime_id,
                factor_type_id=ftype.factor_type_id,
                delay_hours=12.5,
                notes="Bearing on back-order from OEM",
            ),
        )
        assert factor.id is not None
        assert factor.delay_hours == 12.5

    def test_get_factors_by_downtime(self, session: Session):
        downtime, _ = self._downtime_and_type(session)
        other = downtime_crud.add_downtime(session, make_downtime(work_order="WO-999"))
        for dh in (4.0, 6.0):
            downtime_crud.add_downtime_factor(
                session,
                DowntimeFactor(downtime_id=downtime.downtime_id, delay_hours=dh),
            )
        downtime_crud.add_downtime_factor(
            session, DowntimeFactor(downtime_id=other.downtime_id, delay_hours=1.0)
        )
        results = downtime_crud.get_downtime_factors_by_downtime(
            session, downtime.downtime_id
        )
        assert len(results) == 2
        assert {r.delay_hours for r in results} == {4.0, 6.0}

    def test_update_factor(self, session: Session):
        downtime, _ = self._downtime_and_type(session)
        added = downtime_crud.add_downtime_factor(
            session, DowntimeFactor(downtime_id=downtime.downtime_id, delay_hours=2.0)
        )
        result = downtime_crud.update_downtime_factor(
            session,
            added.id,
            DowntimeFactor(downtime_id=downtime.downtime_id, delay_hours=9.0, resolved=True),
        )
        assert result is not None
        assert result.delay_hours == 9.0
        assert result.resolved is True

    def test_update_factor_not_found(self, session: Session):
        assert (
            downtime_crud.update_downtime_factor(
                session, 999, DowntimeFactor(downtime_id=1)
            )
            is None
        )

    def test_delete_factor(self, session: Session):
        downtime, _ = self._downtime_and_type(session)
        added = downtime_crud.add_downtime_factor(
            session, DowntimeFactor(downtime_id=downtime.downtime_id)
        )
        assert downtime_crud.delete_downtime_factor(session, added.id) is True
        assert downtime_crud.get_downtime_factor(session, added.id) is None

    def test_delete_factor_not_found(self, session: Session):
        assert downtime_crud.delete_downtime_factor(session, 999) is False

    def test_factors_cascade_on_downtime_delete(self, session: Session):
        downtime, _ = self._downtime_and_type(session)
        downtime_crud.add_downtime_factor(
            session, DowntimeFactor(downtime_id=downtime.downtime_id, delay_hours=3.0)
        )
        assert downtime_crud.delete_downtime(session, downtime.downtime_id) is True
        assert downtime_crud.get_downtime_factors(session) == []

    def test_add_factor_derives_delay_hours_from_window(self, session: Session):
        # Mon 2025-01-13 08:00 -> Tue 2025-01-14 16:00 = two full 08:00-16:00 day
        # shifts (no holidays, non-shift asset) = 16h. Any manual value is ignored.
        downtime, _ = self._downtime_and_type(session)
        factor = downtime_crud.add_downtime_factor(
            session,
            DowntimeFactor(
                downtime_id=downtime.downtime_id,
                delay_hours=999.0,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
                end_date=date(2025, 1, 14),
                end_time=time(16, 0),
            ),
        )
        assert factor.delay_hours == 16.0

    def test_factor_delay_hours_manual_without_start_time(self, session: Session):
        downtime, _ = self._downtime_and_type(session)
        factor = downtime_crud.add_downtime_factor(
            session,
            DowntimeFactor(
                downtime_id=downtime.downtime_id,
                delay_hours=30.0,
                start_date=date(2025, 1, 13),
            ),
        )
        assert factor.delay_hours == 30.0

    def test_update_factor_recalculates_delay_hours(self, session: Session):
        downtime, _ = self._downtime_and_type(session)
        added = downtime_crud.add_downtime_factor(
            session, DowntimeFactor(downtime_id=downtime.downtime_id, delay_hours=5.0)
        )
        result = downtime_crud.update_downtime_factor(
            session,
            added.id,
            DowntimeFactor(
                downtime_id=downtime.downtime_id,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
                end_date=date(2025, 1, 13),
                end_time=time(16, 0),
            ),
        )
        assert result is not None
        assert result.delay_hours == 8.0


class TestRecomputeOpenDowntimes:
    def test_nothing_open_returns_zero(self, session: Session):
        assert downtime_crud.recompute_open_downtimes(session) == (0, 0)

    def test_refreshes_open_downtime_hours(self, session: Session):
        downtime = downtime_crud.add_downtime(
            session,
            Downtime(shift_asset=False, start_date=date(2025, 1, 13), start_time=time(8, 0)),
        )
        # Stale it out-of-band (as if it hadn't been re-saved in a while) to prove
        # recompute actually persists a fresh value rather than a no-op.
        downtime.downtime_hours = -1.0
        session.add(downtime)
        session.commit()

        dt_count, factor_count = downtime_crud.recompute_open_downtimes(session)

        session.refresh(downtime)
        assert (dt_count, factor_count) == (1, 0)
        assert downtime.downtime_hours is not None
        assert downtime.downtime_hours > 0
        assert downtime.downtime_hours != -1.0

    def test_ignores_closed_downtime(self, session: Session):
        # Mon 2025-01-13 08:00 -> 16:00 = one full day shift = 8h.
        closed = downtime_crud.add_downtime(
            session,
            Downtime(
                shift_asset=False,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
                end_date=date(2025, 1, 13),
                end_time=time(16, 0),
            ),
        )
        assert closed.downtime_hours == 8.0

        dt_count, factor_count = downtime_crud.recompute_open_downtimes(session)

        session.refresh(closed)
        assert (dt_count, factor_count) == (0, 0)
        assert closed.downtime_hours == 8.0

    def test_refreshes_open_factor_delay_hours(self, session: Session):
        downtime = downtime_crud.add_downtime(
            session,
            Downtime(shift_asset=False, start_date=date(2025, 1, 13), start_time=time(8, 0)),
        )
        factor = downtime_crud.add_downtime_factor(
            session,
            DowntimeFactor(
                downtime_id=downtime.downtime_id,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
            ),
        )
        factor.delay_hours = -1.0
        session.add(factor)
        session.commit()

        dt_count, factor_count = downtime_crud.recompute_open_downtimes(session)

        session.refresh(factor)
        assert (dt_count, factor_count) == (1, 1)
        assert factor.delay_hours is not None
        assert factor.delay_hours > 0
        assert factor.delay_hours != -1.0

    def test_ignores_closed_factor(self, session: Session):
        downtime = downtime_crud.add_downtime(
            session,
            Downtime(
                shift_asset=False,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
                end_date=date(2025, 1, 13),
                end_time=time(16, 0),
            ),
        )
        factor = downtime_crud.add_downtime_factor(
            session,
            DowntimeFactor(
                downtime_id=downtime.downtime_id,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
                end_date=date(2025, 1, 13),
                end_time=time(16, 0),
            ),
        )
        assert factor.delay_hours == 8.0

        dt_count, factor_count = downtime_crud.recompute_open_downtimes(session)

        session.refresh(factor)
        assert (dt_count, factor_count) == (0, 0)
        assert factor.delay_hours == 8.0

    def test_ignores_factor_without_a_window(self, session: Session):
        # A factor with no start_date/start_time is manually entered and never
        # auto-calculated (mirrors test_factor_delay_hours_manual_without_start_time),
        # so it must never be touched by the SQL-level "open" filter either.
        downtime = downtime_crud.add_downtime(
            session,
            Downtime(
                shift_asset=False,
                start_date=date(2025, 1, 13),
                start_time=time(8, 0),
                end_date=date(2025, 1, 13),
                end_time=time(16, 0),
            ),
        )
        factor = downtime_crud.add_downtime_factor(
            session,
            DowntimeFactor(downtime_id=downtime.downtime_id, delay_hours=30.0),
        )

        dt_count, factor_count = downtime_crud.recompute_open_downtimes(session)

        session.refresh(factor)
        assert (dt_count, factor_count) == (0, 0)
        assert factor.delay_hours == 30.0
