# ============================================================
# AUTH-SERVICE MODULE VARIABLES
# ============================================================

variable "project" {
  description = "Nombre del proyecto"
  type        = string
}

variable "env" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "environment" {
  description = "Ambiente para condiciones (local, aws)"
  type        = string
}

variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

# ============================================================
# NETWORKING
# ============================================================

variable "vpc_id" {
  description = "ID de la VPC"
  type        = string
}

variable "private_subnets" {
  description = "Lista de subnets privadas"
  type        = list(string)
}

variable "public_subnets" {
  description = "Lista de subnets públicas"
  type        = list(string)
  default     = []
}

# ============================================================
# ECS
# ============================================================

variable "ecs_cluster_name" {
  description = "Nombre del cluster ECS"
  type        = string
}

variable "container_port" {
  description = "Puerto del contenedor"
  type        = number
  default     = 8004
}

variable "desired_count" {
  description = "Número de tareas deseadas"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU para la tarea (256, 512, 1024, etc.)"
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Memoria para la tarea (512, 1024, 2048, etc.)"
  type        = string
  default     = "512"
}

# ============================================================
# ALB
# ============================================================

variable "alb_listener_arn" {
  description = "ARN del listener del ALB compartido"
  type        = string
}

variable "shared_alb_sg_id" {
  description = "Security Group ID del ALB compartido"
  type        = string
}

# ============================================================
# SERVICE CONNECT
# ============================================================

variable "service_connect_namespace_name" {
  description = "Nombre del namespace de Service Connect"
  type        = string
}

# ============================================================
# DATABASE
# ============================================================

variable "shared_db_url_secret_arn" {
  description = "ARN del secret de DATABASE_URL compartido (orders-postgres)"
  type        = string
}

variable "shared_db_password_secret_arn" {
  description = "ARN del secret de DB_PASSWORD compartido"
  type        = string
}

# ============================================================
# ADDITIONAL TAGS
# ============================================================

variable "additional_tags" {
  description = "Tags adicionales para los recursos"
  type        = map(string)
  default     = {}
}