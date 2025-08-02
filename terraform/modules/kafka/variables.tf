variable "kafka_version" {
  description = "Kafka version for MSK"
  type        = string
}

variable "number_of_broker_nodes" {
  description = "Number of MSK broker nodes"
  type        = number
}

variable "instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for MSK brokers"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs for MSK brokers"
  type        = list(string)
}
