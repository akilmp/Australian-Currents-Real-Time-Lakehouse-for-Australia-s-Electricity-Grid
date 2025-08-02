"""Pipeline DAG for NEM data processing.

This DAG orchestrates a real-time lakehouse pipeline.  It submits a Spark
streaming job that ingests Bronze data from Kafka, runs a Spark batch job to
build the Silver layer on MinIO/S3, executes dbt models and tests, and finally
runs Great Expectations validations.  Connections for Kafka, MinIO/S3 and Slack
are created automatically when the DAG is parsed so the pipeline can run in a
fresh local environment.
"""

from __future__ import annotations

import json
import os
import pendulum

from airflow import settings
from airflow.decorators import dag
from airflow.models import Connection
from airflow.operators.bash import BashOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
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

# Absolute path to the repository root so bash commands can reference
# project files regardless of the Airflow working directory.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@dag(
    dag_id="pipeline_nem",
    schedule_interval="@hourly",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    default_args=default_args,
    tags=["nem", "lakehouse"],
)
def pipeline_nem():
    bronze_stream = BashOperator(
        task_id="bronze_stream",
        bash_command=f"bash {REPO_ROOT}/submit_bronze.sh",
        env={
            "KAFKA_BOOTSTRAP_SERVERS": "{{ conn.kafka_default.host }}",
            "CHECKPOINT_PATH": "s3a://lakehouse/checkpoints/bronze_dispatch",
            "AWS_ACCESS_KEY_ID": "{{ conn.minio_default.login }}",
            "AWS_SECRET_ACCESS_KEY": "{{ conn.minio_default.password }}",
            "AWS_ENDPOINT_URL": "{{ conn.minio_default.extra_dejson.endpoint_url }}",
        },
    )

    silver_batch = BashOperator(
        task_id="silver_batch",
        bash_command=(
            "spark-submit --packages "
            "org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.2 "
            f"{REPO_ROOT}/spark_jobs/silver_batch.py"
        ),
        env={
            "AWS_ACCESS_KEY_ID": "{{ conn.minio_default.login }}",
            "AWS_SECRET_ACCESS_KEY": "{{ conn.minio_default.password }}",
            "AWS_ENDPOINT_URL": "{{ conn.minio_default.extra_dejson.endpoint_url }}",
        },
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {REPO_ROOT}/dbt && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {REPO_ROOT}/dbt && dbt test",
    )

    ge_validate_bronze = BashOperator(
        task_id="ge_validate_bronze",
        bash_command=(
            f"cd {REPO_ROOT}/great_expectations && "
            "great_expectations checkpoint run bronze_checkpoint"
        ),
    )

    ge_validate_silver = BashOperator(
        task_id="ge_validate_silver",
        bash_command=(
            f"cd {REPO_ROOT}/great_expectations && "
            "great_expectations checkpoint run silver_checkpoint"
        ),
    )

    notify_success = SlackWebhookOperator(
        task_id="notify_success",
        slack_conn_id="slack_default",
        message="pipeline_nem DAG succeeded",
    )

    notify_failure = SlackWebhookOperator(
        task_id="notify_failure",
        slack_conn_id="slack_default",
        message="pipeline_nem DAG failed",
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    bronze_stream >> silver_batch >> dbt_run >> dbt_test >> ge_validate_bronze >> ge_validate_silver
    ge_validate_silver >> [notify_success, notify_failure]


dag = pipeline_nem()
