variable "project"       { type = string }
variable "env"           { type = string }
variable "aws_region"    { type = string }

# Infra
variable "vpc_id"         { type = string }
variable "private_subnets"{ type = list(string) }
variable "ecs_cluster_arn"{
  description = "ECS Cluster ARN"
  type        = string
}

# Imagen ECR completa, con tag SHA (recomendado) o digest
variable "ecr_image" {
  description = "ECR image URI (e.g., 8386.../orders-service:<sha>)"
  type        = string
}

# Puerto real de la app (coherente con Dockerfile)
variable "app_port" {
  description = "Puerto de la app (debe ser 3000 para este servicio)"
  type        = number
  default     = 3000
}

# Secrets
variable "db_url_secret_arn" {
  description = "ARN del secreto DB_URL en Secrets Manager (string)"
  type        = string
}

# Roles (pasalos desde tu IAM; si ya los manejas en otro lado, usa sus ARNs)
variable "ecs_execution_role_arn" {
  description = "IAM Role ARN para ejecucion de tareas ECS (pull de ECR, logs)"
  type        = string
}
variable "ecs_task_role_arn" {
  description = "IAM Role ARN para permisos en runtime de la task"
  type        = string
}

# Namespace de Service Connect (p.ej., injectado desde networking)
variable "service_connect_namespace_name" {
  description = "Nombre del namespace de Service Connect (p.ej. svc.local)"
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