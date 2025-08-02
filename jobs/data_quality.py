"""Spark jobs with integrated Great Expectations validation."""

from pathlib import Path
import yaml

from pyspark.sql import SparkSession
from great_expectations.dataset import SparkDFDataset


def _validate(df, suite_name: str) -> None:
    """Run Great Expectations validation using a YAML expectation suite."""

    suite_path = Path("great_expectations/expectations") / f"{suite_name}.yml"
    with suite_path.open() as f:
        suite = yaml.safe_load(f)

    ge_df = SparkDFDataset(df)
    validation = ge_df.validate(expectation_suite=suite)
    if not validation["success"]:
        raise ValueError(f"{suite_name} validation failed")


def bronze_job(input_path: str) -> None:
    """Load raw dispatch data and enforce basic quality rules."""

    spark = SparkSession.builder.appName("bronze_job").getOrCreate()
    df = spark.read.parquet(input_path)
    _validate(df, "bronze_suite")
    # Continue with further Bronze processing here


def silver_job(input_path: str) -> None:
    """Validate curated dispatch data before loading to Silver layer."""

    spark = SparkSession.builder.appName("silver_job").getOrCreate()
    df = spark.read.parquet(input_path)
    _validate(df, "silver_suite")
    # Continue with further Silver processing here
