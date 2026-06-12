-- Add baler spec columns to assetmodel
ALTER TABLE assetmodel
  ADD COLUMN IF NOT EXISTS bale_weight INTEGER,
  ADD COLUMN IF NOT EXISTS bale_time   INTEGER,
  ADD COLUMN IF NOT EXISTS ram_force   INTEGER,
  ADD COLUMN IF NOT EXISTS bale_size   VARCHAR,
  ADD COLUMN IF NOT EXISTS baler_type  VARCHAR,
  ADD COLUMN IF NOT EXISTS baler_size  VARCHAR;

-- Migrate existing per-asset baler data up to the model level
-- (uses the first baler record found for each model; assumes same-model units share specs)
UPDATE assetmodel am
SET
  bale_weight = b.bale_weight,
  bale_time   = b.bale_time,
  ram_force   = b.ram_force,
  bale_size   = b.bale_size,
  baler_type  = b.baler_type::VARCHAR,
  baler_size  = b.baler_size::VARCHAR
FROM baler b
JOIN asset a ON b.asset_id = a.asset_id
WHERE am.model_no = a.model_no;

-- Drop the now-redundant baler table
DROP TABLE IF EXISTS baler;
