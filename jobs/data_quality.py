"""Spark jobs with integrated Great Expectations validation."""

from pyspark.sql import SparkSession
from great_expectations.dataset import SparkDFDataset


def bronze_job(input_path: str) -> None:
    """Load raw data, validate basic quality, and continue processing.

    The expectation suite checks for null IDs, null readings, and ensures
    readings fall within 0-1000.
    """
    spark = SparkSession.builder.appName("bronze_job").getOrCreate()
    df = spark.read.parquet(input_path)
    ge_df = SparkDFDataset(df)
    ge_df.expect_column_values_to_not_be_null("id")
    ge_df.expect_column_values_to_not_be_null("reading")
    ge_df.expect_column_values_to_be_between("reading", min_value=0, max_value=1000)
    validation = ge_df.validate()
    if not validation["success"]:
        raise ValueError("Bronze validation failed")
    # Continue with further Bronze processing here


def silver_job(input_path: str) -> None:
    """Validate curated data for completeness and uniqueness before loading.

    Completeness requires 99% non-null IDs and 98% non-null readings. IDs must be
    unique.
    """
    spark = SparkSession.builder.appName("silver_job").getOrCreate()
    df = spark.read.parquet(input_path)
    ge_df = SparkDFDataset(df)
    ge_df.expect_column_values_to_not_be_null("id", mostly=0.99)
    ge_df.expect_column_values_to_not_be_null("reading", mostly=0.98)
    ge_df.expect_column_values_to_be_unique("id")
    validation = ge_df.validate()
    if not validation["success"]:
        raise ValueError("Silver validation failed")
    # Continue with further Silver processing here
