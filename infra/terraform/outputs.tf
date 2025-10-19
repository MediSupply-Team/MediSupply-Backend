# ============================================================
# NETWORK OUTPUTS
# ============================================================
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

# ============================================================
# ECS CLUSTER OUTPUTS
# ============================================================
output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = aws_ecs_cluster.orders.name
}

output "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.orders.arn
}

# ============================================================
# DATABASE OUTPUTS (recursos directos en main.tf)
# ============================================================
output "db_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "db_address" {
  description = "RDS PostgreSQL address"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "Database username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.postgres.id
}

output "db_url_secret_arn" {
  description = "Database URL secret ARN"
  value       = aws_secretsmanager_secret.db_url.arn
}

output "db_password_secret_arn" {
  description = "Database password secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "postgres_security_group_id" {
  description = "PostgreSQL security group ID"
  value       = aws_security_group.postgres_sg.id
}

# ============================================================
# ORDERS SERVICE OUTPUTS
# ============================================================
output "orders_service_name" {
  description = "Orders service name"
  value       = module.orders.service_name
}

output "orders_log_group" {
  description = "Orders log group name"
  value       = module.orders.log_group_name
}

# ============================================================
# CONSUMER OUTPUTS
# ============================================================
output "haproxy_consumer_sqs_queue_url" {
  description = "SQS queue URL"
  value       = module.consumer.sqs_queue_url
}

output "haproxy_consumer_sqs_dlq_url" {
  description = "SQS DLQ URL"
  value       = module.consumer.sqs_dlq_url
}

# ============================================================
# BFF OUTPUTS
# ============================================================
output "bff_alb_dns" {
  description = "BFF ALB DNS name"
  value       = module.bff_venta.alb_dns_name
}

output "bff_alb_url" {
  description = "BFF URL"
  value       = "http://${module.bff_venta.alb_dns_name}"
}

output "bff_ecr_repo_url" {
  description = "BFF ECR repo URL"
  value       = module.bff_venta.ecr_repo_url
}

# ============================================================
# BFF CLIENTE OUTPUTS
# ============================================================
output "bff_cliente_alb_dns" {
  description = "BFF Cliente ALB DNS name"
  value       = module.bff_cliente.alb_dns_name
}

output "bff_cliente_alb_url" {
  description = "BFF Cliente URL"
  value       = "http://${module.bff_cliente.alb_dns_name}"
}

output "bff_cliente_ecr_repo_url" {
  description = "BFF Cliente ECR repo URL"
  value       = module.bff_cliente.ecr_repo_url
}

output "bff_cliente_service_name" {
  description = "BFF Cliente ECS service name"
  value       = module.bff_cliente.service_name
}

# ============================================================
# CLIENTE SERVICE OUTPUTS
# ============================================================
output "cliente_service_alb_dns" {
  description = "Cliente service ALB DNS name"
  value       = module.cliente_service.alb_dns_name
}

output "cliente_service_alb_url" {
  description = "Cliente service URL"
  value       = module.cliente_service.alb_url
}

output "cliente_service_ecr_repo_url" {
  description = "Cliente service ECR repo URL"
  value       = module.cliente_service.ecr_repository_url
}

output "cliente_service_name" {
  description = "Cliente service ECS service name"
  value       = module.cliente_service.service_name
}

output "cliente_service_log_group" {
  description = "Cliente service CloudWatch log group"
  value       = module.cliente_service.cloudwatch_log_group_name
}

output "cliente_db_credentials_secret_arn" {
  description = "Cliente service database credentials secret ARN"
  value       = module.cliente_service.db_credentials_secret_arn
}

# ============================================================
# CATALOGO SERVICE OUTPUTS
# ============================================================
output "catalogo_ecr_repository_url" {
  description = "Catalogo service ECR repository URL"
  value       = module.catalogo_service.ecr_repository_url
}

output "catalogo_db_endpoint" {
  description = "Catalogo service database endpoint"
  value       = module.catalogo_service.db_instance_endpoint
}

output "catalogo_sqs_queue_url" {
  description = "Catalogo service SQS queue URL"
  value       = module.catalogo_service.sqs_queue_url
}

output "catalogo_service_name" {
  description = "Catalogo ECS service name"
  value       = module.catalogo_service.ecs_service_name
}

output "catalogo_target_group_arn" {
  description = "Catalogo ALB target group ARN"
  value       = module.catalogo_service.target_group_arn
}

output "catalogo_cloudwatch_log_group" {
  description = "Catalogo CloudWatch log group"
  value       = module.catalogo_service.cloudwatch_log_group_name
}

# ============================================================
# QUICK REFERENCE
# ============================================================
output "catalogo_service_url" {
  description = "Complete URL for catalogo service through ALB"
  value       = "http://${module.bff_venta.alb_dns_name}/catalog"
}

output "quick_reference" {
  description = "Quick reference commands"
  value = {
    bff_venta_url        = "http://${module.bff_venta.alb_dns_name}"
    bff_cliente_url = "http://${module.bff_cliente.alb_dns_name}"
    catalogo_service_url = "http://${module.bff_venta.alb_dns_name}/catalog"
    catalogo_ecr         = module.catalogo_service.ecr_repository_url
    catalogo_queue       = module.catalogo_service.sqs_queue_url
    connect_to_db        = "export PGPASSWORD=$(aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.db_password.name} --query SecretString --output text) && psql -h ${aws_db_instance.postgres.address} -U ${aws_db_instance.postgres.username} -d ${aws_db_instance.postgres.db_name}"
    catalogo_db          = "aws secretsmanager get-secret-value --secret-id ${module.catalogo_service.db_credentials_secret_arn}"
    view_logs            = "aws logs tail /ecs/${var.project}-${var.env} --follow"
    catalogo_logs        = "aws logs tail ${module.catalogo_service.cloudwatch_log_group_name} --follow"
  }
}

# Rutas Service outputs
output "rutas_alb_dns" {
  description = "DNS del ALB de Rutas"
  value       = module.rutas_service.alb_dns_name
}

output "rutas_alb_url" {
  description = "URL completa del servicio de Rutas"
  value       = "http://${module.rutas_service.alb_dns_name}"
}

output "rutas_service_name" {
  description = "Nombre del servicio de Rutas en ECS"
  value       = module.rutas_service.service_name
}