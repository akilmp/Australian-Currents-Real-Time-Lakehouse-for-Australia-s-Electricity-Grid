"""Pipeline DAG for NEM data processing.

This DAG demonstrates a simple real-time lakehouse pipeline using Airflow's
TaskFlow API.  The pipeline waits for new Bronze data to arrive from Kafka,
processes it into hourly Silver batches stored on MinIO/S3, builds dbt models
on top of the Silver layer, and finally runs Great Expectations validations.
Connections for Kafka, MinIO/S3 and Slack are created automatically when the
DAG is parsed so the pipeline can run in a fresh local environment.
"""

from __future__ import annotations

import json
import os
import pendulum

from airflow import DAG, settings
from airflow.decorators import dag, task
from airflow.models import Connection
from airflow.operators.bash import BashOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.sensors.base import PokeReturnValue
from airflow.utils.trigger_rule import TriggerRule


def _create_connections() -> None:
    """Create Airflow connections used by the DAG if they do not exist.

    Credentials are read from environment variables so that the file can be
    committed to version control without secrets.  Defaults are suitable for a
    local development environment that uses Kafka, MinIO and Slack webhook
    endpoints running on their standard ports.
    """

    session = settings.Session()

    kafka_conn = Connection(
        conn_id="kafka_default",
        conn_type="kafka",
        host=os.getenv("KAFKA_BROKER", "localhost:9092"),
    )

    minio_conn = Connection(
        conn_id="minio_default",
        conn_type="s3",
        login=os.getenv("S3_ACCESS_KEY", "minio"),
        password=os.getenv("S3_SECRET_KEY", "minio123"),
        host=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        extra=json.dumps(
            {
                "aws_access_key_id": os.getenv("S3_ACCESS_KEY", "minio"),
                "aws_secret_access_key": os.getenv("S3_SECRET_KEY", "minio123"),
                "endpoint_url": os.getenv("S3_ENDPOINT", "http://localhost:9000"),
            }
        ),
    )

    slack_conn = Connection(
        conn_id="slack_default",
        conn_type="http",
        host="https://hooks.slack.com/services",
        extra=json.dumps({"webhook_token": os.getenv("SLACK_WEBHOOK", "")}),
    )

    for conn in (kafka_conn, minio_conn, slack_conn):
        if not session.query(Connection).filter(Connection.conn_id == conn.conn_id).first():
            session.add(conn)
    session.commit()


_create_connections()


default_args = {"owner": "airflow"}


@dag(
    dag_id="pipeline_nem",
    schedule_interval="@hourly",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    default_args=default_args,
    tags=["nem", "lakehouse"],
)
def pipeline_nem():
    @task.sensor(poke_interval=30, timeout=600)
    def bronze_stream_sensor() -> PokeReturnValue:
        """Wait for new messages on the Bronze Kafka topic.

        In a real deployment this sensor would consume from Kafka using the
        connection ``kafka_default``.  Here we simply return immediately.
        """

        return PokeReturnValue(is_done=True, xcom_value="new_message")

    @task()
    def silver_batch(_: str) -> str:
        """Process Bronze data into the Silver layer on MinIO/S3."""

        # A real implementation would read from Kafka and write to MinIO/S3
        # using the ``kafka_default`` and ``minio_default`` connections.
        return "silver_table"

    dbt_models = BashOperator(
        task_id="dbt_models",
        bash_command="dbt run && dbt test",
    )

    ge_validation = BashOperator(
        task_id="great_expectations_validation",
        bash_command="great_expectations checkpoint run silver_checkpoint",
    )

    notify = SlackWebhookOperator(
        task_id="notify_slack",
        slack_conn_id="slack_default",
        message="pipeline_nem DAG finished",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    message = bronze_stream_sensor()
    silver = silver_batch(message)
    silver >> dbt_models >> ge_validation >> notify


dag = pipeline_nem()
