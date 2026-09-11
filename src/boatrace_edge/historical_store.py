from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

import psycopg

from .historical import RaceSnapshot


CHECKPOINT_NAME = "official_outcome_archive"


def _store_snapshot(cur: psycopg.Cursor, snapshot: RaceSnapshot) -> None:
    document_ids: dict[str, str] = {}
    for document in snapshot.raw_documents:
        cur.execute(
            """
            INSERT INTO raw_document
                (source_url, fetched_at, content_sha256, content_type, payload)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (content_sha256) DO NOTHING
            """,
            (document.source_url, document.fetched_at, document.content_sha256, document.content_type, document.payload),
        )
        cur.execute("SELECT document_id::text FROM raw_document WHERE content_sha256 = %s", (document.content_sha256,))
        document_ids[document.source_url] = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO race (race_id, race_date, venue_code, race_number, scheduled_start_at, scheduled_deadline_at, odds_status)
        VALUES (%s, %s, %s, %s, NULL, %s, %s)
        ON CONFLICT (race_id) DO UPDATE SET
            scheduled_deadline_at = EXCLUDED.scheduled_deadline_at,
            odds_status = EXCLUDED.odds_status
        """,
        (snapshot.race_id, snapshot.race_date, snapshot.venue_code, snapshot.race_number, snapshot.scheduled_deadline_at, snapshot.odds_status),
    )

    for entry in snapshot.entries:
        cur.execute(
            """
            INSERT INTO entry (race_id, lane, racer_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (race_id, lane) DO UPDATE SET racer_id = EXCLUDED.racer_id
            """,
            (snapshot.race_id, entry.lane, entry.racer_id),
        )

    if snapshot.odds_status == "COMPLETE":
        odds_document_id = document_ids[snapshot.raw_documents[1].source_url]
        for odd in snapshot.odds:
            cur.execute(
                """
                INSERT INTO historical_odds
                    (race_id, combination, odds, as_of_at, as_of_basis, source_document_id)
                VALUES (%s, %s, %s, NULL, 'CLOSING_ODDS_WITHOUT_SOURCE_TIMESTAMP', %s)
                ON CONFLICT (race_id, combination) DO UPDATE
                SET odds = EXCLUDED.odds, source_document_id = EXCLUDED.source_document_id
                """,
                (snapshot.race_id, odd.combination, odd.odds, odds_document_id),
            )

    cur.execute(
        """
        INSERT INTO race_result
            (race_id, first_lane, second_lane, third_lane, decision, payout_3t, payout_2t)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (race_id) DO UPDATE SET
            first_lane = EXCLUDED.first_lane,
            second_lane = EXCLUDED.second_lane,
            third_lane = EXCLUDED.third_lane,
            decision = EXCLUDED.decision,
            payout_3t = EXCLUDED.payout_3t,
            payout_2t = EXCLUDED.payout_2t
        """,
        (
            snapshot.race_id,
            int(snapshot.result.combination_3t.split("-")[0]),
            int(snapshot.result.combination_3t.split("-")[1]),
            int(snapshot.result.combination_3t.split("-")[2]),
            snapshot.result.decision,
            snapshot.result.payout_3t,
            snapshot.result.payout_2t,
        ),
    )


def store_snapshots(
    database_url: str, snapshots: Iterable[RaceSnapshot], *, completed_date: str | None = None
) -> int:
    """Persist a batch and optional checkpoint in one PostgreSQL transaction."""
    count = 0
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for snapshot in snapshots:
                _store_snapshot(cur, snapshot)
                count += 1
            if completed_date is not None:
                completed = date.fromisoformat(completed_date)
                cur.execute(
                    """
                    INSERT INTO ingestion_checkpoint (pipeline_name, last_completed_date, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (pipeline_name) DO UPDATE SET
                        last_completed_date = EXCLUDED.last_completed_date,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ingestion_checkpoint.last_completed_date IS NULL
                       OR EXCLUDED.last_completed_date > ingestion_checkpoint.last_completed_date
                    """,
                    (CHECKPOINT_NAME, completed),
                )
        conn.commit()
    return count


def store_snapshot(database_url: str, snapshot: RaceSnapshot) -> None:
    store_snapshots(database_url, (snapshot,))


def get_checkpoint(database_url: str) -> date | None:
    """Return the last date whose complete batch was committed."""
    with psycopg.connect(database_url) as conn:
        row = conn.execute(
            "SELECT last_completed_date FROM ingestion_checkpoint WHERE pipeline_name = %s",
            (CHECKPOINT_NAME,),
        ).fetchone()
    return row[0] if row else None


def mark_date_completed(database_url: str, race_date: str) -> None:
    """Advance the checkpoint only after a whole calendar-day batch commits."""
    completed = date.fromisoformat(race_date)
    with psycopg.connect(database_url) as conn:
        conn.execute(
            """
            INSERT INTO ingestion_checkpoint (pipeline_name, last_completed_date, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (pipeline_name) DO UPDATE SET
                last_completed_date = EXCLUDED.last_completed_date,
                updated_at = CURRENT_TIMESTAMP
            WHERE ingestion_checkpoint.last_completed_date IS NULL
               OR EXCLUDED.last_completed_date > ingestion_checkpoint.last_completed_date
            """,
            (CHECKPOINT_NAME, completed),
        )
        conn.commit()


def next_checkpoint_date(database_url: str, start: str) -> str:
    """Return the first date that still needs ingestion at or after start."""
    checkpoint = get_checkpoint(database_url)
    start_date = date.fromisoformat(start)
    if checkpoint is None:
        return start
    return max(start_date, checkpoint + timedelta(days=1)).strftime("%Y%m%d")
