variable "project" {
  description = "Project name"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the consumer will run"
  type        = string
}

variable "private_subnets" {
  description = "Private subnet IDs for the consumer tasks"
  type        = list(string)
}

variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN where the consumer will run"
  type        = string
}

variable "use_haproxy" {
  description = "Whether to use HAProxy load balancing"
  type        = bool
  default     = false
}

variable "bff_alb_dns_name" {
  description = "DNS name of the BFF ALB (for HAProxy scenario)"
  type        = string
  default     = ""
}

variable "orders_service_url" {
  description = "URL of the Orders service (via Service Connect or ALB). If empty, defaults to 'http://orders:3000/orders'"
  type        = string
  default     = ""
}

variable "service_connect_namespace_name" {
  description = "Service Connect namespace name (e.g., 'svc.local')"
  type        = string
}

variable "environment" {
  description = "Environment type: local (LocalStack) or aws (AWS)"
  type        = string
  validation {
    condition     = contains(["local", "aws"], var.environment)
    error_message = "Environment must be 'local' or 'aws'."
  }
}

variable "ecr_force_delete" {
  type    = bool
  default = true
  description = "If true, allows deleting the ECR repository even when it still contains images."
}