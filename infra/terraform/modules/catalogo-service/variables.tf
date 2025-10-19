# ============================================================
# CATALOGO SERVICE MODULE - VARIABLES
# ============================================================
# Variables de entrada para el módulo catalogo-service

# Basic Configuration
variable "project" {
  description = "Nombre del proyecto (ej: medisupply)"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project))
    error_message = "Project name debe contener solo letras minúsculas, números y guiones."
  }
}

variable "env" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "Environment debe ser: dev, staging, o prod."
  }
}

# ============================================================
# NUEVAS VARIABLES PARA MANEJO DE RECURSOS EXISTENTES
# ============================================================

variable "check_existing_resources" {
  description = "Verificar si los recursos ya existen antes de crear nuevos"
  type        = bool
  default     = true
}

variable "create_new_resources" {
  description = "Forzar creación de nuevos recursos con sufijo timestamp"
  type        = bool
  default     = false
}

variable "import_existing_resources" {
  description = "Importar recursos existentes al state de Terraform"
  type        = bool
  default     = false
}

variable "skip_deletion_protection" {
  description = "Omitir protección de eliminación para bases de datos (usar con precaución)"
  type        = bool
  default     = false
}

# Network Configuration
variable "vpc_id" {
  description = "ID de la VPC donde desplegar recursos"
  type        = string
}

variable "private_subnets" {
  description = "Lista de subnet IDs privadas para ECS y RDS"
  type        = list(string)
  validation {
    condition     = length(var.private_subnets) >= 2
    error_message = "Se requieren al menos 2 subnets privadas para alta disponibilidad."
  }
}

variable "public_subnets" {
  description = "Lista de subnet IDs públicas"
  type        = list(string)
  validation {
    condition     = length(var.public_subnets) >= 2
    error_message = "Se requieren al menos 2 subnets públicas para alta disponibilidad."
  }
}

# ECS Configuration
variable "ecs_cluster_name" {
  description = "Nombre del cluster ECS existente"
  type        = string
}

variable "alb_listener_arn" {
  description = "ARN del listener del ALB para routing"
  type        = string
}

# Container Configuration
variable "container_port" {
  description = "Puerto en el que corre el contenedor de catalogo-service"
  type        = number
  default     = 8000
  validation {
    condition     = var.container_port > 0 && var.container_port < 65536
    error_message = "Container port debe estar entre 1 y 65535."
  }
}

variable "desired_count" {
  description = "Número deseado de tareas ECS en ejecución"
  type        = number
  default     = 2
  validation {
    condition     = var.desired_count >= 1 && var.desired_count <= 10
    error_message = "Desired count debe estar entre 1 y 10."
  }
}

variable "cpu" {
  description = "CPU allocation para el contenedor (256, 512, 1024, etc.)"
  type        = number
  default     = 256
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU debe ser uno de: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "Memoria allocation para el contenedor (MB)"
  type        = number
  default     = 512
  validation {
    condition     = var.memory >= 128 && var.memory <= 8192
    error_message = "Memory debe estar entre 128 MB y 8192 MB."
  }
}

# Database Configuration
variable "db_instance_class" {
  description = "Clase de instancia RDS para PostgreSQL"
  type        = string
  default     = "db.t3.micro"
  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z]+$", var.db_instance_class))
    error_message = "DB instance class debe seguir el formato: db.{family}.{size}"
  }
}

variable "db_allocated_storage" {
  description = "Almacenamiento inicial de la DB en GB"
  type        = number
  default     = 20
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 100
    error_message = "DB storage debe estar entre 20 GB y 100 GB."
  }
}

variable "db_backup_retention_days" {
  description = "Días de retención de backups automáticos"
  type        = number
  default     = 7
  validation {
    condition     = var.db_backup_retention_days >= 0 && var.db_backup_retention_days <= 35
    error_message = "Backup retention debe estar entre 0 y 35 días."
  }
}

# SQS Configuration
variable "sqs_message_retention_seconds" {
  description = "Tiempo de retención de mensajes SQS en segundos"
  type        = number
  default     = 1209600 # 14 days
  validation {
    condition     = var.sqs_message_retention_seconds >= 60 && var.sqs_message_retention_seconds <= 1209600
    error_message = "Message retention debe estar entre 60 segundos y 14 días."
  }
}

variable "sqs_visibility_timeout_seconds" {
  description = "Timeout de visibilidad para mensajes SQS"
  type        = number
  default     = 30
  validation {
    condition     = var.sqs_visibility_timeout_seconds >= 0 && var.sqs_visibility_timeout_seconds <= 43200
    error_message = "Visibility timeout debe estar entre 0 y 43200 segundos (12 horas)."
  }
}

# CloudWatch Configuration
variable "log_retention_days" {
  description = "Días de retención para logs de CloudWatch"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention debe ser uno de los valores permitidos por CloudWatch."
  }
}

# Health Check Configuration
variable "health_check_path" {
  description = "Path para health check del ALB"
  type        = string
  default     = "/health"
}

variable "health_check_timeout" {
  description = "Timeout para health check en segundos"
  type        = number
  default     = 5
  validation {
    condition     = var.health_check_timeout >= 2 && var.health_check_timeout <= 120
    error_message = "Health check timeout debe estar entre 2 y 120 segundos."
  }
}

variable "health_check_interval" {
  description = "Intervalo entre health checks en segundos"
  type        = number
  default     = 30
  validation {
    condition     = var.health_check_interval >= 5 && var.health_check_interval <= 300
    error_message = "Health check interval debe estar entre 5 y 300 segundos."
  }
}

# Tags
variable "additional_tags" {
  description = "Tags adicionales para aplicar a los recursos"
  type        = map(string)
  default     = {}
}