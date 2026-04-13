-- Unity Catalog bootstrap for AI Compass chat persistence.
--
-- WHERE TO RUN (Databricks UI):
--   1) Open "SQL" / "SQL Editor".
--   2) Pick a running SQL warehouse (top of editor).
--   3) Replace every <CATALOG> below with your UC catalog name (you must have CREATE SCHEMA or use an existing catalog).
--   4) Run the whole script (or statement by statement).
--
-- AFTER TABLES EXIST: ask an admin to GRANT the *Databricks App* identity (not end users):
--   USAGE on catalog + schema; SELECT/INSERT/UPDATE (or MODIFY) on these tables; CAN USE on the SQL warehouse.

CREATE SCHEMA IF NOT EXISTS <CATALOG>.ai_compass;

CREATE TABLE IF NOT EXISTS <CATALOG>.ai_compass.conversations (
  conversation_id STRING NOT NULL,
  user_email STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS <CATALOG>.ai_compass.messages (
  message_id STRING NOT NULL,
  conversation_id STRING NOT NULL,
  user_email STRING NOT NULL,
  role STRING NOT NULL,
  content STRING NOT NULL,
  sequence INT NOT NULL,
  structured_output STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
) USING DELTA;
