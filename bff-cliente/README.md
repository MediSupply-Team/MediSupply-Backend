# BFF-CLIENTE

Backend For Frontend para el módulo de clientes de MediSupply.

## Descripción 

Este BFF actúa como proxy hacia el cliente-service, proporcionando endpoints optimizados para las necesidades del frontend del módulo de clientes.

## Endpoints

- `GET /api/v1/client/` - Listar clientes con filtros
- `GET /api/v1/client/search` - Buscar cliente por NIT/nombre/código
- `GET /api/v1/client/{cliente_id}/historico` - Obtener histórico del cliente
- `GET /api/v1/client/health` - Health check del servicio
- `GET /api/v1/client/metrics` - Métricas del servicio
- `GET /health` - Health check general

## Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en desarrollo
flask run --host=0.0.0.0 --port=8001

# Ejecutar con gunicorn
gunicorn wsgi:app --bind 0.0.0.0:8001
```

## Variables de Entorno

- `CLIENTE_SERVICE_URL`: URL del cliente-service
- `FLASK_ENV`: Entorno (development/production)