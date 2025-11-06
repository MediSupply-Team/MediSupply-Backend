############################
# Orders service (ECS + ALB)#
############################

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

# Log group - Solo crear en AWS, no en LocalStack
resource "aws_cloudwatch_log_group" "orders" {
  count = local.is_local ? 0 : 1

  name              = "/medisupply/${var.env}/orders"
  retention_in_days = 14
  tags = {
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# SECURITY GROUPS
# ============================================================

# Security Group para ECS Tasks
resource "aws_security_group" "ecs_sg" {
  name        = "${var.project}-${var.env}-orders-ecs-sg"
  description = "SG para ECS tasks de orders"
  vpc_id      = var.vpc_id

  # Permitir tráfico desde el ALB
  ingress {
    description     = "Trafico desde ALB"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.orders_alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name    = "${var.project}-${var.env}-orders-ecs-sg"
    Project = var.project
    Env     = var.env
  }
}

# Security Group para ALB
resource "aws_security_group" "orders_alb_sg" {
  name        = "${var.project}-${var.env}-orders-alb-sg"
  description = "Security group for Orders ALB"
  vpc_id      = var.vpc_id

  # Permitir HTTP desde toda la VPC (para BFF-Venta y otros servicios)
  ingress {
    description = "HTTP from VPC"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"]  # CIDR de tu VPC
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project}-${var.env}-orders-alb-sg"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# APPLICATION LOAD BALANCER (INTERNAL)
# ============================================================

resource "aws_lb" "orders_alb" {
  name               = "${var.project}-${var.env}-orders-alb"
  internal           = true  # ALB INTERNO (no accesible desde internet)
  load_balancer_type = "application"
  security_groups    = [aws_security_group.orders_alb_sg.id]
  subnets            = var.private_subnets

  enable_deletion_protection = false
  enable_http2              = true

  tags = {
    Name    = "${var.project}-${var.env}-orders-alb"
    Project = var.project
    Env     = var.env
  }
}

# Target Group
resource "aws_lb_target_group" "orders_tg" {
  name                 = "${var.project}-${var.env}-orders-tg"
  port                 = var.app_port
  protocol             = "HTTP"
  target_type          = "ip"  # Importante para Fargate
  vpc_id               = var.vpc_id
  deregistration_delay = 30

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name    = "${var.project}-${var.env}-orders-tg"
    Project = var.project
    Env     = var.env
  }
}

# Listener
resource "aws_lb_listener" "orders_http" {
  load_balancer_arn = aws_lb.orders_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.orders_tg.arn
  }

  tags = {
    Name    = "${var.project}-${var.env}-orders-listener"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS TASK DEFINITION
# ============================================================

resource "aws_ecs_task_definition" "orders" {
  family                   = "orders"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "orders"
      image     = var.ecr_image
      essential = true

      portMappings = [
        {
          containerPort = var.app_port
          protocol      = "tcp"
          name          = "http"
        }
      ]

      environment = [
        { name = "PORT",                   value = tostring(var.app_port) },
        { name = "ENVIRONMENT",            value = var.env },
        { name = "LOG_LEVEL",              value = "info" }
      ]

      secrets = [
        {
          name      = "DB_URL"
          valueFrom = var.db_url_secret_arn
        }
      ]

      # logConfiguration - Condicional: solo en AWS, no en LocalStack
      logConfiguration = local.is_local ? null : {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.orders[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "orders"
        }
      }

      # Healthcheck de contenedor
      healthCheck = {
        command     = ["CMD-SHELL","python -c \"import sys,urllib.request;r=urllib.request.urlopen('http://127.0.0.1:${var.app_port}/health',timeout=3);sys.exit(0 if r.status==200 else 1)\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 40
      }
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS SERVICE CON ALB
# ============================================================

resource "aws_ecs_service" "orders" {
  name            = "orders-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.orders.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  enable_execute_command = true

  deployment_controller { type = "ECS" }

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = false
  }

  # ============================================================
  # LOAD BALANCER (reemplaza Service Connect)
  # ============================================================
  load_balancer {
    target_group_arn = aws_lb_target_group.orders_tg.arn
    container_name   = "orders"
    container_port   = var.app_port
  }

  # Grace period para health checks del ALB
  health_check_grace_period_seconds = 60

  # Depende del listener para evitar errores de creación
  depends_on = [
    aws_lb_listener.orders_http
  ]

  tags = {
    Project = var.project
    Env     = var.env
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes = [task_definition]
  }
}
