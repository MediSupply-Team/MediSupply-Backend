variable "project" {
  description = "Project name"
  type        = string
}

variable "env" {
  description = "Environment (dev/qa/prod)"
  type        = string
}

variable "environment" {
  description = "Deployment environment (local for LocalStack, aws for real AWS)"
  type        = string
  validation {
    condition     = contains(["local", "aws"], var.environment)
    error_message = "Environment must be either 'local' or 'aws'."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "service_name" {
  description = "Service name"
  type        = string
  default     = "optimizador-rutas"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnets" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "private_subnets" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
}

variable "mapbox_token_secret_arn" {
  description = "Mapbox Access Token secret ARN from Secrets Manager"
  type        = string
}

variable "osrm_url" {
  description = "OSRM server URL"
  type        = string
  default     = "http://osrm-medisupply.duckdns.org:5000"
}

variable "ruta_service_url" {
  description = "Ruta service internal URL"
  type        = string
  default     = "http://localhost:8000"
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8004
}

variable "ecr_image" {
  description = "ECR image (just the tag, repository is created by module)"
  type        = string
  default     = "latest"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "desired_count" {
  description = "Number of tasks"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU units"
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Memory in MB"
  type        = string
  default     = "512"
}

variable "health_check_path" {
  description = "Health check endpoint"
  type        = string
  default     = "/health"
}

variable "shared_http_listener_arn" {
  type        = string
  description = "ARN del listener HTTP del ALB compartido"
}

variable "shared_alb_sg_id" {
  type        = string
  description = "Security Group ID del ALB compartido"
}
