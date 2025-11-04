import os

class Config:
    # Región AWS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

     # Para FIFO
    MESSAGE_GROUP_ID = os.getenv("MESSAGE_GROUP_ID", "grupo1")
    CONTENT_BASED_DEDUP = os.getenv("CONTENT_BASED_DEDUP", "true").lower() == "true"

        # Para LocalStack
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")  # http://localhost:4566

    # Flask
    JSON_SORT_KEYS = False
    
    # Cliente Service Configuration
    CLIENTE_SERVICE_URL = os.getenv("CLIENTE_SERVICE_URL", 
        "http://cliente-service-placeholder.us-east-1.elb.amazonaws.com")
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))