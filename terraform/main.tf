terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "state/terraform.tfstate"
    region         = "ap-southeast-2"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}

module "network" {
  source   = "./modules/network"
  vpc_cidr = var.vpc_cidr
}

module "storage" {
  source             = "./modules/storage"
  bucket_name        = var.bucket_name
  glue_database_name = var.glue_database_name
}

module "kafka" {
  source                 = "./modules/kafka"
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.kafka_broker_nodes
  instance_type          = var.kafka_instance_type
  subnet_ids             = var.kafka_subnet_ids
  security_group_ids     = var.kafka_security_group_ids
}

module "compute" {
  source               = "./modules/compute"
  emr_release_label    = var.emr_release_label
  emr_application_type = var.emr_application_type
  ecs_cluster_name     = var.ecs_cluster_name
  emr_spot_capacity    = var.emr_spot_capacity
}

module "observability" {
  source                 = "./modules/observability"
  amp_workspace_name     = var.amp_workspace_name
  grafana_workspace_name = var.grafana_workspace_name
}

resource "aws_budgets_budget" "monthly" {
  name        = "monthly-budget"
  budget_type = "COST"
  time_unit   = "MONTHLY"

  limit_amount = var.budget_amount
  limit_unit   = "USD"

  notification {
    comparison_operator        = "GREATER_THAN"
    notification_type          = "ACTUAL"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    subscriber_email_addresses = [var.budget_email]
  }
}
