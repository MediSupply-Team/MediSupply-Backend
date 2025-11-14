output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.cliente.repository_url
}

output "service_connect_dns" {
  description = "Service Connect DNS name for internal communication"
  value       = "cliente.svc.local"
}

output "service_connect_port" {
  description = "Service Connect port"
  value       = var.container_port
}

output "service_connect_url" {
  description = "Full Service Connect URL for internal communication"
  value       = "http://cliente.svc.local:${var.container_port}"
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.cliente.name
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name (empty in LocalStack)"
  value       = length(aws_cloudwatch_log_group.cliente) > 0 ? aws_cloudwatch_log_group.cliente[0].name : ""
}

output "db_credentials_secret_arn" {
  description = "Database credentials secret ARN"
  value       = aws_secretsmanager_secret.cliente_db_credentials.arn
}

output "db_url_secret_arn" {
  description = "Database URL secret ARN (for other services to access cliente DB)"
  value       = aws_secretsmanager_secret.cliente_db_credentials.arn
}

# ============================================================
# DEPRECATED OUTPUTS - ALB eliminado para reducir costos
# ============================================================
# Los siguientes outputs han sido eliminados:
# - alb_dns_name
# - alb_url
#
# Usar service_connect_url en su lugar