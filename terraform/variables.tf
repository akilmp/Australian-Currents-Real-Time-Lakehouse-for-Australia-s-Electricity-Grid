variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket for data storage"
  type        = string
}

variable "glue_database_name" {
  description = "Glue catalog database name"
  type        = string
}

variable "kafka_version" {
  description = "Kafka version for MSK"
  type        = string
}

variable "kafka_broker_nodes" {
  description = "Number of MSK broker nodes"
  type        = number
}

variable "kafka_instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
}

variable "kafka_subnet_ids" {
  description = "Subnet IDs for MSK brokers"
  type        = list(string)
}

variable "kafka_security_group_ids" {
  description = "Security group IDs for MSK brokers"
  type        = list(string)
}

variable "emr_release_label" {
  description = "Release label for EMR Serverless"
  type        = string
}

variable "emr_application_type" {
  description = "EMR Serverless application type"
  type        = string
}

variable "emr_spot_capacity" {
  description = "Maximum EMR Serverless spot capacity units"
  type        = number
  default     = 20
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster for Flink"
  type        = string
}

variable "amp_workspace_name" {
  description = "Alias for AMP workspace"
  type        = string
}

variable "grafana_workspace_name" {
  description = "Name of Grafana workspace"
  type        = string
}

variable "budget_amount" {
  description = "Monthly cost budget limit in USD"
  type        = number
  default     = 100
}

variable "budget_email" {
  description = "Email address for budget notifications"
  type        = string
}
