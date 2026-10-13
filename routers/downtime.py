from calendar import monthrange
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select as sql_select

import crud.asset as assets_crud
import crud.downtime as downtimes
import utils.cache as cache
from crud.utility import get_holidays
from schema.database import get_session
from schema.models import (
    Asset,
    Downtime,
    DowntimeCause,
    DowntimeFactor,
    DowntimeFactorType,
    Location,
)
from utils.down_hours import get_production_downtime_hours, split_downtime_by_month
from utils.downtime_scheduler import run_recompute_once
from utils.prod_metrics import availability as calc_availability
from utils.prod_metrics import mtbf as calc_mtbf
from utils.prod_metrics import mttr as calc_mttr
from utils.utils import is_work_day, today_local

downtime_cause_router = APIRouter(prefix="/api/downtime-causes", tags=["DowntimeCause"])
downtime_factor_type_router = APIRouter(
    prefix="/api/downtime-factor-types", tags=["DowntimeFactorType"]
)
downtime_factor_router = APIRouter(
    prefix="/api/downtime-factors", tags=["DowntimeFactor"]
)
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
# Downtime Factor Type endpoints (managed lookup list)


@downtime_factor_type_router.get("", status_code=status.HTTP_200_OK, response_model=list[DowntimeFactorType])
async def get_downtime_factor_types(session: Session = Depends(get_session)):
    return downtimes.get_downtime_factor_types(session)


@downtime_factor_type_router.get("/{factor_type_id}", status_code=status.HTTP_200_OK, response_model=DowntimeFactorType)
async def get_downtime_factor_type(factor_type_id: int, session: Session = Depends(get_session)):
    factor_type = downtimes.get_downtime_factor_type(session, factor_type_id)
    if not factor_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime factor type not found")
    return factor_type


@downtime_factor_type_router.post("", status_code=status.HTTP_201_CREATED, response_model=DowntimeFactorType)
async def add_downtime_factor_type(factor_type: DowntimeFactorType, session: Session = Depends(get_session)):
    return downtimes.add_downtime_factor_type(session, factor_type)


@downtime_factor_type_router.put("/{factor_type_id}", status_code=status.HTTP_200_OK, response_model=DowntimeFactorType)
async def update_downtime_factor_type(
    factor_type_id: int, data: DowntimeFactorType, session: Session = Depends(get_session)
):
    factor_type = downtimes.update_downtime_factor_type(session, factor_type_id, data)
    if factor_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime factor type not found")
    return factor_type


@downtime_factor_type_router.delete("/{factor_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_downtime_factor_type(factor_type_id: int, session: Session = Depends(get_session)):
    deleted = downtimes.delete_downtime_factor_type(session, factor_type_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime factor type not found")


# ------------------------------------------------------------------
# Downtime Factor endpoints (rows against a specific downtime)


@downtime_factor_router.get("", status_code=status.HTTP_200_OK, response_model=list[DowntimeFactor])
async def get_downtime_factors(session: Session = Depends(get_session)):
    return downtimes.get_downtime_factors(session)


@downtime_factor_router.get("/downtime/{downtime_id}", status_code=status.HTTP_200_OK, response_model=list[DowntimeFactor])
async def get_downtime_factors_by_downtime(downtime_id: int, session: Session = Depends(get_session)):
    return downtimes.get_downtime_factors_by_downtime(session, downtime_id)


@downtime_factor_router.get("/{factor_id}", status_code=status.HTTP_200_OK, response_model=DowntimeFactor)
async def get_downtime_factor(factor_id: int, session: Session = Depends(get_session)):
    factor = downtimes.get_downtime_factor(session, factor_id)
    if not factor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime factor not found")
    return factor


@downtime_factor_router.post("", status_code=status.HTTP_201_CREATED, response_model=DowntimeFactor)
async def add_downtime_factor(factor: DowntimeFactor, session: Session = Depends(get_session)):
    result = downtimes.add_downtime_factor(session, factor)
    _bust_metrics_cache()
    return result


@downtime_factor_router.put("/{factor_id}", status_code=status.HTTP_200_OK, response_model=DowntimeFactor)
async def update_downtime_factor(
    factor_id: int, data: DowntimeFactor, session: Session = Depends(get_session)
):
    factor = downtimes.update_downtime_factor(session, factor_id, data)
    if factor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime factor not found")
    _bust_metrics_cache()
    return factor


@downtime_factor_router.delete("/{factor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_downtime_factor(factor_id: int, session: Session = Depends(get_session)):
    deleted = downtimes.delete_downtime_factor(session, factor_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Downtime factor not found")
    _bust_metrics_cache()


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

    today = today_local()
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

    today = today_local()
    holidays = {h.holiday_date for h in get_holidays(session)}

    month_list: list[tuple[int, int]] = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append((y, m))

    all_dts = downtimes.get_downtimes(session)

    locations = session.exec(sql_select(Location)).all()
    location_shift_map: dict[int, bool] = {
        l.location_id: bool(l.shift_depot)
        for l in locations if l.location_id is not None
    }

    active_assets = session.exec(sql_select(Asset).where(Asset.status != "disposed")).all()
    total_hours_per_workday = sum(
        16 if location_shift_map.get(a.location_id, False) else 8
        for a in active_assets
    )

    scheduled: dict[tuple[int, int], float] = {}
    for (y, m) in month_list:
        work_days = sum(
            1 for d in range(1, monthrange(y, m)[1] + 1)
            if is_work_day(date(y, m, d), holidays)
        )
        scheduled[(y, m)] = float(work_days * total_hours_per_workday)

    downtime_hrs: dict[tuple[int, int], float] = {k: 0.0 for k in month_list}
    planned_hrs: dict[tuple[int, int], float] = {k: 0.0 for k in month_list}
    failures: dict[tuple[int, int], int] = {k: 0 for k in month_list}

    # Planned downtime isn't a failure; its hours come out of scheduled time instead.
    for dt in all_dts:
        if dt.start_date is None:
            continue

        start_key = (dt.start_date.year, dt.start_date.month)
        if not dt.planned and start_key in failures:
            failures[start_key] += 1
        bucket = planned_hrs if dt.planned else downtime_hrs

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
            if seg_key in bucket:
                bucket[seg_key] = round(bucket[seg_key] + seg["hours"], 2)

    results = [
        {
            "month": f"{y}-{m:02d}",
            "scheduled_hours": scheduled[(y, m)],
            "downtime_hours": downtime_hrs[(y, m)],
            "planned_hours": planned_hrs[(y, m)],
            "num_failures": failures[(y, m)],
            "mttr": round(calc_mttr(downtime_hrs[(y, m)], failures[(y, m)]), 2) if failures[(y, m)] > 0 else None,
            "mtbf": round(calc_mtbf(scheduled[(y, m)], downtime_hrs[(y, m)], failures[(y, m)], planned_hrs[(y, m)]), 2) if failures[(y, m)] > 0 else None,
            "availability": round(calc_availability(scheduled[(y, m)], downtime_hrs[(y, m)], planned_hrs[(y, m)]), 2),
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

    today = today_local()
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
    planned_hrs: dict[tuple[tuple[int, int], str], float] = {}
    failures: dict[tuple[tuple[int, int], str], int] = {}

    for dt in all_dts:
        if dt.asset_id is None or dt.start_date is None:
            continue
        category = asset_category.get(dt.asset_id)
        if not category:
            continue
        bucket = planned_hrs if dt.planned else downtime_hrs

        start_key = (dt.start_date.year, dt.start_date.month)
        if not dt.planned and start_key in month_set:
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
            bucket[pair] = round(bucket.get(pair, 0.0) + seg["hours"], 2)

    results = [
        {
            "month": f"{y}-{m:02d}",
            "category": category,
            "downtime_hours": downtime_hrs.get(((y, m), category), 0.0),
            "planned_hours": planned_hrs.get(((y, m), category), 0.0),
            "failures": failures.get(((y, m), category), 0),
        }
        for (y, m) in month_list
        for category in all_categories
    ]

    cache.set(cache_key, results, ttl_seconds=_METRICS_TTL)
    return results


@router.get("/availability-30d/{asset_id}", status_code=status.HTTP_200_OK)
async def get_availability_30d(
    asset_id: str,
    session: Session = Depends(get_session),
) -> dict:
    today = today_local()
    window_start_date = today - timedelta(days=29)  # 30 days inclusive

    holidays = {h.holiday_date for h in get_holidays(session)}
    shift_history = sorted(
        assets_crud.get_shift_history(session, asset_id),
        key=lambda h: h.effective_from,
        reverse=True,
    )

    asset = session.get(Asset, asset_id)
    fallback_hours = 8
    if asset and asset.location_id:
        loc = session.get(Location, asset.location_id)
        if loc and loc.shift_depot:
            fallback_hours = 16

    def daily_hours_for_date(d: date) -> int:
        for entry in shift_history:
            if entry.effective_from <= d:
                return entry.daily_hours
        return fallback_hours

    scheduled_hours = 0.0
    d = window_start_date
    while d <= today:
        if is_work_day(d, holidays):
            scheduled_hours += daily_hours_for_date(d)
        d += timedelta(days=1)

    window_start_dt = datetime.combine(window_start_date, time(0, 0, 0))
    window_end_dt = datetime.combine(today, time(23, 59, 59))

    total_downtime = 0.0
    total_planned = 0.0
    for dt in downtimes.get_downtimes_by_asset(session, asset_id):
        if dt.start_date is None or dt.start_time is None:
            continue
        dt_start = datetime.combine(dt.start_date, dt.start_time)
        dt_end = datetime.combine(dt.end_date, dt.end_time) if dt.end_date and dt.end_time else window_end_dt
        if dt_start >= window_end_dt or dt_end <= window_start_dt:
            continue
        clipped_start = max(dt_start, window_start_dt)
        clipped_end = min(dt_end, window_end_dt)
        hours = get_production_downtime_hours(
            clipped_start.date(), clipped_start.time(),
            holidays,
            clipped_end.date(), clipped_end.time(),
            dt.shift_asset,
        )
        if dt.planned:
            total_planned += hours
        else:
            total_downtime += hours

    total_planned = min(total_planned, scheduled_hours)
    total_downtime = min(total_downtime, scheduled_hours - total_planned)
    avail = round(calc_availability(scheduled_hours, total_downtime, total_planned), 1) if scheduled_hours > 0 else 100.0

    return {
        "availability": avail,
        "downtime_hours": round(total_downtime, 2),
        "planned_hours": round(total_planned, 2),
        "scheduled_hours": round(scheduled_hours, 2),
    }


@router.get("/monthly-by-asset/{asset_id}", status_code=status.HTTP_200_OK)
async def get_monthly_downtime_by_asset(
    asset_id: str,
    months: int = Query(default=12, ge=1, le=24),
    session: Session = Depends(get_session),
) -> dict[str, dict[str, float]]:
    today = today_local()
    holidays = {h.holiday_date for h in get_holidays(session)}

    month_set: set[str] = set()
    for i in range(months):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_set.add(f"{y}-{m:02d}")

    totals: dict[str, dict[str, float]] = {}
    for dt in downtimes.get_downtimes_by_asset(session, asset_id):
        if dt.start_date is None or dt.start_time is None:
            continue
        for seg in split_downtime_by_month(
            session, dt.start_date, dt.start_time, dt.end_date, dt.end_time,
            dt.shift_asset, holidays=holidays,
        ):
            try:
                seg_date = datetime.strptime(seg["month"], "%B %Y").date()
            except ValueError:
                continue
            key = seg_date.strftime("%Y-%m")
            if key in month_set:
                month = totals.setdefault(key, {"unplanned": 0.0, "planned": 0.0})
                kind = "planned" if dt.planned else "unplanned"
                month[kind] = round(month[kind] + seg["hours"], 2)

    return totals


@router.get("/monthly-split", status_code=status.HTTP_200_OK)
async def get_downtime_monthly_split(session: Session = Depends(get_session)) -> list[dict]:
    """One flat row per downtime event / calendar-month segment.

    Each event that spans a month boundary is split into per-month production-hour
    segments via ``split_downtime_by_month`` (same shift/holiday-aware logic the
    monthly downtime endpoints use). Consumed by the bale-loss CSV reports so that
    lost bales / weight / value land in the months the downtime actually occurred.
    """
    holidays = {h.holiday_date for h in get_holidays(session)}
    out: list[dict] = []
    for dt in downtimes.get_downtimes(session):
        if dt.start_date is None or dt.start_time is None:
            continue
        for seg in split_downtime_by_month(
            session, dt.start_date, dt.start_time, dt.end_date, dt.end_time,
            dt.shift_asset, holidays=holidays,
        ):
            try:
                month = datetime.strptime(seg["month"], "%B %Y").date().strftime("%Y-%m")
            except ValueError:
                continue
            out.append({
                "downtime_id": dt.downtime_id,
                "asset_id": dt.asset_id,
                "start_date": dt.start_date.isoformat(),
                "start_time": dt.start_time.isoformat() if dt.start_time else None,
                "end_date": dt.end_date.isoformat() if dt.end_date else None,
                "end_time": dt.end_time.isoformat() if dt.end_time else None,
                "planned": dt.planned,
                "month": month,
                "hours": seg["hours"],
            })
    return out


def _monthly_downtime_map(
    session: Session, months: int, asset_ids: set | None = None
) -> dict[str, dict[str, float]]:
    """Trailing-``months`` map of ``{"YYYY-MM": {"unplanned": h, "planned": h}}``.

    ``asset_ids`` restricts the tally to those assets; ``None`` means "every
    downtime" (used for the all-locations rollup, which also picks up rows whose
    asset has no location).
    """
    today = today_local()
    holidays = {h.holiday_date for h in get_holidays(session)}

    month_set: set[str] = set()
    for i in range(months):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_set.add(f"{y}-{m:02d}")

    totals: dict[str, dict[str, float]] = {}
    for dt in downtimes.get_downtimes(session):
        if asset_ids is not None and dt.asset_id not in asset_ids:
            continue
        if dt.start_date is None or dt.start_time is None:
            continue
        for seg in split_downtime_by_month(
            session, dt.start_date, dt.start_time, dt.end_date, dt.end_time,
            dt.shift_asset, holidays=holidays,
        ):
            try:
                seg_date = datetime.strptime(seg["month"], "%B %Y").date()
            except ValueError:
                continue
            key = seg_date.strftime("%Y-%m")
            if key in month_set:
                month = totals.setdefault(key, {"unplanned": 0.0, "planned": 0.0})
                kind = "planned" if dt.planned else "unplanned"
                month[kind] = round(month[kind] + seg["hours"], 2)

    return totals


@router.get("/monthly-by-location/all", status_code=status.HTTP_200_OK)
async def get_monthly_downtime_all_locations(
    months: int = Query(default=12, ge=1, le=24),
    session: Session = Depends(get_session),
) -> dict[str, dict[str, float]]:
    cache_key = f"downtime:metrics:by-loc-all:{months}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    totals = _monthly_downtime_map(session, months, None)
    cache.set(cache_key, totals, ttl_seconds=_METRICS_TTL)
    return totals


@router.get("/monthly-by-location/{location_id}", status_code=status.HTTP_200_OK)
async def get_monthly_downtime_by_location(
    location_id: int,
    months: int = Query(default=12, ge=1, le=24),
    session: Session = Depends(get_session),
) -> dict[str, dict[str, float]]:
    location_asset_ids = {
        a.asset_id
        for a in session.exec(sql_select(Asset).where(Asset.location_id == location_id)).all()
    }
    return _monthly_downtime_map(session, months, location_asset_ids)


@router.get("/factor-summary", status_code=status.HTTP_200_OK)
async def get_downtime_factor_summary(
    months: int = Query(default=12, ge=1, le=36),
    session: Session = Depends(get_session),
) -> list[dict]:
    """Exacerbating-factor delay hours and event counts, bucketed by calendar
    month and factor type. A factor is attributed to its own ``start_date``, or
    the parent downtime's ``start_date`` when it has none. Used to justify
    downtime lost to causes outside hands-on repair (parts, supplier holds...)."""
    cache_key = f"downtime:metrics:factor-summary:{months}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today = today_local()
    month_set: set[str] = set()
    for i in range(months):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_set.add(f"{y}-{m:02d}")

    type_names = {
        t.factor_type_id: t.name
        for t in downtimes.get_downtime_factor_types(session)
    }
    downtime_start = {
        d.downtime_id: d.start_date for d in downtimes.get_downtimes(session)
    }

    agg: dict[tuple[str, str], dict] = {}
    for f in downtimes.get_downtime_factors(session):
        ref_date = f.start_date or downtime_start.get(f.downtime_id)
        if ref_date is None:
            continue
        key = f"{ref_date.year}-{ref_date.month:02d}"
        if key not in month_set:
            continue
        name = type_names.get(f.factor_type_id, "Uncategorised")
        rec = agg.setdefault((key, name), {"delay_hours": 0.0, "events": 0})
        rec["delay_hours"] = round(rec["delay_hours"] + (f.delay_hours or 0.0), 2)
        rec["events"] += 1

    results = [
        {
            "month": month,
            "factor_type": name,
            "delay_hours": v["delay_hours"],
            "events": v["events"],
        }
        for (month, name), v in sorted(agg.items())
    ]

    cache.set(cache_key, results, ttl_seconds=_METRICS_TTL)
    return results


@router.post("/recompute-open", status_code=status.HTTP_200_OK)
async def recompute_open_downtimes_now():
    """Manually trigger the same refresh the hourly background job runs, for
    still-open downtimes/factors — useful to verify immediately rather than
    waiting for the next scheduled run."""
    dt_count, factor_count = run_recompute_once()
    return {"downtimes_updated": dt_count, "factors_updated": factor_count}


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
