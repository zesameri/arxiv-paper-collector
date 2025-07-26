-- PostgreSQL initialization script for ArXiv Paper Collector

-- Create database if it doesn't exist (this is already handled by POSTGRES_DB env var)
-- But we can add extensions and configurations here

-- Enable useful PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For trigram text search
CREATE EXTENSION IF NOT EXISTS "unaccent";  -- For accent-insensitive search

-- Create custom text search configurations for academic papers
-- This will be useful for full-text search on papers

-- Set some PostgreSQL configurations for better performance
-- These are optional and depend on your hardware
-- ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
-- ALTER SYSTEM SET max_connections = 200;
-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';
-- ALTER SYSTEM SET work_mem = '4MB';
-- ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Create a function for better text search on academic content
CREATE OR REPLACE FUNCTION clean_academic_text(text)
RETURNS text AS $$
BEGIN
    -- Remove common academic noise words and clean text for search
    RETURN regexp_replace(
        unaccent(lower($1)),
        '[^a-z0-9\s]',
        ' ',
        'g'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'ArXiv Paper Collector database initialized successfully';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pg_trgm, unaccent';
    RAISE NOTICE 'Custom functions created for academic text search';
END $$; 