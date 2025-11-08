# Guía de Uso - Colección Postman

## 📦 Importar la Colección

1. Abrir Postman
2. Click en **Import**
3. Seleccionar los archivos:
   - `Visita-Service.postman_collection.json` (colección de endpoints)
   - `Visita-Service.postman_environment.json` (variables de entorno)

## 🚀 Configuración Inicial

### 1. Seleccionar el Entorno
En la esquina superior derecha de Postman, seleccionar el entorno **"Visita Service - Local"**

### 2. Verificar Variables
- `base_url`: http://localhost:8003 (cambiar si usas otro puerto)
- `vendedor_id`: 1
- `cliente_id`: 100
- `visita_id`: 1

## 📋 Endpoints Disponibles

### 🏥 Health & Status
- **Health Check**: Verificar que el servicio está activo
- **Video Service Status**: Verificar si Gemini está configurado

### 📝 Visitas
- **Crear Visita (sin archivos)**: Crear visita básica
- **Crear Visita con Fotos y Videos**: Crear visita con multimedia + análisis automático
- **Listar Todas las Visitas**: Ver todas las visitas
- **Listar Visitas con Filtros**: Filtrar por vendedor, cliente o estado
- **Obtener Visita por ID**: Ver detalle completo de una visita
- **Actualizar Estado**: Cambiar estado de visita

### 📸 Hallazgos
- **Agregar Hallazgo de Texto**: Agregar observación textual
- **Subir Foto como Hallazgo**: Agregar foto (jpg, png, gif)
- **Subir Video como Hallazgo**: Agregar video (mp4, avi, mov)
- **Listar Hallazgos**: Ver todos los hallazgos de una visita
- **Descargar Archivo**: Descargar foto o video
- **Eliminar Hallazgo**: Eliminar hallazgo y su archivo

### 🎬 Análisis de Video (Gemini AI)
- **Analizar Video Manualmente**: Lanzar análisis de un video específico
- **Obtener Resultado de Análisis**: Ver resumen, tags y recomendaciones
- **Listar Análisis de una Visita**: Ver todos los análisis de videos
- **Eliminar Análisis**: Eliminar registro de análisis

## 🎯 Flujo de Prueba Recomendado

### Prueba Básica (sin Gemini)

```
1. Health Check
   └─> Verificar que el servicio responde

2. Crear Visita (sin archivos)
   └─> Anotar el ID de la visita creada

3. Agregar Hallazgo de Texto
   └─> Usar el ID de la visita anterior

4. Listar Visitas
   └─> Ver la visita creada

5. Obtener Visita por ID
   └─> Ver detalle completo
```

### Prueba Completa (con Gemini)

```
1. Video Service Status
   └─> Verificar que Gemini está configurado

2. Crear Visita con Fotos y Videos
   ├─> Seleccionar archivos de foto
   ├─> Seleccionar archivos de video
   ├─> auto_analyze_videos = true
   └─> Anotar el ID de la visita y el ID del video_analysis

3. Obtener Resultado de Análisis
   ├─> Usar el ID del video_analysis
   ├─> Si status = "pending" o "processing", esperar y consultar de nuevo
   └─> Si status = "completed", ver summary, tags y recommendations

4. Listar Análisis de una Visita
   └─> Ver todos los análisis de la visita

5. Obtener Visita por ID
   └─> Ver visita completa con hallazgos y análisis
```

## 🔧 Configuración Avanzada

### Usar con Docker

Si el servicio está en Docker:
```
base_url = http://localhost:8003
```

### Usar con AWS/Cloud

Si está desplegado en la nube:
```
base_url = https://api.example.com
```

## 📝 Notas Importantes

### Archivos
- **Fotos**: Máximo recomendado 10MB cada una
- **Videos**: Máximo recomendado 100MB cada uno
- Formatos soportados:
  - Fotos: jpg, jpeg, png, gif
  - Videos: mp4, avi, mov

### Análisis de Video
- El análisis se ejecuta en **background** (asíncrono)
- Consultar el estado con `GET /api/video/analysis/{id}`
- Estados posibles: `pending`, `processing`, `completed`, `failed`
- Tiempo estimado: 30 segundos a 5 minutos según tamaño del video

### Variables de Entorno Necesarias
Para usar el análisis de video, configurar en el servidor:
```env
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-1.5-flash
```

## 🐛 Troubleshooting

### Error 503 en Video Service
**Problema**: Gemini no está configurado  
**Solución**: Configurar `GEMINI_API_KEY` en las variables de entorno del servidor

### Error 413 - File too large
**Problema**: Archivo muy grande  
**Solución**: Reducir tamaño del video (máximo 100MB)

### Status "failed" en análisis
**Problema**: Error procesando video  
**Solución**: Ver `error_message` en la respuesta y verificar:
- API key válida
- Video en formato correcto
- Video no corrupto

## 📚 Documentación Adicional

- [README.md](./README.md) - Documentación general del servicio
- [VIDEO_ANALYSIS.md](./VIDEO_ANALYSIS.md) - Documentación detallada de análisis de video
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## 💡 Ejemplos con cURL

Si prefieres usar cURL en lugar de Postman:

```bash
# Health check
curl http://localhost:8003/health

# Crear visita con video
curl -X POST http://localhost:8003/api/visitas \
  -F "vendedor_id=1" \
  -F "cliente_id=100" \
  -F "nombre_contacto=Dr. Juan Pérez" \
  -F "videos=@video.mp4" \
  -F "auto_analyze_videos=true"

# Consultar análisis
curl http://localhost:8003/api/video/analysis/1
```
