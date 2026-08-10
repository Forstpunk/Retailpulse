# Technology Decisions

| Concern | Technology | Responsibility |
|---|---|---|
| OLTP | PostgreSQL | Operational source |
| Object storage | AWS S3 | Durable raw storage |
| Event transport | Kafka | Event streaming |
| CDC | Debezium | Database change capture |
| Distributed processing | Apache Spark | Data processing |
| Lakehouse | Databricks | Managed Spark/lakehouse |
| Table format | Delta Lake | Transactional tables |
| Analytical transformation | dbt | SQL transformation |
| Orchestration | Airflow | Workflow control |
| Infrastructure | Terraform | Cloud infrastructure |
| Databricks deployment | Declarative Automation Bundles | Databricks CI/CD |
| Python environment | uv | Dependency management |
| Containers | Docker | Local infrastructure |
| CI/CD | GitHub Actions | Validation/deployment |
| Testing | pytest | Python tests |
| Data quality | dbt + Spark + reconciliation | Data correctness |