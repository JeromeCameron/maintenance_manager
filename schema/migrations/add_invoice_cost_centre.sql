-- Migration: track which budget line (cost centre) an invoice belongs to
-- Previously an invoice's cost centre could only be inferred by following
-- invoice -> PO -> cost_centre_id, which breaks for invoices without a PO.

ALTER TABLE invoice
    ADD COLUMN IF NOT EXISTS cost_centre_id VARCHAR REFERENCES costcentre(gl_code);
