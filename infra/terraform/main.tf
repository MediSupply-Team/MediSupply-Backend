# ============================================================
# TERRAFORM CONFIGURATION
# ============================================================
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# ============================================================
# PROVIDER CONFIGURATION (Dinamico segun environment)
# ============================================================
locals {
  is_local = var.environment == "local"
  mapbox_token_dummy_arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:dummy-mapbox-token"
}

provider "aws" {
  region = var.aws_region

  # Configuracion específica para LocalStack
  access_key                  = local.is_local ? "test" : null
  secret_key                  = local.is_local ? "test" : null
  skip_credentials_validation = local.is_local
  skip_metadata_api_check     = local.is_local
  skip_requesting_account_id  = local.is_local
  s3_use_path_style          = local.is_local

  # Endpoints para LocalStack
  dynamic "endpoints" {
    for_each = local.is_local ? [1] : []
    content {
      apigateway     = "http://localhost:4566"
      cloudwatch     = "http://localhost:4566"
      dynamodb       = "http://localhost:4566"
      ec2            = "http://localhost:4566"
      ecr            = "http://localhost:4566"
      ecs            = "http://localhost:4566"
      elb            = "http://localhost:4566"
      elbv2          = "http://localhost:4566"
      iam            = "http://localhost:4566"
      lambda         = "http://localhost:4566"
      rds            = "http://localhost:4566"
      s3             = "http://localhost:4566"
      secretsmanager = "http://localhost:4566"
      sns            = "http://localhost:4566"
      sqs            = "http://localhost:4566"
      ssm            = "http://localhost:4566"
      sts            = "http://localhost:4566"
    }
  }

  default_tags {
    tags = {
      Project   = var.project
      Env       = var.env
      Environment = var.environment
      ManagedBy = "Terraform"
    }
  }
}

# ============================================================
# SHARED INFRASTRUCTURE
# ============================================================

# VPC usando el modulo oficial de AWS
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "${var.project}-${var.env}-vpc"
  cidr = "10.20.0.0/16"
  azs  = ["us-east-1a", "us-east-1b"]

  public_subnets  = ["10.20.1.0/24", "10.20.2.0/24"]
  private_subnets = ["10.20.11.0/24", "10.20.12.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# Service Discovery - Solo en AWS (LocalStack no lo soporta bien)
resource "aws_service_discovery_private_dns_namespace" "svc" {
  count = local.is_local ? 0 : 1

  name        = "svc.local"
  description = "Service Connect namespace"
  vpc         = module.vpc.vpc_id
  
  tags = {
    Project = var.project
    Env     = var.env
  }
}

# ECS Cluster compartido
resource "aws_ecs_cluster" "orders" {
  name = "orders-cluster"

  # Container Insights solo en AWS
  dynamic "setting" {
    for_each = local.is_local ? [] : [1]
    content {
    name  = "containerInsights"
    value = "enabled"
  }
  }

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECR REPOSITORY FOR ORDERS
# ============================================================

resource "aws_ecr_repository" "orders" {
  name                 = "orders-service"
  image_tag_mutability = "MUTABLE"
  force_delete         = true 

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = "orders"
  }
}

# ============================================================
# DATABASE
# ============================================================

resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "-_."
}

resource "aws_security_group" "postgres_sg" {
  name        = "${var.project}-${var.env}-orders-postgres-sg"
  description = "Security group for Orders PostgreSQL RDS"
  vpc_id      = module.vpc.vpc_id

  # En LocalStack, permitir desde VPC completo
  # En AWS, permitir solo desde security groups específicos
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    cidr_blocks = local.is_local ? ["10.20.0.0/16"] : []
    security_groups = local.is_local ? [] : [
      module.orders.security_group_id,
      module.rutas_service.security_group_id,
      module.report_service.security_group_id,
      module.visita_service.security_group_id
    ]
    description = local.is_local ? "Allow from VPC (LocalStack)" : "Allow from services"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres-sg"
    Project = var.project
    Env     = var.env
  }
}

# Subnet group PRIVADO (para AWS)
resource "aws_db_subnet_group" "postgres_private" {
  count = local.is_local ? 0 : 1

  name       = "${var.project}-${var.env}-orders-postgres-subnets-private"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres-subnets-private"
    Project = var.project
    Env     = var.env
  }
}

# Subnet group PÚBLICO (para LocalStack)
resource "aws_db_subnet_group" "postgres_public" {
  count = local.is_local ? 1 : 0

  name       = "${var.project}-${var.env}-orders-postgres-subnets-public"
  subnet_ids = module.vpc.public_subnets

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres-subnets-public"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${var.project}-${var.env}-postgres-params-new"
  family = "postgres15"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  tags = {
    name    = "${var.project}-${var.env}-postgres-params-new"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# IAM ROLES
# ============================================================

resource "aws_iam_role" "rds_monitoring" {
  count = local.is_local ? 0 : 1

  name = "${var.project}-${var.env}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
    }]
  })

  tags = {
    Name    = "${var.project}-${var.env}-rds-monitoring-role"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count = local.is_local ? 0 : 1

  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Execution role: pull de ECR, logs a CloudWatch, etc.
resource "aws_iam_role" "orders_exec" {
  name = "${var.project}-${var.env}-orders-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# Politica administrada estndar para execution role (ECR + logs, etc.)
resource "aws_iam_role_policy_attachment" "orders_exec_managed" {
  role       = aws_iam_role.orders_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Task role: permisos en tiempo de ejecucion de la app (minimos necesarios)
resource "aws_iam_role" "orders_task" {
  name = "${var.project}-${var.env}-orders-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# Policy inline: lectura del secreto de DB especifico para EXECUTION ROLE
resource "aws_iam_role_policy" "orders_exec_db_secret_read" {
  name = "${var.project}-${var.env}-orders-exec-db-secret-read"
  role = aws_iam_role.orders_exec.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowReadDbSecret",
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        Resource = [
          aws_secretsmanager_secret.db_url.arn,
          aws_secretsmanager_secret.db_password.arn
        ]
      }
    ]
  })
}

# Política para ECS Exec (permite conectarse al container via AWS Systems Manager)
resource "aws_iam_role_policy" "orders_task_ecs_exec" {
  name = "${var.project}-${var.env}-orders-task-ecs-exec"
  role = aws_iam_role.orders_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================
# RDS INSTANCE
# ============================================================

resource "aws_db_instance" "postgres" {
  identifier = "${var.project}-${var.env}-orders-postgres"

  # Engine
  engine         = "postgres"
  engine_version = "15.14"

  # Instance
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = var.db_storage_type
  storage_encrypted = var.db_storage_encrypted

  # Database
  db_name  = "orders"
  username = "orders_user"
  password = random_password.db_password.result
  port     = 5432

  # Network - CONDICIONAL: público para LocalStack, privado para AWS
  db_subnet_group_name = local.is_local ? aws_db_subnet_group.postgres_public[0].name : aws_db_subnet_group.postgres_private[0].name
  vpc_security_group_ids = [aws_security_group.postgres_sg.id]
  publicly_accessible    = local.is_local ? true : false

  # Backup
  backup_retention_period = var.db_backup_retention_period
  backup_window           = var.db_backup_window
  maintenance_window      = var.db_maintenance_window

  # Snapshots
  #skip_final_snapshot       = var.db_skip_final_snapshot
  skip_final_snapshot = true
  final_snapshot_identifier = "${var.project}-${var.env}-orders-postgres-final-snapshot"

  # Monitoring - solo en AWS
  enabled_cloudwatch_logs_exports = local.is_local ? [] : (
    var.db_enable_cloudwatch_logs ? ["postgresql", "upgrade"] : []
  )
  
  monitoring_interval = local.is_local ? 0 : var.db_monitoring_interval
  monitoring_role_arn = local.is_local ? null : (
    var.db_monitoring_interval > 0 ? aws_iam_role.rds_monitoring[0].arn : null
  )

  # Performance Insights - solo en AWS
  performance_insights_enabled = local.is_local ? false : var.db_performance_insights_enabled
  performance_insights_retention_period = local.is_local ? null : (
    var.db_performance_insights_enabled ? 7 : null
  )

  multi_az              = var.db_multi_az
  parameter_group_name = aws_db_parameter_group.postgres.name
  deletion_protection   = false
  apply_immediately = true

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# SECRETS MANAGER
# ============================================================

resource "aws_secretsmanager_secret" "db_url" {
  name = "medisupply/${var.env}/orders/DB_URL"
  recovery_window_in_days = 0

  tags = {
    Name    = "medisupply/${var.env}/orders/DB_URL"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "db_url" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+asyncpg://orders_user:${random_password.db_password.result}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"

  lifecycle {
     ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "medisupply/${var.env}/orders/DB_PASSWORD"
  recovery_window_in_days = 0

  tags = {
    Name    = "medisupply/${var.env}/orders/DB_PASSWORD"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result

  lifecycle {
     ignore_changes = [secret_string]
  }
}

# ============================================================
# RUTAS DATABASE SECRETS
# ============================================================

resource "aws_secretsmanager_secret" "rutas_db_url" {
  name                    = "${var.project}/${var.env}/rutas/DB_URL"
  description             = "Database connection URL for Rutas service"
  recovery_window_in_days = 0

  tags = {
    Project = var.project
    Env     = var.env
    Service = "rutas"
  }
}

resource "aws_secretsmanager_secret_version" "rutas_db_url_v" {
  secret_id = aws_secretsmanager_secret.rutas_db_url.id
  secret_string = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/rutas?sslmode=require"

  lifecycle {
     ignore_changes = [secret_string]
  }
}

# ============================================================
# REPORTS DATABASE SECRETS
# ============================================================

resource "aws_secretsmanager_secret" "reports_db_url" {
  name                    = "${var.project}/${var.env}/reports/DB_URL"
  description             = "Database connection URL for reports service"
  recovery_window_in_days = 0

  #recovery_window_in_days = 0

  tags = {
    Project = var.project
    Env     = var.env
    Service = "reports"
  }
}

resource "aws_secretsmanager_secret_version" "reports_db_url_v" {

  secret_id = aws_secretsmanager_secret.reports_db_url.id
  # Usar el mismo usuario que orders
  secret_string = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/reports?sslmode=require"
}

# ============================================================
# VISITA DATABASE SECRETS
# ============================================================

resource "aws_secretsmanager_secret" "visita_db_url" {
  name                    = "${var.project}/${var.env}/visita/DB_URL"
  description             = "Database connection URL for Visita service"
  recovery_window_in_days = 0

  tags = {
    Project = var.project
    Env     = var.env
    Service = "visita"
  }
}

resource "aws_secretsmanager_secret_version" "visita_db_url_v" {
  secret_id = aws_secretsmanager_secret.visita_db_url.id
  # Usar el mismo usuario y base de datos que orders (compartida)
  secret_string = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/visitas?sslmode=require"
  
  lifecycle {
     ignore_changes = [secret_string]
  }
}

#data "aws_secretsmanager_secret" "mapbox_token" {
#  name = "/${var.project}/${var.env}/mapbox-token"
#}

#data "aws_secretsmanager_secret_version" "mapbox_token" {
#  secret_id = data.aws_secretsmanager_secret.mapbox_token.id
#}

# ============================================================
# SERVICES MODULES
# ============================================================

# Orders Service (ECS + Service Connect)
module "orders" {
  source = "./modules/orders"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region
  environment = var.environment  # ← AGREGADO

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  # Imagen ECR completa (repo:tag o repo@sha256:digest) â€” evita :latest
  ecr_image         = "${aws_ecr_repository.orders.repository_url}:latest"
  app_port          = 3000
  db_url_secret_arn = aws_secretsmanager_secret.db_url.arn

  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # ARNs requeridos que faltaban
  ecs_execution_role_arn = aws_iam_role.orders_exec.arn
  ecs_task_role_arn      = aws_iam_role.orders_task.arn
  
  # Service Connect namespace
  service_connect_namespace_name = local.is_local ? "" : aws_service_discovery_private_dns_namespace.svc[0].name
}

# Consumer (SQS + Worker)
module "consumer" {
  source = "./modules/consumer"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region
  environment = var.environment  # ← AGREGADO

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  use_haproxy      = var.use_haproxy
  bff_alb_dns_name = module.bff_venta.alb_dns_name

  # Cluster donde correrÃ¡ el consumer
  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Usar Service Connect en lugar de ALB
  orders_service_url = module.orders.service_connect_url

  # Service Connect namespace - solo en AWS
  service_connect_namespace_name = local.is_local ? "" : aws_service_discovery_private_dns_namespace.svc[0].name
  ecr_force_delete = true
}

# BFF Venta
module "bff_venta" {
  source = "./modules/bff-venta"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region
  environment = var.environment

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  bff_name      = "bff-venta"
  bff_app_port  = 8000
  bff_repo_name = "${var.project}-${var.env}-bff-venta"

  bff_env = {
    FLASK_ENV = var.env
    LOG_LEVEL = "DEBUG"
  }

  # SQS (consumido por bff_venta)
  sqs_url = module.consumer.sqs_queue_url
  sqs_arn = module.consumer.sqs_queue_arn

  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Todos los servicios usan el mismo ALB
  # El ALB tiene reglas de path-based routing configuradas
  catalogo_service_url  = "http://${module.bff_venta.alb_dns_name}/catalog"
  optimizer_service_url = "http://${module.bff_venta.alb_dns_name}"
  rutas_service_url     = "http://${module.bff_venta.alb_dns_name}"
  # Usar Service Connect para Orders (elimina ALB interno)
  orders_service_url = module.orders.service_connect_url
  
  # Service Connect namespace - solo en AWS
  service_connect_namespace_name = local.is_local ? "" : aws_service_discovery_private_dns_namespace.svc[0].name
}

# Cliente Service
module "cliente_service" {
  source = "./modules/cliente-service"

  project = var.project
  env     = var.env
  environment = var.environment  # ← AGREGADO

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  ecs_cluster_name = aws_ecs_cluster.orders.name

  # Service Connect namespace - solo en AWS
  service_connect_namespace_name = local.is_local ? "" : aws_service_discovery_private_dns_namespace.svc[0].name

  # Container configuration
  container_port = 8000
  desired_count  = 1
  cpu            = "512"
  memory         = "1024"

  # Database configuration
  db_instance_class        = "db.t3.micro"
  db_allocated_storage     = 20
  db_backup_retention_days = 7
}

# BFF Cliente
module "bff_cliente" {
  source = "./modules/bff-cliente"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region
  environment = var.environment  # ← AGREGADO

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  bff_name      = "bff-cliente"
  bff_app_port  = 8001
  bff_repo_name = "${var.project}-${var.env}-bff-cliente"

  bff_env = {
    FLASK_ENV = var.env
  }

  # ECS Cluster
  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # SQS (para producir mensajes)
  sqs_url = module.consumer.sqs_queue_url
  sqs_arn = module.consumer.sqs_queue_arn

  # Servicios backend - Usar Service Connect para servicios internos
  catalogo_service_url = "http://${module.bff_venta.alb_dns_name}/catalog"
  cliente_service_url  = local.is_local ? "http://cliente:8000" : module.cliente_service.service_connect_url

  # Service Connect namespace - solo en AWS
  service_connect_namespace_name = local.is_local ? "" : aws_service_discovery_private_dns_namespace.svc[0].name
}

# ============================================================
# MICROSERVICES MODULES
# ============================================================

# Redis (ElastiCache) - Para tracking de tareas asíncronas
module "redis" {
  source = "./modules/redis"
  
  count = local.is_local ? 0 : 1  # Solo en AWS, no en LocalStack
  
  project = var.project
  env     = var.env
  
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnets
  
  # Permitir acceso desde subnets privadas (donde están los ECS tasks)
  allowed_security_groups = []  # Se configurará después con reglas adicionales
  
  redis_engine_version = var.redis_engine_version
  redis_node_type      = var.redis_node_type
}

# Catalogo Service
module "catalogo_service" {
  source = "./modules/catalogo-service"

  project = var.project
  env     = var.env
  environment = var.environment  # ← AGREGADO

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets

  ecs_cluster_name = aws_ecs_cluster.orders.name
  alb_listener_arn = module.bff_venta.alb_listener_arn

  # Service Connect namespace - solo en AWS
  service_connect_namespace_name = local.is_local ? "" : aws_service_discovery_private_dns_namespace.svc[0].name

  # Container configuration
  container_port = var.catalogo_container_port
  desired_count  = var.catalogo_desired_count
  cpu            = var.catalogo_cpu
  memory         = var.catalogo_memory

  # Database configuration
  db_instance_class        = var.catalogo_db_instance_class
  db_allocated_storage     = var.catalogo_db_allocated_storage
  db_backup_retention_days = var.catalogo_db_backup_retention_days

  # Redis configuration
  redis_url = local.is_local ? "redis://redis:6379/1" : module.redis[0].redis_url

  # Additional tags
  additional_tags = var.additional_tags
}

# ============================================================
# BFF-CATALOGO MODULE
# ============================================================
# ============================================================
# BFF-CATALOGO MODULE - DISABLED (using integrated catalogo in bff-venta)
# ============================================================
# module "bff_catalogo" {
#   source = "./modules/bff-catalogo"

#   project    = var.project
#   env        = var.env
#   aws_region = var.aws_region

#   vpc_id          = module.vpc.vpc_id
#   private_subnets = module.vpc.private_subnets
#   public_subnets  = module.vpc.public_subnets

#   ecs_cluster_name = aws_ecs_cluster.orders.name

#   # BFF Configuration
#   bff_port       = 3000
#   bff_cpu        = "256"
#   bff_memory     = "512"
#   desired_count  = 1
#   image_tag      = var.bff_catalogo_image_tag

#   # URL interna del catalogo-service a travÃ©s del ALB
#   catalogo_service_url = "http://${module.bff_venta.alb_dns_name}/catalog"
# }

# Rutas Service
module "rutas_service" {
  source = "./modules/rutas_service"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region
  environment = var.environment  # ← AGREGADO

  service_name = "rutas"

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  ecs_cluster_arn   = aws_ecs_cluster.orders.arn
  db_url_secret_arn = aws_secretsmanager_secret.rutas_db_url.arn

  app_port      = 8000
  image_tag     = "latest"
  desired_count = 1
  cpu           = "256"
  memory        = "512"

  health_check_path = "/health"

  shared_http_listener_arn = module.bff_venta.alb_listener_arn
  shared_alb_sg_id         = module.bff_venta.alb_sg_id
}

# Reports Service
module "report_service" {
  source = "./modules/report_service"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region

  service_name = "reports"

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  ecs_cluster_arn   = aws_ecs_cluster.orders.arn
  db_url_secret_arn = aws_secretsmanager_secret.reports_db_url.arn

  app_port      = 8000
  image_tag     = "latest"
  desired_count = 1
  cpu           = "256"
  memory        = "512"

  health_check_path = "/health"

  shared_http_listener_arn = module.bff_venta.alb_listener_arn
  shared_alb_sg_id         = module.bff_venta.alb_sg_id
  
  # S3 bucket para exportar reportes (usa el mismo bucket de visita)
  s3_bucket_arn  = module.visita_service.s3_bucket_arn
  s3_bucket_name = module.visita_service.s3_bucket_name
  
  depends_on = [module.visita_service]
}

# Visita Service
module "visita_service" {
  source = "./modules/visita_service"

  project     = var.project
  env         = var.env
  environment = var.environment
  aws_region  = var.aws_region

  service_name = "visita"

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  ecs_cluster_arn   = aws_ecs_cluster.orders.arn
  db_url_secret_arn = aws_secretsmanager_secret.visita_db_url.arn

  app_port      = 8003
  image_tag     = "latest"
  desired_count = 1
  cpu           = "256"
  memory        = "512"

  health_check_path = "/health"

  # Usar ALB de BFF Cliente
  shared_http_listener_arn = module.bff_cliente.alb_listener_arn
  shared_alb_sg_id         = module.bff_cliente.alb_sg_id

  # S3 bucket para uploads (fotos/videos)
  s3_bucket_name = "${var.project}-${var.env}-visita-uploads"
}

# ============================================================
# OPTIMIZADOR-RUTAS-SERVICE
# ============================================================

module "optimizador_rutas" {
  source = "./modules/optimizador_rutas"

  project     = var.project
  env         = var.env
  environment = var.environment
  aws_region  = var.aws_region

  service_name = "optimizador-rutas"

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Secret ARN - real Mapbox token from AWS Secrets Manager
  mapbox_token_secret_arn = "arn:aws:secretsmanager:us-east-1:217466752988:secret:/medisupply/dev/mapbox-token-sshGcj"

  shared_http_listener_arn = module.bff_venta.alb_listener_arn
  shared_alb_sg_id         = module.bff_venta.alb_sg_id

  osrm_url         = var.osrm_url
  ruta_service_url = "http://${module.bff_venta.alb_dns_name}"

  app_port      = 8000
  image_tag     = var.optimizador_rutas_image_tag
  desired_count = var.env == "prod" ? 2 : 1
  cpu           = var.env == "prod" ? "512" : "256"
  memory        = var.env == "prod" ? "1024" : "512"

  health_check_path = "/optimizer/health"
}
