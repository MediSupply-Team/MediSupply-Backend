output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.alb.dns_name
}

output "alb_listener_arn" {
  description = "ALB HTTP Listener ARN"
  value       = aws_lb_listener.http.arn
}

output "ecr_repo_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.bff.repository_url
}

output "http_listener_arn" {
  description = "ARN del listener HTTP del ALB del BFF"
  value       = aws_lb_listener.http.arn
}

output "alb_sg_id" {
  description = "ID del Security Group del ALB del BFF"
  value       = aws_security_group.alb_sg.id
}