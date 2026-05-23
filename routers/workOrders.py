from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.workOrders as work_orders
from schema.database import get_session
from schema.models import WorkOrder, WorkOrderPart

router = APIRouter(prefix="/api/work-orders", tags=["WorkOrder"])
work_order_part_router = APIRouter(prefix="/api/work-order-parts", tags=["WorkOrderPart"])


# ------------------------------------------------------------------
# Work Order endpoints


@router.get("", status_code=status.HTTP_200_OK, response_model=list[WorkOrder])
async def get_work_orders(session: Session = Depends(get_session)):
    return work_orders.get_work_orders(session)


@router.get("/{work_order_id}", status_code=status.HTTP_200_OK, response_model=WorkOrder)
async def get_work_order(work_order_id: int, session: Session = Depends(get_session)):
    wo = work_orders.get_work_order(session, work_order_id)
    if not wo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    return wo


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkOrder)
async def add_work_order(work_order: WorkOrder, session: Session = Depends(get_session)):
    return work_orders.add_work_order(session, work_order)


@router.put("/{work_order_id}", status_code=status.HTTP_200_OK, response_model=WorkOrder)
async def update_work_order(
    work_order_id: int, data: WorkOrder, session: Session = Depends(get_session)
):
    wo = work_orders.update_work_order(session, work_order_id, data)
    if wo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    return wo


@router.delete("/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order(work_order_id: int, session: Session = Depends(get_session)):
    deleted = work_orders.delete_work_order(session, work_order_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")


# ------------------------------------------------------------------
# Work Order Part endpoints


@work_order_part_router.get("", status_code=status.HTTP_200_OK, response_model=list[WorkOrderPart])
async def get_work_order_parts(session: Session = Depends(get_session)):
    return work_orders.get_work_order_parts(session)


@work_order_part_router.get("/{work_order_part_id}", status_code=status.HTTP_200_OK, response_model=WorkOrderPart)
async def get_work_order_part(work_order_part_id: int, session: Session = Depends(get_session)):
    wop = work_orders.get_work_order_part(session, work_order_part_id)
    if not wop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order part not found")
    return wop


@work_order_part_router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkOrderPart)
async def add_work_order_part(work_order_part: WorkOrderPart, session: Session = Depends(get_session)):
    return work_orders.add_work_order_part(session, work_order_part)


@work_order_part_router.put("/{work_order_part_id}", status_code=status.HTTP_200_OK, response_model=WorkOrderPart)
async def update_work_order_part(
    work_order_part_id: int, data: WorkOrderPart, session: Session = Depends(get_session)
):
    wop = work_orders.update_work_order_part(session, work_order_part_id, data)
    if wop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order part not found")
    return wop


@work_order_part_router.delete("/{work_order_part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order_part(work_order_part_id: int, session: Session = Depends(get_session)):
    deleted = work_orders.delete_work_order_part(session, work_order_part_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order part not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
