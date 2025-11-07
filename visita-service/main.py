from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Request, BackgroundTasks
from fastapi.responses import Response
from sqlmodel import Session, select
from database import get_session, init_db
from models import Visita, Hallazgo, EstadoVisita, VideoAnalysis
from datetime import datetime
from typing import List, Optional
import storage
import os
from video_analysis_service import video_analysis_service

# Configurar FastAPI sin límites de body size
app = FastAPI(
    title="Visita Service", 
    version="2.0.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Configurar límite máximo de upload
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB en bytes

# Middleware para logging y validación de tamaño
@app.middleware("http")
async def log_and_validate_request(request: Request, call_next):
    """Log requests y validar tamaño de body"""
    # Log del request
    print(f"📥 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    # Si es POST con archivos, verificar content-length
    if request.method == "POST" and "/api/visitas" in request.url.path:
        content_length = request.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            print(f"📦 Content-Length: {size_mb:.2f} MB")
            
            if int(content_length) > MAX_UPLOAD_SIZE:
                return Response(
                    content=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024*1024)}MB",
                    status_code=413,
                    headers={"X-Error": "CustomSizeLimit"}
                )
    
    try:
        response = await call_next(request)
        print(f"📤 Response: {response.status_code}")
        return response
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

# El almacenamiento se configura automáticamente en storage.py

@app.on_event("startup")
def on_startup():
    """Inicializa la base de datos al arrancar"""
    init_db()

# ============================================================
# FUNCIONES AUXILIARES PARA ANÁLISIS DE VIDEO
# ============================================================

async def process_video_analysis(video_analysis_id: int, video_url: str, session: Session):
    """
    Procesa el análisis de video en background
    
    Args:
        video_analysis_id: ID del registro de VideoAnalysis
        video_url: URL del video a analizar
        session: Sesión de base de datos
    """
    from database import engine
    
    try:
        # Crear nueva sesión para el background task
        with Session(engine) as bg_session:
            video_analysis = bg_session.get(VideoAnalysis, video_analysis_id)
            if not video_analysis:
                print(f"❌ VideoAnalysis {video_analysis_id} no encontrado")
                return
            
            # Actualizar estado
            video_analysis.status = "processing"
            bg_session.add(video_analysis)
            bg_session.commit()
            
            print(f"🎬 Iniciando análisis de video {video_analysis_id}: {video_url}")
            
            # Realizar análisis
            result = await video_analysis_service.analyze_video_from_url(video_url)
            
            # Actualizar con resultados
            video_analysis.summary = result.get("summary", "")
            video_analysis.tags = result.get("tags", [])
            video_analysis.recommendations = result.get("recommendations", [])
            video_analysis.status = "completed"
            video_analysis.completed_at = datetime.utcnow()
            
            bg_session.add(video_analysis)
            bg_session.commit()
            
            print(f"✅ Análisis de video {video_analysis_id} completado")
            
    except Exception as e:
        print(f"❌ Error en análisis de video {video_analysis_id}: {str(e)}")
        
        # Actualizar con error
        with Session(engine) as error_session:
            video_analysis = error_session.get(VideoAnalysis, video_analysis_id)
            if video_analysis:
                video_analysis.status = "failed"
                video_analysis.error_message = str(e)
                video_analysis.completed_at = datetime.utcnow()
                error_session.add(video_analysis)
                error_session.commit()

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"ok": True, "service": "visita-service"}

# ============================================================
# ENDPOINTS DE VISITAS
# ============================================================

@app.post("/api/visitas", response_model=dict)
async def crear_visita(
    vendedor_id: int = Form(...),
    cliente_id: int = Form(...),
    nombre_contacto: str = Form(...),
    observaciones: Optional[str] = Form(None),
    estado: EstadoVisita = Form(EstadoVisita.PENDIENTE),
    fotos: Optional[List[UploadFile]] = File(None),
    videos: Optional[List[UploadFile]] = File(None),
    session: Session = Depends(get_session)
):
    """
    Crear una nueva visita a un cliente con fotos, videos y observaciones.
    Los videos se guardan en S3 pero NO se analizan automáticamente.
    Use POST /api/visitas/{visita_id}/analyze para procesar los videos con Gemini.
    
    - **vendedor_id**: ID del vendedor que realiza la visita
    - **cliente_id**: ID del cliente visitado
    - **nombre_contacto**: Nombre de la persona de contacto
    - **observaciones**: Texto con observaciones generales de la visita
    - **estado**: Estado de la visita (exitosa, pendiente, cancelada)
    - **fotos**: Lista de archivos de fotos (jpg, jpeg, png, gif)
    - **videos**: Lista de archivos de videos (mp4, avi, mov)
    """
    # 1. Crear la visita
    visita = Visita(
        vendedor_id=vendedor_id,
        cliente_id=cliente_id,
        nombre_contacto=nombre_contacto,
        observaciones=observaciones,
        estado=estado
    )
    session.add(visita)
    session.commit()
    session.refresh(visita)
    
    hallazgos_creados = []
    video_analyses_creados = []
    
    # 2. Procesar fotos si existen
    if fotos:
        for foto in fotos:
            if foto.filename:  # Verificar que no sea archivo vacío
                extension = foto.filename.split(".")[-1].lower()
                if extension not in ["jpg", "jpeg", "png", "gif"]:
                    # Eliminar la visita creada si hay error
                    session.delete(visita)
                    session.commit()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Formato de foto no válido: {foto.filename}. Permitidos: jpg, jpeg, png, gif"
                    )
                
                # Guardar archivo usando módulo storage
                filename = f"visita_{visita.id}_{datetime.utcnow().timestamp()}.{extension}"
                file_content = await foto.read()
                file_path = await storage.save_file(file_content, filename)
                
                # Crear hallazgo
                hallazgo = Hallazgo(
                    visita_id=visita.id,
                    tipo="foto",
                    contenido=file_path,
                    descripcion=f"Foto: {foto.filename}"
                )
                session.add(hallazgo)
                hallazgos_creados.append(hallazgo)
    
    # 3. Procesar videos si existen
    if videos:
        for video in videos:
            if video.filename:  # Verificar que no sea archivo vacío
                extension = video.filename.split(".")[-1].lower()
                if extension not in ["mp4", "avi", "mov"]:
                    # Eliminar visita y archivos subidos si hay error
                    for h in hallazgos_creados:
                        await storage.delete_file(h.contenido)
                    session.delete(visita)
                    session.commit()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Formato de video no válido: {video.filename}. Permitidos: mp4, avi, mov"
                    )
                
                # Guardar archivo usando módulo storage
                filename = f"visita_{visita.id}_{datetime.utcnow().timestamp()}.{extension}"
                file_content = await video.read()
                file_path = await storage.save_file(file_content, filename)
                
                # Crear hallazgo
                hallazgo = Hallazgo(
                    visita_id=visita.id,
                    tipo="video",
                    contenido=file_path,
                    descripcion=f"Video: {video.filename}"
                )
                session.add(hallazgo)
                hallazgos_creados.append(hallazgo)
    
    # 4. Guardar todos los hallazgos
    session.commit()
    
    # 5. Preparar respuesta
    hallazgos_response = [
        {
            "id": h.id,
            "tipo": h.tipo,
            "descripcion": h.descripcion,
            "url_descarga": f"/api/hallazgos/{h.id}/archivo"
        }
        for h in hallazgos_creados
    ]
    
    return {
        "id": visita.id,
        "vendedor_id": visita.vendedor_id,
        "cliente_id": visita.cliente_id,
        "nombre_contacto": visita.nombre_contacto,
        "observaciones": visita.observaciones,
        "estado": visita.estado,
        "fecha_visita": visita.fecha_visita.isoformat(),
        "created_at": visita.created_at.isoformat(),
        "hallazgos": hallazgos_response,
        "total_fotos": len([h for h in hallazgos_creados if h.tipo == "foto"]),
        "total_videos": len([h for h in hallazgos_creados if h.tipo == "video"])
    }

@app.get("/api/visitas", response_model=List[dict])
def listar_visitas(
    vendedor_id: Optional[int] = Query(None),
    cliente_id: Optional[int] = Query(None),
    estado: Optional[EstadoVisita] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Listar visitas con filtros opcionales.
    """
    query = select(Visita)
    
    if vendedor_id:
        query = query.where(Visita.vendedor_id == vendedor_id)
    if cliente_id:
        query = query.where(Visita.cliente_id == cliente_id)
    if estado:
        query = query.where(Visita.estado == estado)
    
    visitas = session.exec(query).all()
    
    return [
        {
            "id": v.id,
            "vendedor_id": v.vendedor_id,
            "cliente_id": v.cliente_id,
            "nombre_contacto": v.nombre_contacto,
            "observaciones": v.observaciones,
            "estado": v.estado,
            "fecha_visita": v.fecha_visita.isoformat(),
            "created_at": v.created_at.isoformat(),
            "cantidad_hallazgos": len(v.hallazgos) if v.hallazgos else 0
        }
        for v in visitas
    ]

@app.get("/api/visitas/{visita_id}", response_model=dict)
def obtener_visita(
    visita_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener detalle completo de una visita con sus hallazgos y análisis de video.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    hallazgos = [
        {
            "id": h.id,
            "tipo": h.tipo,
            "contenido": h.contenido,
            "descripcion": h.descripcion,
            "created_at": h.created_at.isoformat()
        }
        for h in visita.hallazgos
    ]
    
    # Incluir análisis de video si existen
    video_analyses = []
    if hasattr(visita, 'video_analyses') and visita.video_analyses:
        video_analyses = [
            {
                "id": va.id,
                "video_url": va.video_url,
                "status": va.status,
                "summary": va.summary if va.status == "completed" else None,
                "tags": va.tags if va.status == "completed" else None,
                "recommendations": va.recommendations if va.status == "completed" else None,
                "error_message": va.error_message if va.status == "failed" else None,
                "created_at": va.created_at.isoformat(),
                "completed_at": va.completed_at.isoformat() if va.completed_at else None
            }
            for va in visita.video_analyses
        ]
    
    return {
        "id": visita.id,
        "vendedor_id": visita.vendedor_id,
        "cliente_id": visita.cliente_id,
        "nombre_contacto": visita.nombre_contacto,
        "observaciones": visita.observaciones,
        "estado": visita.estado,
        "fecha_visita": visita.fecha_visita.isoformat(),
        "created_at": visita.created_at.isoformat(),
        "hallazgos": hallazgos,
        "video_analyses": video_analyses
    }

@app.patch("/api/visitas/{visita_id}/estado")
def actualizar_estado_visita(
    visita_id: int,
    estado: EstadoVisita = Form(...),
    session: Session = Depends(get_session)
):
    """
    Actualizar el estado de una visita.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    visita.estado = estado
    visita.updated_at = datetime.utcnow()
    session.add(visita)
    session.commit()
    session.refresh(visita)
    
    return {
        "id": visita.id,
        "estado": visita.estado,
        "updated_at": visita.updated_at.isoformat()
    }

# ============================================================
# ENDPOINTS DE HALLAZGOS (FOTOS/VIDEOS/TEXTOS)
# ============================================================

@app.post("/api/visitas/{visita_id}/hallazgos/texto")
def agregar_hallazgo_texto(
    visita_id: int,
    contenido: str = Form(...),
    descripcion: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """
    Agregar un hallazgo de tipo texto a una visita.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    hallazgo = Hallazgo(
        visita_id=visita_id,
        tipo="texto",
        contenido=contenido,
        descripcion=descripcion
    )
    session.add(hallazgo)
    session.commit()
    session.refresh(hallazgo)
    
    return {
        "id": hallazgo.id,
        "visita_id": hallazgo.visita_id,
        "tipo": hallazgo.tipo,
        "contenido": hallazgo.contenido,
        "descripcion": hallazgo.descripcion,
        "created_at": hallazgo.created_at.isoformat()
    }

@app.post("/api/visitas/{visita_id}/hallazgos/archivo")
async def agregar_hallazgo_archivo(
    visita_id: int,
    archivo: UploadFile = File(...),
    tipo: str = Form(...),  # "foto" o "video"
    descripcion: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """
    Agregar un hallazgo de tipo foto o video a una visita.
    Soporta: jpg, jpeg, png, gif (fotos) y mp4, avi, mov (videos)
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    # Validar tipo
    if tipo not in ["foto", "video"]:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'foto' o 'video'")
    
    # Validar extensión
    extension = archivo.filename.split(".")[-1].lower()
    if tipo == "foto" and extension not in ["jpg", "jpeg", "png", "gif"]:
        raise HTTPException(status_code=400, detail="Formato de foto no válido")
    if tipo == "video" and extension not in ["mp4", "avi", "mov"]:
        raise HTTPException(status_code=400, detail="Formato de video no válido")
    
    # Guardar archivo
    filename = f"visita_{visita_id}_{datetime.utcnow().timestamp()}.{extension}"
    file_content = await archivo.read()
    file_path = await storage.save_file(file_content, filename)
    
    # Crear hallazgo
    hallazgo = Hallazgo(
        visita_id=visita_id,
        tipo=tipo,
        contenido=file_path,
        descripcion=descripcion
    )
    session.add(hallazgo)
    session.commit()
    session.refresh(hallazgo)
    
    return {
        "id": hallazgo.id,
        "visita_id": hallazgo.visita_id,
        "tipo": hallazgo.tipo,
        "contenido": hallazgo.contenido,
        "descripcion": hallazgo.descripcion,
        "created_at": hallazgo.created_at.isoformat()
    }

@app.get("/api/hallazgos/{hallazgo_id}/archivo")
async def descargar_hallazgo_archivo(
    hallazgo_id: int,
    session: Session = Depends(get_session)
):
    """
    Descargar archivo de un hallazgo (foto o video).
    """
    hallazgo = session.get(Hallazgo, hallazgo_id)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    
    if hallazgo.tipo not in ["foto", "video"]:
        raise HTTPException(status_code=400, detail="Este hallazgo no es un archivo")
    
    if not await storage.file_exists(hallazgo.contenido):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    file_content = await storage.get_file(hallazgo.contenido)
    
    # Determinar content-type basado en la extensión
    content_type = "application/octet-stream"
    if hallazgo.tipo == "foto":
        content_type = "image/jpeg"
    elif hallazgo.tipo == "video":
        content_type = "video/mp4"
    
    return Response(content=file_content, media_type=content_type)

@app.get("/api/visitas/{visita_id}/hallazgos")
def listar_hallazgos(
    visita_id: int,
    session: Session = Depends(get_session)
):
    """
    Listar todos los hallazgos de una visita.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    query = select(Hallazgo).where(Hallazgo.visita_id == visita_id)
    hallazgos = session.exec(query).all()
    
    return [
        {
            "id": h.id,
            "tipo": h.tipo,
            "contenido": h.contenido if h.tipo == "texto" else f"/api/hallazgos/{h.id}/archivo",
            "descripcion": h.descripcion,
            "created_at": h.created_at.isoformat()
        }
        for h in hallazgos
    ]

@app.delete("/api/hallazgos/{hallazgo_id}")
async def eliminar_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session)
):
    """
    Eliminar un hallazgo (y su archivo si existe).
    """
    hallazgo = session.get(Hallazgo, hallazgo_id)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    
    # Eliminar archivo si existe
    if hallazgo.tipo in ["foto", "video"]:
        if await storage.file_exists(hallazgo.contenido):
            await storage.delete_file(hallazgo.contenido)
    
    session.delete(hallazgo)
    session.commit()
    
    return {"message": "Hallazgo eliminado exitosamente"}


# ============================================================
# ENDPOINTS DE ANÁLISIS DE VIDEO CON GEMINI
# ============================================================

@app.post("/api/visitas/{visita_id}/analyze")
async def analizar_videos_visita(
    visita_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Analizar todos los videos de una visita con Gemini AI.
    Procesa todos los videos guardados en la visita y genera recomendaciones.
    
    - **visita_id**: ID de la visita cuyos videos se quieren analizar
    
    Retorna información sobre los análisis iniciados. Use GET /api/visitas/{visita_id}/video-analyses
    para consultar el progreso y resultados.
    """
    # Verificar que la visita existe
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    # Verificar que Gemini esté configurado
    if not video_analysis_service.is_configured():
        raise HTTPException(
            status_code=503, 
            detail="Servicio de análisis de video no disponible. Configure GEMINI_API_KEY."
        )
    
    # Obtener todos los hallazgos de tipo video
    query = select(Hallazgo).where(
        Hallazgo.visita_id == visita_id,
        Hallazgo.tipo == "video"
    )
    videos = session.exec(query).all()
    
    if not videos:
        raise HTTPException(
            status_code=404, 
            detail="No se encontraron videos en esta visita"
        )
    
    # Crear registros de análisis para cada video
    analyses_creados = []
    for video in videos:
        # Verificar que el archivo existe
        if not await storage.file_exists(video.contenido):
            print(f"⚠️ Video no encontrado: {video.contenido}")
            continue
        
        # Verificar si ya existe un análisis para este video
        existing = session.exec(
            select(VideoAnalysis).where(
                VideoAnalysis.visita_id == visita_id,
                VideoAnalysis.video_url == video.contenido
            )
        ).first()
        
        if existing and existing.status in ["pending", "processing"]:
            # Ya está en proceso
            analyses_creados.append(existing)
            continue
        
        # Crear nuevo análisis
        video_analysis = VideoAnalysis(
            visita_id=visita_id,
            video_url=video.contenido,
            status="pending"
        )
        session.add(video_analysis)
        session.commit()
        session.refresh(video_analysis)
        
        analyses_creados.append(video_analysis)
        
        # Disparar análisis en background
        background_tasks.add_task(
            process_video_analysis,
            video_analysis.id,
            video.contenido,
            session
        )
        print(f"📊 Análisis de video programado para ID {video_analysis.id}")
    
    if not analyses_creados:
        raise HTTPException(
            status_code=404,
            detail="No se pudieron iniciar análisis. Videos no encontrados en almacenamiento."
        )
    
    return {
        "visita_id": visita_id,
        "total_videos": len(videos),
        "analyses_iniciados": len(analyses_creados),
        "analyses": [
            {
                "id": va.id,
                "video_url": va.video_url,
                "status": va.status,
                "created_at": va.created_at.isoformat()
            }
            for va in analyses_creados
        ],
        "message": f"Se iniciaron {len(analyses_creados)} análisis. Use GET /api/visitas/{visita_id}/video-analyses para ver el progreso."
    }


@app.post("/api/video/analyze")
async def analizar_video_manual(
    background_tasks: BackgroundTasks,
    visita_id: int = Form(...),
    video_url: str = Form(...),
    session: Session = Depends(get_session)
):
    """
    DEPRECATED: Use POST /api/visitas/{visita_id}/analyze en su lugar.
    
    Lanzar análisis manual de un video específico ya subido.
    
    - **visita_id**: ID de la visita asociada
    - **video_url**: URL del video en S3 o path local
    """
    # Verificar que la visita existe
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    # Verificar que Gemini esté configurado
    if not video_analysis_service.is_configured():
        raise HTTPException(
            status_code=503, 
            detail="Servicio de análisis de video no disponible. Configure GEMINI_API_KEY."
        )
    
    # Verificar que el archivo existe
    if not await storage.file_exists(video_url):
        raise HTTPException(status_code=404, detail="Video no encontrado")
    
    # Crear registro de análisis
    video_analysis = VideoAnalysis(
        visita_id=visita_id,
        video_url=video_url,
        status="pending"
    )
    session.add(video_analysis)
    session.commit()
    session.refresh(video_analysis)
    
    # Disparar análisis en background
    background_tasks.add_task(
        process_video_analysis,
        video_analysis.id,
        video_url,
        session
    )
    
    return {
        "id": video_analysis.id,
        "visita_id": video_analysis.visita_id,
        "video_url": video_analysis.video_url,
        "status": video_analysis.status,
        "created_at": video_analysis.created_at.isoformat(),
        "message": "Análisis de video iniciado. Use GET /api/video/analysis/{id} para ver el progreso."
    }


@app.get("/api/video/analysis/{analysis_id}")
def obtener_analisis_video(
    analysis_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener resultados de un análisis de video
    
    - **analysis_id**: ID del análisis de video
    """
    video_analysis = session.get(VideoAnalysis, analysis_id)
    if not video_analysis:
        raise HTTPException(status_code=404, detail="Análisis de video no encontrado")
    
    response = {
        "id": video_analysis.id,
        "visita_id": video_analysis.visita_id,
        "video_url": video_analysis.video_url,
        "status": video_analysis.status,
        "created_at": video_analysis.created_at.isoformat(),
    }
    
    # Agregar resultados si está completado
    if video_analysis.status == "completed":
        response.update({
            "summary": video_analysis.summary,
            "tags": video_analysis.tags,
            "recommendations": video_analysis.recommendations,
            "completed_at": video_analysis.completed_at.isoformat() if video_analysis.completed_at else None
        })
    
    # Agregar error si falló
    if video_analysis.status == "failed":
        response.update({
            "error_message": video_analysis.error_message,
            "completed_at": video_analysis.completed_at.isoformat() if video_analysis.completed_at else None
        })
    
    return response


@app.get("/api/visitas/{visita_id}/video-analyses")
def listar_analisis_videos_visita(
    visita_id: int,
    session: Session = Depends(get_session)
):
    """
    Listar todos los análisis de video de una visita
    
    - **visita_id**: ID de la visita
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    query = select(VideoAnalysis).where(VideoAnalysis.visita_id == visita_id)
    analyses = session.exec(query).all()
    
    return [
        {
            "id": va.id,
            "video_url": va.video_url,
            "status": va.status,
            "summary": va.summary if va.status == "completed" else None,
            "tags": va.tags if va.status == "completed" else None,
            "recommendations": va.recommendations if va.status == "completed" else None,
            "error_message": va.error_message if va.status == "failed" else None,
            "created_at": va.created_at.isoformat(),
            "completed_at": va.completed_at.isoformat() if va.completed_at else None
        }
        for va in analyses
    ]


@app.delete("/api/video/analysis/{analysis_id}")
def eliminar_analisis_video(
    analysis_id: int,
    session: Session = Depends(get_session)
):
    """
    Eliminar un registro de análisis de video
    
    - **analysis_id**: ID del análisis de video
    """
    video_analysis = session.get(VideoAnalysis, analysis_id)
    if not video_analysis:
        raise HTTPException(status_code=404, detail="Análisis de video no encontrado")
    
    session.delete(video_analysis)
    session.commit()
    
    return {"message": "Análisis de video eliminado exitosamente"}


@app.get("/api/video/service-status")
def estado_servicio_video():
    """
    Verificar el estado del servicio de análisis de video
    """
    is_configured = video_analysis_service.is_configured()
    
    return {
        "service": "video-analysis",
        "status": "available" if is_configured else "unavailable",
        "gemini_configured": is_configured,
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "message": "Servicio disponible" if is_configured else "Configure GEMINI_API_KEY para habilitar el servicio"
    }

