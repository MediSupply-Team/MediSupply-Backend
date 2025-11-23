from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from .config import Config
from .services.sqs_client import SQSService
from .routes.health import bp as health_bp
from .routes.orders import bp as orders_bp
from .routes.rutas import bp as rutas_bp
from flasgger import Swagger
from .routes.catalog import bp as catalog_bp
from .routes.inventory import bp as inventory_bp
from .routes.route_optimizer import bp as route_optimizer_bp
from .routes.bodega import bp as bodega_bp

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configurar CORS - solo con origins="*" para evitar duplicados
    CORS(app, 
         origins="*",
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
         expose_headers=["Content-Type"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # ===== SWAGGER =====
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    Swagger(app, config=swagger_config)

    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(rutas_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(route_optimizer_bp)
    app.register_blueprint(bodega_bp)

    # Inicializar servicio SQS
    app.extensions["sqs"] = SQSService(
        region_name=app.config["AWS_REGION"],
        queue_url=app.config["SQS_QUEUE_URL"],
        default_group_id=app.config["MESSAGE_GROUP_ID"],
        content_based_dedup=app.config["CONTENT_BASED_DEDUP"]
    )
    
    return app