output "ecr_repository_url" {
  description = "URL del repositorio ECR"
  value       = aws_ecr_repository.this.repository_url
}

output "ecr_repository_arn" {
  description = "ARN del repositorio ECR"
  value       = aws_ecr_repository.this.arn
}

output "service_name" {
  description = "Nombre del servicio ECS"
  value       = aws_ecs_service.this.name
}

output "service_id" {
  description = "ID completo del servicio"
  value       = local.service_id
}

output "security_group_id" {
  description = "ID del security group del servicio"
  value       = aws_security_group.svc.id
}

output "target_group_arn" {
  description = "ARN del Target Group"
  value       = aws_lb_target_group.this.arn
}

output "s3_bucket_name" {
  description = "Nombre del bucket S3 para uploads"
  value       = aws_s3_bucket.uploads.id
}

output "s3_bucket_arn" {
  description = "ARN del bucket S3 para uploads"
  value       = aws_s3_bucket.uploads.arn
}

output "task_role_arn" {
  description = "ARN del Task Role (con permisos S3)"
  value       = aws_iam_role.task_role.arn
}

output "execution_role_arn" {
  description = "ARN del Execution Role"
  value       = aws_iam_role.execution_role.arn
}
