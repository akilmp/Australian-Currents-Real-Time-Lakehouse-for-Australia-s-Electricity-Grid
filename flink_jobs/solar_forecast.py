import argparse
import json
import os
from datetime import datetime, timedelta

import pandas as pd
from prophet import Prophet
from pyflink.common import Types, WatermarkStrategy
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import ProcessFunction, StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import (
    DeliveryGuarantee,
    KafkaOffsetsInitializer,
    KafkaRecordSerializationSchema,
    KafkaSink,
    KafkaSource,
)
from pyflink.table import Schema, StreamTableEnvironment, DataTypes

WINDOW_DAYS = 14


class Forecast(ProcessFunction):
    """Process function maintaining a sliding window and emitting forecasts."""

    def __init__(self, horizon: int):
        self.horizon = horizon
        self.history = []

    def process_element(self, value, ctx: ProcessFunction.Context):
        ts = datetime.fromisoformat(value["event_time"])
        self.history.append({"ds": ts, "y": value["solar_share"]})
        cutoff = ts - timedelta(days=WINDOW_DAYS)
        self.history = [row for row in self.history if row["ds"] >= cutoff]
        if len(self.history) < 2:
            return
        df = pd.DataFrame(self.history)
        model = Prophet()
        model.fit(df)
        future = model.make_future_dataframe(periods=self.horizon, freq="30min")
        forecast = model.predict(future.tail(self.horizon))[['ds', 'yhat']]
        for _, row in forecast.iterrows():
            yield json.dumps(
                {
                    "event_time": row['ds'].isoformat(),
                    "forecast_solar_share": float(row['yhat']),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--horizon",
        type=int,
        default=int(os.getenv("MODEL_HORIZON", "48")),
        help="Number of 30-minute periods to forecast",
    )
    parser.add_argument(
        "--checkpoint-path",
        default=os.getenv("CHECKPOINT_PATH", "/tmp/flink-checkpoints"),
        help="Checkpoint directory",
    )
    args = parser.parse_args()

    brokers = os.getenv("KAFKA_BROKERS", "redpanda:9092")
    warehouse = os.getenv("ICEBERG_WAREHOUSE", "s3a://lakehouse")

    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(300000)
    env.get_checkpoint_config().set_checkpoint_storage(args.checkpoint_path)
    t_env = StreamTableEnvironment.create(env)

    source = (
        KafkaSource.builder()
        .set_bootstrap_servers(brokers)
        .set_topics("silver_dispatch")
        .set_group_id("solar-forecast")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    ds = (
        env.from_source(
            source, WatermarkStrategy.no_watermarks(), "silver-source"
        )
        .map(lambda s: json.loads(s), output_type=Types.MAP(Types.STRING(), Types.FLOAT()))
    )

    forecast_stream = ds.process(
        Forecast(args.horizon), output_type=Types.STRING()
    )

    sink = (
        KafkaSink.builder()
        .set_bootstrap_servers(brokers)
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic("forecast_solar_share")
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        )
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
        .build()
    )

    forecast_stream.sink_to(sink)

    forecast_table = t_env.from_data_stream(
        forecast_stream.map(
            lambda s: (
                json.loads(s)["event_time"],
                json.loads(s)["forecast_solar_share"],
            ),
            output_type=Types.ROW_NAMED(
                ["event_time", "forecast_solar_share"],
                [Types.STRING(), Types.FLOAT()],
            ),
        ),
        Schema.new_builder()
        .column("event_time", DataTypes.STRING())
        .column("forecast_solar_share", DataTypes.DOUBLE())
        .build(),
    )

    t_env.execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS nem_forecast (
            event_time TIMESTAMP(3),
            forecast_solar_share DOUBLE
        ) PARTITIONED BY (DATE_FORMAT(event_time, 'yyyy-MM-dd'))
        WITH (
            'connector'='iceberg',
            'catalog-name'='local',
            'catalog-type'='hadoop',
            'warehouse'='{warehouse}'
        )
        """
    )

    forecast_table.execute_insert("nem_forecast")

    env.execute("solar_forecast")


if __name__ == "__main__":
    main()
