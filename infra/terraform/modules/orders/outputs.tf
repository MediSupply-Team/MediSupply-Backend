# ============================================================
# ORDERS MODULE - OUTPUTS
# ============================================================

# ============================================================
# ECS SERVICE OUTPUTS (EXISTENTES)
# ============================================================

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.orders.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.orders.id
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.orders.arn
}

output "log_group_name" {
  description = "CloudWatch log group name (empty in LocalStack)"
  value       = length(aws_cloudwatch_log_group.orders) > 0 ? aws_cloudwatch_log_group.orders[0].name : ""
}

output "security_group_id" {
  description = "Security group ID for Orders ECS tasks"
  value       = aws_security_group.ecs_sg.id
}

# ============================================================
# SERVICE CONNECT OUTPUTS (Reemplaza ALB outputs)
# ============================================================

output "service_connect_dns" {
  description = "Service Connect DNS name for internal communication"
  value       = "orders.svc.local"
}

output "service_connect_port" {
  description = "Service Connect port"
  value       = var.app_port
}

output "service_connect_url" {
  description = "Full Service Connect URL for internal communication"
  value       = "http://orders.svc.local:${var.app_port}"
}

# ============================================================
# DEPRECATED OUTPUTS - ALB eliminado para reducir costos
# ============================================================
# Los siguientes outputs han sido eliminados porque el ALB fue removido:
# - alb_dns_name
# - alb_arn
# - alb_zone_id
# - alb_security_group_id
# - target_group_arn
# - target_group_name
# - listener_arn
#
# Usar service_connect_url en su lugar
