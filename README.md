# KangarooCurrents-Real-Time-Lakehouse-for-Australia-s-Electricity-Grid

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

