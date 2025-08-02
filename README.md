# KangarooCurrents-Real-Time-Lakehouse-for-Australia-s-Electricity-Grid



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

