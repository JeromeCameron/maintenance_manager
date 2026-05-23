from datetime import date

from sqlmodel import Session

import crud.inspection as inspection_crud
from schema.models import (
    AssetCategory,
    Inspection,
    InspectionFrequency,
    InspectionItemResult,
    InspectionResult,
    InspectionTemplate,
    InspectionTemplateItem,
)


def make_inspection_template(name: str = "Daily Baler Check") -> InspectionTemplate:
    return InspectionTemplate(
        name=name,
        asset_type=AssetCategory.baler,
        frequency=InspectionFrequency.daily,
        active=True,
    )


def make_inspection_template_item(question: str = "Is pressure normal?") -> InspectionTemplateItem:
    return InspectionTemplateItem(question=question, is_critical=True)


def make_inspection(inspection_no: str = "INS-2025-001", asset_id: str | None = None) -> Inspection:
    return Inspection(
        inspection_no=inspection_no,
        asset_id=asset_id,
        inspection_date=date(2025, 3, 1),
        overall_result=InspectionItemResult.pass_,
    )


def make_inspection_result() -> InspectionResult:
    return InspectionResult(result=InspectionItemResult.pass_)


class TestInspectionTemplate:
    def test_add_inspection_template(self, session: Session):
        template = inspection_crud.add_inspection_template(session, make_inspection_template())
        assert template.id is not None
        assert template.name == "Daily Baler Check"

    def test_get_inspection_templates_empty(self, session: Session):
        assert inspection_crud.get_inspection_templates(session) == []

    def test_get_inspection_templates(self, session: Session):
        inspection_crud.add_inspection_template(session, make_inspection_template("Template A"))
        inspection_crud.add_inspection_template(session, make_inspection_template("Template B"))
        assert len(inspection_crud.get_inspection_templates(session)) == 2

    def test_get_inspection_template(self, session: Session):
        added = inspection_crud.add_inspection_template(session, make_inspection_template())
        result = inspection_crud.get_inspection_template(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_inspection_template_not_found(self, session: Session):
        assert inspection_crud.get_inspection_template(session, 999) is None

    def test_update_inspection_template(self, session: Session):
        added = inspection_crud.add_inspection_template(session, make_inspection_template())
        updated = make_inspection_template()
        updated.active = False
        result = inspection_crud.update_inspection_template(session, added.id, updated)
        assert result is not None
        assert result.active is False

    def test_update_inspection_template_not_found(self, session: Session):
        assert inspection_crud.update_inspection_template(session, 999, make_inspection_template()) is None

    def test_delete_inspection_template(self, session: Session):
        added = inspection_crud.add_inspection_template(session, make_inspection_template())
        assert inspection_crud.delete_inspection_template(session, added.id) is True
        assert inspection_crud.get_inspection_template(session, added.id) is None

    def test_delete_inspection_template_not_found(self, session: Session):
        assert inspection_crud.delete_inspection_template(session, 999) is False


class TestInspectionTemplateItem:
    def test_add_inspection_template_item(self, session: Session):
        item = inspection_crud.add_inspection_template_item(session, make_inspection_template_item())
        assert item.id is not None
        assert item.question == "Is pressure normal?"

    def test_get_inspection_template_items_empty(self, session: Session):
        assert inspection_crud.get_inspection_template_items(session) == []

    def test_get_inspection_template_items(self, session: Session):
        inspection_crud.add_inspection_template_item(session, make_inspection_template_item("Q1"))
        inspection_crud.add_inspection_template_item(session, make_inspection_template_item("Q2"))
        assert len(inspection_crud.get_inspection_template_items(session)) == 2

    def test_get_inspection_template_item(self, session: Session):
        added = inspection_crud.add_inspection_template_item(session, make_inspection_template_item())
        result = inspection_crud.get_inspection_template_item(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_inspection_template_item_not_found(self, session: Session):
        assert inspection_crud.get_inspection_template_item(session, 999) is None

    def test_update_inspection_template_item(self, session: Session):
        added = inspection_crud.add_inspection_template_item(session, make_inspection_template_item())
        updated = make_inspection_template_item()
        updated.is_critical = False
        result = inspection_crud.update_inspection_template_item(session, added.id, updated)
        assert result is not None
        assert result.is_critical is False

    def test_update_inspection_template_item_not_found(self, session: Session):
        assert inspection_crud.update_inspection_template_item(session, 999, make_inspection_template_item()) is None

    def test_delete_inspection_template_item(self, session: Session):
        added = inspection_crud.add_inspection_template_item(session, make_inspection_template_item())
        assert inspection_crud.delete_inspection_template_item(session, added.id) is True
        assert inspection_crud.get_inspection_template_item(session, added.id) is None

    def test_delete_inspection_template_item_not_found(self, session: Session):
        assert inspection_crud.delete_inspection_template_item(session, 999) is False


class TestInspection:
    def test_add_inspection(self, session: Session):
        inspection = inspection_crud.add_inspection(session, make_inspection())
        assert inspection.id is not None
        assert inspection.inspection_no == "INS-2025-001"

    def test_get_inspections_empty(self, session: Session):
        assert inspection_crud.get_inspections(session) == []

    def test_get_inspections(self, session: Session):
        inspection_crud.add_inspection(session, make_inspection("INS-2025-001"))
        inspection_crud.add_inspection(session, make_inspection("INS-2025-002"))
        assert len(inspection_crud.get_inspections(session)) == 2

    def test_get_inspection(self, session: Session):
        added = inspection_crud.add_inspection(session, make_inspection())
        result = inspection_crud.get_inspection(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_inspection_not_found(self, session: Session):
        assert inspection_crud.get_inspection(session, 999) is None

    def test_update_inspection(self, session: Session):
        added = inspection_crud.add_inspection(session, make_inspection())
        updated = make_inspection()
        updated.overall_result = InspectionItemResult.fail
        result = inspection_crud.update_inspection(session, added.id, updated)
        assert result is not None
        assert result.overall_result == InspectionItemResult.fail

    def test_update_inspection_not_found(self, session: Session):
        assert inspection_crud.update_inspection(session, 999, make_inspection()) is None

    def test_delete_inspection(self, session: Session):
        added = inspection_crud.add_inspection(session, make_inspection())
        assert inspection_crud.delete_inspection(session, added.id) is True
        assert inspection_crud.get_inspection(session, added.id) is None

    def test_delete_inspection_not_found(self, session: Session):
        assert inspection_crud.delete_inspection(session, 999) is False

    def test_get_inspections_by_asset(self, session: Session):
        inspection_crud.add_inspection(session, make_inspection("INS-001", asset_id="ASSET-001"))
        inspection_crud.add_inspection(session, make_inspection("INS-002", asset_id="ASSET-001"))
        inspection_crud.add_inspection(session, make_inspection("INS-003", asset_id="ASSET-002"))
        results = inspection_crud.get_inspections_by_asset(session, "ASSET-001")
        assert len(results) == 2
        assert all(i.asset_id == "ASSET-001" for i in results)

    def test_get_inspections_by_asset_empty(self, session: Session):
        inspection_crud.add_inspection(session, make_inspection("INS-001", asset_id="ASSET-002"))
        results = inspection_crud.get_inspections_by_asset(session, "ASSET-001")
        assert results == []


class TestInspectionResult:
    def test_add_inspection_result(self, session: Session):
        result = inspection_crud.add_inspection_result(session, make_inspection_result())
        assert result.id is not None
        assert result.result == InspectionItemResult.pass_

    def test_get_inspection_results_empty(self, session: Session):
        assert inspection_crud.get_inspection_results(session) == []

    def test_get_inspection_results(self, session: Session):
        inspection_crud.add_inspection_result(session, make_inspection_result())
        inspection_crud.add_inspection_result(session, make_inspection_result())
        assert len(inspection_crud.get_inspection_results(session)) == 2

    def test_get_inspection_result(self, session: Session):
        added = inspection_crud.add_inspection_result(session, make_inspection_result())
        result = inspection_crud.get_inspection_result(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_inspection_result_not_found(self, session: Session):
        assert inspection_crud.get_inspection_result(session, 999) is None

    def test_update_inspection_result(self, session: Session):
        added = inspection_crud.add_inspection_result(session, make_inspection_result())
        updated = make_inspection_result()
        updated.result = InspectionItemResult.fail
        result = inspection_crud.update_inspection_result(session, added.id, updated)
        assert result is not None
        assert result.result == InspectionItemResult.fail

    def test_update_inspection_result_not_found(self, session: Session):
        assert inspection_crud.update_inspection_result(session, 999, make_inspection_result()) is None

    def test_delete_inspection_result(self, session: Session):
        added = inspection_crud.add_inspection_result(session, make_inspection_result())
        assert inspection_crud.delete_inspection_result(session, added.id) is True
        assert inspection_crud.get_inspection_result(session, added.id) is None

    def test_delete_inspection_result_not_found(self, session: Session):
        assert inspection_crud.delete_inspection_result(session, 999) is False
