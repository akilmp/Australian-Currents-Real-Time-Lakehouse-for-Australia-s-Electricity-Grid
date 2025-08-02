resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name
}

resource "aws_glue_catalog_database" "catalog" {
  name = var.glue_database_name
}
