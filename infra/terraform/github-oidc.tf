# Proveedor OIDC de GitHub
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# Rol para GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:*:*"
          }
        }
      }
    ]
  })

  tags = {
    Project = var.project
    Env     = var.env
  }
  lifecycle { prevent_destroy = true }
  max_session_duration = 43200  # 12 horas
}

# Políticas
resource "aws_iam_role_policy_attachment" "github_actions_ecr" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
}

resource "aws_iam_role_policy_attachment" "github_actions_ecs" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_iam_policy" "github_actions_passrole" {
  name = "github-actions-ecs-passrole"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = "arn:aws:iam::217466752988:role/medisupply-*"
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:RegisterTaskDefinition",
          "ecs:DescribeTaskDefinition",
          "ecs:UpdateService",
          "ecs:DescribeServices"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_passrole" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_passrole.arn
}

# Política para Terraform State (S3 + DynamoDB)
resource "aws_iam_policy" "github_actions_terraform_state" {
  name = "github-actions-terraform-state"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::miso-tfstate-217466752988",
          "arn:aws:s3:::miso-tfstate-217466752988/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:UpdateItem",
          "dynamodb:DescribeTable"
        ]
        Resource = "arn:aws:dynamodb:us-east-1:217466752988:table/miso-tf-locks"
      }
    ]
  })
  lifecycle { prevent_destroy = true }
}

resource "aws_iam_role_policy_attachment" "github_actions_terraform_state" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_terraform_state.arn
  lifecycle { prevent_destroy = true }
}

# Política para que Terraform pueda gestionar toda la infraestructura
resource "aws_iam_policy" "github_actions_terraform_full" {
  name = "github-actions-terraform-full"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "rds:*",
          "elasticache:*",
          "elasticloadbalancing:*",
          "iam:*",
          "secretsmanager:*",
          "logs:*",
          "cloudwatch:*",
          "sqs:*",
          "sns:*",
          "s3:*",
          "servicediscovery:*",
          "application-autoscaling:*"
        ]
        Resource = "*"
      }
    ]
  })
  lifecycle { prevent_destroy = true }
}

resource "aws_iam_role_policy_attachment" "github_actions_terraform_full" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_terraform_full.arn
  lifecycle { prevent_destroy = true }
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}

# Política mínima con permisos de destroy que te faltan
resource "aws_iam_policy" "github_actions_destroy_extras" {
  name = "github-actions-destroy-extras"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # IAM (lecturas durante destroy)
      {
        Effect = "Allow",
        Action = [
          "iam:ListPolicyVersions",
          "iam:ListInstanceProfilesForRole"
        ],
        Resource = "*"
      },
      # ECS (espera y borrado de servicios)
      {
        Effect = "Allow",
        Action = [
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:ListServices",
          "ecs:UpdateService",
          "ecs:DeleteService"
        ],
        Resource = "*"
      },
      # ECR (borrar repos y lifecycle)
      {
        Effect = "Allow",
        Action = [
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:BatchDeleteImage",
          "ecr:DeleteLifecyclePolicy",
          "ecr:DeleteRepository",
          "ecr:ListTagsForResource",
          "ecr:GetLifecyclePolicy",
        ],
        Resource = "*"
      },
      # RDS (espera de borrado)
      {
        Effect = "Allow",
        Action = [
          "rds:DescribeDBInstances"
        ],
        Resource = "*"
      }
    ]
  })
}

# Adjuntar al rol de GitHub Actions
resource "aws_iam_role_policy_attachment" "github_actions_destroy_extras" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_destroy_extras.arn
}