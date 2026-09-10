BEGIN;

CREATE TABLE race (
    race_id TEXT PRIMARY KEY,
    race_date DATE NOT NULL,
    venue_code TEXT NOT NULL,
    race_number SMALLINT NOT NULL CHECK (race_number BETWEEN 1 AND 12),
    scheduled_start_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE entry (
    race_id TEXT NOT NULL REFERENCES race(race_id),
    lane SMALLINT NOT NULL CHECK (lane BETWEEN 1 AND 6),
    racer_id TEXT NOT NULL,
    PRIMARY KEY (race_id, lane),
    UNIQUE (race_id, racer_id)
);

CREATE TABLE odds_snapshot (
    race_id TEXT NOT NULL REFERENCES race(race_id),
    combination TEXT NOT NULL,
    odds NUMERIC(12,4) NOT NULL CHECK (odds > 0),
    observed_at TIMESTAMPTZ NOT NULL,
    ingestion_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (race_id, combination, observed_at),
    CHECK (ingestion_at >= observed_at)
);

CREATE TABLE prediction_audit (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id TEXT NOT NULL REFERENCES race(race_id),
    generated_at TIMESTAMPTZ NOT NULL,
    feature_cutoff_at TIMESTAMPTZ NOT NULL,
    odds_cutoff_at TIMESTAMPTZ NOT NULL,
    model_version TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    data_version TEXT NOT NULL,
    CHECK (feature_cutoff_at <= generated_at),
    CHECK (odds_cutoff_at <= generated_at)
);

CREATE TABLE settlement (
    race_id TEXT NOT NULL REFERENCES race(race_id),
    combination TEXT NOT NULL,
    stake NUMERIC(14,2) NOT NULL CHECK (stake > 0),
    payout NUMERIC(14,2) NOT NULL CHECK (payout >= 0),
    status TEXT NOT NULL CHECK (status IN ('WIN','LOSS','REFUND','VOID','UNKNOWN')),
    PRIMARY KEY (race_id, combination)
);

CREATE INDEX idx_odds_snapshot_race_observed
    ON odds_snapshot (race_id, observed_at);

CREATE INDEX idx_prediction_audit_race_generated
    ON prediction_audit (race_id, generated_at);

COMMIT;
