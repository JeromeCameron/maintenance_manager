-- Migration: add task table
-- Generic task management: users create tasks, optionally cross-referencing
-- a work order, inspection, downtime, issue, asset, purchase order or invoice.

CREATE TYPE taskstatus AS ENUM ('not_started', 'in_progress', 'on_hold', 'completed', 'archived');
CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'urgent');

CREATE TABLE IF NOT EXISTS task (
    id              SERIAL       PRIMARY KEY,
    title           VARCHAR      NOT NULL,
    description     TEXT,
    status          taskstatus   NOT NULL DEFAULT 'not_started',
    priority        taskpriority NOT NULL DEFAULT 'medium',
    due_date        DATE,
    completed_at    TIMESTAMP,
    created_at      TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT now(),

    user_id         INTEGER      REFERENCES "user"(id),
    assigned_to     INTEGER      REFERENCES "user"(id),

    asset_id        VARCHAR      REFERENCES asset(asset_id),
    work_order_id   INTEGER      REFERENCES workorder(work_order_id),
    inspection_id   INTEGER      REFERENCES inspection(id),
    downtime_id     INTEGER      REFERENCES downtime(downtime_id),
    issue_id        INTEGER      REFERENCES issue(id),
    po_no           VARCHAR      REFERENCES purchaseorder(po_no),
    invoice_id      INTEGER      REFERENCES invoice(id)
);

CREATE INDEX IF NOT EXISTS idx_task_status ON task (status);
CREATE INDEX IF NOT EXISTS idx_task_assigned_to ON task (assigned_to);
CREATE INDEX IF NOT EXISTS idx_task_due_date ON task (due_date);
