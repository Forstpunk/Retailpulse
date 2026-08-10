# ADR-002: Use Apache Airflow for Orchestration

## Status

Accepted

## Context

RetailPulse contains multiple processing systems:

- PostgreSQL ingestion
- S3 landing
- Spark processing
- dbt transformations
- data-quality validation
- reconciliation
- publishing

These operations have dependencies and operational requirements.

## Decision

Apache Airflow will be the orchestration layer.

Airflow will own:

- scheduling
- task dependencies
- retries
- timeouts
- backfills
- data intervals
- workflow-level observability
- failure handling

Airflow will not perform large-scale data transformations.

Spark and dbt will perform transformations.

## Consequences

Airflow becomes the control plane for data workflows while processing engines
remain responsible for computation.