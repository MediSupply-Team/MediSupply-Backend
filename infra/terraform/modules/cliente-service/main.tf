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
          var.db_url_secret_arn
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

# Security Group para ECS tasks
resource "aws_security_group" "cliente_ecs_sg" {
  name        = "${local.service_id}-ecs-sg"
  description = "Security group for cliente-service ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"]  # Permitir desde toda la VPC (Service Connect)
    description = "Allow traffic from VPC (Service Connect)"
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
# ALB ELIMINADO - Usando Service Connect para comunicación interna
# ============================================================
# Los siguientes recursos han sido eliminados para reducir costos:
# - aws_security_group.cliente_alb_sg
# - aws_lb.cliente_alb
# - aws_lb_target_group.cliente
# - aws_lb_listener.cliente_http
#
# Ahorro: ~$16-18/mes
# Comunicación: Via Service Connect (cliente.svc.local:8000)

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
          valueFrom = var.db_url_secret_arn
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
  dynamic "service_connect_configuration" {
    for_each = var.service_connect_namespace_name != "" ? [1] : []
    content {
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
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = "cliente-service"
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
