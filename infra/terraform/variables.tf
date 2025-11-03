# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================
variable "environment" {
  description = "Environment type: local (LocalStack) or aws (AWS)"
  type        = string
  default     = "aws"
  validation {
    condition     = contains(["local", "aws"], var.environment)
    error_message = "Environment must be 'local' or 'aws'."
  }
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
}

# ============================================================
# MAIN DATABASE (Orders & Rutas)
# ============================================================
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = ""
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "db_publicly_accessible" {
  description = "Make database publicly accessible"
  type        = bool
  default     = false
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "db_backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "db_enable_cloudwatch_logs" {
  description = "Enable CloudWatch logs export"
  type        = bool
  default     = true
}

variable "db_performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "db_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds (0, 1, 5, 10, 15, 30, 60)"
  type        = number
  default     = 60
}

# Variables adicionales de DB que vi en los errores
variable "db_storage_type" {
  description = "Storage type (gp2, gp3, io1)"
  type        = string
  default     = "gp3"
}

variable "db_storage_encrypted" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "db_backup_window" {
  description = "Backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Maintenance window (UTC)"
  type        = string
  default     = "mon:04:00-mon:05:00"
}

variable "db_skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = false
}

# ============================================================
# ORDERS SERVICE
# ============================================================
variable "ecr_image" {
  description = "ECR image URI for orders service"
  type        = string
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "orders_ecr_image" {
  description = "URI de la imagen de orders en ECR (repository:tag)"
  type        = string
  default     = ""
}

# ============================================================
# CONSUMER (SQS + Worker)
# ============================================================
variable "use_haproxy" {
  description = "Whether to use HAProxy load balancing"
  type        = bool
  default     = false
}

# ============================================================
# BFF VENTA
# ============================================================
variable "bff_name" {
  description = "BFF service name"
  type        = string
  default     = ""
}

variable "bff_app_port" {
  description = "BFF application port"
  type        = number
}

variable "bff_repo_name" {
  description = "BFF ECR repository name"
  type        = string
  default     = "medisupply-dev-bff-venta"
}

variable "bff_env" {
  description = "Environment variables for BFF"
  type        = map(string)
  default     = {}
}

# ============================================================
# CATALOGO SERVICE
# ============================================================
variable "catalogo_service_url" {
  description = "URL del catalogo service para los BFFs"
  type        = string
  default     = "placeholder-will-be-updated-after-deploy"
}

variable "catalogo_container_port" {
  description = "Catalogo service container port"
  type        = number
  default     = 3000
}

variable "catalogo_desired_count" {
  description = "Desired count of catalogo tasks"
  type        = number
  default     = 2
}

variable "catalogo_cpu" {
  description = "CPU units for catalogo service"
  type        = string
  default     = "512"
}

variable "catalogo_memory" {
  description = "Memory for catalogo service"
  type        = string
  default     = "1024"
}

variable "catalogo_db_instance_class" {
  description = "RDS instance class for catalogo database"
  type        = string
  default     = "db.t3.micro"
}

variable "catalogo_db_allocated_storage" {
  description = "Allocated storage for catalogo database in GB"
  type        = number
  default     = 20
}

variable "catalogo_db_backup_retention_days" {
  description = "Backup retention period for catalogo database"
  type        = number
  default     = 7
}

# ============================================================
# BFF CATALOGO
# ============================================================
variable "bff_catalogo_image_tag" {
  description = "Image tag for BFF catalogo"
  type        = string
  default     = "latest"
}

# ============================================================
# TAGS ADICIONALES
# ============================================================
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# ============================================================
# NETWORKING (probablemente necesarias también)
# ============================================================
variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = ""
}

variable "public_subnets" {
  description = "Public subnet IDs"
  type        = list(string)
  default     = []
}

variable "private_subnets" {
  description = "Private subnet IDs"
  type        = list(string)
  default     = []
}

# ============================================================
# ECS & SERVICE DISCOVERY
# ============================================================
variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
  default     = ""
}

variable "service_connect_namespace_name" {
  description = "Service Connect namespace name"
  type        = string
  default     = ""
}

# ============================================================
# IAM ROLES (si son necesarias)
# ============================================================
variable "ecs_execution_role_arn" {
  description = "IAM Role ARN for ECS task execution"
  type        = string
  default     = ""
}

variable "ecs_task_role_arn" {
  description = "IAM Role ARN for ECS task runtime"
  type        = string
  default     = ""
}

# ============================================================
# SECRETS
# ============================================================
variable "db_url_secret_arn" {
  description = "ARN of DB_URL secret in Secrets Manager"
  type        = string
  default     = ""
}

# ============================================================
# OPTIMIZADOR-RUTAS-SERVICE VARIABLES
# ============================================================

variable "osrm_url" {
  description = "URL del servidor OSRM"
  type        = string
  default     = "http://osrm-medisupply.duckdns.org:5000"
}

variable "optimizador_rutas_image_tag" {
  description = "Docker image tag para optimizador-rutas-service"
  type        = string
  default     = "latest"
}
