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

from pyspark.sql import DataFrame, SparkSession


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

    spark.stop()


if __name__ == "__main__":
    main()
