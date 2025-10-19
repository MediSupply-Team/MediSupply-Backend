from flask import Flask
from dotenv import load_dotenv
from .config import Config
from .services.cliente_client import ClienteServiceClient
from .routes.health import bp as health_bp
from .routes.client import bp as client_bp
from .routes.orders import bp as orders_bp
from flasgger import Swagger

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    # ===== SWAGGER (solo 2 líneas) =====
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
        "specs_route": "/docs"  # Swagger UI en /docs
    }
    Swagger(app, config=swagger_config)

    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(client_bp)  # Rutas de cliente
    app.register_blueprint(orders_bp)

    # Inicializar cliente de cliente-service
    app.extensions["cliente"] = ClienteServiceClient(
        base_url=app.config["CLIENTE_SERVICE_URL"],
        timeout=app.config["HTTP_TIMEOUT"]
    )
    
    return app