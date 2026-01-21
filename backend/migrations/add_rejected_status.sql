-- Migration: Add REJECTED status to PolicyStatus enum
-- Run this SQL in your PostgreSQL database

-- Add the new 'rejected' value to the PolicyStatus enum
ALTER TYPE policystatus ADD VALUE IF NOT EXISTS 'rejected';

-- Note: If the enum already has 'rejected', this will do nothing (IF NOT EXISTS)
-- If you get an error that the value already exists, that's fine - just means it was already added

