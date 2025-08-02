resource "aws_emrserverless_application" "this" {
  name          = "emr-serverless-app"
  release_label = var.emr_release_label
  type          = var.emr_application_type

  maximum_capacity {
    cpu    = "${var.emr_spot_capacity} vCPU"
    memory = "${var.emr_spot_capacity * 4} GB"
  }
}

resource "aws_ecs_cluster" "flink" {
  name = var.ecs_cluster_name
}
