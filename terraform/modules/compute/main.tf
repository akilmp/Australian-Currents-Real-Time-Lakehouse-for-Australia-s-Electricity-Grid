resource "aws_emrserverless_application" "this" {
  name          = "emr-serverless-app"
  release_label = var.emr_release_label
  type          = var.emr_application_type
}

resource "aws_ecs_cluster" "flink" {
  name = var.ecs_cluster_name
}
