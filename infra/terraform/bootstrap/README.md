# 🔐 Bootstrap - Infraestructura Base

## ¿Qué es esto?

Este directorio contiene la **infraestructura base** que debe configurarse **UNA SOLA VEZ** antes de poder ejecutar los pipelines de CI/CD automatizados.

Incluye:
- 🔑 **OIDC Provider** de GitHub para autenticación sin credenciales
- 👤 **IAM Role** para GitHub Actions con permisos completos
- 🗄️ **S3 Bucket** para almacenar el estado de Terraform
- 🔒 **DynamoDB Table** para el locking del estado de Terraform

## ⚠️ Importante

Esta infraestructura:
- ✅ Se aplica **MANUALMENTE** una sola vez
- ❌ **NO** se destruye con el pipeline `destroy.yml`
- 🔧 Solo se modifica cuando sea necesario (cambios en permisos, etc.)
- 🛡️ Tiene `prevent_destroy = true` en recursos críticos

## 🚀 Primera Configuración (Una sola vez)

### Prerrequisitos

1. **AWS CLI** configurado con credenciales de administrador:
   ```bash
   aws configure
   ```

2. **Terraform** instalado (v1.9.0+):
   ```bash
   terraform --version
   ```

### Paso 1: Inicializar Terraform

```bash
cd infra/terraform/bootstrap
terraform init
```

### Paso 2: Revisar el Plan

```bash
terraform plan
```

Verifica que se van a crear:
- S3 bucket: `miso-tfstate-217466752988`
- DynamoDB table: `miso-tf-locks`
- OIDC Provider: `token.actions.githubusercontent.com`
- IAM Role: `github-actions-deploy`
- 5 políticas IAM

### Paso 3: Aplicar la Infraestructura

```bash
terraform apply
```

Escribe `yes` cuando te lo pida.

### Paso 4: Verificar

```bash
# Ver outputs
terraform output

# Verificar el rol
aws iam get-role --role-name github-actions-deploy

# Verificar el bucket
aws s3 ls s3://miso-tfstate-217466752988/
```

## 🎯 Después del Bootstrap

Una vez aplicado el bootstrap:

1. ✅ Los pipelines de GitHub Actions (`CD.yml`, `destroy.yml`) funcionarán automáticamente
2. ✅ GitHub Actions asumirá el rol `github-actions-deploy` sin necesidad de credenciales
3. ✅ Terraform podrá crear/destruir toda la infraestructura de aplicación
4. ✅ El estado de Terraform se guardará en S3 con locking en DynamoDB

## 🔄 ¿Cuándo volver a aplicar?

Solo necesitas volver a este directorio si:

- 📝 Cambias permisos del rol de GitHub Actions
- 🔧 Modificas la configuración del OIDC
- 🔐 Actualizas políticas de seguridad
- 🐛 Necesitas recrear el rol por algún problema

## 🗑️ ¿Cómo destruir? (Caso extremo)

⚠️ **CUIDADO**: Esto eliminará la capacidad de GitHub Actions para desplegar.

```bash
cd infra/terraform/bootstrap

# Eliminar protección prevent_destroy primero
terraform state rm aws_iam_role.github_actions
terraform state rm aws_iam_openid_connect_provider.github
terraform state rm aws_s3_bucket.terraform_state
terraform state rm aws_dynamodb_table.terraform_locks

# Destruir
terraform destroy
```

## 📋 Permisos otorgados a GitHub Actions

El rol `github-actions-deploy` tiene permisos para:

### ✅ Servicios con acceso completo:
- EC2 (VPC, subnets, security groups)
- ECS (clusters, services, tasks)
- ECR (repositorios de imágenes)
- RDS (bases de datos)
- ElastiCache (Redis)
- ELB (load balancers)
- Secrets Manager
- CloudWatch Logs & Metrics
- SQS & SNS
- S3 (excepto bucket de state)
- Service Discovery
- Application Auto Scaling

### ✅ IAM (limitado):
- ✅ Crear/modificar roles que empiezan con `medisupply-*`
- ✅ Crear/modificar políticas de la aplicación
- ✅ PassRole para ECS y RDS
- ❌ **NO PUEDE** modificar el rol `github-actions-deploy` (sí mismo)
- ❌ **NO PUEDE** modificar el OIDC Provider

## 🔐 Seguridad

### Trust Policy (¿Quién puede usar este rol?)

El rol **SOLO** puede ser asumido por:
- Repositorio: `leonelfonsec/MediSupply-Backend`
- A través de: GitHub Actions OIDC
- Sin credenciales estáticas

### Separación de responsabilidades

```
┌─────────────────────────────────────────────┐
│          BOOTSTRAP (Manual)                 │
│  - OIDC Provider                           │
│  - github-actions-deploy role              │
│  - Permisos IAM                            │
│  - S3 State bucket                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│    APLICACIÓN (GitHub Actions)              │
│  - VPC & Networking                        │
│  - ECS Clusters & Services                 │
│  - RDS Databases                           │
│  - Roles de aplicación (medisupply-*)      │
└─────────────────────────────────────────────┘
```

## 🆘 Troubleshooting

### Error: "Backend initialization required"

```bash
cd infra/terraform/bootstrap
terraform init -reconfigure
```

### Error: "Bucket already exists"

Si el bucket S3 ya existe, importa el estado:

```bash
terraform import aws_s3_bucket.terraform_state miso-tfstate-217466752988
```

### Error: "Table already exists"

```bash
terraform import aws_dynamodb_table.terraform_locks miso-tf-locks
```

### Error: "OIDC Provider already exists"

```bash
terraform import aws_iam_openid_connect_provider.github arn:aws:iam::217466752988:oidc-provider/token.actions.githubusercontent.com
```

### Error: "Role already exists"

```bash
terraform import aws_iam_role.github_actions github-actions-deploy
```

## 📞 Contacto

Si tienes problemas con el bootstrap, contacta al equipo de DevOps.
