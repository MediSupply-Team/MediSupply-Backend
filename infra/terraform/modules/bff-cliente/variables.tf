variable "project" { type = string }
variable "env" { type = string }
variable "aws_region" { type = string }
variable "vpc_id" { type = string }
variable "public_subnets" { type = list(string) }
variable "private_subnets" { type = list(string) }
variable "bff_name" { type = string }
variable "bff_app_port" { type = number }
variable "bff_repo_name" { type = string }
variable "bff_env" { type = map(string) }

variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
}

# ✅ VARIABLES AGREGADAS:
variable "sqs_url" {
  description = "SQS Queue URL"
  type        = string
}

variable "sqs_arn" {
  description = "SQS Queue ARN"
  type        = string
}

variable "catalogo_service_url" {
  description = "URL of the catalogo service (internal ALB)"
  type        = string
}

variable "cliente_service_url" {
  description = "URL of the cliente service (internal ALB)"
  type        = string
}