"""Spark job to clean dispatch data.

This job reads the raw dispatch table ``nem.bronze_dispatch`` and performs the
following operations:

* drop duplicate records based on ``trading_interval`` and ``unit_id``
* join unit metadata to append ``station_name``
* write the cleaned result to ``nem.silver_dispatch_clean`` Iceberg table
  partitioned by ``trading_date``

The transformation logic is implemented in :func:`transform_dispatch` so that it
can be unit tested without requiring an Iceberg catalog.
"""
from __future__ import annotations

import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, sum as spark_sum, when, struct, to_json


def transform_dispatch(spark: SparkSession) -> DataFrame:
    """Transform bronze dispatch data into the silver layer.

    Parameters
    ----------
    spark:
        Active :class:`~pyspark.sql.SparkSession`.

    Returns
    -------
    :class:`~pyspark.sql.DataFrame`
        The cleaned dispatch dataframe with metadata joined.
    """
    # Read source tables
    dispatch_df = spark.table("nem.bronze_dispatch")
    metadata_df = spark.table("nem.unit_metadata")

    # Remove duplicate records
    deduped = dispatch_df.dropDuplicates(["trading_interval", "unit_id"])

    # Join metadata to append station_name
    enriched = deduped.join(
        metadata_df.select("unit_id", "station_name"),
        on="unit_id",
        how="left",
    )

    return enriched


def main() -> None:
    """Entry point for running the silver batch job."""
    spark = (
        SparkSession.builder.appName("silver_batch").getOrCreate()
    )

    result_df = transform_dispatch(spark)

    # Write to Iceberg table partitioned by trading_date
    (
        result_df.writeTo("nem.silver_dispatch_clean")
        .using("iceberg")
        .partitionedBy("trading_date")
        .createOrReplace()
    )

    # Publish aggregated solar share to Kafka
    solar_share_df = (
        result_df.groupBy("trading_interval")
        .agg(
            (
                spark_sum(when(col("fuel_type") == "Solar", col("generated_mw")))
                / spark_sum(col("generated_mw"))
            ).alias("solar_share")
        )
        .withColumnRenamed("trading_interval", "event_time")
        .withColumn("event_time", col("event_time").cast("string"))
    )

    brokers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    (
        solar_share_df.select(to_json(struct("event_time", "solar_share")).alias("value"))
        .write.format("kafka")
        .option("kafka.bootstrap.servers", brokers)
        .option("topic", "silver_dispatch")
        .save()
    )

    spark.stop()


if __name__ == "__main__":
    main()
