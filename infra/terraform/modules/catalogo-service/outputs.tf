# ============================================================
# CATALOGO SERVICE MODULE - OUTPUTS
# ============================================================
# Outputs del módulo catalogo-service para uso en otros recursos

# ECR Repository
output "ecr_repository_url" {
  description = "URL del repository ECR para catalogo-service"
  value       = aws_ecr_repository.catalogo.repository_url
}

output "ecr_repository_arn" {
  description = "ARN del repository ECR para catalogo-service"
  value       = aws_ecr_repository.catalogo.arn
}

# RDS Database - COMENTADO: catalogo ahora usa la base de datos compartida
# output "db_instance_endpoint" {
#   description = "Endpoint de la base de datos RDS para catalogo-service"
#   value       = aws_db_instance.catalogo_postgres.endpoint
# }

# output "db_instance_identifier" {
#   description = "Identificador de la instancia RDS para catalogo-service"
#   value       = aws_db_instance.catalogo_postgres.identifier
# }

# output "db_name" {
#   description = "Nombre de la base de datos"
#   value       = aws_db_instance.catalogo_postgres.db_name
# }

# output "db_port" {
#   description = "Puerto de la base de datos"
#   value       = aws_db_instance.catalogo_postgres.port
# }

# S3 Bucket (compartido con visita-service)
output "s3_bucket_name" {
  description = "Nombre del bucket S3 compartido para uploads"
  value       = local.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN del bucket S3 compartido para uploads"
  value       = local.s3_bucket_arn
}

# SQS Queue
output "sqs_queue_url" {
  description = "URL de la cola SQS FIFO para catalogo-service"
  value       = aws_sqs_queue.catalogo_events.url
}

output "sqs_queue_arn" {
  description = "ARN de la cola SQS FIFO para catalogo-service"
  value       = aws_sqs_queue.catalogo_events.arn
}

output "sqs_dlq_url" {
  description = "URL de la Dead Letter Queue para catalogo-service"
  value       = aws_sqs_queue.catalogo_dlq.url
}

# ECS Service
output "ecs_service_name" {
  description = "Nombre del servicio ECS para catalogo-service"
  value       = aws_ecs_service.catalogo.name
}

output "ecs_service_arn" {
  description = "ARN del servicio ECS para catalogo-service"
  value       = aws_ecs_service.catalogo.id
}

output "ecs_task_definition_arn" {
  description = "ARN de la task definition para catalogo-service"
  value       = aws_ecs_task_definition.catalogo.arn
}

# ALB Target Group
output "target_group_arn" {
  description = "ARN del target group ALB para catalogo-service"
  value       = aws_lb_target_group.catalogo.arn
}

# Security Groups
output "ecs_security_group_id" {
  description = "ID del security group para ECS catalogo-service"
  value       = aws_security_group.catalogo_ecs_sg.id
}

output "db_security_group_id" {
  description = "ID del security group para RDS catalogo-service"
  value       = aws_security_group.catalogo_postgres_sg.id
}

# CloudWatch Logs
output "cloudwatch_log_group_name" {
  description = "Nombre del log group de CloudWatch para catalogo-service (empty in LocalStack)"
  value       = length(aws_cloudwatch_log_group.catalogo) > 0 ? aws_cloudwatch_log_group.catalogo[0].name : ""
}

# Secrets Manager - COMENTADO: catalogo ahora usa los secrets compartidos
# output "db_credentials_secret_arn" {
#   description = "ARN del secret de Secrets Manager con credenciales de DB"
#   value       = aws_secretsmanager_secret.catalogo_db_credentials.arn
# }

# IAM Roles
output "ecs_task_role_arn" {
  description = "ARN del rol IAM para tareas ECS"
  value       = aws_iam_role.catalogo_ecs_task_role.arn
}

output "ecs_execution_role_arn" {
  description = "ARN del rol IAM para ejecución ECS"
  value       = aws_iam_role.catalogo_ecs_execution_role.arn
}