from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Inspection, InspectionResult, InspectionTemplate, InspectionTemplateItem


# ------------------------------------------------------------------
# Inspection Template


def get_inspection_templates(session: Session) -> Sequence[InspectionTemplate]:
    return session.exec(select(InspectionTemplate)).all()


def get_inspection_template(session: Session, template_id: int) -> Optional[InspectionTemplate]:
    return session.get(InspectionTemplate, template_id)


def add_inspection_template(
    session: Session, template: InspectionTemplate
) -> InspectionTemplate:
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def update_inspection_template(
    session: Session, template_id: int, data: InspectionTemplate
) -> Optional[InspectionTemplate]:
    db_template: Optional[InspectionTemplate] = session.get(InspectionTemplate, template_id)
    if db_template is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_template, key, value)
    session.add(db_template)
    session.commit()
    session.refresh(db_template)
    return db_template


def delete_inspection_template(session: Session, template_id: int) -> bool:
    template = session.get(InspectionTemplate, template_id)
    if template is None:
        return False
    session.delete(template)
    session.commit()
    return True


# ------------------------------------------------------------------
# Inspection Template Item


def get_inspection_template_items(session: Session) -> Sequence[InspectionTemplateItem]:
    return session.exec(select(InspectionTemplateItem)).all()


def get_inspection_template_item(
    session: Session, item_id: int
) -> Optional[InspectionTemplateItem]:
    return session.get(InspectionTemplateItem, item_id)


def get_template_items_by_template(
    session: Session, template_id: int
) -> Sequence[InspectionTemplateItem]:
    return session.exec(
        select(InspectionTemplateItem)
        .where(InspectionTemplateItem.template_id == template_id)
        .order_by(InspectionTemplateItem.order)
    ).all()


def add_inspection_template_item(
    session: Session, item: InspectionTemplateItem
) -> InspectionTemplateItem:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_inspection_template_item(
    session: Session, item_id: int, data: InspectionTemplateItem
) -> Optional[InspectionTemplateItem]:
    db_item: Optional[InspectionTemplateItem] = session.get(InspectionTemplateItem, item_id)
    if db_item is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def delete_inspection_template_item(session: Session, item_id: int) -> bool:
    item = session.get(InspectionTemplateItem, item_id)
    if item is None:
        return False
    session.delete(item)
    session.commit()
    return True


# ------------------------------------------------------------------
# Inspection


def get_inspections(session: Session) -> Sequence[Inspection]:
    return session.exec(select(Inspection)).all()


def get_inspections_by_asset(session: Session, asset_id: str) -> Sequence[Inspection]:
    return session.exec(select(Inspection).where(Inspection.asset_id == asset_id)).all()


def get_inspection(session: Session, inspection_id: int) -> Optional[Inspection]:
    return session.get(Inspection, inspection_id)


def add_inspection(session: Session, inspection: Inspection) -> Inspection:
    session.add(inspection)
    session.commit()
    session.refresh(inspection)
    return inspection


def update_inspection(
    session: Session, inspection_id: int, data: Inspection
) -> Optional[Inspection]:
    db_inspection: Optional[Inspection] = session.get(Inspection, inspection_id)
    if db_inspection is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_inspection, key, value)
    session.add(db_inspection)
    session.commit()
    session.refresh(db_inspection)
    return db_inspection


def delete_inspection(session: Session, inspection_id: int) -> bool:
    inspection = session.get(Inspection, inspection_id)
    if inspection is None:
        return False
    session.delete(inspection)
    session.commit()
    return True


# ------------------------------------------------------------------
# Inspection Result


def get_inspection_results(session: Session) -> Sequence[InspectionResult]:
    return session.exec(select(InspectionResult)).all()


def get_inspection_result(session: Session, result_id: int) -> Optional[InspectionResult]:
    return session.get(InspectionResult, result_id)


def get_results_by_inspection(
    session: Session, inspection_id: int
) -> Sequence[InspectionResult]:
    return session.exec(
        select(InspectionResult).where(InspectionResult.inspection_id == inspection_id)
    ).all()


def add_inspection_result(session: Session, result: InspectionResult) -> InspectionResult:
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


def update_inspection_result(
    session: Session, result_id: int, data: InspectionResult
) -> Optional[InspectionResult]:
    db_result: Optional[InspectionResult] = session.get(InspectionResult, result_id)
    if db_result is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_result, key, value)
    session.add(db_result)
    session.commit()
    session.refresh(db_result)
    return db_result


def delete_inspection_result(session: Session, result_id: int) -> bool:
    result = session.get(InspectionResult, result_id)
    if result is None:
        return False
    session.delete(result)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
