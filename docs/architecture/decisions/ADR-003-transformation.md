# ADR-003: Separate Spark Transformations from dbt Transformations

## Status

Accepted

## Decision

Use Apache Spark for data-engineering transformations that require:

- large-scale distributed processing
- CDC processing
- complex event processing
- streaming
- heavy joins
- deduplication
- data standardization

Use dbt for:

- analytical SQL
- dimensional modeling
- business logic
- marts
- tests
- documentation
- lineage

## Principle

Spark solves distributed data processing.

dbt solves analytical transformation and modeling.

Neither tool should be used merely because it appears in the technology stack.