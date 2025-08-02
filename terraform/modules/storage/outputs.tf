output "bucket_id" {
  value = aws_s3_bucket.data.id
}

output "glue_database_name" {
  value = aws_glue_catalog_database.catalog.name
}
