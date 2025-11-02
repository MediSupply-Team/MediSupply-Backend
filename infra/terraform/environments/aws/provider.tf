provider "aws" {
  region = var.aws_region
  
  # Tus configuraciones normales de AWS
  # assume_role, profile, etc.
}

terraform {
  backend "s3" {
    # Tu configuración de backend remoto
  }
}