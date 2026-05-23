from sqlmodel import Session

import crud.invoice as invoice_crud
from schema.models import Invoice, InvoiceStatus, InvoiceType


def make_invoice(invoice_no: str = "INV-001") -> Invoice:
    return Invoice(
        invoice_no=invoice_no,
        subtotal=1500.00,
        invoice_type=InvoiceType.parts,
        status=InvoiceStatus.processing,
    )


class TestInvoice:
    def test_add_invoice(self, session: Session):
        invoice = invoice_crud.add_invoice(session, make_invoice())
        assert invoice.id is not None
        assert invoice.invoice_no == "INV-001"
        assert invoice.subtotal == 1500.00

    def test_get_invoices_empty(self, session: Session):
        assert invoice_crud.get_invoices(session) == []

    def test_get_invoices(self, session: Session):
        invoice_crud.add_invoice(session, make_invoice("INV-001"))
        invoice_crud.add_invoice(session, make_invoice("INV-002"))
        assert len(invoice_crud.get_invoices(session)) == 2

    def test_get_invoice(self, session: Session):
        added = invoice_crud.add_invoice(session, make_invoice())
        result = invoice_crud.get_invoice(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_invoice_not_found(self, session: Session):
        assert invoice_crud.get_invoice(session, 999) is None

    def test_update_invoice(self, session: Session):
        added = invoice_crud.add_invoice(session, make_invoice())
        updated = make_invoice()
        updated.subtotal = 2000.00
        result = invoice_crud.update_invoice(session, added.id, updated)
        assert result is not None
        assert result.subtotal == 2000.00

    def test_update_invoice_not_found(self, session: Session):
        assert invoice_crud.update_invoice(session, 999, make_invoice()) is None

    def test_delete_invoice(self, session: Session):
        added = invoice_crud.add_invoice(session, make_invoice())
        assert invoice_crud.delete_invoice(session, added.id) is True
        assert invoice_crud.get_invoice(session, added.id) is None

    def test_delete_invoice_not_found(self, session: Session):
        assert invoice_crud.delete_invoice(session, 999) is False
