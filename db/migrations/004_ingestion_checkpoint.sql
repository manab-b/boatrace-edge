BEGIN;

CREATE TABLE ingestion_checkpoint (
    pipeline_name TEXT PRIMARY KEY,
    last_completed_date DATE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (last_completed_date IS NULL OR last_completed_date >= DATE '2000-01-01')
);

INSERT INTO ingestion_checkpoint (pipeline_name, last_completed_date)
VALUES ('official_outcome_archive', NULL)
ON CONFLICT (pipeline_name) DO NOTHING;

COMMIT;
