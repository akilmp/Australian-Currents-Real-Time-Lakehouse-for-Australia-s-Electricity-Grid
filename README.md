# KangarooCurrents-Real-Time-Lakehouse-for-Australia-s-Electricity-Grid

This repository includes monitoring assets for the real-time electricity grid lakehouse.

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
