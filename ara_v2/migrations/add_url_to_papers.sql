-- Migration: Add url column to papers table
-- Date: 2025-12-29
-- Description: Adds a url column to store external URLs for papers uploaded via public links

ALTER TABLE papers ADD COLUMN IF NOT EXISTS url VARCHAR(500);

-- Create an index for faster URL lookups (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_papers_url ON papers(url);
