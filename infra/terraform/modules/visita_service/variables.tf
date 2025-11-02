variable "project" {
  description = "Nombre del proyecto"
  type        = string
}

variable "env" {
  description = "Entorno (dev, staging, prod)"
  type        = string
}

variable "environment" {
  description = "Entorno completo (local, aws)"
  type        = string
}

variable "aws_region" {
  description = "Region de AWS"
  type        = string
}

variable "service_name" {
  description = "Nombre del servicio"
  type        = string
  default     = "visita"
}

variable "vpc_id" {
  description = "ID de la VPC"
  type        = string
}

variable "public_subnets" {
  description = "Subnets públicas para ALB"
  type        = list(string)
}

variable "private_subnets" {
  description = "Subnets privadas para ECS tasks"
  type        = list(string)
}

variable "ecs_cluster_arn" {
  description = "ARN del cluster ECS"
  type        = string
}

variable "db_url_secret_arn" {
  description = "ARN del secret con DATABASE_URL"
  type        = string
}

variable "app_port" {
  description = "Puerto de la aplicación"
  type        = number
  default     = 8003
}

variable "image_tag" {
  description = "Tag de la imagen Docker"
  type        = string
  default     = "latest"
}

variable "desired_count" {
  description = "Número deseado de tasks"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU para el task"
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Memoria para el task"
  type        = string
  default     = "512"
}

variable "health_check_path" {
  description = "Path para health check"
  type        = string
  default     = "/health"
}

variable "shared_http_listener_arn" {
  description = "ARN del listener HTTP del ALB compartido (bff-cliente-alb)"
  type        = string
}

variable "shared_alb_sg_id" {
  description = "Security Group ID del ALB compartido"
  type        = string
}

variable "s3_bucket_name" {
  description = "Nombre del bucket S3 para archivos (fotos/videos)"
  type        = string
  default     = ""
}
