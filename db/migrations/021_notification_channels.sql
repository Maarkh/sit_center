-- 021_notification_channels.sql
-- Admin-configurable notification routing. Each channel declares its transport
-- (telegram/email/webhook/whatsapp_twilio), its connection config (jsonb), which
-- event types it wants (alert/incident/escalation/predictive/situation/system, or
-- 'all'), and a minimum priority. An event is delivered to every enabled channel
-- whose event_types + min_priority match — so alerts and incidents can route to
-- different channels, several at once, or nowhere (intentional silence).

CREATE TABLE IF NOT EXISTS notification_channels (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    TEXT NOT NULL DEFAULT 'default' REFERENCES tenants(id),
    name         TEXT NOT NULL,
    type         TEXT NOT NULL,                         -- telegram | email | webhook | whatsapp_twilio
    config       JSONB NOT NULL DEFAULT '{}'::jsonb,    -- transport-specific (token, smtp, url, ...)
    event_types  JSONB NOT NULL DEFAULT '[]'::jsonb,    -- ['alert','incident',...] or ['all']
    min_priority TEXT NOT NULL DEFAULT 'info',          -- info | warning | critical
    enabled      BOOLEAN NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notif_channels_tenant ON notification_channels (tenant_id);

-- ✅ notification channels table ready.
