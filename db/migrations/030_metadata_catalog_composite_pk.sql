-- 030_metadata_catalog_composite_pk.sql
-- Fix a cross-tenant isolation/integrity defect in the metric & dimension catalogs.
-- metadata_metrics.metric_name and metadata_dimensions.dimension_key were declared
-- TEXT PRIMARY KEY (GLOBALLY unique) in 001; 006 only ADDED a tenant_id column, never
-- made the key per-tenant. So metadata_service.create_metric/create_dimension's
-- `ON CONFLICT (metric_name)` / `(dimension_key)` upserts are keyed on the global
-- column: tenant B creating a metric whose name tenant A already owns either silently
-- overwrites A's definition (RLS bypassed) or is denied with an existence oracle
-- (RLS effective). Make the catalogs per-tenant.
--
-- Idempotent (DROP IF EXISTS + recreate under the same names). NB: the composite FK
-- re-validates metadata_ml_configs rows — if a prod DB has a legacy ml_config whose
-- (metric_name, tenant_id) doesn't match a metric, this fails loudly (correct: that
-- row was already cross-tenant-inconsistent and must be fixed, not silently kept).

-- The FK depends on the referenced PK, so drop it first.
ALTER TABLE metadata_ml_configs DROP CONSTRAINT IF EXISTS metadata_ml_configs_metric_name_fkey;

-- metadata_metrics: global PK → composite (metric_name, tenant_id)
ALTER TABLE metadata_metrics DROP CONSTRAINT IF EXISTS metadata_metrics_pkey;
ALTER TABLE metadata_metrics ADD CONSTRAINT metadata_metrics_pkey
    PRIMARY KEY (metric_name, tenant_id);

-- metadata_dimensions: global PK → composite (dimension_key, tenant_id)
ALTER TABLE metadata_dimensions DROP CONSTRAINT IF EXISTS metadata_dimensions_pkey;
ALTER TABLE metadata_dimensions ADD CONSTRAINT metadata_dimensions_pkey
    PRIMARY KEY (dimension_key, tenant_id);

-- Re-add the ML-config → metric FK as composite so it references within the same tenant.
ALTER TABLE metadata_ml_configs ADD CONSTRAINT metadata_ml_configs_metric_name_fkey
    FOREIGN KEY (metric_name, tenant_id) REFERENCES metadata_metrics(metric_name, tenant_id)
    ON DELETE CASCADE;

-- ✅ metric/dimension catalogs are now per-tenant; upserts must use the composite key.
