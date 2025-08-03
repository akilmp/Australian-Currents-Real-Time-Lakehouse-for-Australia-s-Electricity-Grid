# Australian Currents – Real‑Time Lakehouse for Australia’s Electricity Grid

## Table of Contents

1. [Project Overview](#project-overview)
2. [Principle Capabilities & Skills Demonstrated](#principle-capabilities--skills-demonstrated)
3. [Solution Architecture](#solution-architecture)
4. [Tech Stack](#tech-stack)
5. [Data Sources](#data-sources)
6. [Repository Layout](#repository-layout)
7. [Local Development Environment](#local-development-environment)
8. [Infrastructure‑as‑Code](#infrastructure-as-code)
9. [Data Pipeline Details](#data-pipeline-details)

   * 9.1 [Streaming Ingestion – Bronze](#91-streaming-ingestion--bronze)
   * 9.2 [Batch Cleansing – Silver](#92-batch-cleansing--silver)
   * 9.3 [Warehouse Modelling – Gold](#93-warehouse-modelling--gold)
   * 9.4 [Online Forecasting](#94-online-forecasting)
10. [Data Quality & Testing](#data-quality--testing)
11. [CI/CD Workflow](#cicd-workflow)
12. [Observability & Alerting](#observability--alerting)
13. [Cost Management](#cost-management)
14. [Demo Recording Guide](#demo-recording-guide)
15. [Troubleshooting & FAQ](#troubleshooting--faq)
16. [Stretch Goals](#stretch-goals)
17. [References](#references)

---

## Project Overview

**KangarooCurrents** is a real‑time data‑lakehouse that tracks Australia’s National Electricity Market (NEM) dispatch every five minutes to reveal the live mix of coal, gas, hydro and renewables.  The platform ingests dispatch CSV files from the Australian Energy Market Operator (AEMO), streams them into an Apache Iceberg lake on S3, transforms and models the data with Spark and dbt, validates quality gates through Great Expectations, publishes interactive Grafana dashboards and performs near‑term solar‑share forecasting using PyFlink.  The system is fully reproducible via Terraform and ships with CI/CD in GitHub Actions.

---

## Principle Capabilities & Skills Demonstrated

| Skill                         | Implementation                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------ |
| **Cloud Storage & Lakehouse** | Iceberg tables (`bronze`, `silver`, `gold`) on Amazon S3 (local MinIO for dev) |
| **Streaming Ingestion**       | Kafka topic **`nem_dispatch`** fed by async Python connector                   |
| **Stream & Batch Processing** | Spark Structured Streaming (Bronze) + Hourly Spark Batch (Silver)              |
| **Data Modelling**            | dbt Core star schema (`fact_dispatch`, `dim_unit`, `dim_region`)               |
| **Orchestration**             | Apache Airflow 2.9 TaskFlow DAGs                                               |
| **Data Quality**              | Great Expectations + dbt tests, fail‑fast in DAG                               |
| **ML & Forecasting**          | PyFlink inference job (Prophet) forecasting 30‑minute solar share              |
| **IaC & CI/CD**               | Terraform 1.7 + GitHub Actions plan/apply, lint, dbt run                       |
| **Observability**             | ADOT Collector ➜ Prometheus ➜ Grafana Cloud; Slack alerts on coal spikes       |
| **FinOps**                    | Partition pruning, EMR spot, S3 lifecycle, Budgets alert                       |

---

## Solution Architecture

```
  +-------------+       +------------------+      +------------------+
  |  AEMO API   |--5m-->│  Python Producer │-->   │ Kafka: nem_dispatch│
  +-------------+       +------------------+      +---------+--------+
                                                    |   Structured   |
                                                    |   Streaming    |
                                                    v                
                                          +----------------------+   
                                          |  Iceberg BRONZE      |
                                          +----------------------+   
                                                    | hourly Airflow
                                                    v                
                                          +----------------------+   
                                          |  Iceberg SILVER      |
                                          +----------------------+   
                                                    | dbt run       
                                                    v                
                                          +----------------------+   
                                          |  Iceberg GOLD        |
                                          +----------------------+   
                                                    |                
               +----------------+   Grafana/Superset |                
               | PyFlink Solar  |<-------------------+                
               | Forecast Job   |                                         
               +----------------+                                         
```

*Control plane*: Airflow and Grafana share Prometheus metrics; Terraform provisions all infra.

---

## Tech Stack

| Layer            | Dev (Docker)                            | Cloud (AWS default)                             |
| ---------------- | --------------------------------------- | ----------------------------------------------- |
| Object Storage   | MinIO                                   | Amazon S3                                       |
| Messaging        | Redpanda                                | MSK (Kafka)                                     |
| Compute (Stream) | Spark 3.5 (Docker)                      | EMR Serverless                                  |
| Compute (Batch)  | Spark 3.5                               | EMR Serverless                                  |
| Modelling        | dbt Core 1.8                            | dbt Core on EC2/Scheduled Lambda                |
| ML               | Flink 1.18 (PyFlink)                    | Flink Kinesis Data Analytics                    |
| Orchestration    | Apache Airflow 2.9                      | MWAA                                            |
| IaC              | Terraform 1.7                           | Same                                            |
| Observability    | ADOT Collector, Prometheus, Grafana OSS | ADOT ➜ Amazon Managed Prometheus, Grafana Cloud |

---

## Data Sources

| Dataset                  | Endpoint                     | Refresh     | Size             |
| ------------------------ | ---------------------------- | ----------- | ---------------- |
| **NEM Dispatch SCADA**   | `https://aemo.com.au/...CSV` | every 5 min | \~60 k rows/hour |
| **Unit Static Metadata** | AEMO unit registry CSV       | monthly     | 1 MB             |

API key not required (public).  Producer script stores latest CRC to skip duplicates and
persists it to a checkpoint file defined by the `CRC_CHECKPOINT_PATH` environment
variable.

---

## Repository Layout

```
kangaroo-currents/
├── docker-compose.yml
├── .env.example
├── terraform/
│   ├── network/           # VPC, SG
│   ├── storage/           # S3, Glue catalog
│   ├── kafka/             # MSK cluster
│   ├── compute/           # EMR, ECS (Flink)
│   └── observability/     # AMP, Grafana Cloud
├── spark_jobs/
│   ├── bronze_stream.py
│   └── silver_batch.py
├── flink_jobs/
│   └── solar_forecast.py
├── dbt/
│   ├── models/*.sql
│   └── tests/*.yml
├── ingest/
│   └── producer.py
├── airflow/
│   └── dags/pipeline_nem.py
├── great_expectations/
│   └── expectations/*.json
├── .github/workflows/
│   └── deploy.yml
└── docs/
    ├── architecture.drawio
    └── demo_script.md
```

---

## Local Development Environment

1. `git clone https://github.com/<you>/kangaroo-currents && cd kangaroo-currents`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt` – installs pinned Python deps (`pyspark`, `dbt-core`, `great_expectations`, `apache-flink`, `prophet`, `pytest`)
4. `cp .env.example .env` – set environment variables for storage and APIs (see below).
5. `docker compose up -d` – spins Redpanda, MinIO, Airflow, Spark Master.
6. Start producer: `python ingest/producer.py`.
7. Trigger Airflow DAG `pipeline_nem` manually to generate Silver & Gold.
8. Explore dashboards: Grafana on `localhost:3000` (admin/admin).

### Environment Variables

| Variable | Description |
| -------- | ----------- |
| `NEM_BUCKET` | S3 bucket that stores raw and processed NEM datasets. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Credentials used by Spark and Airflow to access the bucket. |
| `API_URL` | Source endpoint for NEM dispatch CSV feed. |
| `SLACK_WEBHOOK` / `SLACK_WEBHOOK_URL` | Slack webhooks for Airflow notifications and Alertmanager alerts. |
| `GRAFANA_API_KEY` | API key for pushing metrics and dashboards to Grafana. |

---

## Infrastructure‑as‑Code

* **Remote State**: S3 bucket `kc-tfstate`, DynamoDB lock `kc-tf-lock`.
* **Workspaces**: `dev`, `prod`.
* **Module Outputs**: MSK broker strings, S3 lake bucket, EMR job role ARNs, Prometheus endpoint.

### Deploy

```bash
cd terraform
terraform init -backend-config="profile=prod"
terraform workspace select prod || terraform workspace new prod
terraform apply -var-file=prod.tfvars
```

CI runner performs identical plan/apply via GitHub Actions.

---

## Data Pipeline Details

### Metadata Ingestion

* `spark-submit ingest/load_metadata.py --unit-csv path/to/unit.csv --region-csv path/to/region.csv`
  loads static unit and region metadata into Iceberg tables `nem.unit_metadata`
  and `nem.region_metadata`.

### 9.1 Streaming Ingestion – Bronze

* **Producer**: Async `aiohttp` fetch of latest AEMO dispatch CSV every 300 s.
* **Kafka**: Topic `nem_dispatch`, 3 partitions keyed by `unit_id`.
* **Spark Structured Streaming**: Reads topic; writes Iceberg `nem.bronze_dispatch` partitioned by `trading_date`.

### 9.2 Batch Cleansing – Silver

* Hourly Airflow task runs Spark job `silver_batch.py`:

  * Deduplicate (`trading_interval` × `unit_id` pk).
  * Join static Unit metadata to add `station_name`.
  * Outputs `nem.silver_dispatch_clean`.
  * Publishes solar share to Kafka topic `silver_dispatch`.

### 9.3 Warehouse Modelling – Gold

* **dbt model** `fact_dispatch` aggregates generation by `trading_interval` × `unit_id` × `fuel_type`.
* `dim_unit` and `dim_region` built from metadata and reference tables.
* Incremental, partitioned on `trading_interval`.

### 9.4 Online Forecasting

* PyFlink job `solar_forecast.py` consumes Silver stream, fits Prophet model window = 14 days sliding, emits 30‑min ahead forecast to Kafka topic `forecast_solar_share` and Iceberg table `nem.forecast`.

Run locally:

```bash
docker compose run --rm solar-forecast --horizon 48
```

Deploy to Kinesis Data Analytics for Apache Flink:

1. Build and push the image to ECR.

   ```bash
   docker build -t solar-forecast -f flink_jobs/Dockerfile flink_jobs
   aws ecr create-repository --repository-name solar-forecast
   docker tag solar-forecast:latest <account>.dkr.ecr.<region>.amazonaws.com/solar-forecast:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/solar-forecast:latest
   ```

2. Create a Kinesis Data Analytics application referencing the image. Configure environment variables such as `KAFKA_BROKERS`, `MODEL_HORIZON` and `CHECKPOINT_PATH` and point the job to the `forecast_solar_share` Kafka topic and Iceberg catalog.

---

## Data Quality & Testing

| Layer    | Tool                | Tests                                                          |
| -------- | ------------------- | -------------------------------------------------------------- |
| Bronze   | Great Expectations  | Null checks, numeric ranges for MW ≥ 0, schema drift detection |
| Silver   | Great Expectations  | Completeness ≥ 95 %, uniqueness on (`interval`, `unit_id`)     |
| Gold     | dbt tests           | `not_null` PKs, `accepted_range` for percentage fields         |
| Forecast | Custom drift metric | MAPE > 20 % triggers alert                                     |

Airflow DAG fails on any expectation set < 0.95 success ratio.

---

## CI/CD Workflow

GitHub Actions pipeline `deploy.yml`:

1. **Lint & Test** – run flake8 + pytest for producer and spark utils.
2. **dbt build** – compile models; run unit tests with SQLite adapter.
3. **Terraform** – `fmt -check`, `plan`, `apply` (on `main`).
4. **Docker Push** – build & push Flink job image to ECR.
5. **Airflow DAG Sync** – upload DAG to MWAA S3 bucket.

Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GRAFANA_API_KEY`, Slack webhook.

---

## Observability & Alerting

| Metric               | Source                                  | Alert                                 |   |
| -------------------- | --------------------------------------- | ------------------------------------- | - |
| `coal_percent`       | dbt post-hook -> Prometheus pushgateway | Slack alert if > 70 % for 3 intervals |   |
| Spark batch duration | Spark JMX -> Prometheus                 | PagerDuty if > 10 min                 |   |
| Kafka consumer lag   | Prometheus exporter                     | Auto-scale EMR                        |   |
| MAPE forecast error  | Flink metric -> Prometheus              | Warning > 25 %                        |   |

Grafana dashboards exported as JSON to `docs/grafana/` (Import ID 12050).

### Viewing Grafana Dashboards

1. Start the monitoring stack:

   ```bash
   docker compose up -d \
     prometheus grafana alertmanager \
     spark-exporter kafka-exporter flink-exporter airflow-exporter
   ```

2. Visit [http://localhost:3000](http://localhost:3000) and log in with the default `admin`/`admin` credentials.
3. The built-in Prometheus data source is preconfigured to scrape the exporters defined in `monitoring/prometheus.yml`.
4. Open a dashboard to explore Spark, Kafka, Flink and Airflow metrics.

---

## Cost Management

* **EMR Serverless** spot mode; max\_capacity\_units = 20.
* S3 lifecycle: Bronze → Glacier Deep Archive after 90 days; Silver after 180.
* Iceberg partition pruning cuts query scan ≤ 2 GB per day.
* Monthly dev cost ≈ **AUD 35** (detailed Excel in `docs/cost_breakdown.xlsx`).

---

## Troubleshooting & FAQ

| Issue                                    | Fix                                                           |
| ---------------------------------------- | ------------------------------------------------------------- |
| `Producer 403`                           | AEMO rate‑limit: back‑off 30 s or rotate IP                   |
| Spark `NoSuchTable: nem.bronze_dispatch` | Run Glue Crawler or `spark.sql("CREATE DATABASE nem")` first  |
| Flink job `Checkpoint timeout`           | Increase `state.backend.fs.checkpoint.interval` to 60 s       |
| dbt `Database Error: FileNotFound`       | Iceberg table older than retention: run `VACUUM` before query |

---

## Stretch Goals

* **Cross‑cloud Mirror** – replicate Gold tables to BigQuery via Iceberg → GCS.
* **Real‑time API** – GraphQL endpoint (Hasura) on top of Gold.
* **Data Contracts** – Protobuf schema registry + CI contract tests.
* **Streaming Upserts** – Explore Iceberg v2 MERGE for arrival corrections.

---

## References

* AEMO Data API docs – [https://data.aemo.com.au/](https://data.aemo.com.au/)
* Iceberg official guide – [https://iceberg.apache.org/](https://iceberg.apache.org/)
* “Prophet for Energy Forecasting” – Meta 2024 whitepaper
* AWS Streaming ETL best practices 2025

---

*Last updated: 2 Aug 2025*
