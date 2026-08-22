"""Automatic audit trail: captures create/update/delete on a whitelisted set
of models via a SQLAlchemy `before_flush` session event, plus explicit
helpers for login/login_failed/logout (which aren't ORM mutations).

Who made a change is not visible to a session event, so the acting user is
stashed in a ContextVar by `auth.dependencies.get_current_user` at the start
of every authenticated request and read back here.
"""

import json
from contextvars import ContextVar
from typing import Optional

from sqlalchemy import event, inspect
from sqlmodel import Session

from schema.models import (
    ActivityAction,
    ActivityLog,
    Asset,
    AssetModel,
    AssetPM,
    Budget,
    CostCentre,
    Downtime,
    DowntimeCause,
    Inspection,
    Invoice,
    Issue,
    Location,
    Part,
    PmPlans,
    PurchaseOrder,
    Supplier,
    Task,
    User,
    WorkOrder,
)

# Line-item/junction/derived tables (WorkOrderPart, StockTransaction,
# SupplierCategoryLink, AssetScores, InspectionResult, ...) are deliberately
# excluded to keep the log signal-focused. Add to this set to track more.
TRACKED_MODELS = {
    Asset,
    AssetModel,
    Location,
    Downtime,
    DowntimeCause,
    WorkOrder,
    Issue,
    Task,
    Supplier,
    Invoice,
    PurchaseOrder,
    CostCentre,
    Budget,
    Part,
    PmPlans,
    AssetPM,
    Inspection,
    User,
}

REDACT_FIELDS = {"password"}

_current_actor: ContextVar[Optional[User]] = ContextVar("_current_actor", default=None)
_current_ip: ContextVar[Optional[str]] = ContextVar("_current_ip", default=None)


def set_actor(user: Optional[User], ip: Optional[str] = None) -> None:
    _current_actor.set(user)
    _current_ip.set(ip)


def get_actor() -> Optional[User]:
    return _current_actor.get()


def _pk_value(obj) -> Optional[str]:
    mapper = inspect(obj).mapper
    values = [getattr(obj, col.name) for col in mapper.primary_key]
    if not values or values[0] is None:
        return None
    return "-".join(str(v) for v in values)


def _serialize(value):
    # All app enums are `str, Enum` subclasses, so they pass through here
    # unchanged (already JSON-native); date/datetime/time/Decimal fall back
    # to their string form.
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _compute_diff(obj) -> dict:
    diff = {}
    insp = inspect(obj)
    for attr in insp.mapper.column_attrs:
        hist = insp.attrs[attr.key].history
        if not hist.has_changes():
            continue
        old_raw = hist.deleted[0] if hist.deleted else None
        new_raw = hist.added[0] if hist.added else getattr(obj, attr.key)
        old, new = _serialize(old_raw), _serialize(new_raw)
        if old == new:
            continue
        # Redaction happens after the equality check -- otherwise two
        # different redacted values would both collapse to "***" and look
        # unchanged, silently dropping the entry from the diff.
        if attr.key in REDACT_FIELDS:
            old = "***" if old_raw is not None else None
            new = "***" if new_raw is not None else None
        diff[attr.key] = {"old": old, "new": new}
    return diff


def _build_log(obj, action: ActivityAction, changes: Optional[dict] = None) -> ActivityLog:
    actor = get_actor()
    entity_type = type(obj).__name__
    entity_id = _pk_value(obj)
    label = f"{entity_type} {entity_id}" if entity_id else entity_type
    verb = {"create": "Created", "update": "Updated", "delete": "Deleted"}[action.value]
    return ActivityLog(
        actor_user_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=f"{verb} {label}",
        changes=json.dumps(changes) if changes else None,
        ip_address=_current_ip.get(),
    )


_PENDING_CREATES_KEY = "_pending_activity_creates"


def _before_flush(session, flush_context, instances):
    # New objects don't have a server-generated PK (SERIAL id) yet at this
    # point -- snapshot them now and build their log rows in
    # after_flush_postexec, once the INSERTs have actually run and PKs are
    # populated back onto these same Python objects.
    pending_creates = [obj for obj in session.new if type(obj) in TRACKED_MODELS]
    if pending_creates:
        session.info.setdefault(_PENDING_CREATES_KEY, []).extend(pending_creates)

    for obj in session.dirty:
        if type(obj) in TRACKED_MODELS and session.is_modified(obj, include_collections=False):
            diff = _compute_diff(obj)
            if diff:
                session.add(_build_log(obj, ActivityAction.update, diff))

    for obj in session.deleted:
        if type(obj) in TRACKED_MODELS:
            session.add(_build_log(obj, ActivityAction.delete))


def _after_flush_postexec(session, flush_context):
    pending = session.info.pop(_PENDING_CREATES_KEY, None)
    if not pending:
        return
    for obj in pending:
        session.add(_build_log(obj, ActivityAction.create))
    # `session` is no longer "clean" now that new objects are attached;
    # Session.commit()'s flush loop (see SessionTransaction._prepare_impl)
    # picks this up and performs one more flush before the transaction
    # actually commits, so these log rows land atomically with the change
    # they describe.


def register() -> None:
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "after_flush_postexec", _after_flush_postexec)


def record_login(
    session: Session,
    user: Optional[User],
    success: bool,
    ip: Optional[str] = None,
    username_attempted: Optional[str] = None,
) -> None:
    log = ActivityLog(
        actor_user_id=user.id if user else None,
        actor_username=user.username if user else username_attempted,
        action=ActivityAction.login if success else ActivityAction.login_failed,
        summary=f"{'Login' if success else 'Failed login attempt'} for {(user.username if user else username_attempted) or 'unknown user'}",
        ip_address=ip,
    )
    session.add(log)
    session.commit()


def record_logout(session: Session, user: User, ip: Optional[str] = None) -> None:
    log = ActivityLog(
        actor_user_id=user.id,
        actor_username=user.username,
        action=ActivityAction.logout,
        summary=f"Logout for {user.username}",
        ip_address=ip,
    )
    session.add(log)
    session.commit()
