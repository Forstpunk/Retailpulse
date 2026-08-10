# RetailPulse System Context

## Purpose

RetailPulse is a production-oriented retail data platform designed to ingest
operational, event-driven, and file-based data and transform it into reliable,
historical, analytics-ready data products.

## Primary Business Capabilities

The platform must support:

- sales analytics
- customer analytics
- product analytics
- inventory analytics
- returns analytics
- fulfillment analyticsgit status
- historical dimension analysis

## Data Sources

### PostgreSQL

Operational source containing:

- customers
- products
- stores
- orders
- order_items
- inventory
- payments
- returns
- promotions

### Kafka

Event-driven source containing:

- order events
- inventory events
- customer changes
- payment events

### Vendor Files

External batch sources containing:

- product updates
- inventory feeds
- promotional data

## Storage

Amazon S3 is the durable object-storage layer.

Delta Lake is the transactional table format used by the lakehouse.

## Processing

Apache Spark performs distributed data processing.

## Transformation

dbt manages analytical SQL transformations and dimensional models.

## Orchestration

Apache Airflow manages workflow orchestration, scheduling, retries,
dependencies and backfills.

## Streaming

Apache Kafka provides the event transport layer.

Debezium provides CDC from PostgreSQL into Kafka.

## Serving

Databricks SQL provides analytical access to Gold data products.

## Infrastructure

Terraform manages cloud infrastructure.

Databricks Declarative Automation Bundles manage Databricks project
resources and deployment configuration.

## CI/CD

GitHub Actions validates and deploys the platform.

## Design Principles

1. Idempotency
2. Reproducibility
3. Observability
4. Data quality
5. Fault tolerance
6. Incremental processing
7. Schema evolution
8. Security by default
9. Separation of concerns
10. Infrastructure as code