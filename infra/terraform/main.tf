terraform {
  backend "s3" {
    bucket         = "miso-tfstate-838693051133"
    key            = "infra.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "miso-tf-locks"
  }

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

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project
      Env       = var.env
      ManagedBy = "Terraform"
    }
  }
}

# ============================================================
# SHARED INFRASTRUCTURE
# ============================================================

# VPC usando el mÃ³dulo oficial de AWS
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

# Namespace privado para Service Connect / Cloud Map (mismo VPC)
resource "aws_service_discovery_private_dns_namespace" "svc" {
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

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Project = var.project
    Env     = var.env
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

  # Regla 1: Permitir desde Orders Service
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.orders.security_group_id]
    description     = "Allow PostgreSQL from Orders ECS tasks"
  }

  # Regla 2: Permitir desde Rutas Service
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.rutas_service.security_group_id]
    description     = "Allow PostgreSQL from Rutas ECS tasks"
  }

  # Regla 4 (OPCIONAL): Acceso de desarrollo
  # Descomenta y agrega tu IP para acceder desde tu PC/DBeaver
  # ingress {
  #   from_port   = 5432
  #   to_port     = 5432
  #   protocol    = "tcp"
  #   cidr_blocks = ["TU_IP_AQUI/32"]
  #   description = "Development access from my PC"
  # }

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

resource "aws_db_subnet_group" "postgres_private" {
  name       = "${var.project}-${var.env}-orders-postgres-subnets-private"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres-subnets-private"
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
  name = "${var.project}-${var.env}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "${var.project}-${var.env}-rds-monitoring-role"
    Project = var.project
    Env     = var.env
  }
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
  role = aws_iam_role.orders_exec.id # â† Nota: orders_EXEC no orders_task

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
  role = aws_iam_role.orders_task.id # â Task role, NO execution role

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

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project}-${var.env}-orders-postgres"

  # Engine
  engine         = "postgres"
  engine_version = "15.14"

  # Instance
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  # Database
  db_name  = "orders"
  username = "orders_user"
  password = random_password.db_password.result
  port     = 5432

  # Network - CAMBIOS CLAVE AQUÃ
  db_subnet_group_name   = aws_db_subnet_group.postgres_private.name # â† USA PRIVADAS
  vpc_security_group_ids = [aws_security_group.postgres_sg.id]
  publicly_accessible    = false # â† AHORA ES PRIVADO

  # Backup
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Snapshots
  skip_final_snapshot       = true
  final_snapshot_identifier = "${var.project}-${var.env}-orders-postgres-final-snapshot"

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn

  # Performance
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # High Availability
  multi_az = false # Cambiar a true en producciÃ³n

  # Parameter group
  parameter_group_name = aws_db_parameter_group.postgres.name

  # Deletion protection
  deletion_protection = false # Cambiar a true en producciÃ³n

  # Apply changes immediately (solo para dev/test)
  apply_immediately = true

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret" "db_url" {
  name = "medisupply/${var.env}/orders/DB_URL"

  tags = {
    Name    = "medisupply/${var.env}/orders/DB_URL"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "db_url" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+asyncpg://orders_user:${random_password.db_password.result}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "medisupply/${var.env}/orders/DB_PASSWORD"

  tags = {
    Name    = "medisupply/${var.env}/orders/DB_PASSWORD"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# ============================================================
# RUTAS DATABASE SECRETS
# ============================================================

resource "aws_secretsmanager_secret" "rutas_db_url" {
  name                    = "${var.project}/${var.env}/rutas/DB_URL"
  description             = "Database connection URL for Rutas service"
  recovery_window_in_days = 7

  tags = {
    Project = var.project
    Env     = var.env
    Service = "rutas"
  }
}

resource "aws_secretsmanager_secret_version" "rutas_db_url_v" {
  secret_id = aws_secretsmanager_secret.rutas_db_url.id
  # Usar el mismo usuario que orders
  secret_string = "postgresql://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/rutas?sslmode=require"
}

# ============================================================
# SERVICES MODULES
# ============================================================

# Orders Service (ECS + Service Connect)
module "orders" {
  source = "./modules/orders"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  # Imagen ECR completa (repo:tag o repo@sha256:digest) â€” evita :latest
  ecr_image         = var.ecr_image
  app_port          = 3000
  db_url_secret_arn = aws_secretsmanager_secret.db_url.arn

  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Service Connect namespace (reemplaza lo que antes apuntaba a module.networking)
  service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc.name

  # ARNs requeridos que faltaban
  ecs_execution_role_arn = aws_iam_role.orders_exec.arn
  ecs_task_role_arn      = aws_iam_role.orders_task.arn
}

# Consumer (SQS + Worker)
module "consumer" {
  source = "./modules/consumer"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  use_haproxy      = var.use_haproxy
  bff_alb_dns_name = module.bff_venta.alb_dns_name

  # Cluster donde correrÃ¡ el consumer
  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Service Connect namespace - ESTA ES LA LÃNEA NUEVA
  service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc.name
}

# BFF Venta
module "bff_venta" {
  source = "./modules/bff-venta"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  bff_name      = var.bff_name
  bff_app_port  = var.bff_app_port
  bff_repo_name = var.bff_repo_name

  bff_env = merge(
    var.bff_env,
    {
      RUTAS_SERVICE_URL = "http://${module.rutas_service.alb_dns_name}"
    }
  )

  # SQS (consumido por bff_venta)
  sqs_url = module.consumer.sqs_queue_url
  sqs_arn = module.consumer.sqs_queue_arn

  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Catalogo service serÃ¡ accesible por el mismo ALB en /catalog
  catalogo_service_url = var.catalogo_service_url

  # Service Connect namespace
  service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc.name
}

# Cliente Service
module "cliente_service" {
  source = "./modules/cliente-service"

  project = var.project
  env     = var.env

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  ecs_cluster_name = aws_ecs_cluster.orders.name

  # Service Connect namespace for internal service discovery
  service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc.name

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

  # Servicios backend (usando Service Connect DNS)
  catalogo_service_url = "http://${module.bff_venta.alb_dns_name}/catalog"
  cliente_service_url  = "http://cliente:8000"  # Service Connect DNS

  # Service Connect namespace
  service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc.name
}

# ============================================================
# MICROSERVICES MODULES
# ============================================================

# Catalogo Service
module "catalogo_service" {
  source = "./modules/catalogo-service"

  project = var.project
  env     = var.env

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets

  ecs_cluster_name = aws_ecs_cluster.orders.name
  alb_listener_arn = module.bff_venta.alb_listener_arn

  # Service Connect namespace for internal service discovery
  service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc.name

  # Container configuration
  container_port = var.catalogo_container_port
  desired_count  = var.catalogo_desired_count
  cpu            = var.catalogo_cpu
  memory         = var.catalogo_memory

  # Database configuration
  db_instance_class        = var.catalogo_db_instance_class
  db_allocated_storage     = var.catalogo_db_allocated_storage
  db_backup_retention_days = var.catalogo_db_backup_retention_days

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

  service_name = "rutas"

  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets

  ecs_cluster_arn   = aws_ecs_cluster.orders.arn
  db_url_secret_arn = aws_secretsmanager_secret.rutas_db_url.arn

  app_port      = 8000
  image_tag     = "latest"
  desired_count = 1
  cpu           = "512"
  memory        = "1024"

  health_check_path = "/health"
}
