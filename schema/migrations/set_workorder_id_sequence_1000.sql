-- Migration: start work order IDs at 1000
ALTER SEQUENCE workorder_work_order_id_seq RESTART WITH 1000;
