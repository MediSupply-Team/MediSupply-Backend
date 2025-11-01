locals {
  is_local = var.environment == "local"
  bff_id = "${var.project}-${var.env}-${var.bff_name}"

  # ARN derivado desde la URL SQS
  sqs_arn = replace(var.sqs_url, "https://sqs.${var.aws_region}.amazonaws.com/", "arn:aws:sqs:${var.aws_region}:")
  
  # 🔧 SOLUCIÓN: Calcular la URL del catálogo usando el DNS del ALB de este mismo módulo
  # Si el placeholder está presente, usar el DNS real del ALB
  computed_catalogo_url = var.catalogo_service_url == "placeholder-will-be-updated-after-deploy" ? "http://${aws_lb.alb.dns_name}/catalog" : var.catalogo_service_url
}

resource "aws_ecr_repository" "bff" {
  name         = var.bff_repo_name
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

resource "aws_cloudwatch_log_group" "bff" {
  count             = local.is_local ? 0 : 1
  name              = "/ecs/${local.bff_id}"
  retention_in_days = 14

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "exec_role" {
  name               = "${local.bff_id}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

resource "aws_iam_role_policy_attachment" "exec_attach" {
  role       = aws_iam_role.exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "app_role" {
  name               = "${local.bff_id}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

data "aws_iam_policy_document" "sqs_producer" {
  statement {
    effect = "Allow"

    actions = [
      "sqs:SendMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
    ]

    resources = [var.sqs_arn]
  }
}

resource "aws_iam_policy" "sqs_producer" {
  name   = "${local.bff_id}-sqs-producer"
  policy = data.aws_iam_policy_document.sqs_producer.json
}

resource "aws_iam_role_policy_attachment" "app_attach_sqs" {
  role       = aws_iam_role.app_role.name
  policy_arn = aws_iam_policy.sqs_producer.arn
}

# Policy para ECS Exec (SSM Session Manager)
resource "aws_iam_role_policy" "bff_venta_ecs_exec" {
  name = "${local.bff_id}-ecs-exec"
  role = aws_iam_role.app_role.id

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
          "logs:DescribeLogGroups",
          "logs:CreateLogStream",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_security_group" "alb_sg" {
  name        = "${local.bff_id}-alb-sg"
  description = "ALB SG for ${var.bff_name}"
  vpc_id      = var.vpc_id

  ingress {
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

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

resource "aws_security_group" "svc_sg" {
  name        = "${local.bff_id}-svc-sg"
  description = "Service SG for ${var.bff_name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.bff_app_port
    to_port         = var.bff_app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

resource "aws_lb" "alb" {
  name               = "${local.bff_id}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnets
  idle_timeout       = 60

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}

resource "aws_lb_target_group" "tg" {
  name                 = "${local.bff_id}-tg"
  port                 = var.bff_app_port
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = 30

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}


resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

resource "aws_ecs_task_definition" "td" {
  family                   = local.bff_id
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.exec_role.arn
  task_role_arn            = aws_iam_role.app_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = var.bff_name
      image     = "${aws_ecr_repository.bff.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = var.bff_app_port
          hostPort      = var.bff_app_port
          protocol      = "tcp"
          name          = "bff-venta-http"  # Required for Service Connect
        }
      ]

      logConfiguration = local.is_local ? null : {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.bff[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.bff_name
        }
      }

      environment = concat(
        [for k, v in var.bff_env : { name = k, value = v }],
        [
          { name = "SQS_QUEUE_URL", value = var.sqs_url },
          # 🔧 CAMBIO: Usar la URL computada en lugar de la variable directamente
          { name = "CATALOGO_SERVICE_URL", value = local.computed_catalogo_url }
        ]
      )

      # 👇 health del contenedor (ajustado)
      healthCheck = {
        command     = ["CMD-SHELL", "curl -sf http://localhost:${var.bff_app_port}/health || exit 1"]
        interval    = 15
        timeout     = 5
        retries     = 5
        startPeriod = 90
      }
    }
  ])

  # 🔧 AGREGADO: Lifecycle para crear una nueva versión en cada apply
  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}


resource "aws_ecs_service" "svc" {
  name            = "${local.bff_id}-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.td.arn
  desired_count   = 2 # ⬅️ subimos a 2 para rollouts suaves
  launch_type     = "FARGATE"
  enable_execute_command = true
  health_check_grace_period_seconds = 120 # ⬅️ la "gracia" vive en el service

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.svc_sg.id]
    assign_public_ip = false
  }

  # Service Connect: enable as client only to discover other services
  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_name
    # No 'service' block needed - this service is client-only
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tg.arn
    container_name   = var.bff_name
    container_port   = var.bff_app_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]

  tags = {
    Project   = var.project
    Env       = var.env
    Component = var.bff_name
  }
}
