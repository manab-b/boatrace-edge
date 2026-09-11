# Persistent historical DB setup

The historical ingest must use a persistent PostgreSQL database. The PostgreSQL service in the normal CI job is intentionally ephemeral and is only for tests.

## 1. Create a new Supabase project

The previously connected Supabase project is inactive and cannot be restored, so a new project is required.

Recommended region: `ap-northeast-1`.

Supabase's current connection guidance recommends the Session pooler for IPv4-only environments such as GitHub Actions. Copy the connection string from the project's **Connect** dialog and keep the database password private.

## 2. Add the GitHub Actions secret

Repository → Settings → Secrets and variables → Actions → New repository secret:

- Name: `BOATRACE_EDGE_DATABASE_URL`
- Value: the Supabase PostgreSQL **Session pooler** connection string

Do not commit this value to the repository.

## 3. Run the persistent ingest

Open **Actions → Persistent historical ingest → Run workflow**.

Example:

- `date_from`: `20260101`
- `date_to`: `20260401`
- `timeout_minutes`: `3`

The workflow is resumable. Each calendar day is stored in one PostgreSQL transaction. The checkpoint is advanced only after the entire day commits successfully.

If GitHub Actions stops the run because the attempt timeout is reached, already committed days remain in the database. The next run uses `--resume` and starts from the day after `last_completed_date`.

## 4. Verify persistence

The workflow prints:

- last completed ingestion date
- race count
- expected entry count (`races × 6`)
- actual entry count
- result count
- distinct race dates

A canceled workflow does not destroy the persistent database.

## Security

The ingest uses PostgreSQL directly through the connection string; it does not require exposing the historical tables through Supabase's Data API. Never put the database password in source code, workflow YAML, logs, or issues.
