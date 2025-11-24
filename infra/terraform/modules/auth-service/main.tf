# ============================================================
# AUTH SERVICE MODULE
# ============================================================
# Recursos AWS para auth-service:
# - ECR Repository
# - ECS Service + Task Definition
# - ALB Target Group + Listener Rule
# - Security Groups
# - CloudWatch Logs
# - Secrets Manager (JWT_SECRET)
# - Usa DB compartida (orders-postgres)

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

resource "aws_ecr_repository" "auth" {
  name         = "${var.project}-${var.env}-auth-service"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_ecr_lifecycle_policy" "auth" {
  repository = aws_ecr_repository.auth.name

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
# SECRETS MANAGER - JWT SECRET
# ============================================================

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project}-${var.env}-auth-jwt-secret"
  recovery_window_in_days = 0

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

# ============================================================
# ECS SECURITY GROUP
# ============================================================

resource "aws_security_group" "auth_ecs_sg" {
  name        = "${var.project}-${var.env}-auth-ecs-sg"
  description = "Security group for Auth ECS service"
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
    Name    = "${var.project}-${var.env}-auth-ecs-sg"
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# IAM ROLES AND POLICIES
# ============================================================

# ECS Task Execution Role (pull images, logs, secrets)
resource "aws_iam_role" "auth_ecs_execution_role" {
  name = "${var.project}-${var.env}-auth-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

resource "aws_iam_role_policy_attachment" "auth_ecs_execution_policy" {
  role       = aws_iam_role.auth_ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Policy para acceder a Secrets Manager
resource "aws_iam_role_policy" "auth_secrets_policy" {
  name = "${var.project}-${var.env}-auth-secrets-policy"
  role = aws_iam_role.auth_ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.shared_db_url_secret_arn,
          var.shared_db_password_secret_arn,
          aws_secretsmanager_secret.jwt_secret.arn
        ]
      }
    ]
  })
}

# ECS Task Role (runtime permissions)
resource "aws_iam_role" "auth_ecs_task_role" {
  name = "${var.project}-${var.env}-auth-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

# Policy para ECS Execute Command (debugging)
resource "aws_iam_role_policy" "auth_ecs_exec_policy" {
  name = "${var.project}-${var.env}-auth-ecs-exec-policy"
  role = aws_iam_role.auth_ecs_task_role.id

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
# CLOUDWATCH LOGS
# ============================================================

resource "aws_cloudwatch_log_group" "auth" {
  count             = local.is_local ? 0 : 1
  name              = "/ecs/${var.project}-${var.env}-auth-service"
  retention_in_days = 30

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS TASK DEFINITION
# ============================================================

resource "aws_ecs_task_definition" "auth" {
  family                   = "${var.project}-${var.env}-auth-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.auth_ecs_execution_role.arn
  task_role_arn            = aws_iam_role.auth_ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "auth-service"
      image = "${aws_ecr_repository.auth.repository_url}:latest"

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
          name          = "auth-http"
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
          name  = "PORT"
          value = tostring(var.container_port)
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.shared_db_url_secret_arn
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = var.shared_db_password_secret_arn
        },
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        }
      ]

      logConfiguration = local.is_local ? null : {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.auth[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/auth/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ALB TARGET GROUP
# ============================================================

resource "aws_lb_target_group" "auth" {
  name        = "${var.project}-${var.env}-auth-tg"
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
    path                = "/auth/health"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ALB LISTENER RULE
# ============================================================

resource "aws_lb_listener_rule" "auth" {
  listener_arn = var.alb_listener_arn
  priority     = 100  # Prioridad alta para auth

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.auth.arn
  }

  condition {
    path_pattern {
      values = ["/auth/*"]
    }
  }

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }
}

# ============================================================
# ECS SERVICE
# ============================================================

resource "aws_ecs_service" "auth" {
  name            = "${var.project}-${var.env}-auth-service"
  cluster         = var.ecs_cluster_name
  task_definition = aws_ecs_task_definition.auth.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  enable_execute_command = true

  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.auth_ecs_sg.id]
  }

  # Service Connect: expone auth-service para descubrimiento interno
  # DESHABILITADO EN LOCAL - LocalStack no lo soporta bien
  dynamic "service_connect_configuration" {
    for_each = (!local.is_local && var.service_connect_namespace_name != "") ? [1] : []
    content {
      enabled   = true
      namespace = var.service_connect_namespace_name

      service {
        client_alias {
          dns_name = "auth"
          port     = var.container_port
        }
        port_name = "auth-http"
      }
    }
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.auth.arn
    container_name   = "auth-service"
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_target_group.auth,
    aws_lb_listener_rule.auth
  ]

  tags = {
    Service = "auth-service"
    Project = var.project
    Env     = var.env
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
