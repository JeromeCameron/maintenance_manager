-- Migration: add contact_number, contact_title, notes, category to supplier

ALTER TABLE supplier
    ADD COLUMN IF NOT EXISTS contact_number VARCHAR,
    ADD COLUMN IF NOT EXISTS contact_title  VARCHAR,
    ADD COLUMN IF NOT EXISTS notes          TEXT,
    ADD COLUMN IF NOT EXISTS category       VARCHAR;
