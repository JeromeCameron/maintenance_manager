"""Background job that keeps still-open downtime records current.

``Downtime.downtime_hours`` and ``DowntimeFactor.delay_hours`` are stored,
derived columns computed at write time (see ``crud/downtime.py``). For a
record with no end date/time yet, the calc treats "now" as the effective end
— but since it only runs on save, an open record's numbers are frozen at
whatever "now" was at the last save. This loop periodically re-runs the same
calc against the current time for every still-open downtime/factor, so the
totals shown in the UI advance on their own.

This app has no scheduling/queue infra (no APScheduler/Celery), and the need
here is exactly "run a function every N seconds" — well within stdlib
``asyncio``, so no new dependency is introduced for it.
"""

import asyncio
import logging
import os

from sqlmodel import Session

import utils.cache as cache
from crud.downtime import recompute_open_downtimes
from schema.database import engine

logger = logging.getLogger(__name__)

# Hardcoded, matching this codebase's existing style for tuning constants
# (e.g. `_METRICS_TTL = 300` in routers/downtime.py) rather than env-driven.
_RECOMPUTE_INTERVAL_SECONDS = 60 * 60  # hourly

# Operational kill-switch (not a tuning knob) in case this is ever run with
# multiple worker processes and needs disabling in all-but-one of them. Not
# required for correctness even without that — recomputation is idempotent —
# but costs nothing to have.
_ENABLED = os.getenv("DOWNTIME_RECOMPUTE_ENABLED", "true").strip().lower() != "false"


def run_recompute_once() -> tuple[int, int]:
    """One recompute pass: refresh open downtimes/factors and bust the
    downtime metrics cache if anything changed. Shared by the background loop
    and the manual `/api/downtimes/recompute-open` trigger so there's a single
    code path for both."""
    with Session(engine) as session:
        dt_count, factor_count = recompute_open_downtimes(session)
    if dt_count or factor_count:
        cache.bust_prefix("downtime:metrics:")
        cache.bust_prefix("downtime:hours:")
        logger.info(
            "Downtime auto-recompute: refreshed %d open downtime(s), %d open factor(s)",
            dt_count,
            factor_count,
        )
    return dt_count, factor_count


async def downtime_recompute_loop() -> None:
    """Runs immediately (so a fresh deploy/restart doesn't sit stale for up to
    an hour), then every ``_RECOMPUTE_INTERVAL_SECONDS``, until cancelled."""
    if not _ENABLED:
        logger.info("Downtime auto-recompute disabled via DOWNTIME_RECOMPUTE_ENABLED")
        return
    while True:
        try:
            run_recompute_once()
        except Exception:
            logger.exception("Downtime auto-recompute failed")
        await asyncio.sleep(_RECOMPUTE_INTERVAL_SECONDS)
