from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, select

from schema.report_builder_registry import SOURCES, FilterOp
from schema.report_builder_schemas import (
    CustomReportRequest,
    CustomReportResponse,
    ReportBuilderMetadata,
    ReportFieldMeta,
    ReportSourceMeta,
)

_TYPE_LABELS = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    date: "date",
    datetime: "datetime",
}


def _type_label(py_type: Any) -> str:
    if isinstance(py_type, type) and issubclass(py_type, PyEnum):
        return "enum"
    return _TYPE_LABELS.get(py_type, "string")


def get_report_builder_metadata() -> ReportBuilderMetadata:
    sources = []
    for name, source in SOURCES.items():
        fields = []
        for fname, fdef in source.fields.items():
            enum_values = None
            if isinstance(fdef.py_type, type) and issubclass(fdef.py_type, PyEnum):
                enum_values = [v.value for v in fdef.py_type]
            fields.append(
                ReportFieldMeta(
                    name=fname,
                    label=fdef.label,
                    type=_type_label(fdef.py_type),
                    allowed_ops=list(fdef.allowed_ops),
                    enum_values=enum_values,
                )
            )
        sources.append(ReportSourceMeta(name=name, label=source.label, fields=fields))
    return ReportBuilderMetadata(sources=sources)


def _coerce_scalar(py_type: Any, raw: Any) -> Any:
    if py_type is bool:
        if isinstance(raw, bool):
            return raw
        raise ValueError("expected a boolean value")
    if py_type is date:
        return date.fromisoformat(str(raw))
    if py_type is datetime:
        return datetime.fromisoformat(str(raw))
    if isinstance(py_type, type) and issubclass(py_type, PyEnum):
        try:
            return py_type(raw)
        except ValueError:
            raise ValueError(f"invalid value for {py_type.__name__}")
    if py_type in (int, float, str):
        return py_type(raw)
    raise ValueError("unsupported field type")


def _coerce_value(py_type: Any, op: FilterOp, raw: Any) -> Any:
    try:
        if op == FilterOp.in_:
            if not isinstance(raw, list) or not raw:
                raise ValueError("value must be a non-empty list for the 'in' operator")
            return [_coerce_scalar(py_type, v) for v in raw]
        return _coerce_scalar(py_type, raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {exc}")


def _apply_op(column, op: FilterOp, value):
    if op == FilterOp.eq:
        return column == value
    if op == FilterOp.in_:
        return column.in_(value)
    if op == FilterOp.gte:
        return column >= value
    if op == FilterOp.lte:
        return column <= value
    if op == FilterOp.contains:
        escaped = str(value).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return column.ilike(f"%{escaped}%", escape="\\")
    raise HTTPException(status_code=400, detail=f"Unsupported operator '{op}'")


def run_custom_report(session: Session, req: CustomReportRequest) -> CustomReportResponse:
    source = SOURCES.get(req.data_source)
    if source is None:
        raise HTTPException(status_code=400, detail=f"Unknown data_source '{req.data_source}'")

    unknown_fields = [f for f in req.fields if f not in source.fields]
    if unknown_fields:
        raise HTTPException(status_code=400, detail=f"Unknown field(s): {unknown_fields}")

    unknown_filter_fields = [f.field for f in req.filters if f.field not in source.fields]
    if unknown_filter_fields:
        raise HTTPException(status_code=400, detail=f"Unknown filter field(s): {unknown_filter_fields}")

    select_cols = [source.fields[f].column for f in req.fields]
    stmt = select(*select_cols).select_from(source.base_model)

    needed_models = {source.fields[f].model for f in req.fields}
    needed_models |= {source.fields[f.field].model for f in req.filters}
    for join_model, join_condition in source.joins:
        if join_model in needed_models:
            stmt = stmt.outerjoin(join_model, join_condition)

    for f in req.filters:
        fdef = source.fields[f.field]
        if f.op not in fdef.allowed_ops:
            raise HTTPException(
                status_code=400,
                detail=f"Operator '{f.op.value}' is not allowed on field '{f.field}'",
            )
        value = _coerce_value(fdef.py_type, f.op, f.value)
        stmt = stmt.where(_apply_op(fdef.column, f.op, value))

    stmt = stmt.order_by(source.default_order).limit(req.limit + 1)
    rows = session.exec(stmt).all()
    truncated = len(rows) > req.limit
    rows = rows[: req.limit]

    # sqlmodel's select() returns bare scalars (not Row tuples) when exactly
    # one column is selected -- mirror that with len(req.fields), matching
    # the same `len(entities) == 1` rule select() itself uses.
    if len(req.fields) == 1:
        dict_rows = [{req.fields[0]: r} for r in rows]
    else:
        dict_rows = [dict(zip(req.fields, r)) for r in rows]

    return CustomReportResponse(
        data_source=req.data_source,
        columns=req.fields,
        rows=dict_rows,
        row_count=len(dict_rows),
        truncated=truncated,
    )
