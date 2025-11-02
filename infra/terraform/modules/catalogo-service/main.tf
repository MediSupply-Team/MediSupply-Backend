# ============================================================
# CATALOGO SERVICE MODULE
# ============================================================
# Recursos AWS para catalogo-service:
# - ECR Repository
# - ECS Service + Task Definition
# - RDS PostgreSQL Database
# - SQS FIFO Queue (catalogo-events.fifo)
# - ALB Target Group
# - Security Groups
# - CloudWatch Logs
# - Secrets Manager
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

locals {
  is_local = var.environment == "local"
}

# ============================================================
# ECR REPOSITORY
# ============================================================


resource "aws_ecr_repository" "catalogo" {
  name         = "${var.project}-${var.env}-catalogo-service"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_ecr_lifecycle_policy" "catalogo" {
  repository = aws_ecr_repository.catalogo.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "tagged"
        tagPrefixList = ["v"]
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# ============================================================
# RDS POSTGRESQL DATABASE
# ============================================================

resource "random_password" "catalogo_db_password" {
  length           = 24
  special          = true
  override_special = "-_."
}

resource "aws_security_group" "catalogo_postgres_sg" {
  name        = "${var.project}-${var.env}-catalogo-postgres-sg"
  description = "Security group for Catalogo PostgreSQL RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.catalogo_ecs_sg.id]
    description     = "Allow PostgreSQL from Catalogo ECS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-postgres-sg"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_db_subnet_group" "catalogo_postgres" {
  name       = "${var.project}-${var.env}-catalogo-postgres-subnets"
  subnet_ids = var.private_subnets

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-postgres-subnets"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_db_instance" "catalogo_postgres" {
  identifier = "${var.project}-${var.env}-catalogo-db"

  # Engine configuration
  engine         = "postgres"
  engine_version = "15.14" # Usar versión disponible
  instance_class = var.db_instance_class

  # Database configuration
  db_name  = "catalogo_db"
  username = "catalogo_user"
  password = random_password.catalogo_db_password.result

  # Storage configuration
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  # Network & Security
  vpc_security_group_ids = [aws_security_group.catalogo_postgres_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.catalogo_postgres.name
  publicly_accessible    = false

  # Backup configuration
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.catalogo_rds_monitoring.arn

  # Protection
  deletion_protection = false
  skip_final_snapshot = true

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-db"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# S3 BUCKET FOR BULK UPLOADS
# ============================================================

resource "aws_s3_bucket" "catalogo_bulk_uploads" {
  bucket        = "${var.project}-${var.env}-catalogo-bulk-uploads"
  force_destroy = true

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-bulk-uploads"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
    Purpose = "Bulk product uploads"
  }
}

resource "aws_s3_bucket_versioning" "catalogo_bulk_uploads" {
  bucket = aws_s3_bucket.catalogo_bulk_uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "catalogo_bulk_uploads" {
  bucket = aws_s3_bucket.catalogo_bulk_uploads.id

  rule {
    id     = "delete-old-uploads"
    status = "Enabled"

    expiration {
      days = 30 # Eliminar archivos después de 30 días
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "catalogo_bulk_uploads" {
  bucket = aws_s3_bucket.catalogo_bulk_uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "catalogo_bulk_uploads" {
  bucket = aws_s3_bucket.catalogo_bulk_uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================
# SQS FIFO QUEUE
# ============================================================

resource "aws_sqs_queue" "catalogo_events" {
  name                        = "${var.project}-${var.env}-catalogo-events.fifo"
  fifo_queue                  = true
  content_based_deduplication = true

  # Message settings
  message_retention_seconds  = 1209600 # 14 days
  visibility_timeout_seconds = 30
  receive_wait_time_seconds  = 0

  # Dead letter queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.catalogo_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-events"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_sqs_queue" "catalogo_dlq" {
  name                        = "${var.project}-${var.env}-catalogo-dlq.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  message_retention_seconds   = 1209600 # 14 days

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-dlq"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS SECURITY GROUP
# ============================================================

resource "aws_security_group" "catalogo_ecs_sg" {
  name        = "${var.project}-${var.env}-catalogo-ecs-sg"
  description = "Security group for Catalogo ECS service"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow traffic from ALB"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project}-${var.env}-catalogo-ecs-sg"
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# IAM ROLES AND POLICIES
# ============================================================

# RDS Monitoring Role
resource "aws_iam_role" "catalogo_rds_monitoring" {
  name = "${var.project}-${var.env}-catalogo-rds-monitoring"

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
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_iam_role_policy_attachment" "catalogo_rds_monitoring" {
  role       = aws_iam_role.catalogo_rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ECS Task Execution Role
resource "aws_iam_role" "catalogo_ecs_execution_role" {
  name = "${var.project}-${var.env}-catalogo-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# Permiso para acceder al secreto de la base de datos en Secrets Manager
resource "aws_iam_role_policy" "catalogo_ecs_execution_secrets_policy" {
  name = "catalogo-ecs-execution-secrets-policy"
  role = aws_iam_role.catalogo_ecs_execution_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.catalogo_db_credentials.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "catalogo_ecs_execution_role_policy" {
  role       = aws_iam_role.catalogo_ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role
resource "aws_iam_role" "catalogo_ecs_task_role" {
  name = "${var.project}-${var.env}-catalogo-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# Policy para acceso a SQS, S3 y Secrets Manager
resource "aws_iam_role_policy" "catalogo_task_policy" {
  name = "${var.project}-${var.env}-catalogo-task-policy"
  role = aws_iam_role.catalogo_ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.catalogo_events.arn,
          aws_sqs_queue.catalogo_dlq.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.catalogo_bulk_uploads.arn,
          "${aws_s3_bucket.catalogo_bulk_uploads.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.catalogo_db_credentials.arn
      }
    ]
  })
}

# Policy para ECS Execute Command (debugging y acceso directo)
resource "aws_iam_role_policy" "catalogo_ecs_exec_policy" {
  name = "${var.project}-${var.env}-catalogo-ecs-exec-policy"
  role = aws_iam_role.catalogo_ecs_task_role.id

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
      }
    ]
  })
}

# ============================================================
# SECRETS MANAGER
# ============================================================

resource "aws_secretsmanager_secret" "catalogo_db_credentials" {
  #name = "${var.project}-${var.env}-catalogo-db-credentials-v2" # Cambiar nombre
  name                    = "${var.project}-${var.env}-catalogo-db-credentials-v2-cuentasergio" # Cambiar nombre
  recovery_window_in_days = 0

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "catalogo_db_credentials" {
  secret_id = aws_secretsmanager_secret.catalogo_db_credentials.id
  secret_string = jsonencode({
    username     = aws_db_instance.catalogo_postgres.username
    password     = random_password.catalogo_db_password.result
    endpoint     = aws_db_instance.catalogo_postgres.endpoint
    port         = aws_db_instance.catalogo_postgres.port
    dbname       = aws_db_instance.catalogo_postgres.db_name
    database_url = "postgresql+asyncpg://${aws_db_instance.catalogo_postgres.username}:${urlencode(random_password.catalogo_db_password.result)}@${aws_db_instance.catalogo_postgres.address}:${aws_db_instance.catalogo_postgres.port}/${aws_db_instance.catalogo_postgres.db_name}"
  })
}

# ============================================================
# CLOUDWATCH LOGS
# ============================================================

resource "aws_cloudwatch_log_group" "catalogo" {
  count             = local.is_local ? 0 : 1
  name              = "/ecs/${var.project}-${var.env}-catalogo-service"
  retention_in_days = 30

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS TASK DEFINITION
# ============================================================

resource "aws_ecs_task_definition" "catalogo" {
  family                   = "${var.project}-${var.env}-catalogo-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.catalogo_ecs_execution_role.arn
  task_role_arn            = aws_iam_role.catalogo_ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "catalogo-service"
      image = "${aws_ecr_repository.catalogo.repository_url}:latest"

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
          name          = "catalogo-http" # Unique port name for Service Connect
        }
      ]

      environment = [
        {
          name  = "ENV"
          value = var.env
        },
        {
          name  = "ENVIRONMENT"
          value = var.env
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = "us-east-1"
        },
        {
          name  = "SQS_QUEUE_URL"
          value = aws_sqs_queue.catalogo_events.url
        },
        {
          name  = "SQS_REGION"
          value = "us-east-1"
        },
        {
          name  = "S3_BUCKET_NAME"
          value = aws_s3_bucket.catalogo_bulk_uploads.id
        },
        {
          name  = "DB_HOST"
          value = aws_db_instance.catalogo_postgres.address
        },
        {
          name  = "DB_PORT"
          value = tostring(aws_db_instance.catalogo_postgres.port)
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.catalogo_postgres.db_name
        },
        {
          name  = "DB_USER"
          value = aws_db_instance.catalogo_postgres.username
        }
      ]

      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.catalogo_db_credentials.arn}:password::"
        },
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.catalogo_db_credentials.arn}:database_url::"
        }
      ]

      logConfiguration = local.is_local ? null : {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.catalogo[0].name
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ALB TARGET GROUP
# ============================================================

resource "aws_lb_target_group" "catalogo" {
  name        = "${var.project}-${var.env}-catalogo-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ALB LISTENER RULE
# ============================================================

resource "aws_lb_listener_rule" "catalogo" {
  listener_arn = var.alb_listener_arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.catalogo.arn
  }

  condition {
    path_pattern {
      values = ["/catalog/*", "/catalogo/*"]
    }
  }

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS SERVICE
# ============================================================

resource "aws_ecs_service" "catalogo" {
  name            = "${var.project}-${var.env}-catalogo-service"
  cluster         = var.ecs_cluster_name
  task_definition = aws_ecs_task_definition.catalogo.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  enable_execute_command = true # Permite acceso directo al contenedor para debugging

  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.catalogo_ecs_sg.id]
  }

  # Service Connect: exposes catalogo-service for internal service discovery
  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_name

    service {
      client_alias {
        dns_name = "catalogo"
        port     = var.container_port
      }
      port_name = "catalogo-http" # Must match the portMapping name
    }
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.catalogo.arn
    container_name   = "catalogo-service"
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_target_group.catalogo,
    aws_lb_listener_rule.catalogo
  ]

  tags = {
    Service = "catalogo-service"
    Project = var.project
    Env     = var.env
  }
}