variable "bucket_name" {
  description = "S3 bucket for data storage"
  type        = string
}

variable "glue_database_name" {
  description = "Glue catalog database name"
  type        = string
}
