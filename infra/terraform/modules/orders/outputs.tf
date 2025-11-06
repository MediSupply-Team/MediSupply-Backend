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
# ALB OUTPUTS (NUEVOS)
# ============================================================

output "alb_dns_name" {
  description = "DNS name del ALB interno de Orders"
  value       = aws_lb.orders_alb.dns_name
}

output "alb_arn" {
  description = "ARN del ALB de Orders"
  value       = aws_lb.orders_alb.arn
}

output "alb_zone_id" {
  description = "Zone ID del ALB de Orders (para Route53)"
  value       = aws_lb.orders_alb.zone_id
}

output "alb_security_group_id" {
  description = "ID del Security Group del ALB"
  value       = aws_security_group.orders_alb_sg.id
}

output "target_group_arn" {
  description = "ARN del Target Group de Orders"
  value       = aws_lb_target_group.orders_tg.arn
}

output "target_group_name" {
  description = "Nombre del Target Group de Orders"
  value       = aws_lb_target_group.orders_tg.name
}

output "listener_arn" {
  description = "ARN del Listener HTTP del ALB"
  value       = aws_lb_listener.orders_http.arn
}
