from calendar import monthrange
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select as sql_select

import crud.downtime as downtimes
import utils.cache as cache
from crud.utility import get_holidays
from schema.database import get_session
from schema.models import Asset, Downtime, DowntimeCause
from utils.down_hours import split_downtime_by_month
from utils.prod_metrics import availability as calc_availability
from utils.prod_metrics import mtbf as calc_mtbf
from utils.prod_metrics import mttr as calc_mttr
from utils.utils import is_work_day

downtime_cause_router = APIRouter(prefix="/api/downtime-causes", tags=["DowntimeCause"])
router = APIRouter(prefix="/api/downtimes", tags=["Downtime"])

_METRICS_TTL = 300  # 5 minutes


def _bust_metrics_cache() -> None:
    cache.bust_prefix("downtime:metrics:")
    cache.bust_prefix("downtime:hours:")


# ------------------------------------------------------------------
# Downtime Cause endpoints


@downtime_cause_router.get("", status_code=status.HTTP_200_OK, response_model=list[DowntimeCause])
async def get_downtime_causes(session: Session = Depends(get_session)):
    return downtimes.get_downtime_causes(session)


@downtime_cause_router.get("/{cause_id}", status_code=status.HTTP_200_OK, response_model=DowntimeCause)
async def get_downtime_cause(cause_id: int, session: Session = Depends(get_session)):
    cause = downtimes.get_downtime_cause(session, cause_id)
    if not cause:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime cause not found")
    return cause


@downtime_cause_router.post("", status_code=status.HTTP_201_CREATED, response_model=DowntimeCause)
async def add_downtime_cause(cause: DowntimeCause, session: Session = Depends(get_session)):
    return downtimes.add_downtime_cause(session, cause)


@downtime_cause_router.put("/{cause_id}", status_code=status.HTTP_200_OK, response_model=DowntimeCause)
async def update_downtime_cause(
    cause_id: int, data: DowntimeCause, session: Session = Depends(get_session)
):
    cause = downtimes.update_downtime_cause(session, cause_id, data)
    if cause is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime cause not found")
    return cause


@downtime_cause_router.delete("/{cause_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_downtime_cause(cause_id: int, session: Session = Depends(get_session)):
    deleted = downtimes.delete_downtime_cause(session, cause_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime cause not found")


# ------------------------------------------------------------------
# Downtime endpoints


@router.get("/monthly-hours", status_code=status.HTTP_200_OK)
async def get_monthly_downtime_hours(
    months: int = Query(default=2, ge=1, le=24),
    session: Session = Depends(get_session),
) -> dict[str, float]:
    cache_key = f"downtime:hours:{months}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today = date.today()
    holidays = {h.holiday_date for h in get_holidays(session)}

    target_months: set[tuple[int, int]] = set()
    for i in range(months):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        target_months.add((y, m))

    totals: dict[str, float] = {}

    for dt in downtimes.get_downtimes(session):
        if dt.start_date is None or dt.start_time is None:
            continue

        for seg in split_downtime_by_month(
            session, dt.start_date, dt.start_time, dt.end_date, dt.end_time, dt.shift_asset,
            holidays=holidays,
        ):
            try:
                seg_date = datetime.strptime(seg["month"], "%B %Y").date()
            except ValueError:
                continue
            if (seg_date.year, seg_date.month) not in target_months:
                continue
            key = seg_date.strftime("%Y-%m")
            totals[key] = round(totals.get(key, 0.0) + seg["hours"], 2)

    cache.set(cache_key, totals, ttl_seconds=_METRICS_TTL)
    return totals


@router.get("/monthly-metrics", status_code=status.HTTP_200_OK)
async def get_monthly_metrics(
    months: int = Query(default=6, ge=1, le=24),
    session: Session = Depends(get_session),
) -> list[dict]:
    cache_key = f"downtime:metrics:{months}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today = date.today()
    holidays = {h.holiday_date for h in get_holidays(session)}

    month_list: list[tuple[int, int]] = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append((y, m))

    # Shift status per asset from downtime history
    asset_shift: dict[str, bool] = {}
    all_dts = downtimes.get_downtimes(session)
    for dt in all_dts:
        if dt.asset_id is not None:
            asset_shift[dt.asset_id] = dt.shift_asset

    active_assets = session.exec(sql_select(Asset).where(Asset.status != "disposed")).all()
    hours_per_workday = sum(16 if asset_shift.get(a.asset_id, False) else 8 for a in active_assets)

    scheduled: dict[tuple[int, int], float] = {}
    for (y, m) in month_list:
        work_days = sum(
            1 for d in range(1, monthrange(y, m)[1] + 1)
            if is_work_day(date(y, m, d), holidays)
        )
        scheduled[(y, m)] = float(work_days * hours_per_workday)

    downtime_hrs: dict[tuple[int, int], float] = {k: 0.0 for k in month_list}
    failures: dict[tuple[int, int], int] = {k: 0 for k in month_list}

    for dt in all_dts:
        if dt.planned:
            continue
        if dt.start_date is None:
            continue

        start_key = (dt.start_date.year, dt.start_date.month)
        if start_key in failures:
            failures[start_key] += 1

        if dt.start_time is None:
            continue

        for seg in split_downtime_by_month(
            session, dt.start_date, dt.start_time, dt.end_date, dt.end_time, dt.shift_asset,
            holidays=holidays,
        ):
            try:
                seg_date = datetime.strptime(seg["month"], "%B %Y").date()
            except ValueError:
                continue
            seg_key = (seg_date.year, seg_date.month)
            if seg_key in downtime_hrs:
                downtime_hrs[seg_key] = round(downtime_hrs[seg_key] + seg["hours"], 2)

    results = [
        {
            "month": f"{y}-{m:02d}",
            "scheduled_hours": scheduled[(y, m)],
            "downtime_hours": downtime_hrs[(y, m)],
            "num_failures": failures[(y, m)],
            "mttr": round(calc_mttr(downtime_hrs[(y, m)], failures[(y, m)]), 2) if failures[(y, m)] > 0 else None,
            "mtbf": round(calc_mtbf(scheduled[(y, m)], downtime_hrs[(y, m)], failures[(y, m)]), 2) if failures[(y, m)] > 0 else None,
            "availability": round(calc_availability(scheduled[(y, m)], downtime_hrs[(y, m)]), 2),
        }
        for (y, m) in month_list
    ]

    cache.set(cache_key, results, ttl_seconds=_METRICS_TTL)
    return results


@router.get("/monthly-metrics-by-category", status_code=status.HTTP_200_OK)
async def get_monthly_metrics_by_category(
    months: int = Query(default=12, ge=1, le=24),
    session: Session = Depends(get_session),
) -> list[dict]:
    cache_key = f"downtime:metrics:by-category:{months}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today = date.today()
    holidays = {h.holiday_date for h in get_holidays(session)}

    month_list: list[tuple[int, int]] = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append((y, m))
    month_set = set(month_list)

    all_assets = session.exec(sql_select(Asset).where(Asset.status != "disposed")).all()
    asset_category: dict[str, str] = {a.asset_id: a.category for a in all_assets}
    all_categories = sorted({a.category for a in all_assets})

    all_dts = downtimes.get_downtimes(session)

    downtime_hrs: dict[tuple[tuple[int, int], str], float] = {}
    failures: dict[tuple[tuple[int, int], str], int] = {}

    for dt in all_dts:
        if dt.planned or dt.asset_id is None or dt.start_date is None:
            continue
        category = asset_category.get(dt.asset_id)
        if not category:
            continue

        start_key = (dt.start_date.year, dt.start_date.month)
        if start_key in month_set:
            pair = (start_key, category)
            failures[pair] = failures.get(pair, 0) + 1

        if dt.start_time is None:
            continue

        for seg in split_downtime_by_month(
            session, dt.start_date, dt.start_time, dt.end_date, dt.end_time, dt.shift_asset,
            holidays=holidays,
        ):
            try:
                seg_date = datetime.strptime(seg["month"], "%B %Y").date()
            except ValueError:
                continue
            seg_key = (seg_date.year, seg_date.month)
            if seg_key not in month_set:
                continue
            pair = (seg_key, category)
            downtime_hrs[pair] = round(downtime_hrs.get(pair, 0.0) + seg["hours"], 2)

    results = [
        {
            "month": f"{y}-{m:02d}",
            "category": category,
            "downtime_hours": downtime_hrs.get(((y, m), category), 0.0),
            "failures": failures.get(((y, m), category), 0),
        }
        for (y, m) in month_list
        for category in all_categories
    ]

    cache.set(cache_key, results, ttl_seconds=_METRICS_TTL)
    return results


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Downtime])
async def get_downtimes(session: Session = Depends(get_session)):
    return downtimes.get_downtimes(session)


@router.get("/asset/{asset_id}", status_code=status.HTTP_200_OK, response_model=list[Downtime])
async def get_downtimes_by_asset(asset_id: str, session: Session = Depends(get_session)):
    return downtimes.get_downtimes_by_asset(session, asset_id)


@router.get("/{downtime_id}", status_code=status.HTTP_200_OK, response_model=Downtime)
async def get_downtime(downtime_id: int, session: Session = Depends(get_session)):
    downtime = downtimes.get_downtime(session, downtime_id)
    if not downtime:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime not found")
    return downtime


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Downtime)
async def add_downtime(downtime: Downtime, session: Session = Depends(get_session)):
    result = downtimes.add_downtime(session, downtime)
    _bust_metrics_cache()
    return result


@router.put("/{downtime_id}", status_code=status.HTTP_200_OK, response_model=Downtime)
async def update_downtime(
    downtime_id: int, data: Downtime, session: Session = Depends(get_session)
):
    downtime = downtimes.update_downtime(session, downtime_id, data)
    if downtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime not found")
    _bust_metrics_cache()
    return downtime


@router.delete("/{downtime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_downtime(downtime_id: int, session: Session = Depends(get_session)):
    deleted = downtimes.delete_downtime(session, downtime_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime not found")
    _bust_metrics_cache()


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
