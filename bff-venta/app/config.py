import os

class Config:
    # Región y cola (ajústalo a tu caso)
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # p.ej. https://sqs.us-east-1.amazonaws.com/4117.../prueba-cola.fifo

    # Para FIFO
    MESSAGE_GROUP_ID = os.getenv("MESSAGE_GROUP_ID", "grupo1")
    CONTENT_BASED_DEDUP = os.getenv("CONTENT_BASED_DEDUP", "true").lower() == "true"

    # Para LocalStack
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")  # http://localhost:4566

    # Flask
    JSON_SORT_KEYS = False
    
    # ============================================================
    # SERVICE URLS
    # ============================================================
    # Estos valores vienen de Terraform (variables de entorno del contenedor)
    
    # Catálogo Service
    CATALOGO_SERVICE_URL = os.getenv(
        "CATALOGO_SERVICE_URL", 
        "http://catalogo-service-placeholder.us-east-1.elb.amazonaws.com"
    )
    
    # Rutas Service
    RUTAS_SERVICE_URL = os.getenv("RUTAS_SERVICE_URL")
    
    # Optimizador de Rutas Service
    # IMPORTANTE: Debe coincidir con el nombre en Terraform
    OPTIMIZER_SERVICE_URL = os.getenv(
        "OPTIMIZER_SERVICE_URL",
        "http://route-optimizer-service:8000"  # Fallback para desarrollo local
    )
    
    # Orders Service
    ORDERS_SERVICE_URL = os.getenv(
        "ORDERS_SERVICE_URL",
        "http://orders-service:8000"  # Fallback para desarrollo local
    )

    # Auth Service
    AUTH_SERVICE_URL = os.getenv(
        "AUTH_SERVICE_URL",
        "http://auth:8004"  # Fallback para desarrollo local con Service Connect
    )
    
    
    # Timeouts
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))