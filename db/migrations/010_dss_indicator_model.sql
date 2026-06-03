-- 010_dss_indicator_model.sql
-- DSS module M2 — Indicator & Goal Model.
-- Links raw metrics to business goals: Goal → Indicator → Factor → Metric.
-- Adds a target corridor (two-sided low/high) and subscriptions per indicator.
-- Purely additive: the monitoring tables (canonical_metrics, metadata_rules, ...)
-- are untouched; indicators reference metrics by name, not by FK, so a metric can
-- come and go without breaking the goal model.

-- === Goals — что мы хотим достичь (бизнес-цель) ===
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    description TEXT,
    owner_role TEXT,                       -- роль, отвечающая за цель
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_goals_tenant ON goals (tenant_id);

CREATE TRIGGER update_goals_updated_at
    BEFORE UPDATE ON goals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- === Indicators — измеримый показатель с целевым коридором ===
CREATE TABLE IF NOT EXISTS indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    unit TEXT NOT NULL DEFAULT '',
    -- Целевой коридор. NULL-граница = сторона не ограничена.
    target_low NUMERIC,
    target_high NUMERIC,
    corridor_type TEXT NOT NULL DEFAULT 'static',   -- static | baseline
    baseline_model_ref TEXT,                         -- ссылка на baseline-модель (для corridor_type='baseline')
    -- Какая сторона выхода за коридор является отклонением.
    direction TEXT NOT NULL DEFAULT 'both',          -- both | below | above
    -- «Хроника»: сколько периодов подряд отклонение держится до повышения приоритета (M3).
    chronicle_threshold INT NOT NULL DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_indicator_corridor_type CHECK (corridor_type IN ('static', 'baseline')),
    CONSTRAINT chk_indicator_direction CHECK (direction IN ('both', 'below', 'above')),
    CONSTRAINT chk_indicator_corridor_order
        CHECK (target_low IS NULL OR target_high IS NULL OR target_low <= target_high)
);

CREATE INDEX IF NOT EXISTS idx_indicators_tenant ON indicators (tenant_id);
CREATE INDEX IF NOT EXISTS idx_indicators_goal ON indicators (goal_id);
CREATE INDEX IF NOT EXISTS idx_indicators_active ON indicators (is_active) WHERE is_active = true;

CREATE TRIGGER update_indicators_updated_at
    BEFORE UPDATE ON indicators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- === Factors — факторы, влияющие на показатель (модель влияния, L2) ===
CREATE TABLE IF NOT EXISTS factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    weight NUMERIC NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_factors_indicator ON factors (indicator_id);


-- === Factor ↔ Metric — какие метрики формируют фактор ===
CREATE TABLE IF NOT EXISTS factor_metrics (
    factor_id UUID NOT NULL REFERENCES factors(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    PRIMARY KEY (factor_id, metric_name)
);


-- === Subscriptions — кто/какая роль следит за показателем ===
CREATE TABLE IF NOT EXISTS indicator_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    indicator_id UUID NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    subscriber_role TEXT,
    subscriber_user TEXT,
    channel TEXT NOT NULL DEFAULT 'in_app',          -- in_app | telegram | email | webhook
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_subscription_target
        CHECK (subscriber_role IS NOT NULL OR subscriber_user IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_indicator ON indicator_subscriptions (indicator_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant ON indicator_subscriptions (tenant_id);

-- ✅ M2 schema ready.
