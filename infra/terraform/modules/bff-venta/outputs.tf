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