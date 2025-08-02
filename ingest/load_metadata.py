"""Load AEMO unit and region metadata CSVs into Iceberg tables.

This script reads unit and region metadata from CSV files and writes them into
Iceberg tables ``nem.unit_metadata`` and ``nem.region_metadata`` respectively.

Run manually with::

    spark-submit ingest/load_metadata.py --unit-csv path/to/unit.csv --region-csv path/to/region.csv

In the default mode the tables are written using the Iceberg catalog.  For unit
testing a ``use_iceberg=False`` flag is available which writes to Spark's
default catalog instead.
"""
from __future__ import annotations

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.types import StructField, StructType, StringType


def load_metadata(
    spark: SparkSession, unit_csv: str, region_csv: str, use_iceberg: bool = True
) -> None:
    """Load unit and region metadata CSVs into catalog tables.

    Parameters
    ----------
    spark:
        Active :class:`~pyspark.sql.SparkSession`.
    unit_csv:
        Path to the unit metadata CSV file.
    region_csv:
        Path to the region metadata CSV file.
    use_iceberg:
        When ``True`` (default), the tables are written using the Iceberg
        connector.  When ``False`` they are saved using Spark's built-in catalog
        which is useful for unit tests.
    """

    unit_schema = StructType(
        [
            StructField("unit_id", StringType(), True),
            StructField("fuel_type", StringType(), True),
            StructField("station_name", StringType(), True),
        ]
    )
    region_schema = StructType(
        [
            StructField("region_id", StringType(), True),
            StructField("region_name", StringType(), True),
        ]
    )

    unit_df = spark.read.csv(unit_csv, header=True, schema=unit_schema)
    region_df = spark.read.csv(region_csv, header=True, schema=region_schema)

    if use_iceberg:
        unit_writer = unit_df.writeTo("nem.unit_metadata").using("iceberg")
        region_writer = region_df.writeTo("nem.region_metadata").using("iceberg")
        unit_writer.createOrReplace()
        region_writer.createOrReplace()
    else:  # pragma: no cover - not executed in production
        unit_df.write.mode("overwrite").saveAsTable("nem.unit_metadata")
        region_df.write.mode("overwrite").saveAsTable("nem.region_metadata")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load AEMO metadata into Iceberg tables")
    parser.add_argument("--unit-csv", required=True, help="Path to unit metadata CSV")
    parser.add_argument("--region-csv", required=True, help="Path to region metadata CSV")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("load_metadata").getOrCreate()
    try:
        load_metadata(spark, args.unit_csv, args.region_csv)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
