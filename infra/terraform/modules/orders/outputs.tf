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