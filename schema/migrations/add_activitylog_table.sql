-- Migration: add activitylog table
-- Audit trail of data changes (create/update/delete on tracked models) and
-- auth events (login/login_failed/logout), captured automatically via a
-- SQLAlchemy session event listener -- see utils/activity_log.py.

CREATE TYPE activityaction AS ENUM ('create', 'update', 'delete', 'login', 'login_failed', 'logout');

CREATE TABLE IF NOT EXISTS activitylog (
    id              SERIAL         PRIMARY KEY,
    timestamp       TIMESTAMP      NOT NULL DEFAULT now(),
    actor_user_id   INTEGER        REFERENCES "user"(id),
    actor_username  VARCHAR,
    action          activityaction NOT NULL,
    entity_type     VARCHAR,
    entity_id       VARCHAR,
    summary         VARCHAR        NOT NULL,
    changes         TEXT,
    ip_address      VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_activitylog_timestamp ON activitylog (timestamp);
CREATE INDEX IF NOT EXISTS idx_activitylog_actor_user_id ON activitylog (actor_user_id);
CREATE INDEX IF NOT EXISTS idx_activitylog_action ON activitylog (action);
CREATE INDEX IF NOT EXISTS idx_activitylog_entity_type ON activitylog (entity_type);
