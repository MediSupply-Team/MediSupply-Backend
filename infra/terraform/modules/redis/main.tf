# ============================================================
# REDIS (ELASTICACHE) - Para tracking de tareas asíncronas
# ============================================================

# Security Group para Redis
resource "aws_security_group" "redis" {
  name        = "${var.project}-${var.env}-redis-sg"
  description = "Security group for Redis ElastiCache"
  vpc_id      = var.vpc_id

  # Permitir acceso desde subnets privadas (donde están los ECS tasks)
  dynamic "ingress" {
    for_each = length(var.allowed_security_groups) > 0 ? [1] : []
    content {
      description     = "Redis from ECS security groups"
      from_port       = 6379
      to_port         = 6379
      protocol        = "tcp"
      security_groups = var.allowed_security_groups
    }
  }
  
  # Permitir desde VPC CIDR (fallback si no hay security groups específicos)
  ingress {
    description = "Redis from VPC private subnets"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"]  # VPC CIDR
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project}-${var.env}-redis-sg"
    Environment = var.env
    Project     = var.project
  }
}

# Subnet Group para Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project}-${var.env}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project}-${var.env}-redis-subnet-group"
    Environment = var.env
    Project     = var.project
  }
}

# Redis Cluster (modo standalone, single node para desarrollo)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project}-${var.env}-redis"
  engine               = "redis"
  engine_version       = var.redis_engine_version
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  # Maintenance and backup
  maintenance_window      = "sun:05:00-sun:06:00"
  snapshot_window         = "03:00-04:00"
  snapshot_retention_limit = 1

  tags = {
    Name        = "${var.project}-${var.env}-redis"
    Environment = var.env
    Project     = var.project
  }
}

