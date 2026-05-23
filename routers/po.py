from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.po as purchase_orders
from schema.database import get_session
from schema.models import PurchaseOrder

router = APIRouter(prefix="/api/purchase-orders", tags=["PurchaseOrder"])


@router.get("", status_code=status.HTTP_200_OK, response_model=list[PurchaseOrder])
async def get_purchase_orders(session: Session = Depends(get_session)):
    return purchase_orders.get_purchase_orders(session)


@router.get("/{po_no}", status_code=status.HTTP_200_OK, response_model=PurchaseOrder)
async def get_purchase_order(po_no: str, session: Session = Depends(get_session)):
    po = purchase_orders.get_purchase_order(session, po_no)
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return po


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PurchaseOrder)
async def add_purchase_order(po: PurchaseOrder, session: Session = Depends(get_session)):
    return purchase_orders.add_purchase_order(session, po)


@router.put("/{po_no}", status_code=status.HTTP_200_OK, response_model=PurchaseOrder)
async def update_purchase_order(
    po_no: str, data: PurchaseOrder, session: Session = Depends(get_session)
):
    po = purchase_orders.update_purchase_order(session, po_no, data)
    if po is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return po


@router.delete("/{po_no}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(po_no: str, session: Session = Depends(get_session)):
    deleted = purchase_orders.delete_purchase_order(session, po_no)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
