variable "emr_release_label" {
  description = "Release label for EMR Serverless"
  type        = string
}

variable "emr_application_type" {
  description = "EMR Serverless application type"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster for Flink"
  type        = string
}
