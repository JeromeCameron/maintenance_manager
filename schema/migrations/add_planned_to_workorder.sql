-- Migration: add planned column to workorder
-- planned = TRUE (planned), FALSE (unplanned), NULL (not set)

ALTER TABLE workorder
    ADD COLUMN IF NOT EXISTS planned BOOLEAN;
