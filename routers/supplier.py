from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.supplier as suppliers
from schema.database import get_session
from schema.models import Supplier

router = APIRouter(prefix="/api/suppliers", tags=["Supplier"])


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Supplier])
async def get_suppliers(session: Session = Depends(get_session)):
    return suppliers.get_suppliers(session)


@router.get("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=Supplier)
async def get_supplier(supplier_id: int, session: Session = Depends(get_session)):
    supplier = suppliers.get_supplier(session, supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Supplier)
async def add_supplier(supplier: Supplier, session: Session = Depends(get_session)):
    return suppliers.add_supplier(session, supplier)


@router.put("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=Supplier)
async def update_supplier(
    supplier_id: int, data: Supplier, session: Session = Depends(get_session)
):
    supplier = suppliers.update_supplier(session, supplier_id, data)
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: int, session: Session = Depends(get_session)):
    deleted = suppliers.delete_supplier(session, supplier_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
