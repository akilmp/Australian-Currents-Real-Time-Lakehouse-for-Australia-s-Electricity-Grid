import pathlib
import sys

import pytest
from pyspark.sql import SparkSession

# Ensure the repository root is on the Python path so spark_jobs can be imported
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from spark_jobs.silver_batch import transform_dispatch


@pytest.fixture(scope="session")
def spark():
    spark = (
        SparkSession.builder.master("local[2]").appName("pytest-spark").getOrCreate()
    )
    yield spark
    spark.stop()


def test_transform_dispatch(spark):
    # Load sample data into catalog tables
    spark.sql("CREATE DATABASE IF NOT EXISTS nem")

    base_path = pathlib.Path(__file__).parent / "spark"

    bronze_schema = (
        "unit_id string, trading_interval timestamp, generated_mw double, "
        "fuel_type string, trading_date date"
    )
    bronze_df = spark.read.csv(
        str(base_path / "bronze_dispatch.csv"),
        header=True,
        schema=bronze_schema,
    )
    bronze_df.write.mode("overwrite").saveAsTable("nem.bronze_dispatch")

    meta_schema = "unit_id string, fuel_type string, station_name string"
    meta_df = spark.read.csv(str(base_path / "unit_metadata.csv"), header=True, schema=meta_schema)
    meta_df.write.mode("overwrite").saveAsTable("nem.unit_metadata")

    result = transform_dispatch(spark)

    # After dropping duplicates there should be two rows
    assert result.count() == 2

    # Check that metadata columns were appended correctly
    rows = {(r.unit_id, r.fuel_type, r.station_name) for r in result.collect()}
    assert ("UNIT1", "Coal", "StationA") in rows
    assert ("UNIT2", "Solar", "StationB") in rows

    # Ensure trading_interval and unit_id combinations are unique
    assert (
        result.select("trading_interval", "unit_id").distinct().count() == result.count()
    )
