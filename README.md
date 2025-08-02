# KangarooCurrents-Real-Time-Lakehouse-for-Australia-s-Electricity-Grid

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
