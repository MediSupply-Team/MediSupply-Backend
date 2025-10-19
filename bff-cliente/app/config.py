import os

class Config:
    # Región AWS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # Flask
    JSON_SORT_KEYS = False
    
    # Cliente Service Configuration
    CLIENTE_SERVICE_URL = os.getenv("CLIENTE_SERVICE_URL", 
        "http://cliente-service-placeholder.us-east-1.elb.amazonaws.com")
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))