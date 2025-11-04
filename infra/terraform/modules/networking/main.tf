############################
# Networking / VPC + SC NS #
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

# VPC + subredes
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "${var.project}-${var.env}-vpc"
  cidr = "10.20.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnets  = ["10.20.1.0/24", "10.20.2.0/24"]
  private_subnets = ["10.20.11.0/24", "10.20.12.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Project = var.project
    Env     = var.env
  }
}

# Namespace privado para Service Connect / Cloud Map
resource "aws_service_discovery_private_dns_namespace" "svc" {
  name        = "svc.local"
  description = "Service Connect namespace"
  vpc         = module.vpc.vpc_id
  tags = {
    Project = var.project
    Env     = var.env
  }
}

# (Opcional) Endpoint SQS para tráfico privado (ahorra NAT)
resource "aws_vpc_endpoint" "sqs" {
  vpc_id           = module.vpc.vpc_id
  service_name     = "com.amazonaws.${var.aws_region}.sqs"
  vpc_endpoint_type = "Gateway"
  route_table_ids  = module.vpc.private_route_table_ids

  # Simplificado; puedes endurecer a recursos/acciones concretas
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "*"
      Effect    = "Allow"
      Resource  = "*"
      Principal = "*"
    }]
  })

  tags = {
    Project = var.project
    Env     = var.env
  }
}
