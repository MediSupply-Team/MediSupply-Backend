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
    
    # Catalogo Service Configuration
    CATALOGO_SERVICE_URL = os.getenv("CATALOGO_SERVICE_URL", 
        "http://catalogo-service-placeholder.us-east-1.elb.amazonaws.com")
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))