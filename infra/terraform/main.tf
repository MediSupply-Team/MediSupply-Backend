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

# VPC usando el módulo oficial de AWS
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

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "TEMP: Allow PostgreSQL from anywhere"
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

resource "aws_db_subnet_group" "postgres_public" {
  name       = "${var.project}-${var.env}-orders-postgres-subnets-public"
  subnet_ids = module.vpc.public_subnets

  tags = {
    Name    = "${var.project}-${var.env}-orders-postgres-subnets-public"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_db_parameter_group" "postgres" {
  family = "postgres15"
  name   = "${var.project}-${var.env}-orders-postgres-params"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
  parameter {
    name  = "log_statement"
    value = "all"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Project = var.project
    Env     = var.env
  }
}

resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project}-${var.env}-orders-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })

  tags = {
    Project = var.project
    Env     = var.env
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project}-${var.env}-orders-postgres"

  engine         = "postgres"
  engine_version = "15.14"
  instance_class = "db.t4g.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "orders"
  username = "orders_user"
  password = random_password.db_password.result
  port     = 5432

  publicly_accessible  = true
  apply_immediately    = true
  db_subnet_group_name = aws_db_subnet_group.postgres_public.name

  vpc_security_group_ids = [aws_security_group.postgres_sg.id]

  multi_az                = false
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  copy_tags_to_snapshot   = true

  skip_final_snapshot      = true
  deletion_protection      = false
  delete_automated_backups = true

  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn

  auto_minor_version_upgrade = true
  parameter_group_name       = aws_db_parameter_group.postgres.name

  tags = {
    Project    = var.project
    Env        = var.env
    ManagedBy  = "Terraform"
    Purpose    = "School Project - Production Simulation"
    CostCenter = "Education"
  }
}

resource "aws_secretsmanager_secret" "db_url" {
  name                    = "${var.project}/${var.env}/orders/DB_URL"
  description             = "Database connection URL for Orders service"
  recovery_window_in_days = 7

  tags = {
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "db_url_v" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+asyncpg://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project}/${var.env}/orders/DB_PASSWORD"
  description             = "PostgreSQL master password"
  recovery_window_in_days = 7

  tags = {
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "db_password_v" {
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

# Orders Service
module "orders" {
  source = "./modules/orders"

  project    = var.project
  env        = var.env
  aws_region = var.aws_region

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  ecr_image         = var.ecr_image
  app_port          = var.app_port
  db_url_secret_arn = aws_secretsmanager_secret.db_url.arn

  ecs_cluster_arn = aws_ecs_cluster.orders.arn # ← AGREGAR
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

  ecs_cluster_arn = aws_ecs_cluster.orders.arn # ← AGREGAR
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
      RUTAS_SERVICE_URL = "http://${module.rutas_service.alb_dns_name}" # ← ESTO
    }
  )

  sqs_url = module.consumer.sqs_queue_url
  sqs_arn = module.consumer.sqs_queue_arn # ← AGREGAR ESTA LÍNEA

  ecs_cluster_arn = aws_ecs_cluster.orders.arn

  # Catalogo service will be accessible through the same ALB on /catalog path  
  catalogo_service_url = var.catalogo_service_url
}

# Cliente Service
module "cliente_service" {
  source = "./modules/cliente-service"

  project = var.project
  env     = var.env

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  ecs_cluster_name = aws_ecs_cluster.orders.name

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

  ecs_cluster_arn = aws_ecs_cluster.orders.arn
  
  # Cliente service will be accessible through the internal ALB
  cliente_service_url = module.cliente_service.alb_url
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

#   # URL interna del catalogo-service a través del ALB
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