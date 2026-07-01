from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.invoice as invoices
from schema.database import get_session
from schema.models import Invoice

router = APIRouter(prefix="/api/invoices", tags=["Invoice"])


@router.get("", status_code=status.HTTP_200_OK, response_model=list[Invoice])
async def get_invoices(session: Session = Depends(get_session)):
    return invoices.get_invoices(session)


@router.get("/supplier/{supplier_id}", status_code=status.HTTP_200_OK, response_model=list[Invoice])
async def get_invoices_by_supplier(supplier_id: int, session: Session = Depends(get_session)):
    return invoices.get_invoices_by_supplier(session, supplier_id)


@router.get("/{invoice_id}", status_code=status.HTTP_200_OK, response_model=Invoice)
async def get_invoice(invoice_id: int, session: Session = Depends(get_session)):
    invoice = invoices.get_invoice(session, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Invoice)
async def add_invoice(invoice: Invoice, session: Session = Depends(get_session)):
    return invoices.add_invoice(session, invoice)


@router.put("/{invoice_id}", status_code=status.HTTP_200_OK, response_model=Invoice)
async def update_invoice(
    invoice_id: int, data: Invoice, session: Session = Depends(get_session)
):
    invoice = invoices.update_invoice(session, invoice_id, data)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: int, session: Session = Depends(get_session)):
    deleted = invoices.delete_invoice(session, invoice_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
