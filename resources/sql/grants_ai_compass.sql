-- Grants for AI Compass Databricks App identity.

GRANT USE CATALOG ON CATALOG maksim_spiridonov TO `0bc41cae-da5e-4aa2-afcb-3e3c9d714fdd`;
GRANT USE SCHEMA ON SCHEMA maksim_spiridonov.ai_compass TO `0bc41cae-da5e-4aa2-afcb-3e3c9d714fdd`;

GRANT SELECT, MODIFY
ON TABLE maksim_spiridonov.ai_compass.conversations
TO `0bc41cae-da5e-4aa2-afcb-3e3c9d714fdd`;

GRANT SELECT, MODIFY
ON TABLE maksim_spiridonov.ai_compass.messages
TO `0bc41cae-da5e-4aa2-afcb-3e3c9d714fdd`;

GRANT SELECT, MODIFY
ON TABLE maksim_spiridonov.ai_compass.users
TO `0bc41cae-da5e-4aa2-afcb-3e3c9d714fdd`;