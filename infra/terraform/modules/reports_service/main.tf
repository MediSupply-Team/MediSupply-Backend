terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.env}-report"
  tags = {
    Project = var.project
    Env     = var.env
    Service = "report"
  }
}

data "aws_region" "current" {}

# =========================
# Logs
# =========================
resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30
  tags              = local.tags
}

# =========================
# Security Groups
# =========================
resource "aws_security_group" "svc" {
  name        = "${local.name_prefix}-svc-sg"
  description = "SG for ${local.name_prefix} tasks"
  vpc_id      = var.vpc_id
  tags        = local.tags

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "ALB SG for ${local.name_prefix}"
  vpc_id      = var.vpc_id
  tags        = local.tags

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group_rule" "alb_to_svc" {
  type                     = "ingress"
  from_port                = var.app_port
  to_port                  = var.app_port
  protocol                 = "tcp"
  security_group_id        = aws_security_group.svc.id
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow ALB to reach report tasks"
}

# =========================
# ALB + Target Group
# =========================
resource "aws_lb_target_group" "this" {
  name        = "${local.name_prefix}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    matcher             = "200-399"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 5
  }

  tags = local.tags
}

resource "aws_lb" "this" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnets
  idle_timeout       = 60
  enable_deletion_protection = false
  tags               = local.tags
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# =========================
# IAM (task/exec) + permisos (logs, SSM, secrets)
# =========================
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "execution_role" {
  name               = "${local.name_prefix}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = local.tags
}

resource "aws_iam_role" "task_role" {
  name               = "${local.name_prefix}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = local.tags
}

resource "aws_iam_role_policy" "exec_logs_ssm" {
  name = "${local.name_prefix}-exec-logs"
  role = aws_iam_role.execution_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect = "Allow",
        Action = ["logs:CreateLogStream","logs:PutLogEvents","logs:DescribeLogGroups","logs:DescribeLogStreams"],
        Resource = "*" },
      { Effect = "Allow",
        Action = ["ssmmessages:CreateControlChannel","ssmmessages:CreateDataChannel","ssmmessages:OpenControlChannel","ssmmessages:OpenDataChannel"],
        Resource = "*" }
    ]
  })
}

resource "aws_iam_role_policy" "task_secrets" {
  name = "${local.name_prefix}-secrets"
  role = aws_iam_role.task_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect = "Allow",
        Action = ["secretsmanager:GetSecretValue"],
        Resource = "arn:aws:secretsmanager:*:*:secret:${var.db_url_secret_name}*" }
    ]
  })
}

# =========================
# Task Definition
# =========================
resource "aws_ecs_task_definition" "this" {
  family                   = local.name_prefix
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution_role.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "report",
      image     = var.report_ecr_image,
      essential = true,
      portMappings = [{
        containerPort = var.app_port,
        hostPort      = var.app_port,
        protocol      = "tcp"
      }],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name,
          awslogs-region        = data.aws_region.current.name,
          awslogs-stream-prefix = "ecs"
        }
      },
      environment = [
        # si necesitas inyectar ENV adicionales, agrégalos aquí
      ],
      secrets = [
        { name = "DB_URL", valueFrom = "arn:aws:secretsmanager:${data.aws_region.current.name}:*:secret:${var.db_url_secret_name}" }
      ]
    }
  ])

  tags = local.tags
}

# =========================
# ECS Service
# =========================
resource "aws_ecs_service" "this" {
  name                   = "${local.name_prefix}-svc"
  cluster                = var.cluster_arn
  launch_type            = "FARGATE"
  desired_count          = var.desired_count
  task_definition        = aws_ecs_task_definition.this.arn
  enable_execute_command = true

  network_configuration {
    assign_public_ip = false
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.svc.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "report"
    container_port   = var.app_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]
  tags       = local.tags
}