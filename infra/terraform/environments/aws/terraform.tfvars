# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================
environment = "aws"
project     = "medisupply"
env         = "dev"
aws_region  = "us-east-1"

# ============================================================
# MAIN DATABASE (Orders & Rutas)
# ============================================================
db_instance_class                = "db.t4g.micro"
db_allocated_storage             = 20
db_max_allocated_storage         = 100
db_publicly_accessible           = true
db_multi_az                      = false
db_backup_retention_period       = 7
db_enable_cloudwatch_logs        = true
db_performance_insights_enabled  = true
db_monitoring_interval           = 60

# ============================================================
# ORDERS SERVICE
# ============================================================
ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/miso-prod-orders:latest"
app_port  = 8000

# ============================================================
# CONSUMER (SQS + Worker)
# ============================================================
use_haproxy = true

# ============================================================
# BFF VENTA
# ============================================================
bff_name      = "bff-venta"
bff_app_port  = 8080
bff_repo_name = "miso-prod-bff-venta"

bff_env = {
  FLASK_ENV         = "production"
  LOG_LEVEL         = "INFO"
  ORDERS_SERVICE_URL = "" # Se configura dinámicamente con el ALB
}

# ============================================================
# CATALOGO SERVICE
# ============================================================
catalogo_service_url         = "placeholder-will-be-updated-after-deploy"
catalogo_container_port      = 3000
catalogo_desired_count       = 2
catalogo_cpu                 = "512"
catalogo_memory              = "1024"
catalogo_db_instance_class   = "db.t4g.micro"
catalogo_db_allocated_storage = 20
catalogo_db_backup_retention_days = 7

# ============================================================
# BFF CATALOGO (si lo usas)
# ============================================================
bff_catalogo_image_tag = "v1.0.0"

# ============================================================
# TAGS ADICIONALES
# ============================================================
additional_tags = {
  CostCenter  = "Education"
  Owner       = "MISOTeam"
  Environment = "Production"
  Project     = "SchoolProject"
}