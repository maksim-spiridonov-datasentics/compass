-- Grants for AI Compass Databricks App identity.
-- Run in Databricks SQL Editor using an admin/owner principal.
--
-- Replace these placeholders first:
--   <APP_PRINCIPAL>  : Databricks App service principal identity
--   <WAREHOUSE_NAME> : SQL warehouse name (optional if granted in UI already)

GRANT USE CATALOG ON CATALOG maksim_spiridonov TO `<APP_PRINCIPAL>`;
GRANT USE SCHEMA ON SCHEMA maksim_spiridonov.ai_compass TO `<APP_PRINCIPAL>`;

GRANT SELECT, INSERT, UPDATE
ON TABLE maksim_spiridonov.ai_compass.conversations
TO `<APP_PRINCIPAL>`;

GRANT SELECT, INSERT, UPDATE
ON TABLE maksim_spiridonov.ai_compass.messages
TO `<APP_PRINCIPAL>`;

GRANT SELECT, INSERT, UPDATE
ON TABLE maksim_spiridonov.ai_compass.users
TO `<APP_PRINCIPAL>`;

-- Optional if you prefer SQL grants over App Resource permissions in UI.
-- If your workspace disallows this syntax, grant "Can use" in warehouse UI instead.
GRANT USAGE ON WAREHOUSE `<WAREHOUSE_NAME>` TO `<APP_PRINCIPAL>`;
