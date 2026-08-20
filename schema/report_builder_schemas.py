from typing import Any, Optional

from pydantic import BaseModel, Field

from schema.report_builder_registry import FilterOp


class ReportFilter(BaseModel):
    field: str
    op: FilterOp
    value: Any = None


class CustomReportRequest(BaseModel):
    data_source: str
    fields: list[str] = Field(min_length=1, max_length=30)
    filters: list[ReportFilter] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=1000, ge=1, le=5000)


class CustomReportResponse(BaseModel):
    data_source: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool


class ReportFieldMeta(BaseModel):
    name: str
    label: str
    type: str
    allowed_ops: list[FilterOp]
    enum_values: Optional[list[str]] = None


class ReportSourceMeta(BaseModel):
    name: str
    label: str
    fields: list[ReportFieldMeta]


class ReportBuilderMetadata(BaseModel):
    sources: list[ReportSourceMeta]
