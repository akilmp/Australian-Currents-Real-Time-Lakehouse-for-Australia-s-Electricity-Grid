resource "aws_prometheus_workspace" "this" {
  alias = var.amp_workspace_name
}

resource "aws_grafana_workspace" "this" {
  name                     = var.grafana_workspace_name
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
}
