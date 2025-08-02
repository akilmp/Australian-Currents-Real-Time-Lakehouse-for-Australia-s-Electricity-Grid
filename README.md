# KangarooCurrents-Real-Time-Lakehouse-for-Australia-s-Electricity-Grid

This repository contains Airflow assets for experimenting with a real-time
lakehouse architecture for Australia's National Electricity Market (NEM).

## Airflow DAG

The `airflow/dags/pipeline_nem.py` module defines a TaskFlow DAG that:

- waits for Bronze events to arrive on a Kafka topic,
- batches the data hourly into a Silver table stored on MinIO/S3,
- runs the project's dbt models,
- validates the results with Great Expectations, and
- notifies a Slack channel when the run completes.

Connections for Kafka (`kafka_default`), MinIO/S3 (`minio_default`) and Slack
(`slack_default`) are created automatically using environment variables when
the DAG file is parsed.

### Triggering the DAG locally

1. Ensure Airflow is installed and the repository's `airflow/dags` directory is
   on the `AIRFLOW__CORE__DAGS_FOLDER` path.
2. Set any required credentials via environment variables before starting the
   scheduler:

   ```bash
   export KAFKA_BROKER=localhost:9092
   export S3_ENDPOINT=http://localhost:9000
   export S3_ACCESS_KEY=minio
   export S3_SECRET_KEY=minio123
   export SLACK_WEBHOOK=hooks/xxx/yyy/zzz
   airflow scheduler &
   airflow webserver &
   ```
3. Trigger the pipeline manually:

   ```bash
   airflow dags trigger pipeline_nem
   ```

   The run can also be started from the Airflow UI.

This repository demonstrates basic data quality checks using [Great Expectations](https://greatexpectations.io/).

## Expectation Suites

Expectation suites live in `great_expectations/expectations/`.

- **Bronze** (`bronze_suite`):
  - `id` and `reading` must be non-null.
  - `reading` values must fall between 0 and 1000.
- **Silver** (`silver_suite`):
  - `id` must be 99% complete and unique.
  - `reading` must be 98% complete.

## Validation in Spark Jobs

Sample Spark jobs in `jobs/data_quality.py` load data, apply the relevant expectation
suite, and raise a `ValueError` if validation fails. The thresholds above define
expected success rates; failure triggers a job halt for investigation.


## Exporters
Configuration files for Prometheus exporters are located in `monitoring/exporters` and cover:
- Spark
- Kafka
- Airflow
- Flink

## Grafana Dashboards
JSON exports for Grafana are stored in `docs/grafana` and include dashboards for:
- Generation mix
- Consumer lag
- Forecast error

## Alerting
Prometheus Alertmanager configuration and rules live in `monitoring/alerts`. Alerts are sent to Slack for:
- High coal percentage of total generation
- Pipeline failures

Set the `SLACK_WEBHOOK_URL` environment variable and update channel names as needed before deploying the alerting stack.
## Terraform

Infrastructure as code lives in the [`terraform/`](terraform/) directory. Remote state is stored in S3 with DynamoDB locks. Use workspaces and variable files to manage environments:

```sh
cd terraform
terraform init
terraform workspace new dev    # one-time
terraform workspace select dev
terraform apply -var-file=dev.tfvars

terraform workspace select prod  # or create with `terraform workspace new prod`
terraform apply -var-file=prod.tfvars
```

## Getting Started

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Start the services:

   ```bash
   docker compose up -d
   ```

The `docker-compose.yml` file provisions Redpanda, MinIO, Spark, Airflow, Prometheus and Grafana for local development.

