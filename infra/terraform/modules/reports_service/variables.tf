variable "project"         { type = string }
variable "env"             { type = string }

variable "cluster_arn"     { type = string }
variable "vpc_id"          { type = string }
variable "public_subnets"  { type = list(string) }
variable "private_subnets" { type = list(string) }

variable "report_ecr_image" {
  description = "URI ECR (repository:tag) para reports"
  type        = string
}

variable "app_port" {
  description = "Puerto expuesto por el contenedor"
  type        = number
  default     = 8000
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "cpu" {
  type    = string
  default = "256"
}

variable "memory" {
  type    = string
  default = "512"
}

# Secret OBLIGATORIO (como en rutas): DB_URL en Secrets Manager
variable "db_url_secret_name" {
  description = "Nombre del secret con la DB URL (ej: medisupply/dev/report/DB_URL)"
  type        = string
}