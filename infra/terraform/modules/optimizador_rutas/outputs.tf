output "repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.this.repository_url
}

output "log_group_name" {
  description = "CloudWatch log group name (empty in LocalStack)"
  value       = length(aws_cloudwatch_log_group.this) > 0 ? aws_cloudwatch_log_group.this[0].name : ""
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.this.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.this.id
}

output "target_group_arn" {
  description = "Target group ARN"
  value       = aws_lb_target_group.this.arn
}

output "alb_sg_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "security_group_id" {
  description = "Security group ID for Optimizador Rutas ECS tasks"
  value       = aws_security_group.svc.id
}

output "service_url" {
  description = "Internal service URL (through shared ALB)"
  value       = "Access via shared ALB with path /optimizer/* or /api/v1/optimize/*"
}
