from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, TimestampType, StringType, DoubleType
from pyspark.sql.functions import from_csv, col, to_date, current_timestamp
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Stream nem_dispatch data from Kafka to Iceberg")
    parser.add_argument("--kafka-bootstrap-servers", required=True,
                        help="Kafka bootstrap servers, e.g. localhost:9092")
    parser.add_argument("--checkpoint-path", required=True,
                        help="S3/MinIO path for streaming checkpoints")
    parser.add_argument("--kafka-topic", default="nem_dispatch",
                        help="Kafka topic to subscribe")
    parser.add_argument("--table-name", default="nem.bronze_dispatch",
                        help="Iceberg table name")
    parser.add_argument("--warehouse", default="s3a://warehouse",
                        help="Iceberg warehouse location")
    return parser.parse_args()


def main():
    args = parse_args()

    spark = (
        SparkSession.builder.appName("bronze_dispatch_stream")
        .config("spark.sql.catalog.nem", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.nem.type", "hadoop")
        .config("spark.sql.catalog.nem.warehouse", args.warehouse)
        .getOrCreate()
    )

    # Ensure Iceberg table exists
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {args.table_name} (
            trading_interval TIMESTAMP,
            region STRING,
            demand DOUBLE,
            trading_date DATE,
            ingested_at TIMESTAMP
        )
        USING iceberg
        PARTITIONED BY (trading_date)
        """
    )

    schema = StructType([
        StructField("trading_interval", TimestampType()),
        StructField("region", StringType()),
        StructField("demand", DoubleType()),
    ])

    raw_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", args.kafka_bootstrap_servers)
        .option("subscribe", args.kafka_topic)
        .option("startingOffsets", "latest")
        .load()
        .selectExpr("CAST(value AS STRING) AS csv")
    )

    parsed_df = raw_df.select(from_csv(col("csv"), schema).alias("data")).select("data.*")

    output_df = (
        parsed_df
        .withColumn("trading_date", to_date(col("trading_interval")))
        .withColumn("ingested_at", current_timestamp())
    )

    query = (
        output_df.writeStream
        .format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", args.checkpoint_path)
        .toTable(args.table_name)
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
