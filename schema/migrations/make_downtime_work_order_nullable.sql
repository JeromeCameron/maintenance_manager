-- Migration: make work_order column nullable on downtime table
-- work_order is not always created before a downtime is logged

ALTER TABLE downtime
    ALTER COLUMN work_order DROP NOT NULL;
