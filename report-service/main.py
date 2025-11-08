from fastapi import FastAPI
from routers.reports import router as reports_router
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="MediSupply Reports Service",
    description="Servicio de generación de reportes basado en datos reales del servicio Orders",
    version="2.0.0"
)

@app.get("/health")
def health(): 
    return {"ok": True, "service": "reports"}

# Monta el router de reportes 
app.include_router(reports_router)