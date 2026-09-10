from __future__ import annotations

import argparse
import os

from .historical import collect_race
from .historical_store import store_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest one official BOAT RACE historical race")
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--venue", required=True, help="two-digit BOAT RACE venue code")
    parser.add_argument("--race", required=True, type=int, choices=range(1, 13))
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("--database-url or DATABASE_URL is required")

    snapshot = collect_race(args.date, args.venue, args.race)
    store_snapshot(args.database_url, snapshot)
    print(
        f"ingested race={snapshot.race_id} entries={len(snapshot.entries)} "
        f"odds={len(snapshot.odds)} raw_documents={len(snapshot.raw_documents)}"
    )


if __name__ == "__main__":
    main()
