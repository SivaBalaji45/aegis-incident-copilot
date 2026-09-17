-- Run once against a fresh database before the app's create_all() step.
-- (docker-compose's postgres image already has the pgvector extension binary
-- available via the ankane/pgvector image; this just turns it on.)
CREATE EXTENSION IF NOT EXISTS vector;
