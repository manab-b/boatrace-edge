from datetime import datetime, timezone


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def validate_observation_cutoff(
    observed_at: datetime,
    cutoff_at: datetime,
) -> None:
    if _aware(observed_at) > _aware(cutoff_at):
        raise ValueError("observation occurs after prediction cutoff")


def validate_ingestion_order(
    observed_at: datetime,
    ingestion_at: datetime,
) -> None:
    if _aware(ingestion_at) < _aware(observed_at):
        raise ValueError("ingestion timestamp precedes source observation")
