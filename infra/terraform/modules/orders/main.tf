############################
# Orders service (ECS + SC)#
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

#provider "aws" {
#  region = var.aws_region
#}

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

# Security Group: permite egress; el ingreso para Service Connect
# es tráfico interno entre ENIs. Dejamos opcional una regla
# de ingreso si quieres permitir desde CIDR VPC al puerto app.
resource "aws_security_group" "ecs_sg" {
  name        = "${var.project}-${var.env}-orders-sg"
  description = "SG para ECS tasks de orders"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # (Opcional) Si quieres permitir inbound explicito al puerto app desde VPC:
  ingress {
    description = "Trafico interno VPC al puerto de la app"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"] # ajusta al CIDR de tu VPC
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# Task Definition
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
          name          = "http"   # necesario para Service Connect
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

      # Healthcheck de contenedor (coincide con Dockerfile)
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

# ECS Service con Service Connect habilitado
resource "aws_ecs_service" "orders" {
  name            = "orders-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.orders.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  enable_execute_command  = true

  deployment_controller { type = "ECS" }

  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = false
  }

  # Service Connect: expone 'orders' como DNS interno
  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_name  # p.ej., "svc.local"

    service {
      client_alias {
        dns_name = "orders"
        port     = var.app_port
      }
      port_name = "http"   # debe coincidir con el name del portMapping
    }
  }

  # Sin load_balancer{} (no hay ALB, SC hace routing interno)

  tags = {
    Project = var.project
    Env     = var.env
  }
}
