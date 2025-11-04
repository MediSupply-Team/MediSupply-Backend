output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.cliente.repository_url
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.cliente_alb.dns_name
}

output "alb_url" {
  description = "ALB URL"
  value       = "http://${aws_lb.cliente_alb.dns_name}"
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