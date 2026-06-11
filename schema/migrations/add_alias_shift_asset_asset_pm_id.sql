-- Migration: add alias (asset), shift_asset (downtime), asset_pm_id (workorder)

-- asset.alias — nullable varchar, no default
ALTER TABLE asset
    ADD COLUMN IF NOT EXISTS alias VARCHAR;

-- downtime.shift_asset — bool, not null; default false covers existing rows
ALTER TABLE downtime
    ADD COLUMN IF NOT EXISTS shift_asset BOOLEAN NOT NULL DEFAULT FALSE;

-- workorder.asset_pm_id — nullable int + FK to assetpm
ALTER TABLE workorder
    ADD COLUMN IF NOT EXISTS asset_pm_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'workorder'
          AND constraint_name = 'fk_workorder_asset_pm_id'
    ) THEN
        ALTER TABLE workorder
            ADD CONSTRAINT fk_workorder_asset_pm_id
            FOREIGN KEY (asset_pm_id) REFERENCES assetpm(id) ON DELETE SET NULL;
    END IF;
END $$;
