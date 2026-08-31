# RetailPulse

A production-oriented retail data engineering platform: synthetic OLTP data
generation, idempotent batch ingestion, dimensional modeling, SCD Type 2,
incremental analytics, data-quality gates, pipeline lifecycle/retry
observability, and operational SQL views — all on PostgreSQL and Python.

This README is both a usage guide and the implementation report for the
idempotency → recovery → quality persistence → incremental ETL → SCD2 →
observability → CI/Docker work described below.

## Quick start

```powershell
# 1. Start PostgreSQL (healthchecked; waits for readiness itself)
docker compose up -d

# 2. Install Python dependencies
uv sync

# 3. Apply the schema (two tracks — see "Migrations" below)
#    a. Source/OLTP schema (retail.*) auto-applies on first container boot
#       via docker-entrypoint-initdb.d. On an already-running container,
#       or to re-apply by hand:
Get-ChildItem scripts/sql/*.sql | ForEach-Object {
    Get-Content $_.FullName | docker exec -i retailpulse-postgres psql -U retailpulse -d retailpulse
}

#    b. Warehouse schema (analytics.*) — always manual, in order:
Get-ChildItem migrations/*.sql | ForEach-Object {
    Get-Content $_.FullName | docker exec -i retailpulse-postgres psql -U retailpulse -d retailpulse
}

# 4. Run the pipeline
uv run python -m retailpulse.pipeline.runner

# 5. Run the tests
uv run pytest tests -v
```

`.env.example` documents the Postgres connection variables; copy it to
`.env` to override the safe local defaults baked into
`src/retailpulse/config/settings.py`.

## Architecture

```
                    Scheduler / Orchestrator (Airflow — see airflow/dags/)
                              |
                              v
                    +-------------------+
                    |   Pipeline Runner |   run_pipeline() / resume_pipeline()
                    +-------------------+
                              |
                +-------------+-------------+
                |                           |
                v                           v
       Transaction Ingestion        Analytics Build
       (retail.* source schema)    (extract -> load -> mart refresh)
                |                           |
                v                           v
          Data Quality                 Analytics Marts
       (reconciliation + checks)    (daily_sales, product/customer/
                |                    store performance)
                v
        PostgreSQL Warehouse (analytics.*)

Operational layer:               Retry layer:
  pipeline_runs                    run_with_retry()
  pipeline_stage_runs                |-- transient failure -> retry
  ingestion_quality_results          |-- stage attempt persistence
  pipeline_watermarks                |-- error classification
  v_pipeline_health / _failures /
  _stage_summary / _latest_pipeline_runs
```

Two schemas, two migration tracks, by design:

- **`retail.*`** — the OLTP source system (customers, products, orders, ...).
  DDL lives in `scripts/sql/`, mounted into Postgres as
  `docker-entrypoint-initdb.d`, so it **auto-applies on a fresh container**.
- **`analytics.*`** — the dimensional warehouse (dims, facts, marts, pipeline
  operational tables). DDL lives in `migrations/`, applied **manually** (see
  Quick start) — there is no migration-runner tool in this project; files are
  numbered and applied in order with `psql`.

Both tracks were verified in this work to apply cleanly in order on a
completely fresh `postgres:17` container (see "What was broken" below —
this used to fail).

## What already existed

Before this pass, RetailPulse had a solid, tested core:

- Deterministic Faker-based data generation for the full retail domain.
- Idempotent, checkpointed, resumable transaction ingestion
  (`generators/transaction_ingestion.py`) with physical-batch-level
  checkpointing, deterministic batch IDs (`uuid5` of logical_run_id), and
  failure injection for testing.
- Reconciliation and quality checks (order/item counts, duplicates, orphans,
  financial totals).
- A generic, PostgreSQL-agnostic retry primitive (`pipeline/retry.py`) and
  error classification (`pipeline/errors.py`).
- Stage-level lifecycle tracking (`pipeline/stage_runner.py` +
  `stage_repository.py`) layered cleanly under the pipeline runner.
- Dimensional schema (6 dims, 2 facts, 4 marts) with correct
  `order_date_key`/`category_id` modeling.
- 102 passing tests.

## What was missing or broken, and what changed

### Phase 1 — Logical-run idempotency

The unique index on `pipeline_runs.logical_run_id` already existed, but
`start_pipeline_run()` had no handling for the conflict it created — a
duplicate `logical_run_id` would raise a raw, unhandled `UniqueViolation`.

- `start_pipeline_run()` now does `INSERT ... ON CONFLICT (logical_run_id)
  DO NOTHING RETURNING pipeline_run_id`, and raises a new
  `DuplicateLogicalRunError` (carrying the existing run's id/status) only
  when the conflict is real — the database's unique index is the actual
  safety boundary, not an application-level check-then-insert, so this is
  race-safe by construction.
- `run_pipeline()` catches that error and returns a new `PipelineStatus.
  SKIPPED` result describing the existing run, instead of crashing or
  silently re-running the workload. SUCCESS/RUNNING/FAILED all produce a
  distinct message; FAILED points at `resume_pipeline()`.
- Migrations `017`–`019` (renumbered from a `009`/`010` filename collision —
  see "Repo hygiene" below) plus new tests in `test_pipeline_idempotency.py`.

### Phase 2 — Recovery / resume

Fully greenfield. Since `logical_run_id` is now unique, a logical run has
**at most one** `pipeline_runs` row ever — so resuming a FAILED run reopens
that same row (`reopen_failed_pipeline_run`, a race-safe conditional
`UPDATE ... WHERE status = 'FAILED'`) rather than minting a new
`pipeline_run_id`. `resume_pipeline()` then re-enters the same stage
execution path as `run_pipeline()` (extracted into a shared
`_execute_pipeline_stages()` to avoid duplicating ~250 lines of stage
try/except logic), skipping `transaction_ingestion` entirely if it already
completed. See `test_pipeline_recovery.py`.

### Phase 3 — Operational SQL views

Greenfield. `migrations/020` adds `v_latest_pipeline_runs`,
`v_pipeline_stage_summary`, `v_pipeline_failures`, and `v_pipeline_health`
(the last rolls up retry counts and the terminal failed stage — deliberately
`NULL` for runs that failed a stage but succeeded on retry, since that's not
a health concern). Validated in `test_pipeline_operational_views.py`.

### Phase 4 — Quality result persistence

A `retail.ingestion_quality_results` table already existed but wasn't
linked to a pipeline run and had no check classification. Also found: three
independent, overlapping reimplementations of the same reconciliation
checks (`quality/checks.py`, `quality/report.py`, `quality/reconciliation.py`)
plus a fourth shadow model in `quality/source_checks.py` with a
name-colliding `QualityCheckResult`.

- `migrations/023` adds `pipeline_run_id` (FK to `analytics.pipeline_runs`),
  `check_type` (COMPLETENESS/UNIQUENESS/REFERENTIAL_INTEGRITY/
  FINANCIAL_CONSISTENCY), and `severity` to `ingestion_quality_results`.
- `run_and_persist_transaction_quality()` now threads `pipeline_run_id`
  through from the pipeline runner.
- Reconciliation/quality failures now raise `DataQualityError` instead of a
  bare `RuntimeError` — this matters because `run_with_retry()` explicitly
  never retries `DataQualityError` (retrying a deterministic data mismatch 3
  times is pure waste and was happening silently before).
- Deleted the dead duplicate: `quality/report.py`, `quality/source_checks.py`,
  and their only caller, the unused legacy CLI `generators/runner.py`.

### Phase 5 — Watermarks / incremental processing

**This is where testing against a fresh database, not just the warm shared
dev DB, mattered most** — see "What a fresh-DB test caught" below.

- `migrations/021` adds `analytics.pipeline_watermarks`
  (`pipeline_name, source_name, watermark_column, watermark_value`).
- `analytics/build.py::build_analytics()` was rewritten. It previously
  **only rebuilt marts from whatever facts already happened to exist** — it
  never actually loaded new orders from `retail.*` into the warehouse. It
  now: extracts+loads dimensions (full refresh — cheap, idempotent), reads
  the orders/order_items watermarks, extracts+loads only rows with
  `id > watermark`, refreshes marts, and **only then** advances the
  watermarks. If anything upstream raises, the watermark advance is never
  reached, so the next attempt reprocesses the same increment — verified in
  `test_incremental_analytics.py::test_watermark_does_not_advance_when_mart_refresh_fails`.
- The watermark column is `order_id`/`order_item_id`, not a timestamp —
  RetailPulse's IDs are monotonically assigned, so this sidesteps
  clock-skew/late-arrival edge cases a timestamp watermark would have.

### Phase 6 — SCD Type 2 (`dim_customer.customer_segment`)

Greenfield. `migrations/022` adds `valid_from`/`valid_to`/`is_current`, and
— critically — **drops** the old `customer_id`/`customer_number` UNIQUE
constraints (which assumed one row per customer forever) and replaces them
with **partial unique indexes** (`... WHERE is_current`), since SCD2
legitimately has multiple historical rows per business key.

`customer_loader.py` implements the versioning as three set-based SQL
statements against a staged COPY, not per-row Python branching: (1) close
the current row where `customer_segment` changed, (2) open a new current
row for anything with no current row (new customers + just-closed ones),
(3) in-place update of non-segment attributes for unchanged-segment
customers. Only `customer_segment` is versioned — phone/city/status etc.
are overwritten Type-1-style on the current row, which is how most
production SCD2 dimensions actually mix Type 1 and Type 2 on one table.

`order_fact_loader.py`'s customer join was updated to filter
`is_current = TRUE` — without that, a customer with 2+ historical rows
would fan-out the JOIN and corrupt the fact load. See
`test_customer_scd2.py`.

### Phase 13 — Code quality

- `ruff check --fix` across `src`/`tests`: 153 mechanical fixes (unused
  imports, import ordering, `datetime.timezone.utc` → `datetime.UTC`).
  19 pre-existing findings intentionally left (test-file `datetime()` calls
  without `tzinfo`, two deliberate broad `except Exception` at the pipeline
  stage-failure boundary — that breadth is the architecture, not a bug).
- `mypy src`: fixed the 4 findings in code from this pass (a shared
  `_fetch_scalar()` helper replacing `cursor.fetchone()[0]`, which mypy
  correctly flags as possibly-`None`). 13 pre-existing occurrences of the
  same pattern in `quality/checks.py`, `quality/reconciliation.py`, and
  `generators/bootstrap.py` were left as a known, low-severity limitation
  rather than rewriting files outside this pass's scope.
- Deleted dead code: `generators/runner.py`, `quality/report.py`,
  `quality/source_checks.py`, the empty `analytics/config.py`, and the
  entire `docker/postgres/init/` directory (a stale, unreferenced duplicate
  of `scripts/sql/` — `docker-compose.yml` mounts `scripts/sql`, not this).

### Performance (Phase 8)

`analytics/build.py` calling the loaders for the first time (see below)
immediately hit a real bottleneck: `load_fact_orders`/`load_fact_order_items`
did one `SELECT` + one `INSERT` **per row** to resolve dimension surrogate
keys. This dev database has ~300K accumulated orders / ~620K order items
from repeated test runs; the first incremental backfill was still running
after 20+ minutes.

Rewrote all 7 loaders (`order_fact_loader`, `order_item_fact_loader`,
`category_loader`, `supplier_loader`, `product_loader`, `customer_loader`,
`store_loader`) to stage rows via `COPY` into a temp table, then resolve
keys and upsert with a single set-based `INSERT ... SELECT ... JOIN ... ON
CONFLICT` — turning O(n) round trips into O(1) per batch. Result: the full
test suite went from "still running after 3 minutes" to **56 seconds**, and
a clean 50K-order pipeline run completes end-to-end in well under two
minutes (numbers below).

**Bug this surfaced**: the temp tables were created with a bare `CREATE TEMP
TABLE` (no `IF NOT EXISTS`). `ON COMMIT DROP` only fires at COMMIT, and a
stage retried within the same still-open transaction (e.g.
`run_stage_with_retry`'s `max_attempts=3`) calls the loader again in the
*same* transaction — the second attempt's `CREATE TEMP TABLE` would fail
with "already exists", masking the original transient error. Fixed in all 7
loaders (and the pre-existing `generators/bulk_loaders.py`, which had the
identical bug) with `CREATE TEMP TABLE IF NOT EXISTS` + `TRUNCATE`.

**Benchmark** (`GeneratorConfig()` defaults: 50,000 orders / ~102K order
items, run against this dev DB with its existing ~300K-order backlog —
watermarks mean only the new 50K were processed by `build_analytics`):

| Stage | Count | Duration | Rate |
|---|---|---|---|
| Transaction ingestion | 50,000 orders / 102,275 items | 53.1s | ~942 orders/s |
| Analytics build (extract+load+4 marts) | incremental (50K new) | ~20s | — |
| **Total end-to-end** | | **72.8s** | **~687 orders/s** |

`EXPLAIN (ANALYZE, BUFFERS)` on the `mart_daily_sales` aggregation (full
scan + parallel hash-aggregate over the entire `fact_order`/`fact_order_item`
tables, ~350K rows at benchmark time): **96.6ms**. This is why marts are
**not** incrementalized (Phase 7) — a full rebuild is already sub-100ms at
this scale; incremental mart maintenance would add real complexity (tracking
which date/product/customer/store buckets are dirty) for no measurable
benefit until fact tables reach a much larger scale. Documented tradeoff,
not an oversight.

### What a fresh-DB test caught (important)

The existing test suite — and this dev environment — never ran against a
**genuinely empty** database; it always ran against one already warmed up by
prior manual/test runs. Running the actual pipeline against a brand-new
`postgres:17` container (after applying `scripts/sql/` + `migrations/` in
order) surfaced three real, previously-invisible bugs, all now fixed:

1. **No reference-data bootstrap in the automated path.** `run_pipeline()`
   assumed `retail.categories/suppliers/stores/products/customers` already
   existed. The only code that ever called
   `bootstrap.reference_data_is_ready()` / `reference_loader.
   bootstrap_reference_data()` was the dead `generators/runner.py` — deleted
   in the Phase 13 cleanup, which would have made this gap permanent. Fixed
   by wiring an idempotent bootstrap check into the `transaction_ingestion`
   stage itself (`_ensure_reference_data_and_ingest()` in `pipeline/
   runner.py`), so it's retried/observed like any other stage work.
2. **No date-dimension bootstrap in the automated path.** `dim_date` was
   only ever populated by a standalone script
   (`populate_date_dimension.py`) nobody calls automatically. Fixed with
   `_ensure_date_dimension_covers_orders()` in `analytics/build.py`, which
   extends `dim_date` to cover whatever range is actually present in
   `retail.orders` — self-healing, and decoupled from `GeneratorConfig`.
3. **The `scripts/sql/` migration order was actually broken for a fresh
   bootstrap**: two files shared the `005` prefix
   (`005_create_ingestion_batch_parts.sql` / `005_create_ingestion_metadata.
   sql`), and alphabetically `batch_parts` sorts before `metadata` — but
   `batch_parts` has an FK to the table `metadata` creates. This only ever
   "worked" because this dev DB was bootstrapped by someone running the
   files in a different (correct) order by hand at some point. Fixed by
   renumbering the whole `scripts/sql/` sequence into true dependency order
   and verifying it end-to-end against a fresh container (see "Repo
   hygiene").

After these three fixes, `run_pipeline()` succeeds on a database that has
only ever had `scripts/sql/*.sql` + `migrations/*.sql` applied — verified
directly, not just asserted.

### Repo hygiene

- Fixed a genuine migration-numbering collision:
  `migrations/009_add_pipeline_logical_run_unique.sql` and
  `migrations/010_create_pipeline_stage_runs.sql` collided with the
  pre-existing `009_create_dim_date.sql` / `010_create_fact_order.sql`.
  Renumbered to `017`/`018` (both were already applied to this dev DB —
  renumbering is a filename-only change; there is no migration-tracking
  table in this project, so this is safe).
- A migration creating `retail.ingestion_quality_results` was sitting in
  `migrations/` under the placeholder filename `00X_...` and targeted the
  `retail` schema — the wrong track (it belongs with `scripts/sql/`, the
  self-contained retail-schema track, so it auto-applies on a fresh
  container). Moved to `scripts/sql/010_create_ingestion_quality_results.sql`.
  Its later pipeline_run_id-linking ALTER (`migrations/023`) correctly stays
  in the `migrations/` track instead, since it references
  `analytics.pipeline_runs` — a cross-schema dependency that only the
  manually-applied track can safely assume exists.
- Renumbered the rest of `scripts/sql/` into true dependency order (see
  above) and removed a second, now-genuinely-broken collision:
  `scripts/sql/005_add_customer_number.sql` tried to (re)add a column and
  constraint that `scripts/sql/002_create_tables.sql` had since been edited
  to define inline — reapplying it against a fresh DB failed outright.
  Deleted the now-fully-redundant file.
- Deleted `docker/postgres/init/` — a stale, incomplete, unreferenced
  duplicate of `scripts/sql/` (missing several tables entirely;
  `docker-compose.yml` mounts `scripts/sql`, never this directory).

### Docker / CI / config (Phases 10–12)

- `common/database.py::get_connection()` now retries the initial connect
  through the existing generic `run_with_retry`/`RetryConfig` (5 attempts,
  1s base backoff) — reusing the same retry primitive the pipeline stages
  use rather than inventing a second one. This covers the gap between "the
  container reports started" and "Postgres is actually accepting
  connections", which the Docker healthcheck alone can't communicate to the
  Python app.
- `docker-compose.yml`'s Postgres healthcheck (`pg_isready`, proper
  `start_period`/`retries`) was already correct — no change needed there.
  No app-side `Dockerfile` was added: the app runs on the host via `uv run`
  against the containerized Postgres, which is the existing convention and
  avoids the complexity of a second container needing different hostnames
  in-container vs. on-host for no real benefit in a project this size.
- `.github/workflows/ci.yml` was empty; added a real workflow: a
  `postgres:17` service container, apply both migration tracks in order via
  `psql`, then `ruff check`, `mypy`, `pytest -v`. Fails the build on any of
  the three.
- `.env.example`/`settings.py` were already clean (safe dev defaults, no
  secrets, DSN built from `pydantic-settings`) — no change needed.

### Orchestration (Phase 9)

`docs/architecture/decisions/ADR-002-orchestration.md` (pre-existing in this
repo) already accepts Airflow as the orchestration layer, and an empty
`airflow/dags/` scaffold existed. Added
`airflow/dags/retailpulse_pipeline.py`: a thin `@dag`/`@task` shell that
calls `run_pipeline()` and raises `AirflowException` on `PipelineStatus.
FAILED`, with `max_active_runs=1` (belt-and-suspenders alongside the DB-level
idempotency, which is the real safety boundary). **`apache-airflow` is
deliberately not added to `pyproject.toml`** — it doesn't yet support this
project's Python version, and pulling in an orchestrator's full dependency
footprint to host one DAG file would contradict the "keep it lightweight"
principle this project follows elsewhere (see `docs/architecture/
technology-decisions.md`, which also names Kafka/Spark/Databricks/dbt/
Terraform — all present as **empty, unimplemented scaffold directories**
only; out of scope here by the same principle). The DAG is meant to be
copied into a real Airflow deployment where `retailpulse` is importable.

## Test results

```
125 passed in 56–65s   (varies with prior test-DB state; see "Repo hygiene")
```

Started at 102 passing (baseline). Net +23 tests across:
`test_pipeline_idempotency.py` (5), `test_pipeline_recovery.py` (4),
`test_pipeline_operational_views.py` (4), `test_watermark_repository.py` (4),
`test_incremental_analytics.py` (2), `test_customer_scd2.py` (3), plus one
new case in `test_quality_persistence.py`.

## Static analysis

- `ruff check src tests`: 19 findings remaining, all pre-existing and
  reviewed (see Phase 13 above) — none touch code from this pass.
- `mypy src`: 13 findings remaining, all pre-existing (`cursor.fetchone()`
  nullability in `quality/checks.py`, `quality/reconciliation.py`,
  `generators/bootstrap.py`) — none in code from this pass.

## Known limitations / suggested follow-ups

1. The three fresh-bootstrap bugs above were caught by **manual** testing
   against a throwaway container, not an automated fixture. Recommend a
   CI/pytest fixture that provisions a genuinely empty database (or a
   dedicated CI job, as opposed to the shared dev DB) so this class of bug
   is caught automatically, not just by whoever happens to test cold.
2. `pipeline_runs` has no heartbeat for a RUNNING row, unlike
   `ingestion_batches` (which already has `last_heartbeat_at`/
   `get_stale_started_batches`). A crashed pipeline run stays RUNNING
   forever; `resume_pipeline()` correctly refuses to touch it, but nothing
   currently reclaims it. Mirroring the existing batch-level heartbeat
   pattern at the pipeline level is the natural fix.
3. `quality/checks.py`/`quality/reconciliation.py`/`generators/bootstrap.py`
   still use the `cursor.fetchone()[0]` pattern mypy flags as possibly-`None`
   (harmless in practice — every call site is a `COUNT(*)`/aggregate that
   always returns exactly one row — but worth a follow-up pass for
   consistency with the `_fetch_scalar()` helper introduced in this pass).
4. Dimension loaders (categories/suppliers/products/customers/stores) do a
   full-table extract+upsert every run rather than being watermarked like
   the fact loaders. This is a deliberate choice (dimensions are small —
   tens of thousands of rows at most — and every loader is already an
   idempotent upsert), not an oversight, but would need revisiting if
   dimension volumes grew by orders of magnitude.

## Interview talking points

- **Idempotency is enforced at the database boundary, not in application
  logic.** `start_pipeline_run()` never does check-then-insert; it always
  attempts the INSERT and lets `ON CONFLICT ... RETURNING` tell it whether
  it won the race. This is the difference between "probably safe" and
  "actually safe" under concurrent schedulers.
- **SCD2 via partial unique indexes on one table**, not a separate history
  table — `UNIQUE (customer_id) WHERE is_current` lets the same table
  answer both "who is this customer today" and "who was this customer on
  date X" without a JOIN to a side table, at the cost of a slightly more
  careful set of upsert statements.
- **Watermark-advance-only-after-full-success**, verified by a test that
  injects a mart-refresh failure and asserts the watermark didn't move —
  this is the actual guarantee "incremental processing" needs to mean
  something, not just a performance optimization.
- **A real fresh-environment bug hunt**: this project's tests all passed
  throughout, on a database that had been running for a while — and still
  hid three bugs that would have made "start from nothing" fail on day one.
  Good illustration of why "all tests green" and "actually works" aren't
  the same claim, and why testing cold matters as much as testing warm.
- **Two-layer retry, deliberately not merged**: `pipeline/retry.py` is
  generic and stage-scoped (fast, observable, `pipeline_stage_runs`-tracked);
  an orchestrator-level retry (Airflow DAG `retries=1`) is a second,
  coarser line of defense for failures the inner layer couldn't resolve.
  Not duplication — different failure classes, different granularity.
- **COPY + staging table + set-based JOIN upsert vs. per-row loop**: a
  concrete, measured performance story (300K-row backlog effectively
  hanging vs. a clean 50K-order run completing in under 90 seconds), plus
  the retry-safety subtlety it introduced (`CREATE TEMP TABLE IF NOT
  EXISTS` + `TRUNCATE`, not a bare `CREATE`).

## Commands

```powershell
# Full test suite
uv run pytest tests -v

# One test file
uv run pytest tests/integration/test_pipeline_recovery.py -v

# Lint / type-check
uv run ruff check src tests
uv run mypy src

# Run the pipeline
uv run python -m retailpulse.pipeline.runner

# Apply a single migration (PowerShell)
Get-Content migrations/023_alter_ingestion_quality_results_add_pipeline_link.sql |
    docker exec -i retailpulse-postgres psql -U retailpulse -d retailpulse

# Inspect pipeline health
docker exec retailpulse-postgres psql -U retailpulse -d retailpulse -c ^
    "SELECT * FROM analytics.v_pipeline_health ORDER BY started_at DESC LIMIT 10;"
```
