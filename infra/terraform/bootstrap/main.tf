# ============================================================================
# BOOTSTRAP - Infraestructura Base (Aplicar MANUALMENTE UNA VEZ)
# ============================================================================
# Este módulo configura:
# 1. OIDC Provider de GitHub
# 2. Rol de GitHub Actions con permisos completos
# 3. Backend de Terraform (S3 + DynamoDB)
#
# IMPORTANTE: 
# - Aplicar ANTES del primer deploy automatizado
# - NO destruir con el pipeline de destroy
# - Solo modificar manualmente cuando sea necesario
# ============================================================================

terraform {
  required_version = ">= 1.9.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend local para bootstrap - cambiará a S3 después del primer apply
  backend "s3" {
    bucket         = "miso-tfstate-217466752988"
    key            = "bootstrap/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "miso-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = "bootstrap"
      ManagedBy   = "Terraform"
      Layer       = "Bootstrap"
    }
  }
}

# ============================================================================
# Variables
# ============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "medisupply"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
  default     = "217466752988"
}

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
  default     = "leonelfonsec"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "MediSupply-Backend"
}

# ============================================================================
# S3 Bucket para Terraform State (si no existe)
# ============================================================================

resource "aws_s3_bucket" "terraform_state" {
  bucket = "miso-tfstate-${var.aws_account_id}"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform State Bucket"
    Description = "Stores Terraform state for ${var.project}"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# DynamoDB Table para Terraform Locks (si no existe)
# ============================================================================

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "miso-tf-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform Lock Table"
    Description = "DynamoDB table for Terraform state locking"
  }
}

# ============================================================================
# GitHub OIDC Provider
# ============================================================================

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # Thumbprints actualizados para GitHub Actions (2024)
  thumbprint_list = [
    "1b511abead59c6ce207077c0bf0e0043b1382612",
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "GitHub Actions OIDC Provider"
  }
}

# ============================================================================
# GitHub Actions Role con permisos COMPLETOS
# ============================================================================

resource "aws_iam_role" "github_actions" {
  name               = "github-actions-deploy"
  max_session_duration = 43200  # 12 horas

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
            # ⚠️ NOTA: Esto es permisivo (permite cualquier repo)
            # Para producción, considera restringir a: "repo:${var.github_org}/${var.github_repo}:*"
            "token.actions.githubusercontent.com:sub" = "repo:*:*"
          }
        }
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "GitHub Actions Deployment Role"
  }
}

# ============================================================================
# Políticas IAM - Permisos Amplios para GitHub Actions
# ============================================================================

# Política 1: ECR Full Access (incluyendo CreateRepository)
resource "aws_iam_policy" "github_actions_ecr_full" {
  name = "github-actions-ecr-full"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:*"
        ]
        Resource = "*"
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_ecr_full" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_ecr_full.arn

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_ecs" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"

  lifecycle {
    prevent_destroy = true
  }
}

# Política 2: IAM PassRole para ECS tasks
resource "aws_iam_policy" "github_actions_passrole" {
  name = "github-actions-ecs-passrole"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = "arn:aws:iam::${var.aws_account_id}:role/${var.project}-*"
        Condition = {
          StringEquals = {
            "iam:PassedToService" = [
              "ecs-tasks.amazonaws.com",
              "rds.amazonaws.com"
            ]
          }
        }
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_passrole" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_passrole.arn

  lifecycle {
    prevent_destroy = true
  }
}

# Política 3: Terraform State Access (S3 + DynamoDB)
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
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
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
        Resource = aws_dynamodb_table.terraform_locks.arn
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_terraform_state" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_terraform_state.arn

  lifecycle {
    prevent_destroy = true
  }
}

# Política 4: Permisos Completos de Infraestructura
resource "aws_iam_policy" "github_actions_infrastructure" {
  name = "github-actions-infrastructure-full"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # IAM - Puede gestionar roles/políticas de la aplicación (NO del bootstrap)
      {
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:UpdateRole",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:ListRoleTags",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:ListAttachedRolePolicies",
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:ListPolicyVersions",
          "iam:CreatePolicyVersion",
          "iam:DeletePolicyVersion",
          "iam:SetDefaultPolicyVersion",
          "iam:TagPolicy",
          "iam:UntagPolicy",
          "iam:ListInstanceProfilesForRole"
        ]
        Resource = [
          "arn:aws:iam::${var.aws_account_id}:role/${var.project}-*",
          "arn:aws:iam::${var.aws_account_id}:policy/${var.project}-*",
          "arn:aws:iam::${var.aws_account_id}:policy/github-actions-*"
        ]
        Condition = {
          StringNotEquals = {
            "iam:ResourceTag/Layer" = "Bootstrap"
          }
        }
      },
      # EC2 y Networking
      {
        Effect = "Allow"
        Action = [
          "ec2:*"
        ]
        Resource = "*"
      },
      # RDS
      {
        Effect = "Allow"
        Action = [
          "rds:*"
        ]
        Resource = "*"
      },
      # ElastiCache
      {
        Effect = "Allow"
        Action = [
          "elasticache:*"
        ]
        Resource = "*"
      },
      # ELB
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:*"
        ]
        Resource = "*"
      },
      # Secrets Manager
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:*"
        ]
        Resource = "*"
      },
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:*"
        ]
        Resource = "*"
      },
      # CloudWatch Metrics
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:*"
        ]
        Resource = "*"
      },
      # SQS
      {
        Effect = "Allow"
        Action = [
          "sqs:*"
        ]
        Resource = "*"
      },
      # SNS
      {
        Effect = "Allow"
        Action = [
          "sns:*"
        ]
        Resource = "*"
      },
      # S3 (excepto el bucket de state)
      {
        Effect = "Allow"
        Action = [
          "s3:*"
        ]
        Resource = "*"
        Condition = {
          StringNotLike = {
            "s3:ResourceAccount" = "*tfstate*"
          }
        }
      },
      # Service Discovery
      {
        Effect = "Allow"
        Action = [
          "servicediscovery:*"
        ]
        Resource = "*"
      },
      # Application Auto Scaling
      {
        Effect = "Allow"
        Action = [
          "application-autoscaling:*"
        ]
        Resource = "*"
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_infrastructure" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_infrastructure.arn

  lifecycle {
    prevent_destroy = true
  }
}

# Política 5: Permisos adicionales para Destroy
resource "aws_iam_policy" "github_actions_destroy" {
  name = "github-actions-destroy-operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ECR - Limpiar imágenes antes de borrar repositorios
      {
        Effect = "Allow"
        Action = [
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:BatchDeleteImage",
          "ecr:DeleteLifecyclePolicy",
          "ecr:DeleteRepository",
          "ecr:GetLifecyclePolicy",
          "ecr:ListTagsForResource"
        ]
        Resource = "*"
      },
      # ECS - Eliminar servicios antes de clusters
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:ListServices",
          "ecs:UpdateService",
          "ecs:DeleteService"
        ]
        Resource = "*"
      },
      # RDS - Esperar durante destroy
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "*"
      }
    ]
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_destroy" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_destroy.arn

  lifecycle {
    prevent_destroy = true
  }
}

# ============================================================================
# Outputs
# ============================================================================

output "github_actions_role_arn" {
  description = "ARN del rol de GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}

output "oidc_provider_arn" {
  description = "ARN del OIDC Provider de GitHub"
  value       = aws_iam_openid_connect_provider.github.arn
}

output "terraform_state_bucket" {
  description = "Nombre del bucket S3 para Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "terraform_lock_table" {
  description = "Nombre de la tabla DynamoDB para locks"
  value       = aws_dynamodb_table.terraform_locks.id
}
