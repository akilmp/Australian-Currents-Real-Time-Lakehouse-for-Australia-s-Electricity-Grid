output "emr_application_id" {
  value = aws_emrserverless_application.this.id
}

output "ecs_cluster_id" {
  value = aws_ecs_cluster.flink.id
}
