from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.inspection as inspections
from schema.database import get_session
from schema.models import Inspection, InspectionResult, InspectionTemplate, InspectionTemplateItem

inspection_template_router = APIRouter(prefix="/api/inspection-templates", tags=["InspectionTemplate"])
inspection_template_item_router = APIRouter(prefix="/api/inspection-template-items", tags=["InspectionTemplateItem"])
inspection_router = APIRouter(prefix="/api/inspections", tags=["Inspection"])
inspection_result_router = APIRouter(prefix="/api/inspection-results", tags=["InspectionResult"])


# ------------------------------------------------------------------
# Inspection Template endpoints


@inspection_template_router.get("", status_code=status.HTTP_200_OK, response_model=list[InspectionTemplate])
async def get_inspection_templates(session: Session = Depends(get_session)):
    return inspections.get_inspection_templates(session)


@inspection_template_router.get("/{template_id}", status_code=status.HTTP_200_OK, response_model=InspectionTemplate)
async def get_inspection_template(template_id: int, session: Session = Depends(get_session)):
    template = inspections.get_inspection_template(session, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection template not found")
    return template


@inspection_template_router.post("", status_code=status.HTTP_201_CREATED, response_model=InspectionTemplate)
async def add_inspection_template(template: InspectionTemplate, session: Session = Depends(get_session)):
    return inspections.add_inspection_template(session, template)


@inspection_template_router.put("/{template_id}", status_code=status.HTTP_200_OK, response_model=InspectionTemplate)
async def update_inspection_template(
    template_id: int, data: InspectionTemplate, session: Session = Depends(get_session)
):
    template = inspections.update_inspection_template(session, template_id, data)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection template not found")
    return template


@inspection_template_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection_template(template_id: int, session: Session = Depends(get_session)):
    deleted = inspections.delete_inspection_template(session, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection template not found")


# ------------------------------------------------------------------
# Inspection Template Item endpoints


@inspection_template_item_router.get("", status_code=status.HTTP_200_OK, response_model=list[InspectionTemplateItem])
async def get_inspection_template_items(session: Session = Depends(get_session)):
    return inspections.get_inspection_template_items(session)


@inspection_template_item_router.get("/{item_id}", status_code=status.HTTP_200_OK, response_model=InspectionTemplateItem)
async def get_inspection_template_item(item_id: int, session: Session = Depends(get_session)):
    item = inspections.get_inspection_template_item(session, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection template item not found")
    return item


@inspection_template_item_router.post("", status_code=status.HTTP_201_CREATED, response_model=InspectionTemplateItem)
async def add_inspection_template_item(item: InspectionTemplateItem, session: Session = Depends(get_session)):
    return inspections.add_inspection_template_item(session, item)


@inspection_template_item_router.put("/{item_id}", status_code=status.HTTP_200_OK, response_model=InspectionTemplateItem)
async def update_inspection_template_item(
    item_id: int, data: InspectionTemplateItem, session: Session = Depends(get_session)
):
    item = inspections.update_inspection_template_item(session, item_id, data)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection template item not found")
    return item


@inspection_template_item_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection_template_item(item_id: int, session: Session = Depends(get_session)):
    deleted = inspections.delete_inspection_template_item(session, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection template item not found")


# ------------------------------------------------------------------
# Inspection endpoints


@inspection_router.get("", status_code=status.HTTP_200_OK, response_model=list[Inspection])
async def get_inspections(session: Session = Depends(get_session)):
    return inspections.get_inspections(session)


@inspection_router.get("/asset/{asset_id}", status_code=status.HTTP_200_OK, response_model=list[Inspection])
async def get_inspections_by_asset(asset_id: str, session: Session = Depends(get_session)):
    return inspections.get_inspections_by_asset(session, asset_id)


@inspection_router.get("/{inspection_id}", status_code=status.HTTP_200_OK, response_model=Inspection)
async def get_inspection(inspection_id: int, session: Session = Depends(get_session)):
    inspection = inspections.get_inspection(session, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return inspection


@inspection_router.post("", status_code=status.HTTP_201_CREATED, response_model=Inspection)
async def add_inspection(inspection: Inspection, session: Session = Depends(get_session)):
    return inspections.add_inspection(session, inspection)


@inspection_router.put("/{inspection_id}", status_code=status.HTTP_200_OK, response_model=Inspection)
async def update_inspection(
    inspection_id: int, data: Inspection, session: Session = Depends(get_session)
):
    inspection = inspections.update_inspection(session, inspection_id, data)
    if inspection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return inspection


@inspection_router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection(inspection_id: int, session: Session = Depends(get_session)):
    deleted = inspections.delete_inspection(session, inspection_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")


# ------------------------------------------------------------------
# Inspection Result endpoints


@inspection_result_router.get("", status_code=status.HTTP_200_OK, response_model=list[InspectionResult])
async def get_inspection_results(session: Session = Depends(get_session)):
    return inspections.get_inspection_results(session)


@inspection_result_router.get("/{result_id}", status_code=status.HTTP_200_OK, response_model=InspectionResult)
async def get_inspection_result(result_id: int, session: Session = Depends(get_session)):
    result = inspections.get_inspection_result(session, result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection result not found")
    return result


@inspection_result_router.post("", status_code=status.HTTP_201_CREATED, response_model=InspectionResult)
async def add_inspection_result(result: InspectionResult, session: Session = Depends(get_session)):
    return inspections.add_inspection_result(session, result)


@inspection_result_router.put("/{result_id}", status_code=status.HTTP_200_OK, response_model=InspectionResult)
async def update_inspection_result(
    result_id: int, data: InspectionResult, session: Session = Depends(get_session)
):
    result = inspections.update_inspection_result(session, result_id, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection result not found")
    return result


@inspection_result_router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection_result(result_id: int, session: Session = Depends(get_session)):
    deleted = inspections.delete_inspection_result(session, result_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection result not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
