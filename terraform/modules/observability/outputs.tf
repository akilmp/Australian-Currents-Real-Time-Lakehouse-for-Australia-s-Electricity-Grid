output "amp_workspace_id" {
  value = aws_prometheus_workspace.this.id
}

output "grafana_workspace_id" {
  value = aws_grafana_workspace.this.id
}
