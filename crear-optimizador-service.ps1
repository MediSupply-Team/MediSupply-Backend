# Script para crear optimizador-rutas-service
# Ejecutar: .\crear-optimizador-service.ps1

$serviceName = "optimizador-rutas-service"

Write-Host "🚀 Creando estructura de $serviceName..." -ForegroundColor Cyan

# Crear estructura de carpetas
Write-Host "📁 Creando carpetas..." -ForegroundColor Yellow
New-Item -Path $serviceName -ItemType Directory -Force | Out-Null
New-Item -Path "$serviceName\config" -ItemType Directory -Force | Out-Null
New-Item -Path "$serviceName\services" -ItemType Directory -Force | Out-Null
New-Item -Path "$serviceName\models" -ItemType Directory -Force | Out-Null
New-Item -Path "$serviceName\controllers" -ItemType Directory -Force | Out-Null

Write-Host "✅ Carpetas creadas" -ForegroundColor Green

# Función auxiliar para crear archivos
function Create-File {
    param(
        [string]$Path,
        [string]$Content
    )
    $Content | Out-File -FilePath $Path -Encoding UTF8 -NoNewline
}

# .env
Write-Host "📝 Creando .env..." -ForegroundColor Yellow
$envContent = @'
# Puerto del servidor
PORT=8001

# OSRM
OSRM_URL=http://osrm-medisupply.duckdns.org:5000

# Mapbox
MAPBOX_ACCESS_TOKEN=pk.eyJ1Ijoi...TU_TOKEN_AQUI

# Ruta Service (opcional)
RUTA_SERVICE_URL=http://localhost:8000

# Configuración general
ENVIRONMENT=development
LOG_LEVEL=INFO
'@
Create-File -Path "$serviceName\.env" -Content $envContent

# .gitignore
Write-Host "📝 Creando .gitignore..." -ForegroundColor Yellow
$gitignoreContent = @'
__pycache__/
*.py[cod]
*$py.class
*.so
.env
.venv
venv/
ENV/
.DS_Store
*.log
.pytest_cache/
.coverage
htmlcov/
'@
Create-File -Path "$serviceName\.gitignore" -Content $gitignoreContent

# requirements.txt
Write-Host "📝 Creando requirements.txt..." -ForegroundColor Yellow
$requirementsContent = @'
fastapi==0.104.1
uvicorn[standard]==0.24.0
requests==2.31.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
'@
Create-File -Path "$serviceName\requirements.txt" -Content $requirementsContent

# Dockerfile
Write-Host "📝 Creando Dockerfile..." -ForegroundColor Yellow
$dockerfileContent = @'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'@
Create-File -Path "$serviceName\Dockerfile" -Content $dockerfileContent

# docker-compose.yml
Write-Host "📝 Creando docker-compose.yml..." -ForegroundColor Yellow
$dockerComposeContent = @'
version: "3.9"

services:
  optimizador:
    build: .
    container_name: optimizador-rutas
    restart: always
    env_file: .env
    ports:
      - "8001:8000"
    volumes:
      - .:/app
'@
Create-File -Path "$serviceName\docker-compose.yml" -Content $dockerComposeContent

# config/settings.py
Write-Host "📝 Creando config/settings.py..." -ForegroundColor Yellow
$settingsContent = @'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    port: int = 8001
    environment: str = "development"
    log_level: str = "INFO"
    
    # OSRM
    osrm_url: str
    
    # Mapbox
    mapbox_access_token: str
    
    # Ruta Service
    ruta_service_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
'@
Create-File -Path "$serviceName\config\settings.py" -Content $settingsContent

# services/__init__.py
Write-Host "📝 Creando services/__init__.py..." -ForegroundColor Yellow
Create-File -Path "$serviceName\services\__init__.py" -Content "# Services package"

# services/geocoder_service.py
Write-Host "📝 Creando services/geocoder_service.py..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://gist.githubusercontent.com/anonymous/raw/geocoder_service.py" -OutFile "$serviceName\services\geocoder_service.py" -ErrorAction SilentlyContinue

# Si falla la descarga, crear el archivo localmente
if (-not (Test-Path "$serviceName\services\geocoder_service.py")) {
    $geocoderContent = @'
import requests
from config.settings import settings
from typing import List

class GeocoderService:
    def __init__(self):
        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
        self.access_token = settings.mapbox_access_token
    
    def geocodificar(self, direccion: str, ciudad: str = "Bogota") -> dict:
        try:
            query = f"{direccion}, {ciudad}, Colombia"
            url = f"{self.base_url}/{query}.json"