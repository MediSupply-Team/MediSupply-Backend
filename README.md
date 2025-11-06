# MediSupply-Backend

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <your-repo>
cd <project-folder>

# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```
## 📁 Estructura del Proyecto
```
MediSupply-Backend/
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       ├── outputs.tf
│       └── modules/
│           ├── networking/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── database/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── orders/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── bff-venta/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           └── consumer/
│               ├── main.tf
│               ├── variables.tf
│               └── outputs.tf
├── orders-service/
├── bff-venta/
├── consumer-lb/
├── catalogo-service/
├── cliente-service/
├── ruta-service/
└── README.md
```
\```

---

## 🏗️ Estructura de Infraestructura (Terraform)
```
infra/terraform/
│
├── 📄 Archivos Principales
│   ├── main.tf                 # Backend S3, Provider, VPC, RDS, Llamadas a módulos
│   ├── variables.tf            # Variables globales del proyecto
│   ├── terraform.tfvars        # Valores de configuración
│   └── outputs.tf              # Outputs agregados
│
└── 📦 modules/                 # Módulos por servicio
    │
    ├── networking/             # [Platform Team]
    │   ├── main.tf            # VPC, Subnets, NAT Gateway, ECS Cluster
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── database/               # [Platform Team]
    │   ├── main.tf            # RDS PostgreSQL, Secrets Manager
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── orders/                 # [Backend Team]
    │   ├── main.tf            # ECS Task Definition, Service, IAM
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── bff-venta/              # [Frontend Team]
    │   ├── main.tf            # ALB, ECS Service, SQS Producer
    │   ├── variables.tf
    │   └── outputs.tf
    │
    └── consumer/               # [Backend Team]
        ├── main.tf            # SQS Queues, HAProxy, Worker
        ├── variables.tf
        └── outputs.tf
```
---
# 🚀 Terraform - AWS y LocalStack

> **Nota:** Todos los comandos se ejecutan desde: `<Path de tu proyecto>/infra/terraform`

---

## ☁️ AWS

### Inicializar (solo primera vez o después de cambios en backend)
```powershell
terraform init -backend-config="environments/aws/backend.hcl" -migrate-state
```

### Validar configuración
```powershell
terraform validate
```

### Ver cambios sin aplicar
```powershell
terraform plan -var-file="environments/aws/terraform.tfvars"
```

### Desplegar 
```powershell
terraform apply -var-file="environments/aws/terraform.tfvars" -auto-approve
```

### Destruir
```powershell
terraform destroy -var-file="environments/aws/terraform.tfvars" -auto-approve
```

---

## 🐳 LocalStack

### 1. Iniciar LocalStack
> Ejecutar desde: `<Path de tu proyecto>/infra`
```powershell
docker-compose up -d localstack
```

### 2. Verificar que LocalStack está corriendo
```powershell
docker ps | Select-String localstack
```

### 3. Inicializar Terraform
> Volver a: `<Path de tu proyecto>/infra/terraform`
```powershell
terraform init -backend-config=environments/local/backend.hcl
```

### 4. Ver cambios sin aplicar
```powershell
terraform plan -var-file="environments/local/terraform.tfvars"
```

### 5. Desplegar
```powershell
terraform apply -var-file="environments/local/terraform.tfvars" -auto-approve
```

### 6. Destruir
```powershell
terraform destroy -var-file="environments/local/terraform.tfvars" -auto-approve
```

### 7. Detener LocalStack
> Ejecutar desde: `<Path de tu proyecto>/infra`
```powershell
docker-compose down
```

---

## 🎯 Desplegar Módulos Específicos

### AWS
```powershell
terraform apply -var-file="environments/aws/terraform.tfvars" -target=module.bff_venta -auto-approve
```

### LocalStack
```powershell
terraform apply -var-file="environments/local/terraform.tfvars" -target=module.catalogo_service -auto-approve
```

---

## 📦 Módulos Disponibles

- `module.bff_venta` - BFF de ventas
- `module.bff_cliente` - BFF de clientes  
- `module.catalogo_service` - Servicio de catálogo
- `module.cliente_service` - Servicio de clientes
- `module.orders` - Servicio de órdenes
- `module.consumer` - Consumer de eventos
- `module.rutas_service` - Servicio de rutas
- `module.report_service` - Servicio de reportes

---

## 🔍 Comandos Útiles

### Ver recursos en el state
```powershell
terraform state list
```

### Ver detalles de un recurso
```powershell
terraform state show module.bff_venta.aws_ecs_service.svc
```

### Ver outputs
```powershell
terraform output
```

### Verificar estado del backend (AWS)
```powershell
aws s3 ls s3://miso-tfstate-217466752988/
```