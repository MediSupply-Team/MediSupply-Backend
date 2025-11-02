# Imágenes ECR - Deploy Configuration
# Updated: 25 de octubre de 2025

# Orders Service (existente)
orders_ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-orders-service:latest"
ecr_image        = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-orders-service:latest"

# BFF Venta (actualizado)
bff_venta_ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-bff-venta:latest"

# BFF Cliente
bff_cliente_ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-bff-cliente:latest"

# Catalogo Service (actualizado con Service Connect)
catalogo_ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-catalogo-service:latest"

# Cliente Service
cliente_ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-cliente-service:latest"

# Configuración de puertos
catalogo_container_port = 8000
cliente_container_port  = 8000
bff_app_port           = 8000
bff_cliente_app_port   = 8001

# Environment
project    = "medisupply"
env        = "dev"
aws_region = "us-east-1"

# Catalogo Service URL para BFF (Service Connect DNS)
catalogo_service_url = "http://catalogo:8000"
