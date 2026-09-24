-- Migration: add downtime exacerbating-factor tables
-- Tracks factors that prolong a downtime beyond hands-on repair time
-- (parts on back-order, supplier account on hold pending payment, waiting on an
-- external contractor or PO approval, etc.) so extended downtime outside the
-- maintenance team's control can be justified and reported on.

CREATE TABLE IF NOT EXISTS downtimefactortype (
    factor_type_id  SERIAL   PRIMARY KEY,
    name            VARCHAR  NOT NULL UNIQUE,
    description     VARCHAR,
    active          BOOLEAN  NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS downtimefactor (
    id              SERIAL            PRIMARY KEY,
    downtime_id     INTEGER           NOT NULL REFERENCES downtime(downtime_id) ON DELETE CASCADE,
    factor_type_id  INTEGER           REFERENCES downtimefactortype(factor_type_id),
    delay_hours     DOUBLE PRECISION,
    start_date      DATE,
    start_time      TIME,
    end_date        DATE,
    end_time        TIME,
    resolved        BOOLEAN,
    notes           TEXT
);

-- start_time / end_time were added after the initial cut; keep re-runs in step.
ALTER TABLE downtimefactor ADD COLUMN IF NOT EXISTS start_time TIME;
ALTER TABLE downtimefactor ADD COLUMN IF NOT EXISTS end_time TIME;

CREATE INDEX IF NOT EXISTS idx_downtimefactor_downtime ON downtimefactor (downtime_id);
CREATE INDEX IF NOT EXISTS idx_downtimefactor_type ON downtimefactor (factor_type_id);

-- Seed the common factor types (safe to re-run).
INSERT INTO downtimefactortype (name, description) VALUES
    ('Parts unavailable / on back-order', 'Required spare part not in stock; awaiting delivery'),
    ('Supplier account on hold',          'Supplier will not supply or attend until outstanding payments are settled'),
    ('Awaiting external contractor',       'Specialist or OEM technician not available on site'),
    ('Awaiting PO / approval',             'Purchase order or management approval pending before work can proceed'),
    ('Awaiting supplier quote',            'Waiting on a quotation before the repair can be authorised'),
    ('Access / safety restriction',        'Asset could not be worked on due to access, permit or safety constraints'),
    ('Labour unavailable',                 'No qualified technician available'),
    ('Diagnosis delay',                    'Extended fault-finding or an intermittent fault'),
    ('Weather',                            'Weather prevented work from proceeding')
ON CONFLICT (name) DO NOTHING;
