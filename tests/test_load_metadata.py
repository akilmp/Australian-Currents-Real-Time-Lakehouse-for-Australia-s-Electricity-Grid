import pathlib
import sys

import pytest
from pyspark.sql import SparkSession

# Ensure repo root on path so ingest modules can be imported
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from ingest.load_metadata import load_metadata


@pytest.fixture(scope="session")
def spark():
    spark = SparkSession.builder.master("local[2]").appName("pytest-spark").getOrCreate()
    yield spark
    spark.stop()


def test_load_metadata_tables(spark):
    spark.sql("CREATE DATABASE IF NOT EXISTS nem")
    base_path = pathlib.Path(__file__).parent / "spark"
    unit_csv = str(base_path / "unit_metadata.csv")
    region_csv = str(base_path / "region_metadata.csv")

    load_metadata(spark, unit_csv, region_csv, use_iceberg=False)

    unit_df = spark.table("nem.unit_metadata")
    region_df = spark.table("nem.region_metadata")

    assert unit_df.count() == 2
    assert region_df.count() == 2

    unit_rows = {(r.unit_id, r.station_name) for r in unit_df.collect()}
    assert ("UNIT1", "StationA") in unit_rows

    region_rows = {(r.region_id, r.region_name) for r in region_df.collect()}
    assert ("NSW1", "New South Wales") in region_rows
