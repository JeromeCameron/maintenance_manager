-- Migration: add 'retired' value to assetstatus enum

ALTER TYPE assetstatus ADD VALUE IF NOT EXISTS 'retired';
