# ============================================================
# AUTH-SERVICE OUTPUTS
# ============================================================

output "service_name" {
  description = "Nombre del servicio ECS"
  value       = aws_ecs_service.auth.name
}

output "service_connect_url" {
  description = "URL interna para Service Connect (comunicación entre microservicios)"
  value       = "http://auth:${var.container_port}"
}

output "security_group_id" {
  description = "Security Group ID del ECS service"
  value       = aws_security_group.auth_ecs_sg.id
}

output "target_group_arn" {
  description = "ARN del Target Group del ALB"
  value       = aws_lb_target_group.auth.arn
}

output "ecr_repository_url" {
  description = "URL del repositorio ECR para auth-service"
  value       = aws_ecr_repository.auth.repository_url
}

output "jwt_secret_arn" {
  description = "ARN del secret de JWT en Secrets Manager"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "ecs_service_id" {
  description = "ID del servicio ECS"
  value       = aws_ecs_service.auth.id
}
