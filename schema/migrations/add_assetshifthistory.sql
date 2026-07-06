-- Migration: add assetshifthistory table
-- Tracks changes to an asset's scheduled daily hours over time.
-- The effective period for each row runs from effective_from up to (but not
-- including) the next row's effective_from for that asset.

CREATE TABLE IF NOT EXISTS assetshifthistory (
    id          SERIAL PRIMARY KEY,
    asset_id    VARCHAR   NOT NULL REFERENCES asset(asset_id) ON DELETE CASCADE,
    effective_from DATE   NOT NULL,
    daily_hours INTEGER   NOT NULL CHECK (daily_hours >= 1)
);

CREATE INDEX IF NOT EXISTS idx_assetshifthistory_asset
    ON assetshifthistory (asset_id, effective_from);
