# Terraform Infrastructure

This directory provisions network, storage, Kafka, compute, and observability components.

## Remote State

Remote state is stored in an S3 bucket with DynamoDB table for state locking. Update the backend configuration in `main.tf` or supply values with `-backend-config` when running `terraform init`.

## Workspaces

Use Terraform workspaces to manage separate environments:

```sh
terraform init
terraform workspace new dev    # one-time setup
terraform workspace select dev
terraform apply -var-file=dev.tfvars

terraform workspace new prod   # one-time setup
terraform workspace select prod
terraform apply -var-file=prod.tfvars
```
