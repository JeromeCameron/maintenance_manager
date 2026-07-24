-- Migration: link work order parts to the stock transaction they generate
-- Checking a part out on a work order now auto-creates a matching "issue"
-- stock transaction instead of requiring a separate manual entry.

ALTER TABLE workorderpart
    ADD COLUMN IF NOT EXISTS location_id INTEGER REFERENCES location(location_id),
    ADD COLUMN IF NOT EXISTS stock_transaction_id INTEGER REFERENCES stocktransaction(id);
