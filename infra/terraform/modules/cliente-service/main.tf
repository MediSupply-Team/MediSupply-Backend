terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  is_local   = var.environment == "local"
  service_id = "${var.project}-${var.env}-cliente-service"
}

# ============================================================
# ECR REPOSITORY
# ============================================================
resource "aws_ecr_repository" "cliente" {
  name                 = "${var.project}-${var.env}-cliente-service"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# ============================================================
# CLOUDWATCH LOGS
# ============================================================
resource "aws_cloudwatch_log_group" "cliente" {
  count             = local.is_local ? 0 : 1
  name              = "/ecs/${local.service_id}"
  retention_in_days = 30

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# ============================================================
# DATABASE RESOURCES
# ============================================================
resource "random_password" "cliente_db_password" {
  length  = 24
  special = true
  override_special = ".-_"
}

resource "aws_db_subnet_group" "cliente_postgres" {
  name       = "${local.service_id}-db-subnet-group"
  subnet_ids = var.private_subnets

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_security_group" "cliente_db_sg" {
  name        = "${local.service_id}-db-sg"
  description = "Security group for cliente-service database"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.cliente_ecs_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_db_instance" "cliente_postgres" {
  identifier     = "${local.service_id}-db"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_encrypted     = true

  db_name  = "cliente_db"
  username = "cliente_user"
  password = random_password.cliente_db_password.result

  vpc_security_group_ids = [aws_security_group.cliente_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.cliente_postgres.name

  backup_retention_period = var.db_backup_retention_days
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"

  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# ============================================================
# SECRETS MANAGER
# ============================================================
resource "aws_secretsmanager_secret" "cliente_db_credentials" {
  #name        = "${local.service_id}-db-credentials"
  name        = "${local.service_id}-db-credentials-cuentasergio"
  description = "Database credentials for cliente-service"

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_secretsmanager_secret_version" "cliente_db_credentials" {
  secret_id = aws_secretsmanager_secret.cliente_db_credentials.id
  secret_string = jsonencode({
    username     = aws_db_instance.cliente_postgres.username
    password     = random_password.cliente_db_password.result
    endpoint     = aws_db_instance.cliente_postgres.endpoint
    port         = aws_db_instance.cliente_postgres.port
    dbname       = aws_db_instance.cliente_postgres.db_name
    database_url = "postgresql+asyncpg://${aws_db_instance.cliente_postgres.username}:${urlencode(random_password.cliente_db_password.result)}@${split(":", aws_db_instance.cliente_postgres.endpoint)[0]}:${aws_db_instance.cliente_postgres.port}/${aws_db_instance.cliente_postgres.db_name}"
  })
}

# ============================================================
# IAM ROLES
# ============================================================
resource "aws_iam_role" "cliente_ecs_execution_role" {
  name = "${local.service_id}-exec-role"

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
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_iam_role_policy_attachment" "cliente_ecs_execution_role_policy" {
  role       = aws_iam_role.cliente_ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "cliente_secrets_policy" {
  name = "${local.service_id}-secrets-policy"
  role = aws_iam_role.cliente_ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.cliente_db_credentials.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role" "cliente_ecs_task_role" {
  name = "${local.service_id}-task-role"

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
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# Policy para ECS Execute Command (debugging y acceso directo)
resource "aws_iam_role_policy" "cliente_ecs_exec_policy" {
  name = "${local.service_id}-ecs-exec-policy"
  role = aws_iam_role.cliente_ecs_task_role.id

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
# SECURITY GROUPS
# ============================================================
resource "aws_security_group" "cliente_alb_sg" {
  name        = "${local.service_id}-alb-sg"
  description = "Security group for cliente-service ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
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
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_security_group" "cliente_ecs_sg" {
  name        = "${local.service_id}-ecs-sg"
  description = "Security group for cliente-service ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.cliente_alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# ============================================================
# APPLICATION LOAD BALANCER
# ============================================================
resource "aws_lb" "cliente_alb" {
  name               = "${var.project}-${var.env}-cliente-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.cliente_alb_sg.id]
  subnets            = var.private_subnets

  enable_deletion_protection = false

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_lb_target_group" "cliente" {
  name        = "${var.project}-${var.env}-cliente-tg"
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
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

resource "aws_lb_listener" "cliente_http" {
  load_balancer_arn = aws_lb.cliente_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.cliente.arn
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# ============================================================
# ECS TASK DEFINITION
# ============================================================
resource "aws_ecs_task_definition" "cliente" {
  family                   = local.service_id
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.cliente_ecs_execution_role.arn
  task_role_arn            = aws_iam_role.cliente_ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "cliente-service"
      image = "${aws_ecr_repository.cliente.repository_url}:latest"

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
          name          = "cliente-http"  # Unique port name for Service Connect
        }
      ]

      essential = true

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
          name  = "SLA_MAX_RESPONSE_MS"
          value = "2000"
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        },
        {
          name  = "DEBUG"
          value = "false"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.cliente_db_credentials.arn}:database_url::"
        }
      ]

      logConfiguration = local.is_local ? null : {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.cliente[0].name
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
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}

# ============================================================
# ECS SERVICE
# ============================================================
resource "aws_ecs_service" "cliente" {
  name            = "${local.service_id}-svc"
  cluster         = var.ecs_cluster_name
  task_definition = aws_ecs_task_definition.cliente.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  
  enable_execute_command = true  # Permite acceso directo al contenedor para debugging

  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.cliente_ecs_sg.id]
  }

  # Service Connect: exposes cliente-service for internal service discovery
  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_name

    service {
      client_alias {
        dns_name = "cliente"
        port     = var.container_port
      }
      port_name = "cliente-http"  # Must match the portMapping name
    }
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.cliente.arn
    container_name   = "cliente-service"
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_listener.cliente_http
  ]

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }
}