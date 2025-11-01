output "alb_dns_name"   { value = aws_lb.this.dns_name }
output "alb_arn"        { value = aws_lb.this.arn }
output "target_group_arn" { value = aws_lb_target_group.this.arn }
output "service_name"   { value = aws_ecs_service.this.name }
output "service_arn" {
  description = "ARN del servicio ECS"
  value       = aws_ecs_service.this.id
}
output "log_group_name" { value = aws_cloudwatch_log_group.this.name }
output "alb_sg_id"      { value = aws_security_group.alb.id }
output "security_group_id" { value = aws_security_group.svc.id }