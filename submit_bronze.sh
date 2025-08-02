#!/usr/bin/env bash
set -euo pipefail

JOB_FILE="spark_jobs/bronze_stream.py"
JAR_PACKAGES="org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.2,org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2"

usage() {
  echo "Usage: $0 [local|emr]" >&2
  exit 1
}

MODE=${1:-local}

if [[ "$MODE" == "local" ]]; then
  spark-submit \
    --packages "$JAR_PACKAGES" \
    "$JOB_FILE" \
    --kafka-bootstrap-servers "${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}" \
    --checkpoint-path "${CHECKPOINT_PATH:-s3a://lakehouse/checkpoints/bronze_dispatch}"
elif [[ "$MODE" == "emr" ]]; then
  [[ -z "${APPLICATION_ID:-}" || -z "${EMR_ROLE_ARN:-}" ]] && usage
  JOB_DRIVER=$(cat <<JSON
{"sparkSubmit":{
  "entryPoint":"$JOB_FILE",
  "entryPointArguments":[
    "--kafka-bootstrap-servers","${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}",
    "--checkpoint-path","${CHECKPOINT_PATH:-s3a://lakehouse/checkpoints/bronze_dispatch}"
  ],
  "sparkSubmitParameters":"--packages $JAR_PACKAGES"
}}
JSON
)

  aws emr-serverless start-job-run \
    --application-id "$APPLICATION_ID" \
    --execution-role-arn "$EMR_ROLE_ARN" \
    --job-driver "$JOB_DRIVER"
else
  usage
fi
