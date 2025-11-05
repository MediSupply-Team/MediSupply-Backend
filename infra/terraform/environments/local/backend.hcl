# LocalStack Backend Configuration
bucket         = "terraform-state-local"
key            = "infra.tfstate"
region         = "us-east-1"
endpoint       = "http://localhost:4566"

# LocalStack specific settings
skip_credentials_validation = true
skip_metadata_api_check     = true
skip_requesting_account_id  = true
force_path_style           = true

# NO usar DynamoDB locks en LocalStack (opcional)
# dynamodb_table = "terraform-locks-local"
