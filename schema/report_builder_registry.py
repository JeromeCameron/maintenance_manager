"""Whitelist registry for the custom report builder.

This module is the ONLY place a user-supplied string (data source name, field
name) is translated into a real SQLAlchemy column. Every lookup goes through
these dicts as key access -- never `getattr(Model, user_string)` and never
string-formatted SQL -- so an unrecognized name simply isn't present as a key
and callers must reject it explicitly.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Type

from sqlalchemy.sql.elements import ColumnElement

from schema.models import (
    Asset,
    AssetCategory,
    Budget,
    CostCentre,
    Downtime,
    DowntimeCause,
    Invoice,
    InvoiceStatus,
    InvoiceType,
    Supplier,
    WorkOrder,
    WorkOrderStatus,
)


class FilterOp(str, Enum):
    eq = "eq"
    in_ = "in"
    gte = "gte"
    lte = "lte"
    contains = "contains"


@dataclass(frozen=True)
class FieldDef:
    column: ColumnElement
    model: Type
    label: str
    py_type: Any
    allowed_ops: tuple = ()


@dataclass(frozen=True)
class SourceDef:
    label: str
    base_model: Type
    fields: dict
    default_order: ColumnElement
    joins: tuple = field(default_factory=tuple)  # ordered (model, join_condition)


SOURCES: dict = {
    "downtime": SourceDef(
        label="Downtime",
        base_model=Downtime,
        default_order=Downtime.start_date,
        joins=(
            (Asset, Downtime.asset_id == Asset.asset_id),
            (DowntimeCause, Downtime.cause_id == DowntimeCause.cause_id),
        ),
        fields={
            "downtime_id": FieldDef(Downtime.downtime_id, Downtime, "Downtime ID", int, (FilterOp.eq, FilterOp.in_)),
            "log_date": FieldDef(Downtime.log_date, Downtime, "Log Date", datetime, (FilterOp.gte, FilterOp.lte)),
            "asset_id": FieldDef(Downtime.asset_id, Downtime, "Asset ID", str, (FilterOp.eq, FilterOp.in_)),
            "cause_id": FieldDef(Downtime.cause_id, Downtime, "Cause ID", int, (FilterOp.eq, FilterOp.in_)),
            "start_date": FieldDef(Downtime.start_date, Downtime, "Start Date", date, (FilterOp.gte, FilterOp.lte)),
            "end_date": FieldDef(Downtime.end_date, Downtime, "End Date", date, (FilterOp.gte, FilterOp.lte)),
            "planned": FieldDef(Downtime.planned, Downtime, "Planned", bool, (FilterOp.eq,)),
            "repeat_failure": FieldDef(Downtime.repeat_failure, Downtime, "Repeat Failure", bool, (FilterOp.eq,)),
            "temporary_fix": FieldDef(Downtime.temporary_fix, Downtime, "Temporary Fix", bool, (FilterOp.eq,)),
            "downtime_hours": FieldDef(Downtime.downtime_hours, Downtime, "Downtime Hours", float, (FilterOp.gte, FilterOp.lte)),
            "component_affected": FieldDef(Downtime.component_affected, Downtime, "Component Affected", str, (FilterOp.contains,)),
            "root_cause": FieldDef(Downtime.root_cause, Downtime, "Root Cause", str, (FilterOp.contains,)),
            "corrective_action": FieldDef(Downtime.corrective_action, Downtime, "Corrective Action", str, (FilterOp.contains,)),
            "details": FieldDef(Downtime.details, Downtime, "Details", str, (FilterOp.contains,)),
            "work_order": FieldDef(Downtime.work_order, Downtime, "Work Order #", str, (FilterOp.eq,)),
            "asset_alias": FieldDef(Asset.alias, Asset, "Asset Alias", str, ()),
            "asset_manufacturer": FieldDef(Asset.manufacturer, Asset, "Asset Manufacturer", str, ()),
            "asset_category": FieldDef(Asset.category, Asset, "Asset Category", AssetCategory, (FilterOp.eq, FilterOp.in_)),
            "cause_name": FieldDef(DowntimeCause.name, DowntimeCause, "Cause Name", str, (FilterOp.eq, FilterOp.in_)),
        },
    ),
    "work_order": SourceDef(
        label="Work Orders",
        base_model=WorkOrder,
        default_order=WorkOrder.issue_date,
        joins=(
            (Asset, WorkOrder.asset_id == Asset.asset_id),
            (Supplier, WorkOrder.supplier_id == Supplier.supplier_id),
        ),
        fields={
            "work_order_id": FieldDef(WorkOrder.work_order_id, WorkOrder, "Work Order ID", int, (FilterOp.eq, FilterOp.in_)),
            "issue_date": FieldDef(WorkOrder.issue_date, WorkOrder, "Issue Date", date, (FilterOp.gte, FilterOp.lte)),
            "expected_date": FieldDef(WorkOrder.expected_date, WorkOrder, "Expected Date", date, (FilterOp.gte, FilterOp.lte)),
            "date_completed": FieldDef(WorkOrder.date_completed, WorkOrder, "Date Completed", date, (FilterOp.gte, FilterOp.lte)),
            "priority": FieldDef(WorkOrder.priority, WorkOrder, "Priority", str, (FilterOp.eq, FilterOp.in_)),
            "typ": FieldDef(WorkOrder.typ, WorkOrder, "Type", str, (FilterOp.eq, FilterOp.in_)),
            "asset_id": FieldDef(WorkOrder.asset_id, WorkOrder, "Asset ID", str, (FilterOp.eq, FilterOp.in_)),
            "status": FieldDef(WorkOrder.status, WorkOrder, "Status", WorkOrderStatus, (FilterOp.eq, FilterOp.in_)),
            "description": FieldDef(WorkOrder.description, WorkOrder, "Description", str, (FilterOp.contains,)),
            "notes": FieldDef(WorkOrder.notes, WorkOrder, "Notes", str, (FilterOp.contains,)),
            "planned": FieldDef(WorkOrder.planned, WorkOrder, "Planned", bool, (FilterOp.eq,)),
            "estimated_cost": FieldDef(WorkOrder.estimated_cost, WorkOrder, "Estimated Cost", float, (FilterOp.gte, FilterOp.lte)),
            "actual_cost": FieldDef(WorkOrder.actual_cost, WorkOrder, "Actual Cost", float, (FilterOp.gte, FilterOp.lte)),
            "estimated_hours": FieldDef(WorkOrder.estimated_hours, WorkOrder, "Estimated Hours", float, (FilterOp.gte, FilterOp.lte)),
            "actual_hours": FieldDef(WorkOrder.actual_hours, WorkOrder, "Actual Hours", float, (FilterOp.gte, FilterOp.lte)),
            "asset_alias": FieldDef(Asset.alias, Asset, "Asset Alias", str, ()),
            "asset_manufacturer": FieldDef(Asset.manufacturer, Asset, "Asset Manufacturer", str, ()),
            "supplier_name": FieldDef(Supplier.name, Supplier, "Supplier Name", str, (FilterOp.eq, FilterOp.in_)),
        },
    ),
    "invoice": SourceDef(
        label="Invoices",
        base_model=Invoice,
        default_order=Invoice.invoice_date,
        joins=(
            (Asset, Invoice.asset_id == Asset.asset_id),
            (Supplier, Invoice.supplier_id == Supplier.supplier_id),
            (CostCentre, Invoice.cost_centre_id == CostCentre.gl_code),
        ),
        fields={
            "id": FieldDef(Invoice.id, Invoice, "Invoice ID", int, (FilterOp.eq, FilterOp.in_)),
            "invoice_no": FieldDef(Invoice.invoice_no, Invoice, "Invoice No", str, (FilterOp.eq, FilterOp.contains)),
            "invoice_date": FieldDef(Invoice.invoice_date, Invoice, "Invoice Date", date, (FilterOp.gte, FilterOp.lte)),
            "job_date": FieldDef(Invoice.job_date, Invoice, "Job Date", date, (FilterOp.gte, FilterOp.lte)),
            "rec_date": FieldDef(Invoice.rec_date, Invoice, "Received Date", date, (FilterOp.gte, FilterOp.lte)),
            "asset_id": FieldDef(Invoice.asset_id, Invoice, "Asset ID", str, (FilterOp.eq, FilterOp.in_)),
            "description": FieldDef(Invoice.description, Invoice, "Description", str, (FilterOp.contains,)),
            "cost_centre_id": FieldDef(Invoice.cost_centre_id, Invoice, "GL Code", str, (FilterOp.eq, FilterOp.in_)),
            "subtotal": FieldDef(Invoice.subtotal, Invoice, "Subtotal", float, (FilterOp.gte, FilterOp.lte)),
            "status": FieldDef(Invoice.status, Invoice, "Status", InvoiceStatus, (FilterOp.eq, FilterOp.in_)),
            "invoice_type": FieldDef(Invoice.invoice_type, Invoice, "Invoice Type", InvoiceType, (FilterOp.eq, FilterOp.in_)),
            "tax_cert": FieldDef(Invoice.tax_cert, Invoice, "Tax Cert", bool, (FilterOp.eq,)),
            "asset_alias": FieldDef(Asset.alias, Asset, "Asset Alias", str, ()),
            "supplier_name": FieldDef(Supplier.name, Supplier, "Supplier Name", str, (FilterOp.eq, FilterOp.in_)),
            "cost_centre_description": FieldDef(CostCentre.description, CostCentre, "Cost Centre Description", str, ()),
        },
    ),
    "budget": SourceDef(
        label="Budget",
        base_model=Budget,
        default_order=Budget.month,
        joins=(
            (CostCentre, Budget.gl_code == CostCentre.gl_code),
        ),
        fields={
            "id": FieldDef(Budget.id, Budget, "Budget ID", int, (FilterOp.eq, FilterOp.in_)),
            "gl_code": FieldDef(Budget.gl_code, Budget, "GL Code", str, (FilterOp.eq, FilterOp.in_)),
            "financial_year": FieldDef(Budget.financial_year, Budget, "Financial Year", str, (FilterOp.eq, FilterOp.in_)),
            "month": FieldDef(Budget.month, Budget, "Month", date, (FilterOp.gte, FilterOp.lte)),
            "amount": FieldDef(Budget.amount, Budget, "Amount", float, (FilterOp.gte, FilterOp.lte)),
            "notes": FieldDef(Budget.notes, Budget, "Notes", str, (FilterOp.contains,)),
            "cost_centre_description": FieldDef(CostCentre.description, CostCentre, "Cost Centre Description", str, ()),
        },
    ),
}
