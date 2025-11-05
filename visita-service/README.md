# Visita Service

Servicio para gestionar visitas de vendedores a clientes con registro de hallazgos técnicos/clínicos.

## Funcionalidades

- ✅ Registrar visitas con nombre de contacto y observaciones
- ✅ Estados de visita: `exitosa`, `pendiente`, `cancelada`
- ✅ Subir fotos (jpg, png, gif)
- ✅ Subir videos (mp4, avi, mov)
- ✅ Agregar hallazgos de texto
- ✅ Listar y filtrar visitas
- ✅ Descargar archivos adjuntos 

## Iniciar en Local

### Opción 1: Con Docker Compose (Recomendado)

```bash
cd visita-service
docker-compose up --build
```

El servicio estará disponible en: `http://localhost:8003`

**✨ El contenedor carga automáticamente datos de ejemplo al iniciar** (3 visitas y 3 hallazgos)

### Opción 2: Directamente con Python

```bash
cd visita-service

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
uvicorn main:app --reload --port 8003
```

## Endpoints Principales

### Health Check
```bash
GET http://localhost:8003/health
```

### Crear Visita Completa (Todo en un POST)
```bash
POST http://localhost:8003/api/visitas

# Envía en un solo request:
# - Datos básicos (vendedor_id, cliente_id, nombre_contacto)
# - Observaciones de la visita
# - Estado (exitosa, pendiente, cancelada)
# - Fotos (múltiples archivos jpg, png, gif)
# - Videos (múltiples archivos mp4, avi, mov)

# Ejemplo con curl:
curl -X POST "http://localhost:8003/api/visitas" \
  -F "vendedor_id=5" \
  -F "cliente_id=100" \
  -F "nombre_contacto=Dr. Pedro Martínez" \
  -F "observaciones=El cliente necesita actualizar equipo..." \
  -F "estado=exitosa" \
  -F "fotos=@foto1.jpg" \
  -F "fotos=@foto2.jpg" \
  -F "videos=@video1.mp4"

# Respuesta:
{
  "id": 6,
  "vendedor_id": 5,
  "cliente_id": 100,
  "nombre_contacto": "Dr. Pedro Martínez",
  "observaciones": "...",
  "estado": "exitosa",
  "hallazgos": [
    {"id": 9, "tipo": "foto", "url_descarga": "/api/hallazgos/9/archivo"},
    {"id": 10, "tipo": "foto", "url_descarga": "/api/hallazgos/10/archivo"},
    {"id": 11, "tipo": "video", "url_descarga": "/api/hallazgos/11/archivo"}
  ],
  "total_fotos": 2,
  "total_videos": 1
}
Content-Type: multipart/form-data

vendedor_id=1
cliente_id=10
nombre_contacto="Dr. Juan Pérez"
observaciones="Necesita equipo de ultrasonido"
estado=pendiente
```

### Listar Visitas
```bash
GET http://localhost:8003/api/visitas?vendedor_id=1&estado=pendiente
```

### Obtener Visita Completa
```bash
GET http://localhost:8003/api/visitas/1
```

### Agregar Hallazgo de Texto
```bash
POST http://localhost:8003/api/visitas/1/hallazgos/texto
Content-Type: multipart/form-data

contenido="Equipo de rayos X presenta falla en el generador"
descripcion="Hallazgo crítico"
```

### Subir Foto
```bash
POST http://localhost:8003/api/visitas/1/hallazgos/archivo
Content-Type: multipart/form-data

archivo=@/path/to/photo.jpg
tipo=foto
descripcion="Foto del equipo"
```

### Subir Video
```bash
POST http://localhost:8003/api/visitas/1/hallazgos/archivo
Content-Type: multipart/form-data

archivo=@/path/to/video.mp4
tipo=video
descripcion="Video del procedimiento"
```

### Actualizar Estado
```bash
PATCH http://localhost:8003/api/visitas/1/estado
Content-Type: multipart/form-data

estado=exitosa
```

### Listar Hallazgos de una Visita 
```bash
GET http://localhost:8003/api/visitas/1/hallazgos
```

### Descargar Archivo de Hallazgo
```bash
GET http://localhost:8003/api/hallazgos/1/archivo
```

## Probar con cURL

```bash
# Health check
curl http://localhost:8003/health

# Crear visita
curl -X POST http://localhost:8003/api/visitas \
  -F "vendedor_id=1" \
  -F "cliente_id=10" \
  -F "nombre_contacto=Dr. Juan Pérez" \
  -F "observaciones=Necesita equipo nuevo" \
  -F "estado=pendiente"

# Subir foto
curl -X POST http://localhost:8003/api/visitas/1/hallazgos/archivo \
  -F "archivo=@foto.jpg" \
  -F "tipo=foto" \
  -F "descripcion=Foto del equipo dañado"

# Agregar texto
curl -X POST http://localhost:8003/api/visitas/1/hallazgos/texto \
  -F "contenido=Equipo presenta falla eléctrica" \
  -F "descripcion=Observación técnica"

# Listar visitas
curl "http://localhost:8003/api/visitas?vendedor_id=1"

# Obtener visita completa
curl http://localhost:8003/api/visitas/1

# Actualizar estado
curl -X PATCH http://localhost:8003/api/visitas/1/estado \
  -F "estado=exitosa"
```

## Estructura de Base de Datos

### Tabla `visitas`
- `id`: Primary key
- `vendedor_id`: ID del vendedor
- `cliente_id`: ID del cliente
- `nombre_contacto`: Nombre del contacto en la visita
- `observaciones`: Observaciones generales
- `estado`: `exitosa` | `pendiente` | `cancelada`
- `fecha_visita`: Fecha y hora de la visita
- `created_at`: Fecha de creación
- `updated_at`: Última actualización

### Tabla `hallazgos`
- `id`: Primary key
- `visita_id`: Foreign key a visitas
- `tipo`: `foto` | `video` | `texto`
- `contenido`: Ruta del archivo o texto
- `descripcion`: Descripción opcional
- `created_at`: Fecha de creación

## Base de Datos

Por defecto usa SQLite (`visitas.db`) para desarrollo local. Los archivos subidos se guardan en `./uploads/`.

Para usar PostgreSQL, cambiar `DATABASE_URL` en `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/visitas_db
```

## Documentación Interactiva

Una vez iniciado el servicio, visita:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc
