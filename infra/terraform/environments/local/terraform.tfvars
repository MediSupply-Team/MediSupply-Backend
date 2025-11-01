# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================
environment = "local"
project     = "miso"
env         = "dev"
aws_region  = "us-east-1"

# ============================================================
# MAIN DATABASE (Orders & Rutas)
# ============================================================
db_instance_class                = "db.t3.micro"
db_allocated_storage             = 10
db_max_allocated_storage         = 20
db_publicly_accessible           = true
db_multi_az                      = false
db_backup_retention_period       = 0
db_enable_cloudwatch_logs        = false
db_performance_insights_enabled  = false
db_monitoring_interval           = 0

# ============================================================
# ORDERS SERVICE
# ============================================================
ecr_image = "838693051133.dkr.ecr.us-east-1.amazonaws.com/miso-dev-orders:latest"
app_port  = 8000

# ============================================================
# CONSUMER (SQS + Worker)
# ============================================================
use_haproxy = false

# ============================================================
# BFF VENTA
# ============================================================
bff_name      = "bff-venta"
bff_app_port  = 8080
bff_repo_name = "miso-dev-bff-venta"

bff_env = {
  FLASK_ENV         = "development"
  LOG_LEVEL         = "DEBUG"
  ORDERS_SERVICE_URL = "http://localhost:8000"  # Para local
}

# ============================================================
# CATALOGO SERVICE
# ============================================================
catalogo_service_url         = "placeholder-will-be-updated-after-deploy"
catalogo_desired_count       = 1
catalogo_cpu                 = "256"
catalogo_memory              = "512"
catalogo_db_instance_class   = "db.t3.micro"
catalogo_db_allocated_storage = 20
catalogo_db_backup_retention_days = 0

# ============================================================
# BFF CATALOGO (si lo usas)
# ============================================================
bff_catalogo_image_tag = "latest"

# ============================================================
# TAGS ADICIONALES
# ============================================================
additional_tags = {
  CostCenter  = "Development"
  Owner       = "DevTeam"
  Environment = "LocalStack"
}