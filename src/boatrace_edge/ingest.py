from __future__ import annotations

import argparse
import os

from .historical import collect_race
from .historical_batch import collect_outcome_archive_day, collect_outcome_day, validate_batch_range
from .historical_store import mark_date_completed, next_checkpoint_date, store_snapshot, store_snapshots


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest official BOAT RACE historical data")
    parser.add_argument("--date", help="single race date YYYYMMDD")
    parser.add_argument("--venue", help="single race venue code")
    parser.add_argument("--race", type=int, choices=range(1, 13), help="single race number")
    parser.add_argument("--date-from", help="inclusive batch start date YYYYMMDD")
    parser.add_argument("--date-to", help="inclusive batch end date YYYYMMDD")
    parser.add_argument("--venues", help="comma-separated official venue codes, 01 through 24")
    parser.add_argument("--race-start", type=int, default=1, choices=range(1, 13))
    parser.add_argument("--race-end", type=int, default=12, choices=range(1, 13))
    parser.add_argument("--source", choices=("archive", "html"), default="archive")
    parser.add_argument("--resume", action="store_true", help="resume after the last successfully committed calendar day")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("--database-url or DATABASE_URL is required")

    batch_mode = args.date_from is not None or args.date_to is not None or args.venues is not None
    if batch_mode:
        if args.date or args.venue or args.race:
            raise SystemExit("single-race and batch arguments cannot be mixed")
        if not args.date_from or not args.date_to or not args.venues:
            raise SystemExit("batch mode requires --date-from, --date-to, and --venues")
        venues = tuple(value.strip() for value in args.venues.split(",") if value.strip())
        start_date = next_checkpoint_date(args.database_url, args.date_from) if args.resume else args.date_from
        dates = validate_batch_range(
            start=start_date,
            end=args.date_to,
            venues=venues,
            race_start=args.race_start,
            race_end=args.race_end,
        )
        count = 0
        for race_date in dates:
            if args.source == "archive":
                snapshots = collect_outcome_archive_day(
                    race_date,
                    venues,
                    race_start=args.race_start,
                    race_end=args.race_end,
                )
            else:
                snapshots = tuple(
                    snapshot
                    for venue in venues
                    for snapshot in collect_outcome_day(
                        race_date,
                        venue,
                        race_start=args.race_start,
                        race_end=args.race_end,
                    )
                )
            day_count = store_snapshots(args.database_url, snapshots)
            mark_date_completed(args.database_url, race_date)
            count += day_count
            print(f"committed date={race_date} races={day_count}")
        print(f"ingested official outcome races={count} dates={len(dates)} venues={len(venues)} source={args.source}")
        return

    if args.resume:
        raise SystemExit("--resume is only valid in batch mode")
    if not args.date or not args.venue or args.race is None:
        raise SystemExit("single-race mode requires --date, --venue, and --race")
    snapshot = collect_race(args.date, args.venue, args.race)
    store_snapshot(args.database_url, snapshot)
    print(
        f"ingested race={snapshot.race_id} entries={len(snapshot.entries)} "
        f"odds={len(snapshot.odds)} raw_documents={len(snapshot.raw_documents)}"
    )


if __name__ == "__main__":
    main()
