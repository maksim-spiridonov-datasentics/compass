-- AI Compass DB bootstrap for Databricks SQL warehouse.
-- Catalog: maksim_spiridonov
-- Schema: ai_compass
--
-- Where to run:
--   1) Databricks UI -> SQL -> SQL Editor
--   2) Choose a SQL warehouse
--   3) Paste/run this whole script
--
-- NOTE:
-- - CREATE CATALOG may fail if you do not have catalog-admin permissions.
-- - In that case, ask admin to create catalog and grant you use/create schema.

CREATE CATALOG IF NOT EXISTS maksim_spiridonov;
USE CATALOG maksim_spiridonov;
CREATE SCHEMA IF NOT EXISTS ai_compass;
USE SCHEMA ai_compass;

CREATE TABLE IF NOT EXISTS conversations (
  conversation_id STRING NOT NULL,
  user_email STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS messages (
  message_id STRING NOT NULL,
  conversation_id STRING NOT NULL,
  user_email STRING NOT NULL,
  role STRING NOT NULL,
  content STRING NOT NULL,
  sequence INT NOT NULL,
  structured_output STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS conversations (
  conversation_id STRING NOT NULL,
  user_email STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS users (
  user_email STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
) USING DELTA;

-- Optional but recommended for table maintenance/read performance.
OPTIMIZE conversations;
OPTIMIZE messages;
