-- 032_ml_anomalies_config_optional.sql
-- E: the new calibrated statistical detector (core/anomaly_detect.py, method=
-- 'robust_zscore') is config-free — it watches raw metrics directly and is NOT tied to
-- a metadata_ml_configs row the way the old Prophet/LSTM models were. Make ml_config_id
-- nullable so those rows can be stored in the same anomaly table (method distinguishes
-- them). Existing model-bound rows are unaffected.
ALTER TABLE ml_anomalies ALTER COLUMN ml_config_id DROP NOT NULL;
