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
  service_id = "${var.project}-${var.env}-${var.service_name}"
  bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : "${var.project}-${var.env}-visita-uploads"
}

# ============================================================
# S3 BUCKET PARA FOTOS Y VIDEOS
# ============================================================
resource "aws_s3_bucket" "uploads" {
  bucket        = local.bucket_name
  force_destroy = true # Cuidado en producción

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
    Purpose = "visita-uploads"
  }
}

# Bloquear acceso público por defecto
resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versionamiento (opcional pero recomendado)
resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle para borrar archivos antiguos (opcional, ahorra costos)
resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# CORS para permitir uploads desde navegador (si lo necesitas)
resource "aws_s3_bucket_cors_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"] # En producción, restringir a tu dominio
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# ============================================================
# ECR REPOSITORY
# ============================================================
resource "aws_ecr_repository" "this" {
  name                 = "${var.project}-${var.env}-${var.service_name}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# CLOUDWATCH LOGS
# ============================================================
resource "aws_cloudwatch_log_group" "this" {
  count             = local.is_local ? 0 : 1
  name              = "/ecs/${local.service_id}"
  retention_in_days = 7

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# IAM ROLES
# ============================================================
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Execution Role (para pull de ECR y logs)
resource "aws_iam_role" "execution_role" {
  name               = "${local.service_id}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

resource "aws_iam_role_policy_attachment" "execution_role_policy" {
  role       = aws_iam_role.execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Política adicional para leer Secrets Manager
data "aws_iam_policy_document" "secrets_policy" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [var.db_url_secret_arn]
  }
}

resource "aws_iam_policy" "secrets_policy" {
  name   = "${local.service_id}-secrets-policy"
  policy = data.aws_iam_policy_document.secrets_policy.json
}

resource "aws_iam_role_policy_attachment" "secrets_attach" {
  role       = aws_iam_role.execution_role.name
  policy_arn = aws_iam_policy.secrets_policy.arn
}

# Task Role (permisos de la aplicación en runtime)
resource "aws_iam_role" "task_role" {
  name               = "${local.service_id}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# Política para acceso a S3
data "aws_iam_policy_document" "s3_policy" {
  statement {
    sid = "AllowS3Access"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.uploads.arn,
      "${aws_s3_bucket.uploads.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_policy" {
  name   = "${local.service_id}-s3-policy"
  policy = data.aws_iam_policy_document.s3_policy.json
}

resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.s3_policy.arn
}

# ============================================================
# SECURITY GROUPS
# ============================================================
resource "aws_security_group" "svc" {
  name        = "${local.service_id}-svc-sg"
  description = "SG del servicio ${var.service_name}"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Trafico desde ALB compartido (bff-cliente)"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [var.shared_alb_sg_id]
  }

  # Permitir que el servicio pueda conectarse a RDS (egress ya lo permite, pero RDS necesita permitir ingress desde este SG)
  # Esta regla no es necesaria aquí, pero documentamos que el SG necesita ser agregado al RDS
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# TARGET GROUP
# ============================================================
resource "aws_lb_target_group" "this" {
  name        = "${substr(local.service_id, 0, 28)}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = var.health_check_path
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  deregistration_delay = 30

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# LISTENER RULES - Path-based routing en ALB compartido
# ============================================================

# Regla para /api/visitas/* (con wildcard)
resource "aws_lb_listener_rule" "visita_path" {
  listener_arn = var.shared_http_listener_arn
  priority     = 30 # Ajusta según necesites (rutas usa 10, reports usa 20)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  condition {
    path_pattern {
      values = ["/api/visitas/*"]
    }
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# Regla para /api/visitas exacto (sin nada después)
resource "aws_lb_listener_rule" "visita_path_exact" {
  listener_arn = var.shared_http_listener_arn
  priority     = 31

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  condition {
    path_pattern {
      values = ["/api/visitas"]
    }
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# Regla para /api/hallazgos/* (endpoints de descarga/eliminación)
resource "aws_lb_listener_rule" "hallazgos_path" {
  listener_arn = var.shared_http_listener_arn
  priority     = 32

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  condition {
    path_pattern {
      values = ["/api/hallazgos/*"]
    }
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# ECS TASK DEFINITION
# ============================================================
resource "aws_ecs_task_definition" "this" {
  family                   = local.service_id
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution_role.arn
  task_role_arn            = aws_iam_role.task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = var.app_port
          hostPort      = var.app_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENV", value = var.env },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "PORT", value = tostring(var.app_port) },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.uploads.id },
        { name = "UPLOAD_METHOD", value = "s3" } # Para indicar que use S3
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
          awslogs-group         = aws_cloudwatch_log_group.this[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.service_name
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.app_port}${var.health_check_path} || exit 1"]
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
    Service = var.service_name
  }
}

# ============================================================
# ECS SERVICE
# ============================================================
resource "aws_ecs_service" "this" {
  name            = "${local.service_id}-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.svc.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = var.service_name
    container_port   = var.app_port
  }

  # Esperar a que el target group esté creado
  depends_on = [aws_lb_listener_rule.visita_path]

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
