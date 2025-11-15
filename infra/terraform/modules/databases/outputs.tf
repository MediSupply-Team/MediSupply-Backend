output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "db_address" {
  description = "Database address"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "Database username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "db_instance_id" {
  description = "Database instance ID"
  value       = aws_db_instance.postgres.id
}

output "db_url_secret_arn" {
  description = "Database URL secret ARN"
  value       = aws_secretsmanager_secret.db_url.arn
}

output "db_password_secret_arn" {
  description = "Database password secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.postgres_sg.id
}

# Rutas database outputs
output "rutas_db_url_secret_arn" {
  description = "ARN of Rutas DB URL secret"
  value       = aws_secretsmanager_secret.rutas_db_url.arn
}

output "rutas_db_password_secret_arn" {
  description = "ARN of Rutas DB password secret"
  value       = aws_secretsmanager_secret.rutas_db_password.arn
}

output "rutas_db_password" {
  description = "Rutas database password (sensitive)"
  value       = random_password.rutas_db_password.result
  sensitive   = true
}

# Cliente database outputs
output "cliente_db_url_secret_arn" {
  description = "ARN of Cliente DB URL secret"
  value       = aws_secretsmanager_secret.cliente_db_url.arn
}

output "cliente_db_password_secret_arn" {
  description = "ARN of Cliente DB password secret"
  value       = aws_secretsmanager_secret.cliente_db_password.arn
}

output "cliente_db_password" {
  description = "Cliente database password (sensitive)"
  value       = random_password.cliente_db_password.result
  sensitive   = true
}