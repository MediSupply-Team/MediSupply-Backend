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
db_enable_cloudwatch_logs        = false
db_performance_insights_enabled  = false
db_monitoring_interval           = 0

# ============================================================
# ORDERS SERVICE
# ============================================================
ecr_image = "217466752988.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-orders:latest"
app_port  = 8000

# ============================================================
# CONSUMER (SQS + Worker)
# ============================================================
use_haproxy = true

# ============================================================
# BFF VENTA
# ============================================================
bff_name      = "bff-venta"
bff_app_port  = 8000
bff_repo_name = "medisupply-dev-bff-venta"

bff_env = {
  FLASK_ENV          = "development"
  LOG_LEVEL          = "DEBUG"
  ORDERS_SERVICE_URL = ""
}

# ============================================================
# CATALOGO SERVICE
# ============================================================
catalogo_service_url              = "placeholder-will-be-updated-after-deploy"
catalogo_container_port           = 3000
catalogo_desired_count            = 2
catalogo_cpu                      = "512"
catalogo_memory                   = "1024"
catalogo_db_instance_class        = "db.t4g.micro"
catalogo_db_allocated_storage     = 20
catalogo_db_backup_retention_days = 7

# ============================================================
# BFF CATALOGO
# ============================================================
bff_catalogo_image_tag = "latest"

# ============================================================
# GEMINI AI (para visita-service)
# ============================================================
google_api_key = "AIzaSyDwfzTZLcnN2L379LwrRKDAyfDcsYGVfGc"
gemini_model = "gemini-2.5-flash"

# ============================================================
# TAGS ADICIONALES
# ============================================================
additional_tags = {
  CostCenter  = "Education"
  Owner       = "MISOTeam"
  Environment = "Development"
  Project     = "SchoolProject"
}