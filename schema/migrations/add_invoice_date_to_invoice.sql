-- Migration: add invoice_date to invoice table
ALTER TABLE invoice ADD COLUMN IF NOT EXISTS invoice_date DATE;
