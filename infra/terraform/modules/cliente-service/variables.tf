variable "project" {
  description = "Project name"
  type        = string
}

variable "env" {
  description = "Environment (dev/qa/prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnets" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_cluster_name" {
  description = "ECS Cluster name"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Number of tasks"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU units"
  type        = string
  default     = "512"
}

variable "memory" {
  description = "Memory in MB"
  type        = string
  default     = "1024"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage (GB)"
  type        = number
  default     = 20
}

variable "db_backup_retention_days" {
  description = "RDS backup retention days"
  type        = number
  default     = 7
}

variable "service_connect_namespace_name" {
  description = "Service Connect namespace for internal service discovery"
  type        = string
}