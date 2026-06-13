-- Migration: add 'purchase' value to purchaseordertype enum
ALTER TYPE purchaseordertype ADD VALUE IF NOT EXISTS 'purchase';
