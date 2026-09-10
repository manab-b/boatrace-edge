BEGIN;

ALTER TABLE race
    ALTER COLUMN scheduled_start_at DROP NOT NULL;

ALTER TABLE race
    ADD COLUMN IF NOT EXISTS scheduled_deadline_at TIMESTAMPTZ;

CREATE TABLE raw_document (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    content_sha256 CHAR(64) NOT NULL UNIQUE,
    content_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE race_result (
    race_id TEXT PRIMARY KEY REFERENCES race(race_id),
    first_lane SMALLINT NOT NULL CHECK (first_lane BETWEEN 1 AND 6),
    second_lane SMALLINT NOT NULL CHECK (second_lane BETWEEN 1 AND 6),
    third_lane SMALLINT NOT NULL CHECK (third_lane BETWEEN 1 AND 6),
    decision TEXT NOT NULL,
    payout_3t NUMERIC(12,2) CHECK (payout_3t >= 0),
    payout_2t NUMERIC(12,2) CHECK (payout_2t >= 0),
    CHECK (first_lane <> second_lane),
    CHECK (first_lane <> third_lane),
    CHECK (second_lane <> third_lane)
);

CREATE TABLE historical_odds (
    race_id TEXT NOT NULL REFERENCES race(race_id),
    combination TEXT NOT NULL,
    odds NUMERIC(12,4) NOT NULL CHECK (odds > 0),
    as_of_at TIMESTAMPTZ,
    as_of_basis TEXT NOT NULL CHECK (as_of_basis IN ('SOURCE_OBSERVED','CLOSING_ODDS_WITHOUT_SOURCE_TIMESTAMP')),
    source_document_id UUID NOT NULL REFERENCES raw_document(document_id),
    PRIMARY KEY (race_id, combination)
);

CREATE INDEX idx_raw_document_source_fetched
    ON raw_document (source_url, fetched_at);

CREATE INDEX idx_historical_odds_race
    ON historical_odds (race_id);

CREATE FUNCTION reject_raw_document_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'raw_document is immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER raw_document_immutable
BEFORE UPDATE OR DELETE ON raw_document
FOR EACH ROW EXECUTE FUNCTION reject_raw_document_mutation();

COMMIT;
