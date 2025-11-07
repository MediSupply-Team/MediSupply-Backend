# ECR para haproxy y worker
resource "aws_ecr_repository" "haproxy" {
  name = "${var.project}-${var.env}-haproxy-consumer"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
  tags = { Project = var.project, Env = var.env }
}

resource "aws_ecr_repository" "worker" {
  name = "${var.project}-${var.env}-orders-consumer"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
  tags = { Project = var.project, Env = var.env }
  force_delete = var.ecr_force_delete
}

# SQS + DLQ
resource "aws_sqs_queue" "dlq" {
  name                        = "${var.project}-${var.env}-orders-events-dlq.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  message_retention_seconds   = 1209600
  receive_wait_time_seconds   = 20
  tags                        = { Project = var.project, Env = var.env, Component = "haproxy-consumer" }
}

resource "aws_sqs_queue" "fifo" {
  name                        = "${var.project}-${var.env}-orders-events.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 60
  message_retention_seconds   = 1209600
  receive_wait_time_seconds   = 20
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn,
    maxReceiveCount     = 5
  })
  tags = { Project = var.project, Env = var.env, Component = "haproxy-consumer" }
}

# IAM
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_role" {
  name               = "${var.project}-${var.env}-haproxy-consumer-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = { Project = var.project, Env = var.env }
}

data "aws_iam_policy_document" "sqs_consumer" {
  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility", "sqs:GetQueueAttributes", "sqs:GetQueueUrl"]
    resources = [aws_sqs_queue.fifo.arn, aws_sqs_queue.dlq.arn]
  }
}

resource "aws_iam_policy" "sqs_consumer" {
  name   = "${var.project}-${var.env}-sqs-consumer-policy"
  policy = data.aws_iam_policy_document.sqs_consumer.json
}

resource "aws_iam_role_policy_attachment" "attach_sqs" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.sqs_consumer.arn
}

resource "aws_iam_role" "exec_role" {
  name               = "${var.project}-${var.env}-haproxy-consumer-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = { Project = var.project, Env = var.env }
}

resource "aws_iam_role_policy_attachment" "exec_attach" {
  role       = aws_iam_role.exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Logs - Condicional para LocalStack
resource "aws_cloudwatch_log_group" "lg" {
  count             = local.is_local ? 0 : 1
  name              = "/ecs/${var.project}-${var.env}-haproxy-consumer"
  retention_in_days = 14
  tags              = { Project = var.project, Env = var.env }
}

# SG
resource "aws_security_group" "sg" {
  name        = "${var.project}-${var.env}-haproxy-consumer-sg"
  description = "SG for HAProxy front + egress"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all egress"
  }

  tags = { Project = var.project, Env = var.env }
}

locals {
  is_local = var.environment == "local"
  
  consumer_lb_target = var.use_haproxy ? "http://127.0.0.1/orders" : "http://${var.bff_alb_dns_name}/orders"
  # URL para conectarse al servicio orders via Service Connect o URL personalizada
  orders_url = var.orders_service_url
}

# TaskDefinition: Condicional según use_haproxy
resource "aws_ecs_task_definition" "td" {
  family                   = "${var.project}-${var.env}-haproxy-consumer"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = aws_iam_role.task_role.arn
  execution_role_arn       = aws_iam_role.exec_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "worker",
      image     = "${aws_ecr_repository.worker.repository_url}:latest",
      essential = true,
      logConfiguration = local.is_local ? null : {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.lg[0].name,
          awslogs-region        = var.aws_region,
          awslogs-stream-prefix = "worker"
        }
      },
      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.fifo.url },
        # Usar Service Connect URL
        { name = "LB_TARGET_URL", value = local.orders_url },
        { name = "TARGET_URL", value = local.orders_url },
        { name = "SQS_WAIT", value = "20" },
        { name = "SQS_BATCH", value = "10" },
        { name = "SQS_VISIBILITY", value = "60" },
        { name = "HTTP_TIMEOUT", value = "30" }
      ]
    }
  ])

  tags = { Project = var.project, Env = var.env }
}

# Service con Service Connect habilitado para poder resolver 'orders'
resource "aws_ecs_service" "svc" {
  name            = "${var.project}-${var.env}-haproxy-consumer-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.td.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.sg.id]
    assign_public_ip = false
  }

  # CRITICO: Habilitar Service Connect para que pueda resolver 'orders'
  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_name
    # Consumer solo es cliente, no expone servicios
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [
    aws_sqs_queue.fifo,
    aws_cloudwatch_log_group.lg
  ]

  tags = { Project = var.project, Env = var.env }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
