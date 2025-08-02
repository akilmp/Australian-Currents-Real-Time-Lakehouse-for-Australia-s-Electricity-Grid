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

