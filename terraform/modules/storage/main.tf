resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name

  lifecycle_rule {
    id      = "bronze-transition"
    enabled = true
    prefix  = "bronze/"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }

  lifecycle_rule {
    id      = "silver-transition"
    enabled = true
    prefix  = "silver/"

    transition {
      days          = 180
      storage_class = "GLACIER"
    }
  }
}

resource "aws_glue_catalog_database" "catalog" {
  name = var.glue_database_name
}
