from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/system/version")
async def get_system_version():
    return {
        "platform": "MediSupply",
        "productVersion": "1.0.0",
        "buildDate": datetime.now().isoformat(),
        "gitCommit": "latest",
        "web": {"version": "1.0.0"},
        "mobile": {
            "ventas": "0.1.0",
            "clientes": "0.1.0"
        },
        "services": [
            {"name": "auth", "version": "1.0.0"},
            {"name": "orders", "version": "1.0.0"},
            {"name": "catalogo", "version": "1.0.0"},
            {"name": "cliente", "version": "1.0.0"},
            {"name": "rutas", "version": "1.0.0"},
            {"name": "reports", "version": "1.0.0"},
            {"name": "visita", "version": "1.0.0"},
            {"name": "optimizer", "version": "1.0.0"},
            {"name": "consumer", "version": "1.0.0"},
            {"name": "bff_venta", "version": "1.0.0"},
            {"name": "bff_cliente", "version": "1.0.0"}
        ],
        "infrastructure": {
            "cloud": "AWS",
            "region": "us-east-1",
            "orchestration": "ECS Fargate",
            "database": "RDS PostgreSQL"
        }
    }